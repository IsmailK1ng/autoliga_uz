"""Read-only translation report (SEO TZ task 14) — safe to run on production.

    python manage.py i18n_report          # first 30 untranslated items per list
    python manage.py i18n_report --all    # every untranslated item

Only SELECTs: everything runs inside a transaction marked READ ONLY (PostgreSQL
rejects any write) and reads values_list(...).iterator(), a fixed number of
queries whatever the amount of data. Nothing is cached, written or migrated.

A page "exists" in a language with the same rule as the sitemap / hreflang /
noindex (main.language.object_languages): model title, brand name, dealer name
filled in that language; news needs a title AND body text in that language.
"""
from collections import defaultdict

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection, transaction

from main.models import BranchManager, BrandFAQ, Dealer, News, NewsBlock, Product, ProductCategory
from main.seo import html_to_text

LANGS = [code for code, _name in settings.LANGUAGES]
OTHER = [code for code in LANGS if code != settings.LANGUAGE_CODE]  # ru, en
STATIC_PAGES = 7  # home, products, news, dealers, contact, team, test-drive (StaticViewSitemap)


def filled(value):
    return bool(str(value or '').strip())


class Command(BaseCommand):
    help = 'Read-only report: how much of the site content is translated into ru / en.'

    def add_arguments(self, parser):
        parser.add_argument('--all', action='store_true', help='List every untranslated item (default: first 30 per list).')

    def handle(self, *args, all=False, **options):
        limit = None if all else 30
        outermost = not connection.in_atomic_block  # always true from the command line
        with transaction.atomic():
            if outermost and connection.vendor == 'postgresql':
                with connection.cursor() as cursor:
                    cursor.execute('SET TRANSACTION READ ONLY')  # the database refuses any write from here on
            self.report(limit)

    # ---------------------------------------------------------------- helpers
    def rows(self, queryset, *fields):
        return queryset.values_list(*fields).iterator(chunk_size=500)

    def line(self, label, total, counts):
        parts = []
        for code in OTHER:
            pct = f"{counts[code] * 100 / total:5.1f}%" if total else "   - "
            parts.append(f"{code}: {counts[code]:4}/{total:<4} {pct}")
        self.stdout.write(f"  {label:34} active {total:5}   " + "   ".join(parts))

    def missing(self, title, items, limit):
        for code in OTHER:
            names = items[code]
            if not names:
                continue
            shown = names if limit is None else names[:limit]
            more = '' if limit is None or len(names) <= limit else f"  … and {len(names) - limit} more (--all)"
            self.stdout.write(f"  {title} without {code} ({len(names)}): " + ", ".join(shown) + more)

    # ----------------------------------------------------------------- report
    def report(self, limit):
        w = self.stdout.write
        w(self.style.MIGRATE_HEADING(f"Translation report (read-only) — default language {settings.LANGUAGE_CODE}, checking {', '.join(OTHER)}"))
        sitemap = {code: STATIC_PAGES for code in LANGS}
        missing = {}

        # Models (Product.title)
        counts, miss, total = defaultdict(int), defaultdict(list), 0
        for slug, *titles in self.rows(Product.objects.filter(is_active=True).order_by('order', 'slug'),
                                      'slug', *[f'title_{c}' for c in LANGS]):
            total += 1
            for code, title in zip(LANGS, titles):
                if filled(title):
                    counts[code] += 1
                    sitemap[code] += 1
                elif code in OTHER:
                    miss[code].append(slug)
        w("\nPages (key fields)")
        self.line('Models (title)', total, counts)
        missing['Models'] = miss

        # Brands (ProductCategory.name); sitemap: brands that have active models
        with_models = set(Product.objects.filter(is_active=True).values_list('category_id', flat=True).distinct())
        counts, miss, total = defaultdict(int), defaultdict(list), 0
        for pk, slug, *names in self.rows(ProductCategory.objects.filter(is_active=True).order_by('order', 'slug'),
                                         'pk', 'slug', *[f'name_{c}' for c in LANGS]):
            total += 1
            for code, name in zip(LANGS, names):
                if filled(name):
                    counts[code] += 1
                    if pk in with_models:
                        sitemap[code] += 1
                elif code in OTHER:
                    miss[code].append(slug)
        self.line('Brands (name)', total, counts)
        missing['Brands'] = miss

        # News: title AND body text (text blocks) in that language
        body = defaultdict(set)  # news_id -> languages with body text
        for news_id, *texts in self.rows(NewsBlock.objects.filter(news__is_active=True, block_type='text'),
                                        'news_id', *[f'text_{c}' for c in LANGS]):
            for code, text in zip(LANGS, texts):
                if html_to_text(text):
                    body[news_id].add(code)
        counts, miss, total = defaultdict(int), defaultdict(list), 0
        for pk, slug, *titles in self.rows(News.objects.filter(is_active=True).order_by('-created_at', 'pk'),
                                          'pk', 'slug', *[f'title_{c}' for c in LANGS]):
            total += 1
            for code, title in zip(LANGS, titles):
                if filled(title) and code in body[pk]:
                    counts[code] += 1
                    sitemap[code] += 1
                elif code in OTHER:
                    miss[code].append(slug + ('' if filled(title) else ' (no title)') + ('' if code in body[pk] else ' (no body)'))
        self.line('News (title + body text)', total, counts)
        missing['News'] = miss

        # Dealers (name)
        counts, miss, total = defaultdict(int), defaultdict(list), 0
        for pk, *names in self.rows(Dealer.objects.filter(is_active=True).order_by('order', 'pk'), 'pk', *[f'name_{c}' for c in LANGS]):
            total += 1
            for code, name in zip(LANGS, names):
                if filled(name):
                    counts[code] += 1
                    sitemap[code] += 1
                elif code in OTHER:
                    miss[code].append(f"{pk}:{names[0] or '?'}")
        self.line('Dealers (name)', total, counts)
        missing['Dealers'] = miss

        # Content shown on pages (no own URL)
        w("\nContent on pages (no own URL)")
        counts, miss, total = defaultdict(int), defaultdict(list), 0
        for pk, *vals in self.rows(BranchManager.objects.filter(is_active=True).order_by('pk'), 'pk',
                                   *[f'full_name_{c}' for c in LANGS], *[f'position_{c}' for c in LANGS]):
            total += 1
            names, positions = vals[:len(LANGS)], vals[len(LANGS):]
            for i, code in enumerate(LANGS):
                if filled(names[i]) and filled(positions[i]):
                    counts[code] += 1
                elif code in OTHER:
                    miss[code].append(f"{pk}:{names[0] or '?'}")
        self.line('Managers (name + position)', total, counts)
        missing['Managers'] = miss

        counts, miss, total = defaultdict(int), defaultdict(list), 0
        for pk, brand, *vals in self.rows(BrandFAQ.objects.filter(is_active=True).order_by('category_id', 'order', 'pk'),
                                         'pk', 'category__slug', *[f'question_{c}' for c in LANGS], *[f'answer_{c}' for c in LANGS]):
            total += 1
            questions, answers = vals[:len(LANGS)], vals[len(LANGS):]
            for i, code in enumerate(LANGS):
                if filled(questions[i]) and html_to_text(answers[i]):
                    counts[code] += 1
                elif code in OTHER:
                    miss[code].append(f"{brand}#{pk}")
        self.line('Brand FAQ (question + answer)', total, counts)
        missing['Brand FAQ'] = miss
        w("  Trims: not translated (ProductTrim has no ru/en fields) — names and prices are shown as entered.")

        w("\nSitemap URLs per language (same rules as /sitemap.xml)")
        for code in LANGS:
            w(f"  {code}: {sitemap[code]}")
        w(f"  total: {sum(sitemap.values())}")

        w("\nNot translated" + ("" if limit is None else f" (first {limit} per list, --all for every item)"))
        any_missing = False
        for title, miss in missing.items():
            if any(miss.values()):
                any_missing = True
                self.missing(title, miss, limit)
        if not any_missing:
            w("  nothing — every active item is translated into " + " and ".join(OTHER))
