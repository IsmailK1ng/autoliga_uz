# main/serializers.py

from rest_framework import serializers
import logging

logger = logging.getLogger('django')
from main.serializers_base import LanguageSerializerMixin

from .models import (
    News, NewsBlock, ContactForm, JobApplication,
    Product, FeatureIcon, ProductCardSpec, ProductParameter, ProductFeature, ProductGallery, ProductCategory,
    Vacancy, VacancyResponsibility, VacancyRequirement, VacancyCondition, VacancyIdealCandidate
)


# ========== НОВОСТИ ==========

class NewsBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsBlock
        fields = '__all__'


class NewsSerializer(serializers.ModelSerializer):
    blocks = NewsBlockSerializer(many=True, read_only=True)

    class Meta:
        model = News
        fields = '__all__'


# ========== ЗАЯВКИ ==========

class ContactFormSerializer(serializers.ModelSerializer):
    manager_name = serializers.CharField(source='manager.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    region_display = serializers.CharField(source='get_region_display', read_only=True)

    class Meta:
        model = ContactForm
        fields = [
            'id', 'name', 'phone', 'region', 'region_display',
            'product', 'referer', 'utm_data', 'visitor_uid',
            'message', 'status', 'status_display',
            'priority', 'priority_display',
            'manager', 'manager_name', 'admin_comment', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'status_display', 'priority_display', 'region_display']

    def validate_visitor_uid(self, value):
        """Валидация visitor_uid от amoCRM Pixel"""
        if value:
            if not (value.replace('-', '').replace('_', '').isalnum() and len(value) <= 100):
                raise serializers.ValidationError("Невалидный visitor_uid")
        return value

    def create(self, validated_data):
        import json
        from urllib.parse import urlparse, parse_qs

        validated_data.setdefault('status', 'new')
        validated_data.setdefault('priority', 'medium')

        request = self.context.get('request')

        if request:
            if not validated_data.get('referer'):
                referer = request.META.get('HTTP_REFERER')
                if referer:
                    validated_data['referer'] = referer

            utm_from_body = validated_data.get('utm_data')

            if utm_from_body:
                if isinstance(utm_from_body, str):
                    pass
                elif isinstance(utm_from_body, dict):
                    validated_data['utm_data'] = json.dumps(utm_from_body, ensure_ascii=False)
            else:
                referer = validated_data.get('referer') or request.META.get('HTTP_REFERER')

                if referer:
                    parsed = urlparse(referer)
                    query_params = parse_qs(parsed.query)

                    utm_params = {}
                    for key in ['utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content']:
                        if key in query_params:
                            utm_params[key] = query_params[key][0]

                    if utm_params:
                        validated_data['utm_data'] = json.dumps(utm_params, ensure_ascii=False)

        contact_form = super().create(validated_data)
        return contact_form


class JobApplicationSerializer(serializers.ModelSerializer):
    """Заявки на вакансии с валидацией резюме"""
    vacancy_title = serializers.CharField(source='vacancy.title', read_only=True)

    class Meta:
        model = JobApplication
        fields = ['id', 'vacancy', 'vacancy_title', 'region', 'resume', 'created_at']
        read_only_fields = ['id', 'created_at', 'vacancy_title']

    def validate_resume(self, value):
        """Валидация файла резюме"""
        try:
            # Проверка размера (10 MB)
            if value.size > 10 * 1024 * 1024:
                raise serializers.ValidationError("Fayl hajmi juda katta. Maksimal 10 MB")

            # Проверка формата
            allowed_extensions = ['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png']
            file_ext = value.name.lower().split('.')[-1]
            if file_ext not in allowed_extensions:
                raise serializers.ValidationError("Noto'g'ri fayl formati. PDF, DOC, DOCX, JPG yoki PNG foydalaning")

            return value

        except serializers.ValidationError:
            raise  # Пробрасываем ValidationError
        except Exception as e:
            logger.error(f"Критическая ошибка валидации резюме: {str(e)}", exc_info=True)
            raise serializers.ValidationError("Xatolik yuz berdi")


# ========== ПРОДУКТЫ ==========

class FeatureIconSerializer(serializers.ModelSerializer):
    """Иконки для характеристик"""
    icon_url = serializers.SerializerMethodField()

    class Meta:
        model = FeatureIcon
        fields = ['id', 'name', 'icon_url']

    def get_icon_url(self, obj):
        request = self.context.get('request')
        if obj.icon:
            if request:
                return request.build_absolute_uri(obj.icon.url)
            return obj.icon.url
        return None


class ProductCardSpecSerializer(serializers.ModelSerializer):
    """4 характеристики для карточки продукта"""
    icon = FeatureIconSerializer(read_only=True)

    class Meta:
        model = ProductCardSpec
        fields = ['id', 'icon', 'value', 'order']


class ProductCardSerializer(LanguageSerializerMixin, serializers.ModelSerializer):
    """Карточки продуктов для списка"""
    card_specs = ProductCardSpecSerializer(many=True, read_only=True)
    image_url = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'title', 'slug',
            'category',
            'image_url', 'card_specs', 'is_featured', 'order'
        ]

    def get_category(self, obj):
        """Возвращает одну категорию"""
        if obj.category and obj.category.is_active:
            language = self.get_current_language()  # ✅ Теперь работает
            name = getattr(obj.category, f'name_{language}', None) or obj.category.name
            return {
                'id': obj.category.id,
                'slug': obj.category.slug,
                'name': name
            }
        return None

    def get_image_url(self, obj):
        """Возвращает URL изображения для карточки"""
        image = obj.card_image if obj.card_image else obj.main_image
        if image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(image.url)
            return image.url
        return None


