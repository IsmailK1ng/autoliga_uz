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


# Pages that are always noindex,follow (legal pages)
NOINDEX_PAGES = {'privacy', 'terms'}


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

    # privacy / terms are noindex,follow by design (legal_base.html): no hreflang on noindex pages
    if url_name in NOINDEX_PAGES:
        return ''
    # ?q= catalog search results are noindex,follow (products.html): no hreflang either (task 15)
    if context.get('search_query'):
        return ''
    languages = _available_languages(context, request, url_name)
    # task 14: an untranslated page (noindex in this language) carries no hreflang at all
    if translation.get_language() not in languages:
        return ''
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



# ---------------------------------------------------------------- language switcher (task 14)

LANGUAGE_LABELS = {'uz': "O'zbek", 'ru': 'Русский', 'en': 'English'}
# A page that does not exist in a language (untranslated object): the switcher goes to this list instead
LANGUAGE_FALLBACK_PAGE = {'product_detail': 'products', 'brand': 'products', 'news_detail': 'news', 'dealer_detail': 'dealers'}


@register.simple_tag(takes_context=True)
def language_links(context):
    """Switcher links: the same page in every language as plain <a href>.

    While the cookie transition lasts (main.language), the O'zbek link goes through
    /set-language/?language=uz&next=<page> (rel="nofollow"): it sets the cookie to uz
    and lands on the unprefixed page, so an old ru/en cookie cannot bounce the visitor
    back. Crawlers still reach every language through the plain ru/en links, the
    hreflang tags and the sitemap.
    """
    from urllib.parse import urlencode
    from main.language import transition_active

    request = context.get('request')
    current = translation.get_language() or settings.LANGUAGE_CODE
    url_name = request.resolver_match.url_name if request is not None and request.resolver_match else None
    base, available = '/', [code for code, _name in settings.LANGUAGES]
    if url_name:
        try:
            base = _canonical_base(request, url_name)
            available = _available_languages(context, request, url_name)
        except NoReverseMatch:
            base = '/'
    links = []
    for code, _name in settings.LANGUAGES:
        path = base
        if code not in available:
            fallback = LANGUAGE_FALLBACK_PAGE.get(url_name)
            with translation.override(settings.LANGUAGE_CODE):
                path = reverse(fallback) if fallback else '/'
        href = _language_prefix(code) + path
        nofollow = code == settings.LANGUAGE_CODE and transition_active()
        if nofollow:
            href = '/set-language/?' + urlencode({'language': code, 'next': href})
        links.append({'code': code, 'label': LANGUAGE_LABELS.get(code, code), 'href': href,
                      'current': code == current, 'nofollow': nofollow})
    return links


# ---------------------------------------------------------------- admin meta-data of the static pages (seo.PageSEO)

# The page keys are the URL names
PAGE_SEO_KEYS = {'home', 'products', 'dealers', 'news', 'contact', 'team', 'test_drive'}


def _page_seo(context):
    """Active seo.PageSEO of this static page, or None. One query per request (cached on it)."""
    request = context.get('request')
    if request is None:
        return None
    if not hasattr(request, '_page_seo'):
        page = None
        url_name = request.resolver_match.url_name if request.resolver_match else None
        # a brand-filtered catalog (/products/?category=...) keeps the brand's own SEO
        brand_filter = url_name == 'products' and (request.GET.get('brand') or request.GET.get('category'))
        if url_name in PAGE_SEO_KEYS and not brand_filter:
            from django.db.models import Prefetch
            from seo.models import FAQItem, PageSEO
            page = (PageSEO.objects.filter(page_key=url_name, is_active=True)
                    .prefetch_related(Prefetch('faq_items', queryset=FAQItem.objects.filter(is_active=True)))
                    .first())
        request._page_seo = page
    return request._page_seo


@register.simple_tag(takes_context=True)
def page_seo(context):
    """{% page_seo as pseo %}: title / description / og_image (absolute URL) set in the admin for
    this static page. Only values that pass the length rules; '' otherwise, so the template
    default stays (on / that is home_title). robots, canonical and hreflang are not affected."""
    page = _page_seo(context)
    if page is None:
        return {}
    data = page.meta(_jsonld_language(context))
    data['og_image'] = context['request'].build_absolute_uri(page.og_image.url) if page.og_image else ''
    return data


@register.simple_tag(takes_context=True)
def page_faq(context):
    """{% page_faq as faqs %}: visible FAQ entries of a model page (view's product_faqs) or of a
    static page (its active PageSEO). Same list for the block and for page_faq_jsonld."""
    if context.get('product_faqs') is not None:
        return context['product_faqs']
    page = _page_seo(context)
    if page is None:
        return []
    from main.seo import visible_faqs
    return visible_faqs(page.faq_items.all())


@register.simple_tag(takes_context=True)
def page_faq_jsonld(context):
    """FAQPage of the same entries as the visible block (page_faq); nothing without entries."""
    entries = page_faq(context)
    return mark_safe(sd.to_script(sd.faq_page([(e['question'], e['answer_text']) for e in entries])))


@register.simple_tag(takes_context=True)
def home_title(context):
    """Home page <title> / og:title with the brands of the menu (same SITE_MENU, no extra query)."""
    from main.seo import home_title as build
    names = [brand.name or brand.name_uz for brand in (context.get('SITE_MENU') or [])]
    return build(names, _jsonld_language(context))


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
    data = {'@context': 'https://schema.org', **sd.auto_dealer(context['request'], dealer, images, _jsonld_language(context))}
    return mark_safe(sd.to_script(data))


@register.simple_tag(takes_context=True)
def dealers_jsonld(context):
    """One AutoDealer per active dealer (/dealers/, /contact/)."""
    from main.models import Dealer
    dealers = Dealer.objects.filter(is_active=True).order_by('order', 'name')
    return mark_safe(sd.to_script(sd.auto_dealers(context['request'], dealers, _jsonld_language(context))))
