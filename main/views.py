# main/views.py

from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import translation
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser
from django.http import HttpResponseRedirect
from rest_framework.decorators import api_view, permission_classes
from rest_framework.throttling import AnonRateThrottle
from .models import (
    News, ContactForm, JobApplication, Vacancy, Product, ProductCategory, Dealer, DealerImage, Review, TestDriveRequest, BranchManager
)
from .serializers import (
    NewsSerializer, ContactFormSerializer, JobApplicationSerializer,
    ProductCardSerializer, ProductDetailSerializer, ProductCategorySerializer,
    ReviewListSerializer, ReviewCreateSerializer, TestDriveSerializer,
    BotTelegramUserSerializer, BotDealerSerializer, BotBrandSerializer,
    BotCarSerializer, BotTestDriveSerializer,
)
from .models import TelegramUser
import logging
import json
from django.db.models import Prefetch


logger = logging.getLogger('django')

from django.utils import timezone

def current_year(request):
    return {'current_year': timezone.now().year}

# === FRONTEND views === 



def index(request):
    """Главная страница с динамическим слайдером"""
    try:
        from django.utils.translation import get_language
        current_lang = get_language()
        
        news_list = News.objects.filter(
            is_active=True
        ).select_related('author').order_by('-order', '-created_at')[:8]
        
        featured_products = Product.objects.filter(
            is_active=True,
            is_featured=True
        ).order_by('-slider_order', '-created_at')[:10]
        
        productCategory = ProductCategory.objects.filter(
            is_active=True
        ).prefetch_related(
            Prefetch(
                'products',
                queryset=Product.objects.filter(
                    is_active=True
                ).only('id', 'slug', 'title', 'main_image'),  # faqat kerakli fieldlar
                to_attr='active_products'  #  cache'ga oladi
            )
        )





        slider_data = []
        for product in featured_products:
            title = getattr(product, f'title_{current_lang}', None) or product.title
            price = getattr(product, f'slider_price_{current_lang}', None) or product.slider_price or 'Narx so\'rang'
            power = getattr(product, f'slider_power_{current_lang}', None) or product.slider_power or '—'
            fuel = getattr(product, f'slider_fuel_consumption_{current_lang}', None) or product.slider_fuel_consumption or '—'
            
            slider_item = {
                'year': product.slider_year,
                'title': title,
                'price': price,
                'power': power,
                'mpg': fuel,
                'image': None,
                'link': f'/products/{product.slug}/',
            }
            
            if product.slider_image:
                slider_item['image'] = product.slider_image.url
            elif product.main_image:
                slider_item['image'] = product.main_image.url
            
            slider_data.append(slider_item)
        
        # Менеджеры для секции "Наша команда"
        team_managers = BranchManager.objects.filter(
            is_active=True
        ).select_related('dealer').order_by('order', 'id')

        context = {
            'news_list': news_list,
            'slider_products': json.dumps(slider_data, ensure_ascii=False),
            'featured_count': len(slider_data),
            'productCategory': productCategory,
            'RECAPTCHA_SITE_KEY': getattr(settings, 'RECAPTCHA_SITE_KEY', ''),
            'team_managers': team_managers,
        }
        
        return render(request, 'main/index.html', context)
    
    except Exception as e:
        logger.error(f"Ошибка на главной странице: {str(e)}", exc_info=True)
        return render(request, 'main/index.html', {'slider_products': '[]', 'news_list': []})





def about(request):
    return render(request, 'main/about.html')





def contact(request):
    return render(request, 'main/contact.html')


def services(request):
    return render(request, 'main/services.html')


def product_detail(request, product_id):
    return render(request, 'main/product_detail.html', {'product_id': product_id})

def lizing(request):
    return render(request, 'main/lizing.html')


def news(request):
    """Страница со всеми новостями"""
    try:
        news_list = News.objects.filter(
            is_active=True
        ).select_related('author').order_by('-order', '-created_at')
        
        return render(request, 'main/news.html', {'news_list': news_list})
    
    except Exception as e:
        logger.error(f"Ошибка на странице новостей: {str(e)}", exc_info=True)
        return render(request, 'main/news.html', {'news_list': []})


