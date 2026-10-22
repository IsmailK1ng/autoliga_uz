from django.conf import settings


def site_contacts(request):
    """Expose site-wide contact details (phone, email) to all templates."""
    return {'SITE_CONTACTS': settings.SITE_CONTACTS}


def seo(request):
    """Expose SEO_YEAR (used in model and brand titles/H1) to all templates."""
    return {'SEO_YEAR': settings.SEO_YEAR}