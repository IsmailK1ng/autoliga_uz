# seo/models.py
"""
SEO of the static pages and the generic FAQ (admin section "SEO").

PageSEO: title / description / og:image of one static page, per language. A value is used
only when it is filled and passes the length rules below; otherwise the page keeps its
template default (never an empty tag). H1 stays in the templates (marketing decision).

FAQItem: question + answer of a static page (via its PageSEO) or of a model page (Product),
exactly one of the two.
"""

from ckeditor.fields import RichTextField
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from main.seo import clean

TITLE_LENGTH = (30, 65)
DESCRIPTION_LENGTH = (120, 160)


def valid_text(value, bounds):
    """Whitespace-collapsed value when its length is within bounds, else ''."""
    value = clean(value)
    return value if bounds[0] <= len(value) <= bounds[1] else ''


class PageSEO(models.Model):
    """Мета-данные статической страницы"""

    PAGE_CHOICES = [
        ('home', 'Главная ( / )'),
        ('products', 'Модели ( /products/ )'),
        ('dealers', 'Дилеры ( /dealers/ )'),
        ('news', 'Новости ( /news/ )'),
        ('contact', 'Контакты ( /contact/ )'),
        ('team', 'Команда ( /team/ )'),
        ('test_drive', 'Тест-драйв ( /test-drive/ )'),
    ]

    page_key = models.CharField("Страница", max_length=20, choices=PAGE_CHOICES, unique=True)
    title = models.CharField(
        "SEO-заголовок (title)",
        max_length=TITLE_LENGTH[1],
        blank=True,
        help_text="30–65 символов. Пустое или неверной длины — на странице остаётся заголовок по умолчанию",
    )
    description = models.CharField(
        "SEO-описание (description)",
        max_length=DESCRIPTION_LENGTH[1],
        blank=True,
        help_text="120–160 символов. Пустое или неверной длины — на странице остаётся описание по умолчанию",
    )
    og_image = models.ImageField(
        "Картинка для соцсетей (og:image)",
        upload_to='seo/og/',
        blank=True,
        help_text="Рекомендуется 1200×630. Пустое — картинка по умолчанию",
    )
    is_active = models.BooleanField(
        "Активна",
        default=True,
        help_text="Выключено — страница использует значения по умолчанию и не показывает FAQ",
    )
    updated_at = models.DateTimeField("Изменено", auto_now=True)

    class Meta:
        verbose_name = "SEO страницы"
        verbose_name_plural = "SEO — мета-данные страниц"
        ordering = ['page_key']

    def __str__(self):
        return self.get_page_key_display()

    def meta(self, language):
        """dict(title, description) for a language: only values that pass the length rules, else ''."""
        return {
            'title': valid_text(getattr(self, f'title_{language}', ''), TITLE_LENGTH),
            'description': valid_text(getattr(self, f'description_{language}', ''), DESCRIPTION_LENGTH),
        }


class FAQItem(models.Model):
    """Вопрос-ответ статической страницы или модели"""

    page = models.ForeignKey(
        PageSEO,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='faq_items',
        verbose_name="Страница",
    )
    product = models.ForeignKey(
        'main.Product',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='faq_items',
        verbose_name="Модель",
    )
    question = models.CharField("Вопрос", max_length=255)
    answer = RichTextField("Ответ", config_name='default')
    order = models.PositiveIntegerField("Порядок", default=0)
    is_active = models.BooleanField("Активен", default=True)

    class Meta:
        verbose_name = "Вопрос-ответ (FAQ)"
        verbose_name_plural = "FAQ — вопросы и ответы"
        ordering = ['order', 'id']
        constraints = [
            models.CheckConstraint(
                check=Q(page__isnull=False, product__isnull=True) | Q(page__isnull=True, product__isnull=False),
                name='seo_faqitem_exactly_one_target',
            ),
        ]

    def __str__(self):
        return self.question

    def clean(self):
        # "neither" is checked by the FAQ form (an inline of an unsaved page has no id yet) and the DB constraint
        if self.page_id and self.product_id:
            raise ValidationError("Вопрос относится либо к странице, либо к модели — не к обеим сразу.")

    @property
    def target(self):
        return self.page or self.product
