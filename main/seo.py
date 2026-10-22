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


# Brand page /brand/<slug>/ (task 8): H1 "{Brend} narxlari 2026 Toshkentda",
# title/description follow the model patterns of task 3.
BRAND_TITLE = {
    'uz': "{name} narxlari {year} Toshkentda | Autoliga rasmiy diler",
    'ru': "Цены {name} {year} в Ташкенте | Autoliga официальный дилер",
    'en': "{name} prices {year} in Tashkent | Autoliga official dealer",
}

BRAND_H1 = {
    'uz': "{name} narxlari {year} Toshkentda",
    'ru': "Цены {name} {year} в Ташкенте",
    'en': "{name} prices {year} in Tashkent",
}

BRAND_DESCRIPTION = {
    # (with a lowest price, without a price)
    'uz': ("{name} avtomobillari: narxlari {price} so'mdan. ", "{name} avtomobillari: narxi so‘rov asosida. "),
    'ru': ("Автомобили {name}: цены от {price} сум. ", "Автомобили {name}: цена по запросу. "),
    'en': ("{name} cars: prices from {price} UZS. ", "{name} cars: price on request. "),
}

CARD_PRICE = {
    # (from the lowest trim price, no price)
    'uz': ("{price} so'mdan", "Narxi so‘rov asosida"),
    'ru': ("от {price} сум", "Цена по запросу"),
    'en': ("from {price} UZS", "Price on request"),
}


def price_label(product, language):
    """Card/table price: lowest active trim price, else the free-text slider_price."""
    lang = language if language in CARD_PRICE else 'uz'
    from_price, no_price = CARD_PRICE[lang]
    min_price = min_trim_price(product)
    if min_price:
        return from_price.format(price=format_price(min_price))
    return clean(product.slider_price) or no_price


def brand_seo(brand, products, language):
    """Return dict(title, description, h1) for a brand page in the given language."""
    lang = language if language in BRAND_TITLE else 'uz'
    year = settings.SEO_YEAR
    name = clean(brand.name) or clean(getattr(brand, 'name_uz', ''))

    title = clean(brand.seo_title) or BRAND_TITLE[lang].format(name=name, year=year)

    description = clean(brand.seo_description)
    if not description:
        prices = [p for p in (min_trim_price(product) for product in products) if p]
        with_price, without_price = BRAND_DESCRIPTION[lang]
        head = with_price.format(name=name, price=format_price(min(prices))) if prices else without_price.format(name=name)
        description = head + PRODUCT_DESCRIPTION_TAIL[lang]

    return {
        'title': title,
        'description': description,
        'h1': BRAND_H1[lang].format(name=name, year=year),
    }
