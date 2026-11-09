# seo/admin.py

from django import forms
from django.conf import settings
from django.contrib import admin
from django.utils.html import format_html_join
from modeltranslation.admin import TabbedTranslationAdmin
from reversion.admin import VersionAdmin

from main.admin import ContentAdminMixin, CustomReversionMixin
from main.seo import clean
from seo.inlines import FAQItemInline
from seo.models import DESCRIPTION_LENGTH, TITLE_LENGTH, FAQItem, PageSEO, valid_text

LANGUAGES = settings.MODELTRANSLATION_LANGUAGES


class PageSEOForm(forms.ModelForm):
    """Title 30–65 and description 120–160 characters (whitespace collapsed); empty is allowed."""

    class Meta:
        model = PageSEO
        fields = '__all__'

    def clean(self):
        data = super().clean()
        for field, bounds, label in (('title', TITLE_LENGTH, "Заголовок"), ('description', DESCRIPTION_LENGTH, "Описание")):
            for lang in LANGUAGES:
                name = f'{field}_{lang}'
                if name not in data:
                    continue
                value = clean(data[name])
                data[name] = value
                if value and not bounds[0] <= len(value) <= bounds[1]:
                    self.add_error(name, f"{label}: {len(value)} символов, нужно {bounds[0]}–{bounds[1]}.")
        return data


@admin.register(PageSEO)
class PageSEOAdmin(ContentAdminMixin, CustomReversionMixin, VersionAdmin, TabbedTranslationAdmin):
    form = PageSEOForm
    list_display = ['__str__', 'title_status', 'description_status', 'faq_count', 'is_active', 'updated_at']
    list_editable = ['is_active']
    list_filter = ['is_active']
    readonly_fields = ['updated_at']
    history_latest_first = True
    fieldsets = (
        (None, {'fields': ('page_key', 'is_active')}),
        ('Мета-данные', {'fields': ('title', 'description', 'og_image')}),
        ('Служебное', {'fields': ('updated_at',), 'classes': ('collapse',)}),
    )
    inlines = [FAQItemInline]

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('faq_items')

    @staticmethod
    def _status(obj, field, bounds):
        # ✓ used on the site, ✗ filled but ignored (wrong length), — empty
        marks = []
        for lang in LANGUAGES:
            value = clean(getattr(obj, f'{field}_{lang}', ''))
            marks.append((lang, '✓' if valid_text(value, bounds) else '✗' if value else '—'))
        return format_html_join(' ', '{} {}', marks)

    @admin.display(description="Title uz / ru / en")
    def title_status(self, obj):
        return self._status(obj, 'title', TITLE_LENGTH)

    @admin.display(description="Description uz / ru / en")
    def description_status(self, obj):
        return self._status(obj, 'description', DESCRIPTION_LENGTH)

    @admin.display(description="FAQ")
    def faq_count(self, obj):
        return len(obj.faq_items.all())


class FAQItemForm(forms.ModelForm):
    class Meta:
        model = FAQItem
        fields = '__all__'

    def clean(self):
        data = super().clean()
        if bool(data.get('page')) == bool(data.get('product')):
            raise forms.ValidationError("Выберите ровно одно: страницу или модель.")
        return data


@admin.register(FAQItem)
class FAQItemAdmin(ContentAdminMixin, CustomReversionMixin, VersionAdmin, TabbedTranslationAdmin):
    form = FAQItemForm
    list_display = ['question', 'target_display', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    list_filter = ['is_active', 'page', ('product', admin.RelatedOnlyFieldListFilter)]
    search_fields = ['question']
    autocomplete_fields = ['product']
    history_latest_first = True
    fields = ('page', 'product', 'question', 'answer', 'order', 'is_active')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('page', 'product')

    @admin.display(description="Где показывается")
    def target_display(self, obj):
        return obj.target or "—"
