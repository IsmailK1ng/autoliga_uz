from django.conf import settings
from django.db.models import Prefetch
from django.utils.functional import SimpleLazyObject


def site_contacts(request):
    """Expose site-wide contact details (phone, email) to all templates."""
    return {'SITE_CONTACTS': settings.SITE_CONTACTS}


def seo(request):
    """Expose SEO_YEAR (used in model and brand titles/H1) to all templates."""
    return {'SEO_YEAR': settings.SEO_YEAR}


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