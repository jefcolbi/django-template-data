import os

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from pathlib import Path

from django.template.backends.django import Template
from django.template.loader import get_template

from template_data.models import TemplateData
from template_data.management.commands.add_data import DataMixin
import json
import re
from lxml import etree
from traceback_with_variables import format_exc, activate_by_import

from importlib import import_module
import inspect
from pathlib import Path
import importlib.util
from template_data.models import TemplateData

from django.conf import settings
from django.contrib.admin.options import ModelAdmin
from django.urls import URLResolver, URLPattern
import logging

logger = logging.getLogger()


def is_modeladmin_view(view):
    """Return True if the view is an admin view."""
    view = inspect.unwrap(view)  # In case this is a decorated view
    self = getattr(view, "__self__", None)
    return self is not None and isinstance(self, ModelAdmin)


def get_all_views(urlpatterns):
    """Given a URLconf, return a set of all view objects."""
    views = set()
    for pattern in urlpatterns:
        if hasattr(pattern, "url_patterns"):
            views |= get_all_views(pattern.url_patterns)
        else:
            if hasattr(pattern.callback, "cls"):
                view = pattern.callback.cls
            elif hasattr(pattern.callback, "view_class"):
                view = pattern.callback.view_class
            else:
                view = pattern.callback
            if not is_modeladmin_view(view):
                views.add((view, pattern.name))
    return views


def get_module_path(module_name):
    """Return the path for a given module name."""
    spec = importlib.util.find_spec(module_name)
    if spec is None:
        raise ImportError(f"Module '{module_name}' not found")
    return Path(spec.origin).resolve()


def is_subpath(path, directory):
    """Return True if path is below directory and isn't within a "venv"."""
    try:
        path.relative_to(directory)
    except ValueError:
        return False
    else:
        # Return True if view isn't under a directory ending in "venv"
        return not any(p.endswith("venv") for p in path.parts)


def get_all_local_views():
    """Return a set of all local views in this project."""
    root_urlconf = import_module(settings.ROOT_URLCONF)
    all_urlpatterns = root_urlconf.urlpatterns
    print(all_urlpatterns)
    try:
        root_directory = settings.ROOT_DIR
    except AttributeError:
        root_directory = Path.cwd()  # Assume we're in the root directory
    return {
        (view, name)
        for view, name in get_all_views(all_urlpatterns)
        if is_subpath(get_module_path(view.__module__), root_directory)
    }


class Command(DataMixin, BaseCommand):
    """Install the theme"""

    rgx_tag_comment = re.compile(r"(?<![=\"])(\{\%[ \w\.'=|]+\%\})")
    rgx_tag_uncomment = re.compile(r"<!-- (\{\%[ \w\.'=|]+\%\}) -->")
    rgx_unindent = re.compile(r"\n    ")
    rgx_bloc_linify = re.compile(r"\n(\{\% block [\w]+ ?\%\})")

    def add_arguments(self, parser):
        parser.add_argument('--views', action='store_true')
        parser.add_argument('--file', action='store')
        parser.add_argument('--pagename', action='store')
        parser.add_argument('--default-lang', action='store', default='fr')

    def handle(self, *args, **options):
        print(options)
        self.default_lang = options['default_lang']
        if options.get('views'):
            return self.handle_views(**options)
        elif options.get('file'):
            return self.handle_single(**options)

    def handle_single(self, *args, **options):
        tpl: Template = get_template(options['file'])
        tpl_path = Path(str(tpl.origin))
        return self.process_template_file(tpl_path, options['pagename'])

    def handle_views(self, *args, **options):
        try:
            all_views = get_all_local_views()
            print("Number of local views:", len(all_views))

            for view, view_name in all_views:
                tpl_name = getattr(view, 'template_name', None)
                if not tpl_name:
                    continue

                print(f"Working on template {tpl_name}")

                tpl: Template = get_template(tpl_name)
                tpl_path = Path(str(tpl.origin))

                if not view_name:
                    raise ValueError(f"The view {view} doesn't have a valid name: {view_name}")

                self.process_template_file(tpl_path, page_name=view_name)

        except Exception as e:
            logger.error(format_exc(e))

    def process_template_file(self, tpl_path:Path, page_name=None,):
        page_name = 'global' if page_name is None else page_name
        try:
            with tpl_path.open() as fp:
                tpl_content = fp.read()

            with (tpl_path.parent / tpl_path.name.replace('.html', '.html.bak')).open('w') as fp:
                fp.write(tpl_content)

            new_content = self.rgx_tag_comment.sub(r"<!-- \1 -->", tpl_content)
            faked_content = f"<fake>\n{new_content}\n</fake>"

            with (tpl_path.parent / tpl_path.name.replace('.html', '.new.html')).open('w') as fp:
                fp.write(faked_content)

            root = etree.fromstring(faked_content)

            for node in root.iter():
                tpl_data_key = node.get('tpl-data-key')
                if tpl_data_key:
                    lang = node.get('tpl-data-lang') or self.default_lang
                    previous_text = node.text
                    node.text = f"{{{{ {tpl_data_key} }}}}"
                    node.attrib.pop('tpl-data-key')
                    try:
                        node.attrib.pop('tpl-data-lang')
                    except:
                        pass

                    defaults = {'value': previous_text}
                    TemplateData.objects.update_or_create(key=tpl_data_key, lang=lang,
                                        page=page_name, defaults=defaults)

            etree.indent(root, space="    ")
            rewritten_content = etree.tostring(root).decode()
            rewritten_content = self.rgx_tag_uncomment.sub(r"\1", rewritten_content)
            rewritten_content = rewritten_content.replace('<fake>', '').replace('</fake>', '').strip()
            rewritten_content = self.rgx_unindent.sub('\n', rewritten_content)
            rewritten_content = self.rgx_bloc_linify.sub(r"\n\n\n\1", rewritten_content)
            # print(rewritten_content)

            with tpl_path.open('w') as fp:
                fp.write(rewritten_content)

            os.remove((tpl_path.parent / tpl_path.name.replace('.html', '.html.bak')))
            os.remove((tpl_path.parent / tpl_path.name.replace('.html', '.new.html')))
            logger.info(f"Finish working on file {tpl_path}")
        except etree.XMLSyntaxError as e:
            logger.error(str(e))
            line = re.search('line (\d+)', str(e)).group(1)
            logger.warning(faked_content.split('\n')[int(line)-1])