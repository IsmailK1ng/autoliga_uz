from django.conf import settings


def site_contacts(request):
    """Expose site-wide contact details (phone, email) to all templates."""
    return {'SITE_CONTACTS': settings.SITE_CONTACTS}