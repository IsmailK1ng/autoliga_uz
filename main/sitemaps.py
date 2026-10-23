from django.conf import settings
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import Dealer, News, Product, ProductCategory
from .seo import news_body_text


class StaticViewSitemap(Sitemap):
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


class ProductSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Product.objects.filter(is_active=True)

    def location(self, obj):
        return reverse(
            "product_detail",
            kwargs={"product_id": obj.slug}
        )

    def lastmod(self, obj):
        return obj.updated_at


class BrandSitemap(Sitemap):
    """/brand/<slug>/ pages (task 8): same brands as the menu (with active models)"""
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return ProductCategory.objects.filter(is_active=True, products__is_active=True).distinct().order_by("order", "slug")

    def location(self, obj):
        return reverse("brand", kwargs={"slug": obj.slug})

    def lastmod(self, obj):
        return obj.updated_at


class NewsSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        # News without body text is noindex (task 9): keep it out of the sitemap
        news = News.objects.filter(is_active=True).prefetch_related("blocks").order_by("-created_at", "pk")
        return [item for item in news if news_body_text(item.blocks.all(), settings.LANGUAGE_CODE)]

    def location(self, obj):
        return reverse(
            "news_detail",
            kwargs={"slug": obj.slug}
        )

    def lastmod(self, obj):
        return obj.updated_at

class DealerSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Dealer.objects.filter(is_active=True)

    def location(self, obj):
        return obj.get_absolute_url()
