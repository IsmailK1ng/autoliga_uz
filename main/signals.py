from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache


LANGUAGES = ('uz', 'ru', 'en')


def _clear_bot_cache(model_name, instance=None):
    """Bot API cache ni tozalash Р В Р вЂ Р В РІР‚С™Р Р†Р вЂљРЎСљ model o'zgarganda avtomatik chaqiriladi."""
    if model_name == 'ProductCategory':
        for lang in LANGUAGES:
            cache.delete(f'bot:brands:{lang}')
            # Brand o'zgarganda unga tegishli cars cache ham eskiradi
            cache.delete(f'bot:cars:{instance.id}:{lang}') if instance else None

    elif model_name == 'Product':
        for lang in LANGUAGES:
            if instance and instance.category_id:
                cache.delete(f'bot:cars:{instance.category_id}:{lang}')
            cache.delete(f'bot:car:{instance.id}:{lang}') if instance else None
            # Test-drayv uchun products ro'yxati ham cache'da turadi
            cache.delete(f'bot:td_data:{lang}')

    elif model_name == 'Dealer':
        for lang in LANGUAGES:
            cache.delete(f'bot:dealers:{lang}')
            # Test-drayv uchun dealers ro'yxati ham cache'da turadi
            cache.delete(f'bot:td_data:{lang}')


@receiver(post_save, sender='main.ProductCategory')
@receiver(post_delete, sender='main.ProductCategory')
def clear_brand_cache(sender, instance, **kwargs):
    _clear_bot_cache('ProductCategory', instance)


@receiver(post_save, sender='main.Product')
@receiver(post_delete, sender='main.Product')
def clear_product_cache(sender, instance, **kwargs):
    _clear_bot_cache('Product', instance)


@receiver(post_save, sender='main.Dealer')
@receiver(post_delete, sender='main.Dealer')
def clear_dealer_cache(sender, instance, **kwargs):
    _clear_bot_cache('Dealer', instance)
