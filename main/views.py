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

)

from .models import TelegramUser

import logging

import json

from django.db.models import Prefetch





logger = logging.getLogger('django')



# === FRONTEND views === 



def index(request):

    """Р“Р»Р°РІРЅР°СЏ СЃС‚СЂР°РЅРёС†Р° СЃ РґРёРЅР°РјРёС‡РµСЃРєРёРј СЃР»Р°Р№РґРµСЂРѕРј"""

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

            power = getattr(product, f'slider_power_{current_lang}', None) or product.slider_power or 'вЂ”'

            fuel = getattr(product, f'slider_fuel_consumption_{current_lang}', None) or product.slider_fuel_consumption or 'вЂ”'

            

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

        

        # РњРµРЅРµРґР¶РµСЂС‹ РґР»СЏ СЃРµРєС†РёРё "РќР°С€Р° РєРѕРјР°РЅРґР°"

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

        logger.error(f"РћС€РёР±РєР° РЅР° РіР»Р°РІРЅРѕР№ СЃС‚СЂР°РЅРёС†Рµ: {str(e)}", exc_info=True)

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

    """РЎС‚СЂР°РЅРёС†Р° СЃРѕ РІСЃРµРјРё РЅРѕРІРѕСЃС‚СЏРјРё"""

    try:

        news_list = News.objects.filter(

            is_active=True

        ).select_related('author').order_by('-order', '-created_at')

        

        return render(request, 'main/news.html', {'news_list': news_list})

    

    except Exception as e:

        logger.error(f"РћС€РёР±РєР° РЅР° СЃС‚СЂР°РЅРёС†Рµ РЅРѕРІРѕСЃС‚РµР№: {str(e)}", exc_info=True)

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

    """РЎС‚СЂР°РЅРёС†Р° РєРѕРјР°РЅРґС‹ вЂ” РјРµРЅРµРґР¶РµСЂС‹ РїРѕ С„РёР»РёР°Р»Р°Рј"""

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

    """РЎС‚СЂР°РЅРёС†Р° Р·Р°РїРёСЃРё РЅР° С‚РµСЃС‚-РґСЂР°Р№РІ"""

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

    """РЎС‚СЂР°РЅРёС†Р° СЃ РІР°РєР°РЅСЃРёСЏРјРё"""

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

        logger.error(f"РћС€РёР±РєР° РЅР° СЃС‚СЂР°РЅРёС†Рµ РІР°РєР°РЅСЃРёР№: {str(e)}", exc_info=True)

        return render(request, 'main/jobs.html', {'vacancies': [], 'vacancies_data': []})





def news_detail(request, slug):

    """Р”РµС‚Р°Р»СЊРЅР°СЏ СЃС‚СЂР°РЅРёС†Р° РЅРѕРІРѕСЃС‚Рё"""

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

                'home': 'Р“Р»Р°РІРЅР°СЏ',

                'news': 'РќРѕРІРѕСЃС‚Рё Autoliga',

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

        logger.error(f"РћС€РёР±РєР° РЅР° СЃС‚СЂР°РЅРёС†Рµ РЅРѕРІРѕСЃС‚Рё {slug}: {str(e)}", exc_info=True)

        return redirect('news')





def set_language_get(request):

    """РџРµСЂРµРєР»СЋС‡РµРЅРёРµ СЏР·С‹РєР° РўРћР›Р¬РљРћ РґР»СЏ СЃР°Р№С‚Р°"""

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

    """API endpoint РґР»СЏ CRUD РѕРїРµСЂР°С†РёР№ СЃ РЅРѕРІРѕСЃС‚СЏРјРё"""

    serializer_class = NewsSerializer

    permission_classes = [AllowAny]

    

    def get_queryset(self):

        return News.objects.select_related('author').prefetch_related('blocks').order_by('-created_at')





from rest_framework.permissions import AllowAny, IsAdminUser

from rest_framework.decorators import permission_classes



