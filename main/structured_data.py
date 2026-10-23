# main/structured_data.py
"""
Schema.org JSON-LD (SEO TZ task 7).

Every value comes from settings (SITE_CONTACTS) or admin data. A field that is
empty in the admin is left out of the markup; nothing is filled in by hand.

    Organization    every page (base.html and the standalone product page)
    BreadcrumbList  every internal page, same items as the visual breadcrumb
    Car             model page; AggregateOffer only when a trim has a price
    AutoDealer      /dealers/, /contact/ (every active dealer), /dealers/<pk>/
    NewsArticle     /news/<slug>/
    FAQPage         /brand/<slug>/ (built in views.brand_detail)
"""

import json
import re

from django.conf import settings
from django.templatetags.static import static
from django.urls import NoReverseMatch, reverse
from django.utils.html import strip_tags

from .seo import clean, product_seo

ORGANIZATION_NAME = 'AUTOLIGA'
ORGANIZATION_ALTERNATE_NAME = 'AUTOLIGA Uzbekistan'
# Existing uz text (from the home page markup); ru/en are not translated yet
ORGANIZATION_DESCRIPTION = {
    'uz': "AUTOLIGA — rasmiy avtosalonlar va servislar tarmog‘i. JETOUR, SOUEAST, JAC va GEELY avtomobillari.",
}
LOGO = 'images/logo/autoliga-logo.png'

HOME_LABEL = {'uz': 'Bosh sahifa', 'ru': 'Главная', 'en': 'Home'}
# Same labels as the visual breadcrumbs in the templates
PAGE_LABELS = {
    'products': {'uz': 'Modellar', 'ru': 'Модели', 'en': 'Models'},
    'news': {'uz': 'Autoliga yangiliklar', 'ru': 'Новости Autoliga', 'en': 'Autoliga News'},
    'dealers': {'uz': 'Dilerlar', 'ru': 'Дилеры', 'en': 'Dealers'},
    'contact': {'uz': 'Kontaktlar', 'ru': 'Контакты', 'en': 'Contacts'},
    'team': {'uz': 'Bizning jamoa', 'ru': 'Наша команда', 'en': 'Our team'},
    'test_drive': {'uz': 'Test-drayvga yozilish', 'ru': 'Запись на тест-драйв', 'en': 'Book a test drive'},
    'privacy': {'uz': 'Maxfiylik siyosati', 'ru': 'Политика конфиденциальности', 'en': 'Privacy policy'},
    'terms': {'uz': 'Foydalanish shartlari', 'ru': 'Условия использования', 'en': 'Terms of use'},
}


def _lang(language):
    return language if language in HOME_LABEL else settings.LANGUAGE_CODE


def domain(request):
    return request.build_absolute_uri('/').rstrip('/')


def absolute(request, path):
    return path if path.startswith('http') else domain(request) + path


def organization_id(request):
    return f"{domain(request)}/#organization"


def organization_ref(request):
    """Seller / publisher: points to the Organization node, with name and logo
    repeated so validators that do not follow @id still see them."""
    return {
        '@type': 'Organization',
        '@id': organization_id(request),
        'name': ORGANIZATION_NAME,
        'logo': {'@type': 'ImageObject', 'url': absolute(request, static(LOGO))},
    }


def to_script(data):
    """<script type="application/ld+json"> with <, > and & escaped (no </script> break-out)."""
    if not data:
        return ''
    payload = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    payload = payload.replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    return f'<script type="application/ld+json">{payload}</script>'


# ---------------------------------------------------------------- Organization

def organization(request, language, brands=()):
    lang = _lang(language)
    data = {
        '@context': 'https://schema.org',
        '@type': 'Organization',
        '@id': organization_id(request),
        'name': ORGANIZATION_NAME,
        'alternateName': ORGANIZATION_ALTERNATE_NAME,
        'url': domain(request) + '/',
        'logo': absolute(request, static(LOGO)),
    }
    if ORGANIZATION_DESCRIPTION.get(lang):
        data['description'] = ORGANIZATION_DESCRIPTION[lang]
    contacts = settings.SITE_CONTACTS
    if contacts.get('phone'):
        data['telephone'] = contacts['phone']
    if contacts.get('email'):
        data['email'] = contacts['email']
    data['areaServed'] = {'@type': 'Country', 'name': 'Uzbekistan'}
    # Brands = active brands with active models (same list as the menu)
    names = [clean(b.name or b.name_uz) for b in brands]
    if names:
        data['brand'] = [{'@type': 'Brand', 'name': n} for n in names if n]
    if contacts.get('social'):
        data['sameAs'] = list(contacts['social'])
    return data


