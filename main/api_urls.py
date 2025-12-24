
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    NewsViewSet, 
    ContactFormViewSet, 
    ProductViewSet,
    ProductCategoryViewSet,
)

router = DefaultRouter()
router.register(r'news', NewsViewSet, basename='news')
router.register(r'contact', ContactFormViewSet, basename='contact')
router.register(r'products', ProductViewSet, basename='products')
router.register(r'product-categories', ProductCategoryViewSet, basename='product-category')


urlpatterns = [
    path('uz/', include(router.urls)),
    path('ru/', include(router.urls)),
    path('en/', include(router.urls)),
]