class ContactFormViewSet(viewsets.ModelViewSet):

    serializer_class = ContactFormSerializer

    

    # вњ… РРЎРџР РђР’Р›Р•РќРћ: Р Р°Р·РЅС‹Рµ РїСЂР°РІР° РґР»СЏ СЂР°Р·РЅС‹С… РјРµС‚РѕРґРѕРІ

    def get_permissions(self):

        if self.action in ['create']:

            # POST С‚СЂРµР±СѓРµС‚ CSRF РІ headers

            return [AllowAny()]

        else:

            # GET/PUT/DELETE С‚РѕР»СЊРєРѕ РґР»СЏ Р°РґРјРёРЅРѕРІ

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

            

            # РћС‚РїСЂР°РІР»СЏРµРј РІ amoCRM

            try:

                from main.services.amocrm.lead_sender import LeadSender

                LeadSender.send_lead(contact_form)

                contact_form.refresh_from_db()

            except Exception as amocrm_error:

                logger.error(

                    f"РћС€РёР±РєР° amoCRM РґР»СЏ Р»РёРґР° #{contact_form.id}: {str(amocrm_error)}", 

                    exc_info=True

                )

            

            # РћС‚РїСЂР°РІР»СЏРµРј РІ Telegram (РџРћРЎР›Р• amoCRM)

            try:

                from main.services.telegram import TelegramNotificationSender

                TelegramNotificationSender.send_lead_notification(contact_form)

            except Exception as telegram_error:

                logger.error(

                    f"РћС€РёР±РєР° Telegram РґР»СЏ Р»РёРґР° #{contact_form.id}: {str(telegram_error)}", 

                    exc_info=True

                )

            

            return Response({

                'success': True,

                'message': 'Xabar yuborildi!'

            }, status=status.HTTP_201_CREATED)

            

        except Exception as e:

            logger.error(f"РљСЂРёС‚РёС‡РµСЃРєР°СЏ РѕС€РёР±РєР° СЃРѕР·РґР°РЅРёСЏ С„РѕСЂРјС‹: {str(e)}", exc_info=True)

            return Response({

                'success': False,

                'message': 'Xatolik yuz berdi.'

            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    



class JobApplicationViewSet(viewsets.ModelViewSet):

    """API endpoint РґР»СЏ РїСЂРёРµРјР° Р·Р°СЏРІРѕРє РЅР° РІР°РєР°РЅСЃРёРё"""

    serializer_class = JobApplicationSerializer

    

    def get_queryset(self):

        """вњ… РћРїС‚РёРјРёР·Р°С†РёСЏ: Р·Р°РіСЂСѓР¶Р°РµРј РІР°РєР°РЅСЃРёСЋ СЃСЂР°Р·Сѓ"""

        return JobApplication.objects.select_related('vacancy').order_by('-created_at')

    

    def get_permissions(self):

        if self.action == 'create':

            return [AllowAny()]

        else:

            return [IsAdminUser()]

    

    def create(self, request, *args, **kwargs):

        """РЎРѕР·РґР°РЅРёРµ РЅРѕРІРѕР№ Р·Р°СЏРІРєРё СЃ СЂРµР·СЋРјРµ"""

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

            logger.error(f"РћС€РёР±РєР° СЃРѕР·РґР°РЅРёСЏ Р·Р°СЏРІРєРё РЅР° РІР°РєР°РЅСЃРёСЋ: {str(e)}", exc_info=True)

            return Response({

                'success': False, 

                'message': 'Xatolik yuz berdi'

            }, status=500)

    

    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])

    def unprocessed(self, request):

        """РџРѕР»СѓС‡РёС‚СЊ РЅРµРѕР±СЂР°Р±РѕС‚Р°РЅРЅС‹Рµ Р·Р°СЏРІРєРё"""

        try:

            unprocessed = self.get_queryset().filter(is_processed=False)

            serializer = self.get_serializer(unprocessed, many=True)

            return Response({

                'count': unprocessed.count(),

                'results': serializer.data

            })

        except Exception as e:

            logger.error(f"РћС€РёР±РєР° РїРѕР»СѓС‡РµРЅРёСЏ РЅРµРѕР±СЂР°Р±РѕС‚Р°РЅРЅС‹С… Р·Р°СЏРІРѕРє: {str(e)}", exc_info=True)

            return Response({'error': 'Internal error'}, status=500)

    

    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])

    def mark_processed(self, request, pk=None):

        """РћС‚РјРµС‚РёС‚СЊ Р·Р°СЏРІРєСѓ РєР°Рє РѕР±СЂР°Р±РѕС‚Р°РЅРЅСѓСЋ"""

        try:

            application = self.get_object()

            application.is_processed = True

            application.save()

            return Response({

                'status': 'processed',

                'message': f'Ariza #{application.id} ko\'rib chiqilgan deb belgilandi'

            })

        except Exception as e:

            logger.error(f"РћС€РёР±РєР° РѕР±РЅРѕРІР»РµРЅРёСЏ Р·Р°СЏРІРєРё #{pk}: {str(e)}", exc_info=True)

            return Response({'error': 'Internal error'}, status=500)





