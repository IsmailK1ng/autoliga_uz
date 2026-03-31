

# bot_service.py faqat ORM funktsiyalarini saqlaydi. 

"""
Bot Service Layer - ORM-based functions for Telegram bot
Clean architecture: Service в†’ Models
No serializers, no APIView, no DRF dependencies

USAGE EXAMPLES:

# Get telegram user
user = BotService.get_telegram_user(123456789)

# Create/update user
user, created = BotService.create_or_update_telegram_user(
    123456789,
    first_name="John",
    phone="+998901234567"
)

# Get brands
brands = BotService.get_brands(lang="uz")  # [{'id': 1, 'name': 'Chevrolet'}, ...]

# Get cars by brand
cars = BotService.get_cars_by_brand(brand_id=1, lang="uz")

# Get car details
car = BotService.get_car_detail(car_id=1, lang="uz")

# Get dealers
dealers = BotService.get_dealers(lang="uz")

# Get test drive form data
form_data = BotService.get_test_drive_form_data(lang="uz")

# Create test drive request
test_drive, error = BotService.create_test_drive_request({
    'name': 'John Doe',
    'phone': '+998901234567',
    'dealer_id': 1,
    'product_id': 1,
    'preferred_date': '2024-01-15',
    'preferred_time': '10:00',
    'agree_terms': True
})

# Clear cache
BotService.clear_bot_cache()
"""

from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.utils import timezone
from typing import List, Dict, Optional, Tuple, Any
from main.models import TelegramUser, Dealer, Product, ProductCategory, TestDriveRequest