# -------------------------------------------------------------- BreadcrumbList

def breadcrumb_items(request, url_name, context, language):
    """(name, path) pairs after "Home" for the current page, or None (home, 404, ...)."""
    lang = _lang(language)

    def page(name):
        return (PAGE_LABELS[name][lang], reverse(name))

    if url_name in PAGE_LABELS:
        if url_name == 'products' and (context.get('category_slug') and context.get('category_info')):
            return [page('products'), (context['category_info'].get('breadcrumb'), reverse('brand', kwargs={'slug': context['category_slug']}))]
        return [page(url_name)]
    if url_name == 'brand' and context.get('brand'):
        brand = context['brand']
        return [page('products'), (context.get('brand_name') or brand.name or brand.name_uz, reverse('brand', kwargs={'slug': brand.slug}))]
    if url_name == 'product_detail' and context.get('product'):
        product = context['product']
        items = []
        if product.category:
            items.append((product.category.name or product.category.name_uz, reverse('brand', kwargs={'slug': product.category.slug})))
        items.append((product.title or product.title_uz, product.get_absolute_url()))
        return items
    if url_name == 'news_detail' and context.get('news'):
        news = context['news']
        return [page('news'), (news.title or news.title_uz, reverse('news_detail', kwargs={'slug': news.slug}))]
    if url_name == 'dealer_detail' and context.get('dealer'):
        dealer = context['dealer']
        return [page('dealers'), (dealer.name or dealer.name_uz, dealer.get_absolute_url())]
    return None


def breadcrumb_list(request, url_name, context, language):
    try:
        items = breadcrumb_items(request, url_name, context, language)
    except NoReverseMatch:
        return None
    if not items:
        return None
    trail = [(HOME_LABEL[_lang(language)], reverse('home'))] + items
    return {
        '@context': 'https://schema.org',
        '@type': 'BreadcrumbList',
        'itemListElement': [
            {'@type': 'ListItem', 'position': i, 'name': clean(name), 'item': absolute(request, path)}
            for i, (name, path) in enumerate(trail, start=1) if clean(name)
        ],
    }


# ------------------------------------------------------------------------- Car

POWER_RE = re.compile(r'(\d{2,4})\s*(?:o\.?\s*k\.?|ot\s+kuchi|л\.?\s*с\.?|hp|bhp|ps)\b', re.I)


def engine_powers(product):
    """Distinct horsepower values from the trims ("184 o.k.", "184 л.с.", "184 hp"),
    falling back to slider_power. Free text without a number + unit is skipped."""
    trims = getattr(product, 'active_trims', None)
    if trims is None:
        trims = product.trims.filter(is_active=True)
    values = []
    for text in [t.power for t in trims] or [product.slider_power]:
        match = POWER_RE.search(text or '')
        if match and int(match.group(1)) not in values:
            values.append(int(match.group(1)))
    return values


def car(request, product, language):
    url = absolute(request, request.path)
    data = {
        '@context': 'https://schema.org',
        '@type': 'Car',
        '@id': f"{url}#car",
        'name': clean(product.display_name),
        'url': url,
        'description': product_seo(product, language)['description'],
    }
    if product.category:
        data['brand'] = {'@type': 'Brand', 'name': clean(product.category.name or product.category.name_uz)}
    images = [absolute(request, f.url) for f in (product.main_image, product.card_image) if f]
    if images:
        data['image'] = list(dict.fromkeys(images))
    year = clean(product.slider_year)
    if re.fullmatch(r'(19|20)\d\d', year):
        data['vehicleModelDate'] = year
    powers = engine_powers(product)
    if powers:
        engines = [{'@type': 'EngineSpecification',
                    'enginePower': {'@type': 'QuantitativeValue', 'value': p, 'unitCode': 'BHP'}} for p in powers]
        data['vehicleEngine'] = engines[0] if len(engines) == 1 else engines

    trims = getattr(product, 'active_trims', None)
    if trims is None:
        trims = product.trims.filter(is_active=True)
    prices = [t.price for t in trims if t.price]
    # No price in the admin -> no Offer at all (TZ task 7)
    if prices:
        data['offers'] = {
            '@type': 'AggregateOffer',
            'priceCurrency': 'UZS',
            'lowPrice': min(prices),
            'highPrice': max(prices),
            'offerCount': len(prices),
            'url': url,
            'seller': organization_ref(request),
        }
    return data


# ------------------------------------------------------------------ AutoDealer

