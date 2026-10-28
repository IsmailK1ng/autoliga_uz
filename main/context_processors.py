import re

from django.conf import settings
from django.db.models import Prefetch
from django.utils.functional import SimpleLazyObject

# A GA4 measurement ID is "G-" + letters/digits; anything else is not rendered,
# so the ID can go into the gtag snippet as it is (no escaping needed).
GA_ID_RE = re.compile(r'^G-[A-Z0-9]+$')
GTM_ID_RE = re.compile(r'^GTM-[A-Z0-9]+$')


def site_contacts(request):
    """Expose site-wide contact details (phone, email) to all templates."""
    return {'SITE_CONTACTS': settings.SITE_CONTACTS}


def seo(request):
    """Expose SEO_YEAR (used in model and brand titles/H1) and the analytics settings.

    ANALYTICS_ENABLED is True only when DEBUG is False, so local runs never send
    hits to Google Analytics / Tag Manager. GA_DIRECT_ENABLED=False empties only
    the direct gtag.js id; the GTM container keeps loading.
    """
    ga_id = (settings.GA_MEASUREMENT_ID or '').strip()
    gtm_id = (settings.GTM_CONTAINER_ID or '').strip()
    return {
        'SEO_YEAR': settings.SEO_YEAR,
        'GA_MEASUREMENT_ID': ga_id if settings.GA_DIRECT_ENABLED and GA_ID_RE.match(ga_id) else '',
        'GTM_CONTAINER_ID': gtm_id if GTM_ID_RE.match(gtm_id) else '',
        'ANALYTICS_ENABLED': not settings.DEBUG,
    }


def _menu_brands():
    from main.models import Product, ProductCategory
    active_products = Product.objects.filter(is_active=True).order_by('order', 'title')
    # Only active brands that have at least one active model; only active models
    return list(
        ProductCategory.objects.filter(is_active=True, products__is_active=True)
        .distinct()
        .order_by('order', 'name')
        .prefetch_related(Prefetch('products', queryset=active_products, to_attr='menu_products'))
    )


def site_menu(request):
    """Brands with their active models for the header menu and the footer (task 6).

    Lazy: the two queries (brands + models, no N+1) run only when a template
    actually uses SITE_MENU, so admin and API responses pay nothing.
    """
    return {'SITE_MENU': SimpleLazyObject(_menu_brands)}