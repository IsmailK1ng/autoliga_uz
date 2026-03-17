from django.utils import translation
from django.conf import settings
from django.http import JsonResponse
from django.core.cache import cache
import hashlib
import logging
import time

logger = logging.getLogger('django')
security_logger = logging.getLogger('security')


# ============ UTILITY ============

def get_client_ip(request):
    """Real IP olish — nginx/proxy ortida ishlaydi."""
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '0.0.0.0')


def _ip_cache_key(prefix, ip):
    """IP dan qisqa, xavfsiz cache key yasash."""
    ip_hash = hashlib.md5(ip.encode()).hexdigest()[:12]
    return f"{prefix}:{ip_hash}"


# ============ LANGUAGE MIDDLEWARE ============

class ForceRussianMiddleware:
    """Принудительно устанавливает русский язык для админки, узбекский для сайта"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            if request.path.startswith('/admin/'):
                translation.activate('ru')
                request.LANGUAGE_CODE = 'ru'

            elif request.path.startswith('/api/'):
                language = 'uz'
                if '/api/uz/' in request.path:
                    language = 'uz'
                elif '/api/ru/' in request.path:
                    language = 'ru'
                elif '/api/en/' in request.path:
                    language = 'en'
                elif '/api/kg/' in request.path:
                    saved_language = request.session.get('_language')
                    cookie_language = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME)
                    language = saved_language or cookie_language or 'ky'

                translation.activate(language)
                request.LANGUAGE_CODE = language

            else:
                language = 'uz'
                if request.path.startswith('/uz/'):
                    language = 'uz'
                elif request.path.startswith('/ru/'):
                    language = 'ru'
                elif request.path.startswith('/en/'):
                    language = 'en'
                else:
                    saved_language = request.session.get('_language')
                    cookie_language = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME)
                    language = saved_language or cookie_language or 'uz'

                if language in [lang[0] for lang in settings.LANGUAGES]:
                    translation.activate(language)
                    request.LANGUAGE_CODE = language
                else:
                    translation.activate('uz')
                    request.LANGUAGE_CODE = 'uz'

            response = self.get_response(request)

            if request.path.startswith('/admin/'):
                response['Content-Language'] = 'ru'
            else:
                response['Content-Language'] = request.LANGUAGE_CODE

            return response

        except Exception as e:
            logger.error(f"Ошибка в ForceRussianMiddleware: {str(e)}", exc_info=True)
            translation.activate('uz')
            return self.get_response(request)


# ============ PERMISSIONS MIDDLEWARE ============

class RefreshUserPermissionsMiddleware:
    """Сбрасывает кэш прав при каждом запросе"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            if request.user.is_authenticated and not request.user.is_superuser:
                if hasattr(request.user, '_perm_cache'):
                    delattr(request.user, '_perm_cache')
                if hasattr(request.user, '_user_perm_cache'):
                    delattr(request.user, '_user_perm_cache')
                if hasattr(request.user, '_group_perm_cache'):
                    delattr(request.user, '_group_perm_cache')

            return self.get_response(request)

        except Exception as e:
            logger.error(f"Ошибка в RefreshUserPermissionsMiddleware: {str(e)}", exc_info=True)
            return self.get_response(request)


# ============ SECURITY HEADERS MIDDLEWARE ============

