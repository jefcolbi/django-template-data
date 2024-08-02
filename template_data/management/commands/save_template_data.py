from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from pathlib import Path
from template_data.models import TemplateData
from template_data.management.commands.add_data import DataMixin
import json


class Command(DataMixin, BaseCommand):
    """Install the theme"""

    def add_arguments(self, parser):
        parser.add_argument("file", type=str, help="The json file where to store the data")
        parser.add_argument('--indent', type=int, default=4, help='The indentation number')

    def handle(self, *args, **options):
        file_name = options['file']
        indent = options.get('indent')

        try:
            data = []

            for tpl_data in TemplateData.objects.all():
                tpl_data_dict = {}
                for k, v in tpl_data.__dict__.items():
                    if k in ['type', 'page', 'inherit_page']:
                        tpl_data_dict[k] = v
                    elif k.startswith('value_') or k.startswith('media_'):
                        tpl_data_dict[k] = v
                print(tpl_data_dict)
                data.append({tpl_data.key: tpl_data_dict})

            with (settings.BASE_DIR / file_name).open('w') as fp:
                json.dump(data, fp, indent=indent)

            print(f"saved data to {file_name}")
        except Exception as e:
            import traceback

            traceback.print_exc()