def dealers(request):
    dealers_qs = Dealer.objects.filter(is_active=True).order_by('order', 'name')
    dealers_data = []
    for d in dealers_qs:
        # modeltranslation: d.name joriy tilga qarab qaytaradi.
        # Agar bo'sh bo'lsa, boshqa tillardan olish
        name = (d.name or
                getattr(d, 'name_uz', '') or
                getattr(d, 'name_ru', '') or
                getattr(d, 'name_en', '') or '')
        address = (d.address or
                   getattr(d, 'address_uz', '') or
                   getattr(d, 'address_ru', '') or
                   getattr(d, 'address_en', '') or '')
        working_hours = (d.working_hours or
                         getattr(d, 'working_hours_uz', '') or
                         getattr(d, 'working_hours_ru', '') or
                         getattr(d, 'working_hours_en', '') or '')
        dealers_data.append({
            'id': d.id,
            'name': name,
            'region': d.region,
            'address': address,
            'phone': d.phone or '',
            'working_hours': working_hours,
            'instagram': d.instagram or '',
            'telegram': d.telegram or '',
            'facebook': d.facebook or '',
            'youtube': d.youtube or '',
            'logo': d.logo.url if d.logo else '',
            'lat': float(d.latitude) if d.latitude else None,
            'lng': float(d.longitude) if d.longitude else None,
            'detail_url': d.get_absolute_url(),
        })
    return render(request, 'main/dealers.html', {
        'dealers_json': json.dumps(dealers_data, ensure_ascii=False),
    })


def team(request):
    """Страница команды — менеджеры по филиалам"""
    dealers_with_managers = Dealer.objects.filter(
        is_active=True,
        managers__is_active=True
    ).prefetch_related('managers').distinct().order_by('order', 'name')
    return render(request, 'main/team.html', {
        'dealers': dealers_with_managers,
    })


def dealer_detail(request, pk):
    """Diler markazi batafsil sahifasi"""
    dealer = get_object_or_404(
        Dealer.objects.prefetch_related('images', 'managers'),
        pk=pk,
        is_active=True
    )
    images = dealer.images.all().order_by('order')
    managers = dealer.managers.filter(is_active=True).order_by('order', 'full_name')

    return render(request, 'main/dealer_detail.html', {
        'dealer': dealer,
        'images': images,
        'managers': managers,
    })


def test_drive(request):
    """Страница записи на тест-драйв"""
    products = Product.objects.filter(is_active=True).order_by('order', 'title')
    products_data = [{'id': p.id, 'title': p.title} for p in products]

    dealers = Dealer.objects.filter(is_active=True).order_by('order', 'name')
    dealers_data = [{'id': d.id, 'name': d.name, 'address': d.address or ''} for d in dealers]

    return render(request, 'main/test_drive.html', {
        'products_json': json.dumps(products_data, ensure_ascii=False),
        'dealers_json': json.dumps(dealers_data, ensure_ascii=False),
        'RECAPTCHA_SITE_KEY': getattr(settings, 'RECAPTCHA_SITE_KEY', ''),
    })


def jobs(request):
    """Страница с вакансиями"""
    try:
        from .serializers import VacancySerializer
        
        vacancies = Vacancy.objects.filter(is_active=True).prefetch_related(
            'responsibilities', 
            'requirements', 
            'ideal_candidates',
            'conditions'
        ).order_by('order', '-created_at')
        
        serializer = VacancySerializer(vacancies, many=True, context={'request': request})
        vacancies_data = serializer.data
        
        return render(request, 'main/jobs.html', {
            'vacancies': vacancies,
            'vacancies_data': vacancies_data
        })
    
    except Exception as e:
        logger.error(f"Ошибка на странице вакансий: {str(e)}", exc_info=True)
        return render(request, 'main/jobs.html', {'vacancies': [], 'vacancies_data': []})