class SecurityHeadersMiddleware:
    """Xavfsizlik headerlarini qo'shadi — CSP, Permissions-Policy va boshqalar.

    CSP strategiyasi:
    - 'unsafe-eval' O'CHIRILGAN (XSS himoya uchun muhim)
    - 'unsafe-inline' faqat style uchun (Google Fonts talab qiladi)
    - script uchun 'unsafe-inline' saqlangan (GTM/Analytics inline snippet talab qiladi)
    - Admin sahifalariga CSP qo'yilmaydi (CKEditor, Jazzmin buziladi)
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Admin sahifalariga CSP qo'ymaymiz (CKEditor, Jazzmin o'z JS ishlatadi)
        if not request.path.startswith('/admin/'):
            response['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' "
                "https://www.googletagmanager.com https://www.google-analytics.com "
                "https://www.google.com https://www.gstatic.com "
                "https://mc.yandex.ru https://yastatic.net; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com data:; "
                "img-src 'self' data: https: blob:; "
                "connect-src 'self' https://www.google-analytics.com "
                "https://mc.yandex.ru https://www.google.com; "
                "frame-src https://www.google.com https://www.youtube.com; "
                "object-src 'none'; "
                "base-uri 'self'; "
                "form-action 'self';"
            )

        response['Permissions-Policy'] = (
            'camera=(), microphone=(), geolocation=(), '
            'payment=(), usb=(), magnetometer=(), '
            'gyroscope=(), accelerometer=()'
        )

        if 'X-Powered-By' in response:
            del response['X-Powered-By']
        if 'Server' in response:
            del response['Server']

        return response


# ============ RATE LIMIT + AUTO-BLOCK MIDDLEWARE ============

class RateLimitMiddleware:
    """Cache-based rate limiting + IP auto-block.

    Ishlash tartibi:
    1. IP bloklangan? -> 403 qaytarish (1 ta cache lookup)
    2. Rate limit oshganmi? -> 429 qaytarish + violation counter oshirish
    3. Violation threshold oshsa -> IP ni bloklash

    Cache key dizayni (Redis-optimized):
      rl:{endpoint_hash}:{ip_hash} -> hit count (TTL = window)
      block:{ip_hash}              -> 1 (TTL = block_duration)
      viol:{ip_hash}               -> violation count (TTL = violation_window)

    Konfiguratsiya settings.py da:
      RATE_LIMIT_RULES = {
          '/api/bot/': {'limit': 60, 'window': 60},
          '/api/': {'limit': 100, 'window': 60},
          '/admin/login/': {'limit': 5, 'window': 300},
      }
    """

    # Default rules (settings.py da override qilish mumkin)
    DEFAULT_RULES = {
        '/api/bot/': {'limit': 60, 'window': 60},
        '/api/': {'limit': 100, 'window': 60},
        '/admin/login/': {'limit': 5, 'window': 300},
    }

    # Auto-block sozlamalari
    VIOLATION_THRESHOLD = 5       # 5 marta rate limit oshsa -> block
    VIOLATION_WINDOW = 600        # 10 minut ichida
    BLOCK_DURATION = 1800         # 30 minut block

    def __init__(self, get_response):
        self.get_response = get_response
        self.rules = getattr(settings, 'RATE_LIMIT_RULES', self.DEFAULT_RULES)

    def __call__(self, request):
        # Static fayllarni o'tkazib yuborish
        if request.path.startswith(('/static/', '/media/', '/favicon')):
            return self.get_response(request)

        ip = get_client_ip(request)

        # 1. IP bloklangan?
        block_key = _ip_cache_key('block', ip)
        if cache.get(block_key):
            security_logger.warning(f"Blocked IP attempted access: {ip} -> {request.path}")
            return JsonResponse(
                {'error': 'Access temporarily blocked'},
                status=403
            )

        # 2. Rate limit tekshirish
        rule = self._match_rule(request.path)
        if rule:
            if not self._check_rate(ip, request.path, rule):
                # Violation counter oshirish
                self._record_violation(ip)
                security_logger.warning(
                    f"Rate limit exceeded: {ip} -> {request.path} "
                    f"(limit: {rule['limit']}/{rule['window']}s)"
                )
                return JsonResponse(
                    {'error': 'Too many requests'},
                    status=429
                )

        return self.get_response(request)

    def _match_rule(self, path):
        """Eng aniq (uzun) mos keladigan rule ni topish."""
        matched = None
        matched_len = 0
        for prefix, rule in self.rules.items():
            if path.startswith(prefix) and len(prefix) > matched_len:
                matched = rule
                matched_len = len(prefix)
        return matched

    def _check_rate(self, ip, path, rule):
        """Cache-based sliding window counter.

        Har bir (endpoint, IP) uchun bitta cache key.
        TTL = window, shuning uchun eskirgan keylar avtomatik o'chadi.
        Returns True if allowed, False if exceeded.
        """
        # Endpoint hash: /api/bot/ va /api/bot/status bitta rule bo'lsa bitta key
        prefix = None
        for p in self.rules:
            if path.startswith(p):
                prefix = p
                break
        if not prefix:
            prefix = path

        rate_key = _ip_cache_key(f'rl:{prefix}', ip)

        try:
            current = cache.get(rate_key, 0)
            if current >= rule['limit']:
                return False
            # Atomic increment with TTL
            # cache.incr fails if key doesn't exist in some backends
            if current == 0:
                cache.set(rate_key, 1, timeout=rule['window'])
            else:
                try:
                    cache.incr(rate_key)
                except ValueError:
                    cache.set(rate_key, 1, timeout=rule['window'])
            return True
        except Exception:
            # Cache xatosi bo'lsa -> request ni o'tkazib yuborish (fail-open)
            return True

    def _record_violation(self, ip):
        """Violation counter. Threshold oshsa -> IP ni bloklash."""
        viol_key = _ip_cache_key('viol', ip)
        try:
            count = cache.get(viol_key, 0)
            if count + 1 >= self.VIOLATION_THRESHOLD:
                # IP ni bloklash
                block_key = _ip_cache_key('block', ip)
                cache.set(block_key, 1, timeout=self.BLOCK_DURATION)
                cache.delete(viol_key)
                security_logger.error(
                    f"IP AUTO-BLOCKED: {ip} "
                    f"({self.VIOLATION_THRESHOLD} violations in {self.VIOLATION_WINDOW}s, "
                    f"blocked for {self.BLOCK_DURATION}s)"
                )
            else:
                if count == 0:
                    cache.set(viol_key, 1, timeout=self.VIOLATION_WINDOW)
                else:
                    try:
                        cache.incr(viol_key)
                    except ValueError:
                        cache.set(viol_key, 1, timeout=self.VIOLATION_WINDOW)
        except Exception:
            pass  # Cache xatosi bo'lsa -> bloklashni o'tkazib yuborish


# ============ ADMIN LOGIN PROTECTION ============

class AdminBruteForceMiddleware:
    """Admin login sahifasiga brute force himoya.

    - Faqat POST /admin/login/ ga ishlaydi
    - Muvaffaqiyatsiz urinishlarni sanaydi
    - 5 ta noto'g'ri urinishdan keyin IP ni 15 minut bloklaydi
    - Muvaffaqiyatli logindan keyin counter tozalanadi
    """

    MAX_ATTEMPTS = 5
    LOCKOUT_DURATION = 900  # 15 minut

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Faqat admin login POST ga ishlaydi
        if not (request.path == '/admin/login/' and request.method == 'POST'):
            return self.get_response(request)

        ip = get_client_ip(request)
        attempts_key = _ip_cache_key('admin_fail', ip)
        lockout_key = _ip_cache_key('admin_lock', ip)

        # Lockout tekshirish
        if cache.get(lockout_key):
            security_logger.warning(f"Admin login locked out: {ip}")
            return JsonResponse(
                {'error': 'Too many login attempts. Try again later.'},
                status=403
            )

        response = self.get_response(request)

        # Login natijasini tekshirish
        # Muvaffaqiyatli login -> redirect (302), muvaffaqiyatsiz -> 200 (forma qayta ko'rsatiladi)
        if response.status_code == 200:
            # Login muvaffaqiyatsiz
            try:
                attempts = cache.get(attempts_key, 0) + 1
                if attempts >= self.MAX_ATTEMPTS:
                    cache.set(lockout_key, 1, timeout=self.LOCKOUT_DURATION)
                    cache.delete(attempts_key)
                    security_logger.error(
                        f"Admin brute force detected, IP locked: {ip} "
                        f"({self.MAX_ATTEMPTS} failed attempts)"
                    )
                else:
                    cache.set(attempts_key, attempts, timeout=self.LOCKOUT_DURATION)
            except Exception:
                pass
        elif response.status_code == 302:
            # Login muvaffaqiyatli -> counter tozalash
            try:
                cache.delete(attempts_key)
            except Exception:
                pass

        return response


# ============ REQUEST SIZE LIMIT ============

class RequestSizeLimitMiddleware:
    """Katta request body larni bloklash — DDoS/upload bomb himoya.

    - API uchun: 2 MB (JSON payloads)
    - Fayl upload uchun: 15 MB (resume, avatar)
    - Admin uchun: cheklov yo'q
    """

    API_MAX_SIZE = 2 * 1024 * 1024       # 2 MB
    UPLOAD_MAX_SIZE = 15 * 1024 * 1024    # 15 MB

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/admin/'):
            return self.get_response(request)

        content_length = request.META.get('CONTENT_LENGTH')
        if content_length:
            try:
                size = int(content_length)
            except (ValueError, TypeError):
                return self.get_response(request)

            content_type = request.META.get('CONTENT_TYPE', '')
            if 'multipart/form-data' in content_type:
                max_size = self.UPLOAD_MAX_SIZE
            else:
                max_size = self.API_MAX_SIZE

            if size > max_size:
                security_logger.warning(
                    f"Oversized request blocked: {get_client_ip(request)} -> "
                    f"{request.path} ({size} bytes, max {max_size})"
                )
                return JsonResponse(
                    {'error': 'Request too large'},
                    status=413
                )

        return self.get_response(request)