class ProductViewSet(viewsets.ReadOnlyModelViewSet):

    """API РґР»СЏ РїСЂРѕРґСѓРєС‚РѕРІ"""

    permission_classes = [AllowAny]

    lookup_field = 'slug'

    

    def get_queryset(self):

        try:

            queryset = Product.objects.filter(is_active=True).select_related(

                'category'  # вњ… РРЎРџР РђР’Р›Р•РќРћ: select_related РІРјРµСЃС‚Рѕ prefetch_related

            ).prefetch_related(

                'card_specs__icon',

                'parameters',

                'features__icon',

                'gallery'

            ).order_by('order', 'title')

            

            category_slug = self.request.query_params.get('category', None)

            if category_slug:

                queryset = queryset.filter(

                    category__slug=category_slug,  # вњ… РРЎРџР РђР’Р›Р•РќРћ

                    category__is_active=True

                )

            

            return queryset

        except Exception as e:

            logger.error(f"РћС€РёР±РєР° РїРѕР»СѓС‡РµРЅРёСЏ РїСЂРѕРґСѓРєС‚РѕРІ: {str(e)}", exc_info=True)

            return Product.objects.none()

    

    def get_serializer_class(self):

        if self.action == 'retrieve':

            return ProductDetailSerializer

        return ProductCardSerializer



def products(request):

    """РЎС‚СЂР°РЅРёС†Р° СЃРѕ СЃРїРёСЃРєРѕРј РїСЂРѕРґСѓРєС‚РѕРІ РїРѕ РєР°С‚РµРіРѕСЂРёСЏРј"""

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

            # РџРµСЂРІР°СЏ Р°РєС‚РёРІРЅР°СЏ РєР°С‚РµРіРѕСЂРёСЏ РїРѕ СѓРјРѕР»С‡Р°РЅРёСЋ

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

        

        # РџРѕР»СѓС‡Р°РµРј РІСЃРµ РєР°С‚РµРіРѕСЂРёРё РґР»СЏ РЅР°РІРёРіР°С†РёРё

        all_categories = ProductCategory.objects.filter(is_active=True).order_by('order')

        

        return render(request, 'main/products.html', {

            'category_slug': category_slug,

            'category_info': category_info,

            'all_categories': all_categories

        })

    except Exception as e:

        logger.error(f"РћС€РёР±РєР° РЅР° СЃС‚СЂР°РЅРёС†Рµ РїСЂРѕРґСѓРєС‚РѕРІ: {str(e)}", exc_info=True)

        return render(request, 'main/products.html', {

            'category_slug': None,

            'category_info': {},

            'all_categories': []

        })



@api_view(['POST'])

@permission_classes([AllowAny])

def log_js_error(request):

    """Р›РѕРіРёСЂРѕРІР°РЅРёРµ JS РѕС€РёР±РѕРє СЃ С„СЂРѕРЅС‚РµРЅРґР°"""

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

        logger.error(f"РћС€РёР±РєР° Р»РѕРіРёСЂРѕРІР°РЅРёСЏ JS РѕС€РёР±РєРё: {str(e)}", exc_info=True)

        return Response({'status': 'error'}, status=500)

    

