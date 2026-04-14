from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import (
    Product
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





# ========== REGISTER ==========
sitemaps = {
    'static': StaticSitemap,
    'products': ProductSitemap,
}