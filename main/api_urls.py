
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    NewsViewSet,
    ContactFormViewSet,
    ProductViewSet,
    ProductCategoryViewSet,
    ReviewViewSet,
    TestDriveViewSet,
    BotUserView,
    BotBrandsView,
    BotCarsView,
    BotCarDetailView,
    BotDealersView,
    BotTestDriveView,
)

router = DefaultRouter()
router.register(r'news', NewsViewSet, basename='news')
router.register(r'contact', ContactFormViewSet, basename='contact')
router.register(r'products', ProductViewSet, basename='products')
router.register(r'product-categories', ProductCategoryViewSet, basename='product-category')
router.register(r'reviews', ReviewViewSet, basename='reviews')
router.register(r'test-drive', TestDriveViewSet, basename='test-drive')


urlpatterns = [
    path('uz/', include(router.urls)),
    path('ru/', include(router.urls)),
    path('en/', include(router.urls)),
    # Bot API
    path('bot/user/', BotUserView.as_view(), name='bot-user'),
    path('bot/brands/', BotBrandsView.as_view(), name='bot-brands'),
    path('bot/cars/', BotCarsView.as_view(), name='bot-cars'),
    path('bot/car-detail/', BotCarDetailView.as_view(), name='bot-car-detail'),
    path('bot/dealers/', BotDealersView.as_view(), name='bot-dealers'),
    path('bot/test-drive/', BotTestDriveView.as_view(), name='bot-test-drive'),
]


