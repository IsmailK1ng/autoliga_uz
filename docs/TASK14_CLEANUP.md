# Task 14 cleanup — after 2027-01-31

The cookie transition (visitors who still carry the old `django_language=ru|en`
cookie get one 302 from an unprefixed page to `/ru/...` or `/en/...`) ends on
**2027-01-31**. After that date the code already behaves as if it were gone
(`transition_active()` returns False), so this cleanup is tidy-up, not a fix.
Do it in one small commit and run the Task 14 tests afterwards.

## Remove

1. **Cookie redirect** — `main/language.py`
   - the `COOKIE_REDIRECT_UNTIL` constant and `transition_active()`;
   - the `_cookie_redirect()` method and its call in `SiteLanguageMiddleware.__call__`;
   - the `patch_vary_headers(response, ('Cookie',))` for unprefixed pages
     (it exists only for the transition);
   - `NO_REDIRECT_PREFIXES`, `BOT_RE` and `REDIRECT_STATUSES` if nothing else uses them
     (`REDIRECT_STATUSES` is also used by the `/uz/` rule — keep it then).

2. **O'zbek switcher link** — `main/templatetags/seo_tags.py`, `language_links()`
   - drop the `/set-language/?language=uz&next=...` branch and `rel="nofollow"`:
     the uz link becomes a plain `href` like ru/en;
   - remove the `transition_active` import.
   - `main/templates/main/includes/header.html` needs no change (it prints whatever
     `language_links` returns).

3. **`/set-language/` GET path** — `main/views.py`, `set_language_get()`
   - keep the URL alive for old cached HTML for a while longer (it is harmless),
     or replace the view with a 301 to the prefixed `next`/Referer page without
     setting a cookie; remove `Disallow: /set-language/` from `robots.txt` only
     when the URL itself is removed.

4. **Unused `ForceRussianMiddleware` class** — `myproject/middleware.py`
   - no longer in `MIDDLEWARE` since Task 14 group 1; delete the class.

5. **`/api/kg/` rule** — `main/language.py`, API branch
   - copied unchanged from `ForceRussianMiddleware`; there is no `/api/kg/` route
     and no `ky`/`kg` language. Delete it **only after confirming** nothing calls
     `/api/kg/...` (check the access log, the Telegram bot and any mobile/partner
     client).

## Check after the cleanup

```bash
# no cookie redirect any more: same answer with and without the old cookie
curl -sI -H "Cookie: django_language=ru" https://autoliga.uz/products/ | grep -iE "^HTTP|^location"   # 200, no location
curl -sI https://autoliga.uz/products/ | grep -iE "^HTTP|^location"                                    # 200
# the switcher's O'zbek link is a plain link
curl -s https://autoliga.uz/ru/products/ | grep -o 'href="[^"]*" hreflang="uz"'                       # href="/products/"
```
