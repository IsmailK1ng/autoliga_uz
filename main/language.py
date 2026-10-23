# main/language.py
"""
Site language from the URL only (SEO TZ task 14).

    /...      -> uz (default, no prefix)
    /ru/...   -> ru
    /en/...   -> en
    /uz/...   -> 301 to the same page without /uz/ (one hop: if that page itself
                 redirects, e.g. ?category= or an old slug, its redirect is used)

The same URL always returns the same language; the django_language cookie and
the session no longer change the language of a page. /admin/ stays ru and the
API keeps its /api/<lang>/ rule (unchanged from ForceRussianMiddleware).

Transition (until COOKIE_REDIRECT_UNTIL): visitors who still carry the ru/en
cookie from the old POST switcher get ONE 302 from an unprefixed page to the
same page under /ru/ or /en/. Only HTML GET/HEAD of real site pages, never
without the cookie, never for bots, /api/, /admin/, /static/, /media/, the
sitemap or robots.txt. The 302 is uncacheable for other visitors:
Vary: Cookie, Cache-Control: private, no-store and X-Accel-Expires: 0
(nginx/Engintron). Delete the transition block after the end date.
"""

import datetime
import re

from django.conf import settings
from django.http import HttpResponsePermanentRedirect, HttpResponseRedirect
from django.utils import timezone, translation
from django.utils.cache import patch_vary_headers

DEFAULT = settings.LANGUAGE_CODE
PREFIXED = [code for code, _name in settings.LANGUAGES if code != DEFAULT]

# Transition for visitors with the old ru/en cookie (decided 2026-10-23). Remove after this date.
COOKIE_REDIRECT_UNTIL = datetime.date(2027, 1, 31)
NO_REDIRECT_PREFIXES = ('/admin/', '/api/', '/static/', '/media/', '/sitemap', '/robots.txt', '/i18n/',
                        '/set-language/', '/nested_admin/', '/captcha/')
BOT_RE = re.compile(r'bot|crawl|spider|slurp|facebookexternalhit|whatsapp|lighthouse|pagespeed|preview|headless', re.I)
REDIRECT_STATUSES = (301, 302, 303, 307, 308)


def _activate(request, language):
    translation.activate(language)
    request.LANGUAGE_CODE = language


# Field that must be filled for an object page to exist in a language (same rule as the
# hreflang tags in main/templatetags/seo_tags.py); news also need body text (task 9).
OBJECT_LANGUAGE_FIELD = {'Product': 'title', 'ProductCategory': 'name', 'Dealer': 'name', 'News': 'title'}


def object_languages(obj):
    """Languages in which an object page really exists (sitemap entries, task 14)."""
    codes = [code for code, _name in settings.LANGUAGES]
    field = OBJECT_LANGUAGE_FIELD.get(type(obj).__name__)
    if field is None:
        return codes
    filled = [code for code in codes if str(getattr(obj, f'{field}_{code}', '') or '').strip()]
    if type(obj).__name__ == 'News':
        from .seo import news_body_text
        blocks = list(obj.blocks.all())
        filled = [code for code in filled if news_body_text(blocks, code)]
    return filled


def transition_active(today=None):
    return (today or timezone.localdate()) <= COOKIE_REDIRECT_UNTIL


class SiteLanguageMiddleware:
    """Language from the URL prefix only (replaces LocaleMiddleware + ForceRussianMiddleware)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info

        if path.startswith('/admin/'):
            _activate(request, 'ru')
            response = self.get_response(request)
            response['Content-Language'] = 'ru'
            return response

        if path.startswith('/api/'):
            # unchanged from ForceRussianMiddleware
            language = 'uz'
            if '/api/uz/' in path:
                language = 'uz'
            elif '/api/ru/' in path:
                language = 'ru'
            elif '/api/en/' in path:
                language = 'en'
            elif '/api/kg/' in path:
                language = request.session.get('_language') or request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME) or 'ky'
            _activate(request, language)
            response = self.get_response(request)
            response['Content-Language'] = request.LANGUAGE_CODE
            return response

        first = path.split('/')[1] if path.count('/') >= 1 else ''
        if first == DEFAULT:
            return self._default_prefix(request, path)

        language = first if first in PREFIXED else DEFAULT
        _activate(request, language)
        response = self.get_response(request)
        response['Content-Language'] = language

        if language == DEFAULT and transition_active() and not path.startswith(NO_REDIRECT_PREFIXES):
            redirect = self._cookie_redirect(request, path, response)
            if redirect is not None:
                return redirect
            # caches must keep cookie and no-cookie answers apart while the transition lasts
            patch_vary_headers(response, ('Cookie',))
        return response

    # /uz/... -> /... (one hop)
    def _default_prefix(self, request, path):
        stripped = path[len(DEFAULT) + 1:] or '/'
        query = request.META.get('QUERY_STRING', '')
        request.path_info = stripped
        request.path = stripped
        request.META['PATH_INFO'] = stripped
        _activate(request, DEFAULT)
        response = self.get_response(request)
        if response.status_code in REDIRECT_STATUSES:
            return response  # the page itself redirects: go straight to its final address
        if response.status_code == 200:
            return HttpResponsePermanentRedirect(stripped + (f'?{query}' if query else ''))
        return response

    # Transition: old ru/en cookie on an unprefixed page -> one 302 to the prefixed page.
    # Decided after the page answered, so every case stays one hop:
    #   200 HTML page          -> 302 /<lang>/<same path>?<same query>
    #   page redirects itself  -> its target with the /<lang> prefix (?category=, old slugs)
    #   anything else (404...) -> unchanged
    def _cookie_redirect(self, request, path, response):
        if request.method not in ('GET', 'HEAD'):
            return None
        language = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME)
        if language not in PREFIXED:
            return None
        if BOT_RE.search(request.META.get('HTTP_USER_AGENT', '')) or request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return None
        if response.status_code == 200 and response.get('Content-Type', '').startswith('text/html'):
            query = request.META.get('QUERY_STRING', '')
            location = f'/{language}{path}' + (f'?{query}' if query else '')
        elif response.status_code in REDIRECT_STATUSES:
            target = response.get('Location', '')
            first = target.split('/')[1] if target.startswith('/') and not target.startswith('//') else None
            if first is None or first in PREFIXED or target.startswith(NO_REDIRECT_PREFIXES):
                return None
            location = f'/{language}{target}'
        else:
            return None
        redirect = HttpResponseRedirect(location)
        patch_vary_headers(redirect, ('Cookie',))
        redirect['Cache-Control'] = 'private, no-store, max-age=0'
        redirect['X-Accel-Expires'] = '0'  # nginx / Engintron: never cache this answer
        redirect['Content-Language'] = language
        return redirect
