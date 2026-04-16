from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import (
    Product,
    News,
    Dealer,
)


# ========== STATIC PAGES ==========
class StaticSitemap(Sitemap):
    priority = 0.7
    changefreq = "weekly"

    def items(self):
        return [
            'home',
            'contact',
            'products',
            'team',
            'test_drive',]

    def location(self, item):
        return reverse(item)

# ========== PRODUCTS ==========
class ProductSitemap(Sitemap):
    priority = 0.9
    changefreq = "daily"

    def items(self):
        return Product.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at


class NewsSitemap(Sitemap):
    priority = 0.8
    changefreq = "weekly"

    def items(self):
        return News.objects.filter(is_active=True)

    def location(self, obj):
        return reverse('news_detail', kwargs={'slug': obj.slug})

    def lastmod(self, obj):
        return obj.updated_at


class DealerSitemap(Sitemap):
    priority = 0.7
    changefreq = "weekly"

    def items(self):
        return Dealer.objects.filter(is_active=True)

    def location(self, obj):
        return obj.get_absolute_url()





# ========== REGISTER ==========
sitemaps = {
    'static': StaticSitemap,
    'products': ProductSitemap,
    'news': NewsSitemap,
    'dealers': DealerSitemap,
}