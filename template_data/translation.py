from modeltranslation.translator import translator, TranslationOptions
from .models import TemplateData


class TemplateDataTranslationOptions(TranslationOptions):
    fields = ('value', 'media')


translator.register(TemplateData, TemplateDataTranslationOptions)
