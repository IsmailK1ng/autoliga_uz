# main/redirects.py
"""
301 redirects and slug history (SEO TZ task 13).

* Redirect rows are looked up only when a response is already a 404
  (RedirectFallbackMiddleware), so normal 200 pages run no extra query and a
  live page always wins over a redirect.
* old_path is stored normalized: leading and trailing slash, no domain, no
  query, no language prefix. /ru/ and /en/ requests use the same row and are
  sent to the target in their own language; the query string is kept.
* Targets are a product, a brand, a news item (followed by object, so later
  slug changes need no new row) or a free URL.
* One hop: a row pointing to another row's old_path is collapsed to that
  row's target; a redirect to itself is rejected; a live page cannot be an
  old_path.
* Slug history: changing the slug of a product, brand or news item records
  the old path automatically (main/signals.py -> record_slug_change).
"""

import re
from urllib.parse import urlsplit

from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import HttpResponsePermanentRedirect
from django.urls import Resolver404, resolve, reverse
from django.utils import translation

LANGUAGE_CODES = [code for code, _name in settings.LANGUAGES]
LANG_PREFIX_RE = re.compile(r'^/(%s)(?=/|$)' % '|'.join(map(re.escape, LANGUAGE_CODES)))
SKIP_PREFIXES = ('/admin/', '/api/', '/static/', '/media/', '/sitemap', '/robots.txt', '/i18n/')
TARGET_FIELDS = ('target_product', 'target_brand', 'target_news', 'target_url')
OBJECT_URLS = {
    # field: (url name, kwarg)
    'target_product': ('product_detail', 'product_id'),
    'target_brand': ('brand', 'slug'),
    'target_news': ('news_detail', 'slug'),
}


def normalize_path(value):
    """"https://autoliga.uz/ru/products/soueast?x=1" -> "/products/soueast/"."""
    path = urlsplit((value or '').strip()).path or '/'
    if not path.startswith('/'):
        path = '/' + path
    path = re.sub(r'/{2,}', '/', path)
    path = LANG_PREFIX_RE.sub('', path) or '/'
    return path if path.endswith('/') else path + '/'


def is_internal(url):
    """A path, or a full URL on one of this site's hosts (with or without www.)."""
    host = urlsplit((url or '').strip()).netloc.lower().split(':')[0]
    if not host:
        return True
    own = {h.lower().lstrip('.').removeprefix('www.') for h in settings.ALLOWED_HOSTS if h != '*'}
    return host.removeprefix('www.') in own


def object_path(url_name, kwarg, slug):
    """Unprefixed (default language) path of a product / brand / news page."""
    with translation.override(settings.LANGUAGE_CODE):
        return reverse(url_name, kwargs={kwarg: slug})


def target_location(redirect):
    """(path_or_url, is_internal) the redirect points to, or (None, False) when the
    target object is inactive (then the old URL stays a 404)."""
    for field, (url_name, kwarg) in OBJECT_URLS.items():
        if getattr(redirect, f'{field}_id'):
            obj = getattr(redirect, field)
            return (object_path(url_name, kwarg, obj.slug), True) if obj.is_active else (None, False)
    url = (redirect.target_url or '').strip()
    if not url:
        return None, False
    if is_internal(url):
        parts = urlsplit(url)
        return normalize_path(parts.path) + (f'?{parts.query}' if parts.query else ''), True
    return url, False


def _copy_target(source, destination):
    for field in TARGET_FIELDS:
        setattr(destination, field, getattr(source, field))


def _live_page(path):
    """True when `path` is a working page of the site (a redirect there would never fire)."""
    from .models import Dealer, News, Product, ProductCategory
    try:
        match = resolve(path)
    except Resolver404:
        return False
    checks = {
        'product_detail': lambda kw: Product.objects.filter(slug=kw.get('product_id'), is_active=True).exists(),
        'brand': lambda kw: ProductCategory.objects.filter(slug=kw.get('slug'), is_active=True).exists(),
        'news_detail': lambda kw: News.objects.filter(slug=kw.get('slug'), is_active=True).exists(),
        'dealer_detail': lambda kw: Dealer.objects.filter(pk=kw.get('pk'), is_active=True).exists(),
    }
    check = checks.get(match.url_name)
    return check(match.kwargs) if check else True