def news_detail(request, slug):
    """Детальная страница новости"""
    try:
        news = get_object_or_404(
            News.objects.prefetch_related('blocks'), 
            slug=slug, 
            is_active=True
        )
        
        language = getattr(request, 'LANGUAGE_CODE', 'uz')
        breadcrumbs = {
            'uz': {
                'home': 'Bosh sahifa',
                'news': 'Autoliga yangiliklar',
                'current': news.title_uz if hasattr(news, 'title_uz') else news.title
            },
            'ru': {
                'home': 'Главная',
                'news': 'Новости Autoliga',
                'current': news.title_ru if hasattr(news, 'title_ru') else news.title
            },
            'en': {
                'home': 'Home',
                'news': 'Autoliga News',
                'current': news.title_en if hasattr(news, 'title_en') else news.title
            }
        }
        
        return render(request, 'main/news_detail.html', {
            'news': news,
            'blocks': news.blocks.all(),
            'breadcrumbs': breadcrumbs.get(language, breadcrumbs['uz'])
        })
    
    except Exception as e:
        logger.error(f"Ошибка на странице новости {slug}: {str(e)}", exc_info=True)
        return redirect('news')


def set_language_get(request):
    """Переключение языка ТОЛЬКО для сайта"""
    language = request.GET.get('language') or request.POST.get('language')
    
    if language and language in ['uz', 'ru', 'en']:
        request.session['_language'] = language
        next_url = request.META.get('HTTP_REFERER', '/')
        
        response = redirect(next_url)
        response.set_cookie(
            settings.LANGUAGE_COOKIE_NAME,
            language,
            max_age=365*24*60*60,
            path='/',
            samesite='Lax'
        )
        return response
    
    return redirect('/')


# === API ViewSets ===

class NewsViewSet(viewsets.ModelViewSet):
    """API endpoint для CRUD операций с новостями"""
    serializer_class = NewsSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        return News.objects.select_related('author').prefetch_related('blocks').order_by('-created_at')


from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.decorators import permission_classes

