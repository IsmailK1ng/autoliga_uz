# main/seo.py
"""
Title / description / H1 patterns from the SEO TZ (tasks 3 and 4).

Model page (uz pattern from the TZ, ru/en are translations of it):
    title:       "{Brend} {Model} narxi 2026 Toshkentda | Autoliga rasmiy diler"
    description: "{Brend} {Model}: narxi {min_price} so'mdan, {quvvat}. Kredit va test-drayv.
                  Toshkent, Samarqand, Olmaliq."
    H1:          "{Brend} {Model} 2026"

seo_title / seo_description filled in the admin always win over the pattern.
"""

from django.conf import settings

PRODUCT_TITLE = {
    'uz': "{name} narxi {year} Toshkentda | Autoliga rasmiy diler",
    'ru': "{name} цена {year} в Ташкенте | Autoliga официальный дилер",
    'en': "{name} price {year} in Tashkent | Autoliga official dealer",
}

PRODUCT_PRICE = {
    # (from the lowest trim price, free-text slider_price, no price)
    'uz': ("narxi {price} so'mdan", "narxi {price}", "narxi so‘rov asosida"),
    'ru': ("цена от {price} сум", "цена {price}", "цена по запросу"),
    'en': ("price from {price} UZS", "price {price}", "price on request"),
}

PRODUCT_DESCRIPTION_TAIL = {
    'uz': "Kredit va test-drayv. Toshkent, Samarqand, Olmaliq.",
    'ru': "Кредит и тест-драйв. Ташкент, Самарканд, Алмалык.",
    'en': "Financing and test drive. Tashkent, Samarkand, Olmaliq.",
}


def clean(text):
    """Collapse whitespace and line breaks (TZ task 3)."""
    return ' '.join(str(text or '').split())


def format_price(value):
    """289900000 -> '289 900 000'"""
    return f"{value:,}".replace(',', ' ')


def min_trim_price(product):
    """Lowest price among active trims (uses the active_trims prefetch when present)."""
    trims = getattr(product, 'active_trims', None)
    if trims is None:
        trims = product.trims.filter(is_active=True)
    prices = [t.price for t in trims if t.price]
    return min(prices) if prices else None


def product_seo(product, language):
    """Return dict(title, description, h1) for a product page in the given language."""
    lang = language if language in PRODUCT_TITLE else 'uz'
    year = settings.SEO_YEAR
    name = clean(product.display_name)

    title = clean(product.seo_title) or PRODUCT_TITLE[lang].format(name=name, year=year)

    description = clean(product.seo_description)
    if not description:
        from_price, free_price, no_price = PRODUCT_PRICE[lang]
        min_price = min_trim_price(product)
        if min_price:
            price = from_price.format(price=format_price(min_price))
        elif product.slider_price:
            price = free_price.format(price=clean(product.slider_price))
        else:
            price = no_price
        parts = [f"{name}: {price}"]
        if product.slider_power:
            parts.append(clean(product.slider_power))
        # "156 o.k." already ends with a dot; avoid "o.k.."
        description = f"{', '.join(parts).rstrip('.')}. {PRODUCT_DESCRIPTION_TAIL[lang]}"

    return {
        'title': title,
        'description': description,
        'h1': f"{name} {year}",
    }
