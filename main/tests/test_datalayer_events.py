"""GTM dataLayer events (docs/GA4_DATALAYER_EVENTS.md): the helper, view_model,
slugs on the test-drive options and data-track attributes are in the HTML,
and no visitor-typed values are wired into the dataLayer."""

import re

from django.test import TestCase

from main.dealer_info import dealer_card
from main.models import Dealer, Product, ProductCategory, ProductTrim


class DataLayerEventsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.brand = ProductCategory.objects.create(name='Jetour', slug='jetour')
        cls.product = Product.objects.create(
            title='T1', title_uz='T1', slug='jetour-t1', category=cls.brand,
            main_image='products/main/none.jpg', is_active=True,
        )
        ProductTrim.objects.create(product=cls.product, name='Luxury', price=420_000_000, is_active=True)
        ProductTrim.objects.create(product=cls.product, name='Base', price=389_000_000, is_active=True)
        cls.dealer = Dealer.objects.create(name='Jetour Yunusobod', region='toshkent-shahri', is_active=True)

    def html(self, url):
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, url)
        return response.content.decode('utf-8')

    def test_helper_on_every_page(self):
        for url in ('/', '/contact/', '/test-drive/', '/products/jetour-t1/'):
            self.assertEqual(self.html(url).count('w.autoligaTrack = {'), 1, url)

    def test_view_model(self):
        html = self.html('/products/jetour-t1/')
        push = re.search(r"event: 'view_model',(.*?)\}\);", html, re.S).group(1)
        push = push.replace('\\u002D', '-')  # escapejs; the same string once the browser parses the JS
        self.assertIn("car_model: 'jetour-t1'", push)
        self.assertIn("car_brand: 'jetour'", push)
        self.assertRegex(push, r'price_from: 389000000\s*$')

    def test_product_page_form_and_buttons(self):
        html = self.html('/products/jetour-t1/')
        self.assertIn('id="faw-contact-form" data-car-model="jetour-t1" data-car-brand="jetour"', html)
        self.assertIn("form_type: 'price'", html)
        self.assertIn('data-track="test_drive_button" data-model="jetour-t1"', html)
        self.assertNotIn('lead_form_submitted', html)

    def test_test_drive_options_carry_slugs(self):
        html = self.html('/test-drive/')
        self.assertIn('data-model="jetour-t1" data-brand="jetour"', html)
        self.assertIn(f'value="{self.dealer.id}" data-slug="jetour-yunusobod"', html)
        self.assertIn('form_type: "test_drive"', html)
        self.assertNotIn('test_drive_submitted', html)

    def test_contact_forms(self):
        self.assertIn('page_type: "home"', self.html('/'))
        self.assertIn("form_type: 'review'", self.html('/'))
        self.assertIn('page_type: "contact"', self.html('/contact/'))

    def test_dealer_slug_falls_back_to_id(self):
        dealer = Dealer(id=7, name='', region='toshkent-shahri')
        self.assertEqual(dealer_card(dealer, 'uz')['slug'], '7')

    def test_no_personal_fields_in_lead_pushes(self):
        """Every lead_submit / form_start goes through the helper, whose key list has no PII."""
        for url in ('/', '/contact/', '/test-drive/', '/products/jetour-t1/'):
            html = self.html(url)
            keys = re.search(r"var KEYS = \[(.*?)\]", html).group(1)
            for field in ('name', 'phone', 'message', 'region'):
                self.assertNotIn(f"'{field}'", keys)
            self.assertNotRegex(html, r"dataLayer\.push\(\{\s*event:\s*['\"]lead_")