class BotService:
    """Service layer for Telegram bot operations using Django ORM"""

    # ========== TELEGRAM USER MANAGEMENT ==========

    @staticmethod
    def get_telegram_user(telegram_id: int) -> Optional[TelegramUser]:
        """Get TelegramUser by telegram_id"""
        try:
            return TelegramUser.objects.get(telegram_id=telegram_id)
        except ObjectDoesNotExist:
            return None

    @staticmethod
    def create_or_update_telegram_user(telegram_id: int, **kwargs) -> Tuple[TelegramUser, bool]:
        """
        Create or update TelegramUser
        Returns: (user, created)
        """
        user, created = TelegramUser.objects.get_or_create(
            telegram_id=telegram_id, defaults=kwargs
        )
        if not created:
            # Update only provided fields
            update_fields = []
            for key, value in kwargs.items():
                if value is not None and hasattr(user, key):
                    setattr(user, key, value)
                    update_fields.append(key)
            if update_fields:
                user.save(update_fields=update_fields)
        return user, created

    # ========== BRANDS (ProductCategory) ==========

    @staticmethod
    def get_brands(lang: str = "uz") -> List[Dict[str, Any]]:
        """
        Get active brands/categories with caching
        Returns: [{'id': int, 'name': str}, ...]
        """
        cache_key = f'bot:brands:{lang}'
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        brands = ProductCategory.objects.filter(is_active=True).order_by('order', 'name')
        result = [
            {
                'id': brand.id,
                'name': getattr(brand, f'name_{lang}', None) or brand.name
            }
            for brand in brands
        ]
        cache.set(cache_key, result, timeout=600)  # 10 minutes
        return result

    # ========== CARS (Product) ==========

    @staticmethod
    def get_cars_by_brand(brand_id: int, lang: str = "uz") -> List[Dict[str, Any]]:
        """
        Get active cars by brand with caching
        Returns: [{'id': int, 'title': str}, ...]
        """
        cache_key = f'bot:cars:{brand_id}:{lang}'
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        cars = Product.objects.filter(
            category_id=brand_id,
            is_active=True
        ).order_by('order', 'title')

        result = [
            {
                'id': car.id,
                'title': getattr(car, f'title_{lang}', None) or car.title
            }
            for car in cars
        ]
        cache.set(cache_key, result, timeout=600)
        return result

    @staticmethod
    def get_car_detail(car_id: int, lang: str = "uz") -> Optional[Dict[str, Any]]:
        """
        Get detailed car info with optimized queries
        Uses select_related and prefetch_related
        """
        try:
            car = Product.objects.select_related('category').prefetch_related(
                'features'
            ).get(id=car_id, is_active=True)
        except ObjectDoesNotExist:
            return None

        # Get localized fields
        title = getattr(car, f'title_{lang}', None) or car.title
        price = getattr(car, f'slider_price_{lang}', None) or car.slider_price
        power = getattr(car, f'slider_power_{lang}', None) or car.slider_power
        fuel = getattr(car, f'slider_fuel_consumption_{lang}', None) or car.slider_fuel_consumption

        # Get top 6 features
        features = car.features.all().order_by('order')[:6]
        feat_list = [
            getattr(f, f'name_{lang}', None) or f.name
            for f in features
        ]

        return {
            'id': car.id,
            'title': title,
            'slug': car.slug,
            'category': {
                'id': car.category.id,
                'name': getattr(car.category, f'name_{lang}', None) or car.category.name
            } if car.category else None,
            'main_image': car.main_image.url if car.main_image else None,
            'card_image': car.card_image.url if car.card_image else None,
            'price': price,
            'year': car.slider_year,
            'power': power,
            'fuel': fuel,
            'features': feat_list,
        }

    # ========== DEALERS ==========

    @staticmethod
    def get_dealers(lang: str = "uz") -> List[Dict[str, Any]]:
        """
        Get active dealers with caching
        Returns: [{'id': int, 'name': str, 'region': str, 'address': str, 'phone': str, 'hours': str}, ...]
        """
        cache_key = f'bot:dealers:{lang}'
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        dealers = Dealer.objects.filter(is_active=True).order_by('order', 'name')
        result = [
            {
                'id': dealer.id,
                'name': getattr(dealer, f'name_{lang}', None) or dealer.name,
                'region': dealer.region,
                'address': getattr(dealer, f'address_{lang}', None) or dealer.address,
                'phone': dealer.phone,
                'hours': getattr(dealer, f'working_hours_{lang}', None) or dealer.working_hours,
            }
            for dealer in dealers
        ]
        cache.set(cache_key, result, timeout=600)
        return result

    # ========== TEST DRIVE ==========

    @staticmethod
    def get_test_drive_form_data(lang: str = "uz") -> Dict[str, Any]:
        """
        Get data for test drive form (dealers, products, time slots)
        """
        cache_key = f'bot:td_data:{lang}'
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        # Get dealers
        dealers = Dealer.objects.filter(is_active=True).order_by('order', 'name')
        dealers_data = [
            {
                'id': dealer.id,
                'name': getattr(dealer, f'name_{lang}', None) or dealer.name
            }
            for dealer in dealers
        ]

        # Get products
        products = Product.objects.filter(is_active=True).order_by('order', 'title')
        products_data = [
            {
                'id': product.id,
                'title': getattr(product, f'title_{lang}', None) or product.title
            }
            for product in products
        ]

        result = {
            'dealers': dealers_data,
            'products': products_data,
            'time_slots': [
                '10:00', '10:30', '11:00', '11:30', '12:00', '12:30',
                '13:00', '13:30', '14:00', '14:30', '15:00', '15:30',
                '16:00', '16:30', '17:00'
            ],
        }
        cache.set(cache_key, result, timeout=600)
        return result

    @staticmethod
    def create_test_drive_request(data: Dict[str, Any]) -> Tuple[Optional[TestDriveRequest], Optional[str]]:
        """
        Create test drive request with validation
        Returns: (TestDriveRequest or None, error_message or None)

        Validation:
        - Daily limit: 2 requests per phone number
        """
        try:
            with transaction.atomic():
                phone = data.get('phone', '')

                # Check daily limit
                if phone:
                    today = timezone.now().date()
                    today_count = TestDriveRequest.objects.filter(
                        phone=phone,
                        created_at__date=today
                    ).count()
                    if today_count >= 2:
                        return None, 'daily_limit'

                # Create request
                request_obj = TestDriveRequest.objects.create(**data)

                # Send notification (optional, can be moved to caller)
                try:
                    from main.services.telegram import TelegramNotificationSender
                    TelegramNotificationSender.send_test_drive_notification(request_obj)
                except Exception as e:
                    # Log error but don't fail the request
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Telegram notification error: {e}")

                return request_obj, None

        except Exception as e:
            return None, str(e)

    # ========== UTILITY METHODS ==========

    @staticmethod
    def clear_bot_cache():
        """Clear all bot-related cache"""
        cache_keys = [
            key for key in cache.keys('*')
            if key.startswith('bot:')
        ]
        cache.delete_many(cache_keys)

    @staticmethod
    def get_brand_by_id(brand_id: int, lang: str = "uz") -> Optional[Dict[str, Any]]:
        """Get single brand by ID"""
        try:
            brand = ProductCategory.objects.get(id=brand_id, is_active=True)
            return {
                'id': brand.id,
                'name': getattr(brand, f'name_{lang}', None) or brand.name,
                'slug': brand.slug
            }
        except ObjectDoesNotExist:
            return None

    @staticmethod
    def get_dealer_by_id(dealer_id: int, lang: str = "uz") -> Optional[Dict[str, Any]]:
        """Get single dealer by ID"""
        try:
            dealer = Dealer.objects.get(id=dealer_id, is_active=True)
            return {
                'id': dealer.id,
                'name': getattr(dealer, f'name_{lang}', None) or dealer.name,
                'region': dealer.region,
                'address': getattr(dealer, f'address_{lang}', None) or dealer.address,
                'phone': dealer.phone,
                'hours': getattr(dealer, f'working_hours_{lang}', None) or dealer.working_hours,
            }
        except ObjectDoesNotExist:
            return None