class ContactFormViewSet(viewsets.ModelViewSet):
    serializer_class = ContactFormSerializer
    
    # ✅ ИСПРАВЛЕНО: Разные права для разных методов
    def get_permissions(self):
        if self.action in ['create']:
            # POST требует CSRF в headers
            return [AllowAny()]
        else:
            # GET/PUT/DELETE только для админов
            return [IsAdminUser()]
    
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'priority', 'region', 'amocrm_status'] 
    search_fields = ['name', 'phone']
    ordering_fields = ['created_at', 'priority']
    
    
    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            contact_form = serializer.save()
            
            # Отправляем в amoCRM
            try:
                from main.services.amocrm.lead_sender import LeadSender
                LeadSender.send_lead(contact_form)
                contact_form.refresh_from_db()
            except Exception as amocrm_error:
                logger.error(
                    f"Ошибка amoCRM для лида #{contact_form.id}: {str(amocrm_error)}", 
                    exc_info=True
                )
            
            # Отправляем в Telegram (ПОСЛЕ amoCRM)
            try:
                from main.services.telegram import TelegramNotificationSender
                TelegramNotificationSender.send_lead_notification(contact_form)
            except Exception as telegram_error:
                logger.error(
                    f"Ошибка Telegram для лида #{contact_form.id}: {str(telegram_error)}", 
                    exc_info=True
                )
            
            return Response({
                'success': True,
                'message': 'Xabar yuborildi!'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Критическая ошибка создания формы: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'message': 'Xatolik yuz berdi.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

class JobApplicationViewSet(viewsets.ModelViewSet):
    """API endpoint для приема заявок на вакансии"""
    serializer_class = JobApplicationSerializer
    
    def get_queryset(self):
        """✅ Оптимизация: загружаем вакансию сразу"""
        return JobApplication.objects.select_related('vacancy').order_by('-created_at')
    
    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        else:
            return [IsAdminUser()]
    
    def create(self, request, *args, **kwargs):
        """Создание новой заявки с резюме"""
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            
            return Response({
                'success': True,
                'message': 'Rezyume muvaffaqiyatli yuborildi! Tez orada siz bilan bog\'lanamiz.',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            logger.error(f"Ошибка создания заявки на вакансию: {str(e)}", exc_info=True)
            return Response({
                'success': False, 
                'message': 'Xatolik yuz berdi'
            }, status=500)
    
    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def unprocessed(self, request):
        """Получить необработанные заявки"""
        try:
            unprocessed = self.get_queryset().filter(is_processed=False)
            serializer = self.get_serializer(unprocessed, many=True)
            return Response({
                'count': unprocessed.count(),
                'results': serializer.data
            })
        except Exception as e:
            logger.error(f"Ошибка получения необработанных заявок: {str(e)}", exc_info=True)
            return Response({'error': 'Internal error'}, status=500)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def mark_processed(self, request, pk=None):
        """Отметить заявку как обработанную"""
        try:
            application = self.get_object()
            application.is_processed = True
            application.save()
            return Response({
                'status': 'processed',
                'message': f'Ariza #{application.id} ko\'rib chiqilgan deb belgilandi'
            })
        except Exception as e:
            logger.error(f"Ошибка обновления заявки #{pk}: {str(e)}", exc_info=True)
            return Response({'error': 'Internal error'}, status=500)


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """API для продуктов"""
    permission_classes = [AllowAny]
    lookup_field = 'slug'
    
    def get_queryset(self):
        try:
            queryset = Product.objects.filter(is_active=True).select_related(
                'category'  # ✅ ИСПРАВЛЕНО: select_related вместо prefetch_related
            ).prefetch_related(
                'card_specs__icon',
                'parameters',
                'features__icon',
                'gallery'
            ).order_by('order', 'title')
            
            category_slug = self.request.query_params.get('category', None)
            if category_slug:
                queryset = queryset.filter(
                    category__slug=category_slug,  # ✅ ИСПРАВЛЕНО
                    category__is_active=True
                )
            
            return queryset
        except Exception as e:
            logger.error(f"Ошибка получения продуктов: {str(e)}", exc_info=True)
            return Product.objects.none()
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductCardSerializer

def products(request):
    """Страница со списком продуктов по категориям"""
    try:
        category_slug = request.GET.get('category')
        
        if category_slug:
            category = get_object_or_404(ProductCategory, slug=category_slug, is_active=True)
            language = getattr(request, 'LANGUAGE_CODE', 'uz')
            
            category_info = {
                'id': category.id,
                'title': getattr(category, f'name_{language}', None) or category.name,
                'slogan': getattr(category, f'description_{language}', None) or category.description or '',
                'hero_image': category.hero_image.url if category.hero_image else 'images/default_hero.png',
                'breadcrumb': getattr(category, f'name_{language}', None) or category.name
            }
        else:
            # Первая активная категория по умолчанию
            category = ProductCategory.objects.filter(is_active=True).order_by('order').first()
            if category:
                language = getattr(request, 'LANGUAGE_CODE', 'uz')
                category_info = {
                    'id': category.id,
                    'title': getattr(category, f'name_{language}', None) or category.name,
                    'slogan': getattr(category, f'description_{language}', None) or category.description or '',
                    'hero_image': category.hero_image.url if category.hero_image else 'images/default_hero.png',
                    'breadcrumb': getattr(category, f'name_{language}', None) or category.name
                }
                category_slug = category.slug
            else:
                category_info = {}
                category_slug = None
        
        # Получаем все категории для навигации
        all_categories = ProductCategory.objects.filter(is_active=True).order_by('order')
        
        return render(request, 'main/products.html', {
            'category_slug': category_slug,
            'category_info': category_info,
            'all_categories': all_categories
        })
    except Exception as e:
        logger.error(f"Ошибка на странице продуктов: {str(e)}", exc_info=True)
        return render(request, 'main/products.html', {
            'category_slug': None,
            'category_info': {},
            'all_categories': []
        })

@api_view(['POST'])
@permission_classes([AllowAny])
def log_js_error(request):
    """Логирование JS ошибок с фронтенда"""
    try:
        error_data = request.data
        
        message = error_data.get('message', 'Unknown error')
        source = error_data.get('source', 'Unknown source')
        lineno = error_data.get('lineno', 0)
        url = error_data.get('url', 'Unknown URL')
        
        logger.error(
            f"JavaScript Error: {message} | "
            f"Source: {source}:{lineno} | "
            f"Page: {url}",
            extra={'js_error': error_data}
        )
        
        return Response({'status': 'logged'})
    
    except Exception as e:
        logger.error(f"Ошибка логирования JS ошибки: {str(e)}", exc_info=True)
        return Response({'status': 'error'}, status=500)
    
class ProductCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """API для категорий продуктов"""
    serializer_class = ProductCategorySerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return ProductCategory.objects.filter(is_active=True).order_by('order')


class ReviewCreateThrottle(AnonRateThrottle):
    """1 ta IP dan kuniga faqat 1 ta comment"""
    scope = 'review_create'

    THROTTLE_MESSAGES = {
        'uz': "Siz allaqachon sharh qoldirgansiz. {wait} dan keyin qayta urinib ko'ring.",
        'ru': "Вы уже оставили отзыв. Попробуйте снова через {wait}.",
        'en': "You have already left a review. Please try again in {wait}.",
    }

    def get_cache_key(self, request, view):
        x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded:
            ip = x_forwarded.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return self.cache_format % {
            'scope': self.scope,
            'ident': ip,
        }

    def wait(self):
        return super().wait()

    def throttle_failure(self):
        return False


class ReviewViewSet(viewsets.GenericViewSet):
    """API для отзывов клиентов"""
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.action == 'create':
            return ReviewCreateSerializer
        return ReviewListSerializer

    def get_throttles(self):
        # Throttle create ichida qo'lda tekshiriladi (3 tilda xabar uchun)
        return []

    def get_queryset(self):
        return Review.objects.filter(status='approved').order_by('-created_at')

    def list(self, request, *args, **kwargs):
        """GET: список одобренных отзывов с пагинацией"""
        from rest_framework.pagination import PageNumberPagination

        class ReviewPagination(PageNumberPagination):
            page_size = 4
            page_size_query_param = 'page_size'
            max_page_size = 20

        paginator = ReviewPagination()
        queryset = self.get_queryset()
        page = paginator.paginate_queryset(queryset, request)
        serializer = self.get_serializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def create(self, request, *args, **kwargs):
        """POST: создание нового отзыва (с reCAPTCHA + rate limit)"""
        # Throttle tekshirish
        throttle = ReviewCreateThrottle()
        if not throttle.allow_request(request, self):
            wait = throttle.wait()
            lang = getattr(request, 'LANGUAGE_CODE', 'uz')
            if lang not in ReviewCreateThrottle.THROTTLE_MESSAGES:
                lang = 'uz'
            # Kutish vaqtini formatlaymiz
            if wait is not None:
                hours = int(wait // 3600)
                minutes = int((wait % 3600) // 60)
                if hours > 0:
                    wait_str = f"{hours} soat {minutes} minut" if lang == 'uz' else \
                               f"{hours} ч {minutes} мин" if lang == 'ru' else \
                               f"{hours}h {minutes}m"
                else:
                    wait_str = f"{minutes} minut" if lang == 'uz' else \
                               f"{minutes} мин" if lang == 'ru' else \
                               f"{minutes}m"
            else:
                wait_str = "1 soat" if lang == 'uz' else \
                           "1 час" if lang == 'ru' else "1 hour"
            message = ReviewCreateThrottle.THROTTLE_MESSAGES[lang].format(wait=wait_str)
            return Response({
                'success': False,
                'message': message,
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'success': True,
            'message': 'Спасибо! Ваш отзыв отправлен на проверку. После модерации он появится на сайте.'
        }, status=status.HTTP_201_CREATED)


class TestDriveViewSet(viewsets.GenericViewSet):
    """API для заявок на тест-драйв"""
    serializer_class = TestDriveSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return TestDriveRequest.objects.all().order_by('-created_at')

    def create(self, request, *args, **kwargs):
        """POST: создание заявки на тест-драйв"""
        # Kunlik limit: 1 telefon raqamdan 2 ta test-drayv
        phone = request.data.get('phone', '')
        if phone:
            from django.utils import timezone
            today = timezone.now().date()
            today_count = TestDriveRequest.objects.filter(
                phone=phone, created_at__date=today
            ).count()
            if today_count >= 2:
                return Response({
                    'success': False,
                    'message': 'Kuniga 2 tadan ortiq test-drayv ariza yuborib bo\'lmaydi.',
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        test_drive_obj = serializer.save()

        # Отправка в Telegram
        try:
            from main.services.telegram import TelegramNotificationSender
            TelegramNotificationSender.send_test_drive_notification(test_drive_obj)
        except Exception as e:
            logger.error(f"Ошибка Telegram для тест-драйва #{test_drive_obj.id}: {e}", exc_info=True)

        return Response({
            'success': True,
            'message': 'OK',
        }, status=status.HTTP_201_CREATED)


# ========== BOT API ==========

from rest_framework.views import APIView
from rest_framework.permissions import BasePermission
from django.core.cache import cache


class IsBotAuthenticated(BasePermission):
    """Bot API token tekshirish.
    Header: Authorization: Bearer <BOT_API_TOKEN>
    """
    def has_permission(self, request, view):
        token = settings.BOT_API_TOKEN
        if not token:
            # Token sozlanmagan — development da ruxsat berish
            return settings.DEBUG
        auth = request.META.get('HTTP_AUTHORIZATION', '')
        return auth == f'Bearer {token}'


class BotUserView(APIView):
    """GET ?telegram_id=123 — получить пользователя, POST — создать/обновить"""
    permission_classes = [IsBotAuthenticated]

    def get(self, request):
        tg_id = request.query_params.get('telegram_id')
        if not tg_id:
            return Response({'error': 'telegram_id required'}, status=400)
        try:
            user = TelegramUser.objects.get(telegram_id=int(tg_id))
            return Response(BotTelegramUserSerializer(user).data)
        except TelegramUser.DoesNotExist:
            return Response({'exists': False}, status=404)

    def post(self, request):
        tg_id = request.data.get('telegram_id')
        if not tg_id:
            return Response({'error': 'telegram_id required'}, status=400)
        user, created = TelegramUser.objects.get_or_create(telegram_id=int(tg_id))
        for field in ('username', 'first_name', 'age', 'phone', 'region', 'language'):
            val = request.data.get(field)
            if val is not None:
                setattr(user, field, val)
        user.save()
        return Response(BotTelegramUserSerializer(user).data, status=200 if not created else 201)


class BotBrandsView(APIView):
    """GET ?lang=uz — список брендов"""
    permission_classes = [IsBotAuthenticated]

    def get(self, request):
        lang = request.query_params.get('lang', 'uz')
        cache_key = f'bot:brands:{lang}'
        data = cache.get(cache_key)
        if data is None:
            brands = ProductCategory.objects.filter(is_active=True).order_by('order', 'name')
            data = [{'id': b.id, 'name': getattr(b, f'name_{lang}', None) or b.name} for b in brands]
            cache.set(cache_key, data, timeout=600)  # 10 minut
        return Response(data)


class BotCarsView(APIView):
    """GET ?brand_id=1&lang=uz — список машин бренда"""
    permission_classes = [IsBotAuthenticated]

    def get(self, request):
        brand_id = request.query_params.get('brand_id')
        lang = request.query_params.get('lang', 'uz')
        if not brand_id:
            return Response({'error': 'brand_id required'}, status=400)
        cache_key = f'bot:cars:{brand_id}:{lang}'
        data = cache.get(cache_key)
        if data is None:
            cars = Product.objects.filter(category_id=int(brand_id), is_active=True).order_by('order', 'title')
            data = [{'id': c.id, 'title': getattr(c, f'title_{lang}', None) or c.title} for c in cars]
            cache.set(cache_key, data, timeout=600)
        return Response(data)


class BotCarDetailView(APIView):
    """GET ?car_id=1&lang=uz — детали машины"""
    permission_classes = [IsBotAuthenticated]

    def get(self, request):
        car_id = request.query_params.get('car_id')
        lang = request.query_params.get('lang', 'uz')
        if not car_id:
            return Response({'error': 'car_id required'}, status=400)
        cache_key = f'bot:car:{car_id}:{lang}'
        data = cache.get(cache_key)
        if data is None:
            try:
                c = Product.objects.get(id=int(car_id))
            except Product.DoesNotExist:
                return Response({'error': 'not found'}, status=404)

            title = getattr(c, f'title_{lang}', None) or c.title
            price = getattr(c, f'slider_price_{lang}', None) or c.slider_price
            power = getattr(c, f'slider_power_{lang}', None) or c.slider_power
            fuel = getattr(c, f'slider_fuel_consumption_{lang}', None) or c.slider_fuel_consumption

            features = c.features.all().order_by('order')[:6]
            feat_list = [getattr(f, f'name_{lang}', None) or f.name for f in features]

            data = {
                'title': title,
                'main_image': c.main_image.url if c.main_image else None,
                'card_image': c.card_image.url if c.card_image else None,
                'price': price,
                'year': c.slider_year,
                'power': power,
                'fuel': fuel,
                'features': feat_list,
            }
            cache.set(cache_key, data, timeout=600)
        return Response(data)


class BotDealersView(APIView):
    """GET ?lang=uz — список дилеров"""
    permission_classes = [IsBotAuthenticated]

    def get(self, request):
        lang = request.query_params.get('lang', 'uz')
        cache_key = f'bot:dealers:{lang}'
        data = cache.get(cache_key)
        if data is None:
            dealers = Dealer.objects.filter(is_active=True).order_by('order', 'name')
            data = []
            for d in dealers:
                data.append({
                    'id': d.id,
                    'name': getattr(d, f'name_{lang}', None) or d.name,
                    'region': d.region,
                    'address': getattr(d, f'address_{lang}', None) or d.address,
                    'phone': d.phone,
                    'hours': getattr(d, f'working_hours_{lang}', None) or d.working_hours,
                })
            cache.set(cache_key, data, timeout=600)
        return Response(data)


class BotTestDriveView(APIView):
    """POST — создать заявку на тест-драйв из бота"""
    permission_classes = [IsBotAuthenticated]

    def get(self, request):
        """GET — список дилеров и продуктов для формы"""
        lang = request.query_params.get('lang', 'uz')
        dealers = Dealer.objects.filter(is_active=True).order_by('order', 'name')
        products = Product.objects.filter(is_active=True).order_by('order', 'title')
        return Response({
            'dealers': [{'id': d.id, 'name': getattr(d, f'name_{lang}', None) or d.name} for d in dealers],
            'products': [{'id': p.id, 'title': getattr(p, f'title_{lang}', None) or p.title} for p in products],
            'time_slots': ['10:00', '10:30', '11:00', '11:30', '12:00', '12:30',
                           '13:00', '13:30', '14:00', '14:30', '15:00', '15:30',
                           '16:00', '16:30', '17:00'],
        })

    def post(self, request):
        # Kunlik limit: 1 telefon raqamdan 2 ta test-drayv
        phone = request.data.get('phone', '')
        if phone:
            from django.utils import timezone
            today = timezone.now().date()
            today_count = TestDriveRequest.objects.filter(
                phone=phone, created_at__date=today
            ).count()
            if today_count >= 2:
                return Response({
                    'success': False,
                    'error': 'daily_limit',
                    'message': 'Kuniga 2 tadan ortiq test-drayv ariza yuborib bo\'lmaydi.'
                }, status=429)

        serializer = BotTestDriveSerializer(data=request.data)
        if serializer.is_valid():
            obj = serializer.save()
            try:
                from main.services.telegram import TelegramNotificationSender
                TelegramNotificationSender.send_test_drive_notification(obj)
            except Exception as e:
                logger.error(f"Telegram notification error: {e}", exc_info=True)
            return Response({'success': True, 'id': obj.id}, status=201)
        return Response({'success': False, 'errors': serializer.errors}, status=400)
 






 