class ProductCategoryViewSet(viewsets.ReadOnlyModelViewSet):

    """API РґР»СЏ РєР°С‚РµРіРѕСЂРёР№ РїСЂРѕРґСѓРєС‚РѕРІ"""

    serializer_class = ProductCategorySerializer

    permission_classes = [AllowAny]



    def get_queryset(self):

        return ProductCategory.objects.filter(is_active=True).order_by('order')





class ReviewCreateThrottle(AnonRateThrottle):

    """1 ta IP dan kuniga faqat 1 ta comment"""

    scope = 'review_create'



    THROTTLE_MESSAGES = {

        'uz': "Siz allaqachon sharh qoldirgansiz. {wait} dan keyin qayta urinib ko'ring.",

        'ru': "Р’С‹ СѓР¶Рµ РѕСЃС‚Р°РІРёР»Рё РѕС‚Р·С‹РІ. РџРѕРїСЂРѕР±СѓР№С‚Рµ СЃРЅРѕРІР° С‡РµСЂРµР· {wait}.",

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

    """API РґР»СЏ РѕС‚Р·С‹РІРѕРІ РєР»РёРµРЅС‚РѕРІ"""

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

        """GET: СЃРїРёСЃРѕРє РѕРґРѕР±СЂРµРЅРЅС‹С… РѕС‚Р·С‹РІРѕРІ СЃ РїР°РіРёРЅР°С†РёРµР№"""

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

        """POST: СЃРѕР·РґР°РЅРёРµ РЅРѕРІРѕРіРѕ РѕС‚Р·С‹РІР° (СЃ reCAPTCHA + rate limit)"""

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
                    if lang == 'uz':
                        wait_str = f"{hours} soat {minutes} minut"
                    elif lang == 'ru':
                        wait_str = f"{hours} ч {minutes} мин"
                    else:
                        wait_str = f"{hours}h {minutes}m"
                else:
                    if lang == 'uz':
                        wait_str = f"{minutes} minut"
                    elif lang == 'ru':
                        wait_str = f"{minutes} мин"
                    else:
                        wait_str = f"{minutes}m"

            else:
                if lang == 'uz':
                    wait_str = "1 soat"
                elif lang == 'ru':
                    wait_str = "1 час"
                else:
                    wait_str = "1 hour"

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

            'message': 'РЎРїР°СЃРёР±Рѕ! Р’Р°С€ РѕС‚Р·С‹РІ РѕС‚РїСЂР°РІР»РµРЅ РЅР° РїСЂРѕРІРµСЂРєСѓ. РџРѕСЃР»Рµ РјРѕРґРµСЂР°С†РёРё РѕРЅ РїРѕСЏРІРёС‚СЃСЏ РЅР° СЃР°Р№С‚Рµ.'

        }, status=status.HTTP_201_CREATED)





class TestDriveViewSet(viewsets.GenericViewSet):

    """API РґР»СЏ Р·Р°СЏРІРѕРє РЅР° С‚РµСЃС‚-РґСЂР°Р№РІ"""

    serializer_class = TestDriveSerializer

    permission_classes = [AllowAny]



    def get_queryset(self):

        return TestDriveRequest.objects.all().order_by('-created_at')



    def create(self, request, *args, **kwargs):

        """POST: СЃРѕР·РґР°РЅРёРµ Р·Р°СЏРІРєРё РЅР° С‚РµСЃС‚-РґСЂР°Р№РІ"""

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



        # РћС‚РїСЂР°РІРєР° РІ Telegram

        try:

            from main.services.telegram import TelegramNotificationSender

            TelegramNotificationSender.send_test_drive_notification(test_drive_obj)

        except Exception as e:

            logger.error(f"РћС€РёР±РєР° Telegram РґР»СЏ С‚РµСЃС‚-РґСЂР°Р№РІР° #{test_drive_obj.id}: {e}", exc_info=True)



        return Response({

            'success': True,

            'message': 'OK',

        }, status=status.HTTP_201_CREATED)





