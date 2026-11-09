from django.apps import AppConfig


class SeoConfig(AppConfig):
    """Own app so Jazzmin shows one "SEO" section (page meta-data + FAQ)."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'seo'
    verbose_name = 'SEO'