def collapse(redirect):
    """old -> old2 -> new becomes old -> new (internal free-URL targets only)."""
    from .models import Redirect
    location, internal = target_location(redirect)
    if not (internal and location) or any(getattr(redirect, f'{f}_id') for f in OBJECT_URLS):
        return
    hop = Redirect.objects.filter(old_path=normalize_path(location), is_active=True).exclude(pk=redirect.pk).first()
    if hop:
        _copy_target(hop, redirect)


def points_to_itself(redirect):
    location, internal = target_location(redirect)
    return bool(internal and location and normalize_path(location) == redirect.old_path)


def validate(redirect):
    """Model.clean(): the admin form shows these errors."""
    redirect.old_path = normalize_path(redirect.old_path)
    if redirect.old_path == '/' or redirect.old_path.startswith(SKIP_PREFIXES):
        raise ValidationError({'old_path': "Этот адрес нельзя перенаправить."})
    targets = [f for f in TARGET_FIELDS if (getattr(redirect, f'{f}_id') if f in OBJECT_URLS else (redirect.target_url or '').strip())]
    if len(targets) != 1:
        raise ValidationError("Укажите ровно одну цель: модель, бренд, новость или адрес.")
    if _live_page(redirect.old_path):
        raise ValidationError({'old_path': "По этому адресу открывается рабочая страница. Сначала измените её slug или "
                                           "отключите её — тогда редирект сработает."})
    collapse(redirect)
    if points_to_itself(redirect):
        raise ValidationError("Редирект ведёт сам на себя (или по цепочке обратно на этот адрес).")
    location, _internal = target_location(redirect)
    if not location:
        raise ValidationError("Цель не активна — редирект не сработает.")


def after_save(redirect):
    """Rows that pointed to this row's old_path now point straight to its target (one hop).
    A row that would now point to itself is switched off."""
    from .models import Redirect
    if not redirect.is_active:
        return
    for other in Redirect.objects.filter(is_active=True, target_url__isnull=False).exclude(pk=redirect.pk).exclude(target_url=''):
        location, internal = target_location(other)
        if internal and location and normalize_path(location) == redirect.old_path:
            _copy_target(redirect, other)
            if points_to_itself(other):
                other.is_active = False
            other.save()


def record_slug_change(instance, old_slug):
    """Slug history: old /products|brand|news/<old>/ -> the object (one hop, also for /ru/ and /en/)."""
    from .models import News, Product, ProductCategory, Redirect
    field = {Product: 'target_product', ProductCategory: 'target_brand', News: 'target_news'}[type(instance)]
    url_name, kwarg = OBJECT_URLS[field]
    old_path, new_path = object_path(url_name, kwarg, old_slug), object_path(url_name, kwarg, instance.slug)
    # the new path is a live page now: a row for it (e.g. slug changed back) would loop
    Redirect.objects.filter(old_path=new_path).delete()
    row, _created = Redirect.objects.get_or_create(old_path=old_path)
    for f in TARGET_FIELDS:
        setattr(row, f, None if f in OBJECT_URLS else '')
    setattr(row, field, instance)
    row.is_active, row.is_automatic = True, True
    row.save()


def find_redirect(request, path=None):
    """Location for a request that ended in 404 (or for `path`), or None. One indexed query."""
    from .models import Redirect
    path = path or request.path_info
    row = (Redirect.objects.filter(old_path=normalize_path(path), is_active=True)
           .select_related('target_product', 'target_brand', 'target_news').first())
    if row is None:
        return None
    location, internal = target_location(row)
    if not location:
        return None
    if internal:
        language = translation.get_language() or settings.LANGUAGE_CODE
        prefix = '' if language == settings.LANGUAGE_CODE or language not in LANGUAGE_CODES else f'/{language}'
        if normalize_path(location) == normalize_path(path):
            return None
        location = prefix + location
    query = request.META.get('QUERY_STRING', '')
    if query:
        location += ('&' if '?' in location else '?') + query
    return location


class RedirectFallbackMiddleware:
    """301 for old URLs, consulted only when the response is a 404."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if response.status_code != 404 or request.method not in ('GET', 'HEAD'):
            return response
        if LANG_PREFIX_RE.sub('', request.path_info).startswith(SKIP_PREFIXES):
            return response
        location = find_redirect(request)
        return HttpResponsePermanentRedirect(location) if location else response