DAYS = {
    'du': 'Mo', 'se': 'Tu', 'ch': 'We', 'pa': 'Th', 'ju': 'Fr', 'sh': 'Sa', 'ya': 'Su', 'yak': 'Su',
    'пн': 'Mo', 'вт': 'Tu', 'ср': 'We', 'чт': 'Th', 'пт': 'Fr', 'сб': 'Sa', 'вс': 'Su',
    'mo': 'Mo', 'tu': 'Tu', 'we': 'We', 'th': 'Th', 'fr': 'Fr', 'sa': 'Sa', 'su': 'Su',
}
EVERY_DAY = ('har kuni', 'ежедневно', 'daily', 'every day')
HOURS_RE = re.compile(
    r'^(?:(?P<d1>[a-zа-я]{2,4})\.?\s*[-–—]\s*(?P<d2>[a-zа-я]{2,4})\.?|(?P<every>[a-zа-я ]+?))[\s,:]*'
    r'(?P<h1>\d{1,2})[:.](?P<m1>\d\d)\s*[-–—]\s*(?P<h2>\d{1,2})[:.](?P<m2>\d\d)$', re.I)


def opening_hours(text):
    """"Du-Yak 9:00 - 18:00" -> "Mo-Su 09:00-18:00". Anything else -> None (left out)."""
    match = HOURS_RE.match(clean(text).lower())
    if not match:
        return None
    if match['every']:
        if match['every'].strip() not in EVERY_DAY:
            return None
        days = 'Mo-Su'
    else:
        d1, d2 = DAYS.get(match['d1']), DAYS.get(match['d2'])
        if not (d1 and d2):
            return None
        days = f"{d1}-{d2}"
    h1, h2 = int(match['h1']), int(match['h2'])
    if h1 > 23 or h2 > 24:
        return None
    return f"{days} {h1:02d}:{match['m1']}-{h2:02d}:{match['m2']}"


def auto_dealer(request, dealer, images=None):
    url = absolute(request, dealer.get_absolute_url())
    data = {
        '@type': 'AutoDealer',
        '@id': f"{url}#dealer",
        'name': clean(dealer.name or dealer.name_uz),
        'url': url,
        'parentOrganization': {'@id': organization_id(request)},
    }
    description = clean(dealer.seo_description) or clean(dealer.description)
    if description:
        data['description'] = description
    if clean(dealer.phone):
        data['telephone'] = clean(dealer.phone)
    address = clean(dealer.address or dealer.address_uz)
    if address:
        data['address'] = {
            '@type': 'PostalAddress',
            'streetAddress': address,
            'addressRegion': dealer.get_region_display(),
            'addressCountry': 'UZ',
        }
    if dealer.latitude is not None and dealer.longitude is not None:
        data['geo'] = {'@type': 'GeoCoordinates', 'latitude': float(dealer.latitude), 'longitude': float(dealer.longitude)}
    hours = opening_hours(dealer.working_hours or dealer.working_hours_uz)
    if hours:
        data['openingHours'] = hours
    pictures = [absolute(request, dealer.logo.url)] if dealer.logo else []
    pictures += [absolute(request, i.image.url) for i in (images or []) if getattr(i, 'image', None)]
    if pictures:
        data['image'] = pictures if len(pictures) > 1 else pictures[0]
    same_as = [u for u in (dealer.instagram, dealer.telegram, dealer.facebook, dealer.youtube) if u]
    if same_as:
        data['sameAs'] = same_as
    return data


def auto_dealers(request, dealers):
    nodes = [auto_dealer(request, d) for d in dealers]
    if not nodes:
        return None
    return {'@context': 'https://schema.org', '@graph': nodes}


# ----------------------------------------------------------------- NewsArticle

def news_article(request, news, language, description=None):
    url = absolute(request, request.path)
    headline = clean(news.title or news.title_uz)
    data = {
        '@context': 'https://schema.org',
        '@type': 'NewsArticle',
        '@id': f"{url}#article",
        'mainEntityOfPage': url,
        'headline': headline[:110],
        'inLanguage': _lang(language),
        'publisher': organization_ref(request),
        'author': organization_ref(request),
    }
    # Same text as the meta description (views.news_detail -> seo.news_description)
    description = description or clean(news.seo_description) or clean(strip_tags(news.desc or ''))
    if description:
        data['description'] = description
    if news.preview_image:
        data['image'] = [absolute(request, news.preview_image.url)]
    if news.created_at:
        data['datePublished'] = news.created_at.isoformat()
    if news.updated_at:
        data['dateModified'] = news.updated_at.isoformat(timespec='seconds')
    return data
