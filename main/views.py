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
from .models import (
    News, ContactForm, JobApplication, Vacancy, Product, ProductCategory
)
from .serializers import (
    NewsSerializer, ContactFormSerializer, JobApplicationSerializer, 
    ProductCardSerializer, ProductDetailSerializer, ProductCategorySerializer
)
import logging
import json


logger = logging.getLogger('django')

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
        
        context = {
            'news_list': news_list,
            'slider_products': json.dumps(slider_data, ensure_ascii=False),
            'featured_count': len(slider_data),
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
    return render(request, 'main/dealers.html')


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