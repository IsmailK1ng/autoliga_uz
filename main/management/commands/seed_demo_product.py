# main/management/commands/seed_demo_product.py
"""
LOCAL ONLY: creates one demo product with trims, parameters and a gallery,
so the server-rendered product page (/products/<slug>/) can be checked.

    python manage.py seed_demo_product           # create / refresh demo data
    python manage.py seed_demo_product --delete  # remove demo data and files

Refuses to run unless DEBUG=True and the database host is local.
"""

from io import BytesIO

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from PIL import Image, ImageDraw

from main.models import (
    ParameterCategory,
    Product,
    ProductCategory,
    ProductGallery,
    ProductParameter,
    ProductTrim,
)

LOCAL_DB_HOSTS = {'', 'localhost', '127.0.0.1', '::1'}

CATEGORY_SLUG = 'demo-brand'
PRODUCT_SLUG = 'demo-x70-test'
PARAM_CATEGORY_SLUGS = ('demo-dvigatel', 'demo-xavfsizlik')

TRIMS = [
    # name, price (UZS), engine, power, transmission, fuel, dimensions
    ('Comfort', 289_900_000, '1.5T', '156 o.k.', '7DCT', '7.2 l/100 km', '4720 x 1860 x 1720 mm'),
    ('Premium', 319_900_000, '1.5T', '156 o.k.', '7DCT', '7.4 l/100 km', '4720 x 1860 x 1720 mm'),
    ('Luxury', 349_900_000, '2.0T', '254 o.k.', '7DCT', '8.1 l/100 km', '4720 x 1860 x 1720 mm'),
]

PARAMETERS = {
    'demo-dvigatel': (
        {'uz': 'Dvigatel', 'ru': 'Двигатель', 'en': 'Engine'},
        [
            {'uz': 'Hajmi: 1.5T / 2.0T', 'ru': 'Объём: 1.5T / 2.0T', 'en': 'Displacement: 1.5T / 2.0T'},
            {'uz': 'Quvvati: 156-254 o.k.', 'ru': 'Мощность: 156-254 л.с.', 'en': 'Power: 156-254 hp'},
            {'uz': 'Uzatmalar qutisi: 7DCT', 'ru': 'Коробка передач: 7DCT', 'en': 'Transmission: 7DCT'},
            {'uz': "Yoqilg'i sarfi: 7.2-8.1 l/100 km", 'ru': 'Расход топлива: 7.2-8.1 л/100 км', 'en': 'Fuel use: 7.2-8.1 l/100 km'},
        ],
    ),
    'demo-xavfsizlik': (
        {'uz': 'Xavfsizlik', 'ru': 'Безопасность', 'en': 'Safety'},
        [
            {'uz': '6 ta xavfsizlik yostiqchasi', 'ru': '6 подушек безопасности', 'en': '6 airbags'},
            {'uz': 'ABS, EBD, ESP', 'ru': 'ABS, EBD, ESP', 'en': 'ABS, EBD, ESP'},
            {'uz': '360° kamera', 'ru': 'Камера 360°', 'en': '360° camera'},
        ],
    ),
}

GALLERY_COLORS = ['#2f4858', '#33658a', '#86bbd8', '#f26419']


def make_image(label, color, size=(1600, 900)):
    """Solid-colour JPEG with a text label, returned as ContentFile."""
    img = Image.new('RGB', size, color)
    draw = ImageDraw.Draw(img)
    draw.text((60, 60), label, fill='white')
    buf = BytesIO()
    img.save(buf, format='JPEG', quality=85)
    return ContentFile(buf.getvalue())


class Command(BaseCommand):
    help = 'LOCAL ONLY: create (or --delete) a demo product with trims, parameters and gallery.'

    def add_arguments(self, parser):
        parser.add_argument('--delete', action='store_true', help='Remove the demo data and its image files.')

    def handle(self, *args, **options):
        db_host = settings.DATABASES['default'].get('HOST') or ''
        if not settings.DEBUG or db_host not in LOCAL_DB_HOSTS:
            raise CommandError(
                f'Refusing to run: DEBUG={settings.DEBUG}, DB HOST={db_host!r}. '
                'This command is for local development only.'
            )

        self.delete_demo()
        if options['delete']:
            self.stdout.write(self.style.SUCCESS('Demo data removed.'))
            return

        with transaction.atomic():
            product = self.create_demo()
        self.stdout.write(self.style.SUCCESS(f'Demo product ready: {product.get_absolute_url()}'))

    def delete_demo(self):
        product = Product.objects.filter(slug=PRODUCT_SLUG).first()
        if product:
            for item in product.gallery.all():
                item.image.delete(save=False)
            product.main_image.delete(save=False)
            product.delete()
        ParameterCategory.objects.filter(slug__in=PARAM_CATEGORY_SLUGS).delete()
        ProductCategory.objects.filter(slug=CATEGORY_SLUG).delete()

    def create_demo(self):
        category = ProductCategory.objects.create(
            slug=CATEGORY_SLUG,
            name_uz='Demo brend', name_ru='Демо бренд', name_en='Demo brand',
            is_active=True,
            order=999,
        )

        product = Product(
            slug=PRODUCT_SLUG,
            category=category,
            title_uz='Demo X70', title_ru='Demo X70', title_en='Demo X70',
            slider_year='2025',
            slider_price_uz="289 900 000 so'mdan",
            slider_price_ru='от 289 900 000 сум',
            slider_price_en='from 289,900,000 UZS',
            slider_power_uz='156-254 o.k.', slider_power_ru='156-254 л.с.', slider_power_en='156-254 hp',
            slider_fuel_consumption_uz='7.2 l/100 km',
            slider_fuel_consumption_ru='7.2 л/100 км',
            slider_fuel_consumption_en='7.2 l/100 km',
            is_active=True,
        )
        product.main_image.save('demo-x70-main.jpg', make_image('Demo X70 - main', '#1b1b1b'), save=False)
        product.save()

        for order, (name, price, engine, power, gearbox, fuel, dims) in enumerate(TRIMS):
            ProductTrim.objects.create(
                product=product, name=name, price=price, engine=engine, power=power,
                transmission=gearbox, fuel_consumption=fuel, dimensions=dims, order=order,
            )

        for cat_order, (slug, (names, params)) in enumerate(PARAMETERS.items()):
            param_category = ParameterCategory.objects.create(
                slug=slug, name_uz=names['uz'], name_ru=names['ru'], name_en=names['en'], order=cat_order,
            )
            for order, text in enumerate(params):
                ProductParameter.objects.create(
                    product=product, category=param_category, order=order,
                    text_uz=text['uz'], text_ru=text['ru'], text_en=text['en'],
                )

        for order, color in enumerate(GALLERY_COLORS, start=1):
            item = ProductGallery(product=product, order=order)
            item.image.save(f'demo-x70-gallery-{order}.jpg', make_image(f'Demo X70 - gallery {order}', color), save=False)
            item.save()

        return product
