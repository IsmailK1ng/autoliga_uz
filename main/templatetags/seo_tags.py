# main/templatetags/seo_tags.py

from django import template
from django.conf import settings
from django.urls import reverse, NoReverseMatch
from django.utils import translation
from django.utils.safestring import mark_safe

from main import structured_data as sd

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


def _canonical_base(request, url_name):
    """Unprefixed (default-language) path of the canonical form of this page.

    Query parameters (utm_*, fbclid, page, q, ...) are dropped. A catalog search
    inside a brand (/products/?category=<slug>&q=..., noindex) points to the
    brand page /brand/<slug>/ (task 8); without q those URLs 301 there anyway.
    """
    with translation.override(settings.LANGUAGE_CODE):
        if url_name == 'products':
            category = request.GET.get('brand') or request.GET.get('category')
            if category:
                return reverse('brand', kwargs={'slug': category})
        return reverse(url_name, kwargs=request.resolver_match.kwargs)


def _language_prefix(lang):
    return '' if lang == settings.LANGUAGE_CODE else f'/{lang}'


def _available_languages(context, request, url_name):
    """Languages in which this page really has content."""
    languages = [code for code, _name in settings.LANGUAGES]
    # A view can decide itself (news: title and body text in that language)
    if context.get('hreflang_languages') is not None:
        return [lang for lang in languages if lang in context['hreflang_languages']]
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
        # Default-language path: unprefixed uz URL even on /ru/ and /en/ pages
        path = _canonical_base(request, url_name)
    except NoReverseMatch:
        return ''

    languages = _available_languages(context, request, url_name)
    if len(languages) < 2:
        return ''

    domain = request.build_absolute_uri('/').rstrip('/')
    tags = []
    for lang in languages:
        tags.append(f'<link rel="alternate" hreflang="{lang}" href="{domain}{_language_prefix(lang)}{path}" />')
    if default in languages:
        tags.append(f'<link rel="alternate" hreflang="x-default" href="{domain}{path}" />')
    return mark_safe('\n    '.join(tags))


@register.simple_tag(takes_context=True)
def canonical_url(context):
    request = context.get('request')
    if not request:
        return ''

    url_name = request.resolver_match.url_name if request.resolver_match else None
    path = request.path
    if url_name:
        try:
            path = _language_prefix(translation.get_language()) + _canonical_base(request, url_name)
        except NoReverseMatch:
            pass
    canonical = f"{request.scheme}://{request.get_host()}{path}"
    return mark_safe(f'<link rel="canonical" href="{canonical}" />')


# ---------------------------------------------------------------- JSON-LD (task 7)

def _jsonld_language(context):
    return context.get('LANGUAGE_CODE') or translation.get_language() or settings.LANGUAGE_CODE


@register.simple_tag(takes_context=True)
def site_jsonld(context):
    """Organization (every page) + BreadcrumbList (internal pages)."""
    request = context.get('request')
    if request is None:
        return ''
    language = _jsonld_language(context)
    brands = context.get('SITE_MENU') or []
    url_name = request.resolver_match.url_name if request.resolver_match else None
    scripts = [sd.to_script(sd.organization(request, language, brands))]
    if url_name:
        scripts.append(sd.to_script(sd.breadcrumb_list(request, url_name, context.flatten(), language)))
    return mark_safe('\n    '.join(s for s in scripts if s))


@register.simple_tag(takes_context=True)
def car_jsonld(context, product):
    return mark_safe(sd.to_script(sd.car(context['request'], product, _jsonld_language(context))))


@register.simple_tag(takes_context=True)
def news_jsonld(context, news):
    return mark_safe(sd.to_script(sd.news_article(context['request'], news, _jsonld_language(context),
                                                  description=context.get('news_description'))))


@register.simple_tag(takes_context=True)
def dealer_jsonld(context, dealer, images=None):
    data = {'@context': 'https://schema.org', **sd.auto_dealer(context['request'], dealer, images)}
    return mark_safe(sd.to_script(data))


@register.simple_tag(takes_context=True)
def dealers_jsonld(context):
    """One AutoDealer per active dealer (/dealers/, /contact/)."""
    from main.models import Dealer
    dealers = Dealer.objects.filter(is_active=True).order_by('order', 'name')
    return mark_safe(sd.to_script(sd.auto_dealers(context['request'], dealers)))
