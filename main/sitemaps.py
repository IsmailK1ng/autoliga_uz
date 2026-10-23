from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .language import object_languages
from .models import Dealer, News, Product, ProductCategory


class LanguageSitemap(Sitemap):
    """Task 14: every page once per language it really exists in (/..., /ru/..., /en/...),
    with <xhtml:link> alternates and x-default = the uz URL. Untranslated pages are left out."""
    i18n = True
    alternates = True
    x_default = True

    def get_languages_for_item(self, item):
        return object_languages(item)


class StaticViewSitemap(LanguageSitemap):
    priority = 0.8
    changefreq = "weekly"

    def items(self):
        return [
            "home",
            "products",
            "news",
            "dealers",
            "contact",
            "team",
            "test_drive",
        ]

    def location(self, item):
        return reverse(item)


class ProductSitemap(LanguageSitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Product.objects.filter(is_active=True).order_by("order", "slug")

    def location(self, obj):
        return reverse(
            "product_detail",
            kwargs={"product_id": obj.slug}
        )

    def lastmod(self, obj):
        return obj.updated_at


class BrandSitemap(LanguageSitemap):
    """/brand/<slug>/ pages (task 8): same brands as the menu (with active models)"""
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return ProductCategory.objects.filter(is_active=True, products__is_active=True).distinct().order_by("order", "slug")

    def location(self, obj):
        return reverse("brand", kwargs={"slug": obj.slug})

    def lastmod(self, obj):
        return obj.updated_at


class NewsSitemap(LanguageSitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        # News without body text in a language is noindex there (task 9): object_languages() leaves it out
        return list(News.objects.filter(is_active=True).prefetch_related("blocks").order_by("-created_at", "pk"))

    def location(self, obj):
        return reverse(
            "news_detail",
            kwargs={"slug": obj.slug}
        )

    def lastmod(self, obj):
        return obj.updated_at

class DealerSitemap(LanguageSitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Dealer.objects.filter(is_active=True).order_by("order", "pk")

    def location(self, obj):
        return obj.get_absolute_url()
