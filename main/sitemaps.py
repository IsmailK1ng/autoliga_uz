from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import News, Product


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


class NewsSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return News.objects.filter(is_active=True)

    def location(self, obj):
        return reverse(
            "news_detail",
            kwargs={"slug": obj.slug}
        )

    def lastmod(self, obj):
        return obj.updated_at