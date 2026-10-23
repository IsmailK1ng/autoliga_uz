# main/dealer_info.py
"""
Dealer data shown on /dealers/, /dealers/<pk>/, /contact/ and in the AutoDealer
JSON-LD (SEO TZ tasks 7 and 10). One place, so the visible text, the map data
and the structured data never disagree. Everything comes from the admin;
empty fields stay empty.

Future city pages: dealers are grouped by `region` (DEALER_REGION_CHOICES keys
are URL-safe slugs such as "toshkent-shahri", none of them numeric), and the
groups on /dealers/ already carry id="<region>". A later
path('dealers/<slug:region>/', ...) does not clash with the existing
path('dealers/<int:pk>/', ...) dealer pages.
"""

import re
from urllib.parse import urlencode

from .models import DEALER_REGION_CHOICES

REGION_ORDER = [key for key, _label in DEALER_REGION_CHOICES]
# Same labels as the region filter on /dealers/ (uz from the model choices)
REGION_LABELS = {
    'uz': dict(DEALER_REGION_CHOICES),
    'ru': {
        'qoraqalpogiston': 'Каракалпакстан', 'xorazm': 'Хорезм', 'buxoro': 'Бухара', 'navoiy': 'Навои',
        'samarqand': 'Самарканд', 'qashqadaryo': 'Кашкадарья', 'surxondaryo': 'Сурхандарья', 'jizzax': 'Джизак',
        'sirdaryo': 'Сырдарья', 'toshkent-viloyati': 'Ташкентская обл.', 'toshkent-shahri': 'г. Ташкент',
        'namangan': 'Наманган', 'andijon': 'Андижан', 'fargona': 'Фергана',
    },
    'en': {
        'qoraqalpogiston': 'Karakalpakstan', 'xorazm': 'Khorezm', 'buxoro': 'Bukhara', 'navoiy': 'Navoi',
        'samarqand': 'Samarkand', 'qashqadaryo': 'Kashkadarya', 'surxondaryo': 'Surkhandarya', 'jizzax': 'Jizzakh',
        'sirdaryo': 'Sirdaryo', 'toshkent-viloyati': 'Tashkent Region', 'toshkent-shahri': 'Tashkent City',
        'namangan': 'Namangan', 'andijon': 'Andijan', 'fargona': 'Fergana',
    },
}
PHONE_SPLIT_RE = re.compile(r'[,;/\n]+')


def _clean(value):
    return ' '.join(str(value or '').split())


def translated(obj, field):
    """Current-language value, else uz, ru, en (the order the dealers page always used)."""
    for name in (field, f'{field}_uz', f'{field}_ru', f'{field}_en'):
        value = _clean(getattr(obj, name, ''))
        if value:
            return value
    return ''


def region_label(region, language):
    labels = REGION_LABELS.get(language) or REGION_LABELS['uz']
    return labels.get(region) or REGION_LABELS['uz'].get(region, region)


def phone_links(phone):
    """"+998 71 200 00 00, +998 90 000-00-00" -> [(display, "tel:+998712000000"), ...].
    The tel: value keeps only "+" and digits; a fragment with fewer than 7 digits gets no link."""
    links = []
    for part in PHONE_SPLIT_RE.split(phone or ''):
        display = _clean(part)
        if not display:
            continue
        digits = re.sub(r'\D', '', display)
        tel = ('+' if display.startswith('+') else '') + digits
        links.append((display, f'tel:{tel}' if len(digits) >= 7 else ''))
    return links


def map_url(dealer, address=''):
    """Google Maps link from the admin coordinates, else a search for the admin address."""
    if dealer.latitude is not None and dealer.longitude is not None:
        return 'https://www.google.com/maps/search/?' + urlencode({'api': 1, 'query': f'{dealer.latitude},{dealer.longitude}'})
    if address:
        return 'https://www.google.com/maps/search/?' + urlencode({'api': 1, 'query': address})
    return ''


def map_embed_url(dealer):
    """Embeddable map (no API key) for the dealer page; only with admin coordinates."""
    if dealer.latitude is None or dealer.longitude is None:
        return ''
    return 'https://maps.google.com/maps?' + urlencode({'q': f'{dealer.latitude},{dealer.longitude}', 'z': 16, 'output': 'embed'})


def dealer_card(dealer, language):
    """Everything the dealers page, the map script and the JSON-LD need for one dealer."""
    address = translated(dealer, 'address')
    phones = phone_links(dealer.phone)
    return {
        'id': dealer.id,
        'name': translated(dealer, 'name'),
        'region': dealer.region,
        'region_label': region_label(dealer.region, language),
        'address': address,
        'phone': _clean(dealer.phone),
        'phones': phones,
        'working_hours': translated(dealer, 'working_hours'),
        'map_url': map_url(dealer, address),
        'instagram': dealer.instagram or '',
        'telegram': dealer.telegram or '',
        'facebook': dealer.facebook or '',
        'youtube': dealer.youtube or '',
        'logo': dealer.logo.url if dealer.logo else '',
        'lat': float(dealer.latitude) if dealer.latitude is not None else None,
        'lng': float(dealer.longitude) if dealer.longitude is not None else None,
        'detail_url': dealer.get_absolute_url(),
    }


def group_by_region(cards):
    """[(region, label, [cards])] in the order of DEALER_REGION_CHOICES."""
    groups = {}
    for card in cards:
        groups.setdefault(card['region'], []).append(card)
    order = {key: i for i, key in enumerate(REGION_ORDER)}
    return [(region, items[0]['region_label'], items)
            for region, items in sorted(groups.items(), key=lambda kv: order.get(kv[0], len(order)))]
