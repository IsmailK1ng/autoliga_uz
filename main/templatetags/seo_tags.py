# main/templatetags/seo_tags.py

from django import template
from django.conf import settings
from django.urls import reverse, NoReverseMatch
from django.utils import translation
from django.utils.http import urlencode
from django.utils.safestring import mark_safe

register = template.Library()

# Pages backed by a translated object: (context variable, field that must be
# filled for the page to exist in a language). Other pages have their ru/en
# text in the templates and exist in every language.
TRANSLATED_OBJECTS = {
    'product_detail': ('product', 'title'),
    'news_detail': ('news', 'title'),
    'dealer_detail': ('dealer', 'name'),
    'brand': ('brand', 'name'),
}


def _canonical_query(request, url_name):
    """Brand listings: ?category=<slug> is the one canonical form (?brand= is an
    alias). Every other query parameter (utm_*, fbclid, page, q, ...) is dropped."""
    if url_name == 'products':
        category = request.GET.get('brand') or request.GET.get('category')
        if category:
            return '?' + urlencode({'category': category})
    return ''


def _available_languages(context, request, url_name):
    """Languages in which this page really has content."""
    languages = [code for code, _name in settings.LANGUAGES]
    obj, field = None, None
    if url_name in TRANSLATED_OBJECTS:
        key, field = TRANSLATED_OBJECTS[url_name]
        obj = context.get(key)
    elif url_name == 'products':
        slug = request.GET.get('brand') or request.GET.get('category')
        if slug:
            from main.models import ProductCategory
            obj, field = ProductCategory.objects.filter(slug=slug).first(), 'name'
    if obj is None:
        return languages
    return [lang for lang in languages if str(getattr(obj, f'{field}_{lang}', '') or '').strip()]


@register.simple_tag(takes_context=True)
def hreflang_tags(context):
    """
    <link rel="alternate" hreflang> for the languages this page exists in.

    uz has no prefix, ru/en are /ru/ and /en/; x-default is the uz URL.
    A product, news item, dealer or brand without a translation in a language
    gets no hreflang for that language. Fewer than two languages -> no tags.
    """
    request = context.get('request')
    if not request or not request.resolver_match:
        return ''
    url_name = request.resolver_match.url_name
    if not url_name:
        return ''

    default = settings.LANGUAGE_CODE
    try:
        # Reverse in the default language: gives the unprefixed uz path even on /ru/ and /en/ pages
        with translation.override(default):
            path = reverse(url_name, kwargs=request.resolver_match.kwargs)
    except NoReverseMatch:
        return ''
    path += _canonical_query(request, url_name)

    languages = _available_languages(context, request, url_name)
    if len(languages) < 2:
        return ''

    domain = request.build_absolute_uri('/').rstrip('/')
    tags = []
    for lang in languages:
        prefix = '' if lang == default else f'/{lang}'
        tags.append(f'<link rel="alternate" hreflang="{lang}" href="{domain}{prefix}{path}" />')
    if default in languages:
        tags.append(f'<link rel="alternate" hreflang="x-default" href="{domain}{path}" />')
    return mark_safe('\n    '.join(tags))


@register.simple_tag(takes_context=True)
def canonical_url(context):
    request = context.get('request')
    if not request:
        return ''

    url_name = request.resolver_match.url_name if request.resolver_match else None
    canonical = f"{request.scheme}://{request.get_host()}{request.path}{_canonical_query(request, url_name)}"
    return mark_safe(f'<link rel="canonical" href="{canonical}" />')
