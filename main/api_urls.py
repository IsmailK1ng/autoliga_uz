
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    # DealerViewSet,
    # DealerServiceViewSet,
    # BecomeADealerPageViewSet,
    # BecomeADealerApplicationViewSet
    NewsViewSet, 
    ContactFormViewSet, 
    ProductViewSet,
)

router = DefaultRouter()
router.register(r'news', NewsViewSet, basename='news')
router.register(r'contact', ContactFormViewSet, basename='contact')
router.register(r'products', ProductViewSet, basename='products')
# router.register(r'become-dealer-page', BecomeADealerPageViewSet, basename='become-dealer-page')
# router.register(r'dealer-applications', BecomeADealerApplicationViewSet, basename='dealer-applications')


urlpatterns = [
    path('uz/', include(router.urls)),
    path('ru/', include(router.urls)),
    path('en/', include(router.urls)),
]