class ProductFeatureSerializer(LanguageSerializerMixin, serializers.ModelSerializer):
    """8 характеристик с иконками"""
    icon = FeatureIconSerializer(read_only=True)
    name = serializers.SerializerMethodField()

    class Meta:
        model = ProductFeature
        fields = ['id', 'icon', 'name', 'order']

    def get_name(self, obj):
        lang = self.get_current_language()
        return getattr(obj, f'name_{lang}', None) or obj.name


class ProductGallerySerializer(serializers.ModelSerializer):
    """Галерея продукта"""
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ProductGallery
        fields = ['id', 'image_url', 'order']

    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class ProductDetailSerializer(LanguageSerializerMixin, serializers.ModelSerializer):
    """Детальная страница продукта"""
    card_specs = ProductCardSpecSerializer(many=True, read_only=True)
    spec_groups = serializers.SerializerMethodField()
    features = ProductFeatureSerializer(many=True, read_only=True)
    gallery = ProductGallerySerializer(many=True, read_only=True)
    main_image_url = serializers.SerializerMethodField()
    card_image_url = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'title', 'slug',
            'category',
            'main_image_url', 'card_image_url',
            'card_specs', 'spec_groups', 'features', 'gallery',
            'is_active', 'is_featured', 'order'
        ]

    def get_category(self, obj):
        if obj.category and obj.category.is_active:
            language = self.get_current_language()
            name = getattr(obj.category, f'name_{language}', None) or obj.category.name
            description = getattr(obj.category, f'description_{language}', None) or obj.category.description or ''
            return {
                'id': obj.category.id,
                'slug': obj.category.slug,
                'name': name,
                'description': description
            }
        return None

    def get_title(self, obj):
        lang = self.get_current_language()
        return getattr(obj, f'title_{lang}', None) or obj.title

    def get_spec_groups(self, obj):
        language = self.get_current_language()

        # ✅ ДИНАМИК: ParameterCategory ForeignKey dan nom olish
        parameters = obj.parameters.select_related('category').all().order_by(
            'category__order', 'order'
        )

        grouped = {}
        order_map = {}

        for param in parameters:
            cat_obj = param.category

            if cat_obj is None:
                cat_key = 0
                cat_name = '—'
                cat_order = 9999
            else:
                cat_key = cat_obj.id
                # 3 tilda nom olish
                cat_name = getattr(cat_obj, f'name_{language}', None) or cat_obj.name or '—'
                cat_order = cat_obj.order

            if cat_key not in grouped:
                grouped[cat_key] = {
                    'category_name': cat_name,
                    'parameters': []
                }
                order_map[cat_key] = cat_order

            text_value = getattr(param, f'text_{language}', None) or param.text or ''
            grouped[cat_key]['parameters'].append({
                'id': param.id,
                'text': text_value,
                'order': param.order
            })

        # Kategoriya order bo'yicha saralash
        result = [
            grouped[k]
            for k in sorted(grouped.keys(), key=lambda k: order_map.get(k, 9999))
        ]

        return result

    def get_main_image_url(self, obj):
        if obj.main_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.main_image.url)
            return obj.main_image.url
        return None

    def get_card_image_url(self, obj):
        if obj.card_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.card_image.url)
            return obj.card_image.url
        return None


