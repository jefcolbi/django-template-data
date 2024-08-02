from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from pathlib import Path
from template_data.models import TemplateData
from template_data.management.commands.add_data import DataMixin
import json


class Command(DataMixin, BaseCommand):
    """Install the theme"""

    def add_arguments(self, parser):
        parser.add_argument("file", type=str, help="The json file where to load the data")

    def handle(self, *args, **options):
        file_name = options['file']

        try:
            with (settings.BASE_DIR / file_name).open() as fp:
                data = json.load(fp)

            for item in data:
                for key, details in item.items():
                    page = details.pop('page')
                    TemplateData.objects.update_or_create(key=key, page=page,
                                                          defaults=details)
                    break

            print(f"restored {file_name}")
        except Exception as e:
            import traceback

            traceback.print_exc()
