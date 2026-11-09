from modeltranslation.translator import register, TranslationOptions
from seo.models import FAQItem, PageSEO


@register(PageSEO)
class PageSEOTranslationOptions(TranslationOptions):
    fields = ('title', 'description')


@register(FAQItem)
class FAQItemTranslationOptions(TranslationOptions):
    fields = ('question', 'answer')
