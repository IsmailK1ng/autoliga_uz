# seo/inlines.py
"""FAQ inline, shared by PageSEOAdmin (seo.admin) and ProductAdmin (main.admin).
Kept apart from seo.admin, which imports main.admin (mixins): no circular import."""

from modeltranslation.admin import TranslationStackedInline

from seo.models import FAQItem


class FAQItemInline(TranslationStackedInline):
    model = FAQItem
    extra = 0
    fields = ('question', 'answer', 'order', 'is_active')
    ordering = ('order', 'id')
    verbose_name = "Вопрос-ответ"
    verbose_name_plural = "❓ FAQ на странице"


class ProductFAQInline(FAQItemInline):
    verbose_name_plural = "❓ FAQ на странице модели"