class ProductCategorySerializer(LanguageSerializerMixin, serializers.ModelSerializer):
    """Сериализатор для категорий продуктов"""
    name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    hero_image_url = serializers.SerializerMethodField()

    class Meta:
        model = ProductCategory
        fields = ['id', 'slug', 'name', 'description', 'hero_image_url', 'order']  # ✅ Убрали icon_url

    def get_name(self, obj):
        """Название на текущем языке"""
        lang = self.get_current_language()
        return getattr(obj, f'name_{lang}', None) or obj.name

    def get_description(self, obj):
        """Описание на текущем языке"""
        lang = self.get_current_language()
        return getattr(obj, f'description_{lang}', None) or obj.description or ''

    def get_hero_image_url(self, obj):
        """URL фонового изображения"""
        if obj.hero_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.hero_image.url)
            return obj.hero_image.url
        return None


# ========== СЕРИАЛИЗАТОР ДЛЯ ВАКАНСИЙ ==========

class VacancySerializer(LanguageSerializerMixin, serializers.ModelSerializer):
    """Вакансии с поддержкой переводов"""
    title = serializers.SerializerMethodField()
    short_description = serializers.SerializerMethodField()
    contact_info = serializers.SerializerMethodField()
    responsibilities = serializers.SerializerMethodField()
    requirements = serializers.SerializerMethodField()
    conditions = serializers.SerializerMethodField()
    ideal_candidates = serializers.SerializerMethodField()

    class Meta:
        model = Vacancy
        fields = [
            'id', 'title', 'short_description', 'contact_info',
            'responsibilities', 'requirements', 'conditions', 'ideal_candidates',
            'is_active', 'created_at'
        ]

    def get_title(self, obj):
        lang = self.get_current_language()
        return getattr(obj, f'title_{lang}', None) or obj.title

    def get_short_description(self, obj):
        lang = self.get_current_language()
        return getattr(obj, f'short_description_{lang}', None) or obj.short_description or ''

    def get_contact_info(self, obj):
        lang = self.get_current_language()
        return getattr(obj, f'contact_info_{lang}', None) or obj.contact_info or ''

    def get_responsibilities(self, obj):
        lang = self.get_current_language()
        responsibilities = obj.responsibilities.all().order_by('order')
        return [
            {
                'id': item.id,
                'title': getattr(item, f'title_{lang}', None) or item.title or '',
                'text': getattr(item, f'text_{lang}', None) or item.text or ''
            }
            for item in responsibilities
        ]

    def get_requirements(self, obj):
        lang = self.get_current_language()
        requirements = obj.requirements.all().order_by('order')
        return [
            {
                'id': item.id,
                'text': getattr(item, f'text_{lang}', None) or item.text or ''
            }
            for item in requirements
        ]

    def get_conditions(self, obj):
        lang = self.get_current_language()
        conditions = obj.conditions.all().order_by('order')
        return [
            {
                'id': item.id,
                'text': getattr(item, f'text_{lang}', None) or item.text or ''
            }
            for item in conditions
        ]

    def get_ideal_candidates(self, obj):
        lang = self.get_current_language()
        candidates = obj.ideal_candidates.all().order_by('order')
        return [
            {
                'id': item.id,
                'text': getattr(item, f'text_{lang}', None) or item.text or ''
            }
            for item in candidates
        ]