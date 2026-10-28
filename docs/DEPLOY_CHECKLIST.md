# Deploy checklist — internal SEO TZ (tasks 1–16)

## Before you start (both stages)

Do all four before typing any deploy command.

**(a) Take the DB dump and the site archive.** In cPanel → Terminal, paste the block below as it is.
- The DB credentials are read from `/home/autolig1/site/.env` into a subshell. They are never printed, never typed on the command line and never kept in the shell history, and they disappear when the block ends.
- Both files go to `~/backups/`, i.e. `/home/autolig1/backups`, which is outside `public_html` so it isn't reachable from the web.
- They are readable only by you, which matters because the archive contains `.env`.

```bash
mkdir -p ~/backups && chmod 700 ~/backups
STAMP=$(date +%F_%H%M)
(
  # read DB_* from .env literally (no shell expansion), strip CR and surrounding quotes
  while IFS='=' read -r key value; do
    value="${value%$'\r'}"; value="${value#[\"\']}"; value="${value%[\"\']}"
    export "$key=$value"
  done < <(grep -E '^DB_(NAME|USER|PASSWORD|HOST|PORT)=' /home/autolig1/site/.env)
  PGPASSWORD="$DB_PASSWORD" pg_dump -h "${DB_HOST:-localhost}" -p "${DB_PORT:-5432}" -U "$DB_USER" \
      --format=custom --no-owner --file="$HOME/backups/autoliga_db_$STAMP.dump" "$DB_NAME" \
    && echo "dump OK" || echo "DUMP FAILED - stop here"
)
tar -czf ~/backups/autoliga_site_$STAMP.tar.gz -C /home/autolig1 site \
    public_html/.htaccess public_html/static/.htaccess public_html/media/.htaccess 2>/dev/null; echo "archive exit code: $? (0 or 1 is fine; 1 = a .htaccess that does not exist yet)"
chmod 600 ~/backups/autoliga_*_$STAMP.*
```
Check the size, and that the dump is readable:
```bash
ls -lh ~/backups/autoliga_*_$STAMP.*                       # neither file may be 0 bytes; the dump is usually several MB
pg_restore --list ~/backups/autoliga_db_$STAMP.dump | grep -c "TABLE DATA"   # a number > 0 (one line per table); an error = bad dump
tar -tzf ~/backups/autoliga_site_$STAMP.tar.gz | grep -c "site/manage.py"   # 1
df -h ~ | tail -1                                           # enough free space left for the deploy
```
The media files (`public_html/media`) are not in the archive. The deploy never changes or deletes them: the WebP copies are new files in `media/_resp/`. cPanel's own backup covers them.

**(b) Write down the commit that is live now.**
```bash
cd /home/autolig1/site && git log -1 --format="%h %ad %s" --date=iso | tee ~/backups/live_commit_$STAMP.txt
git status --short | head                                   # must be empty; if not, someone edited files on the server: stop and find out why
```
Copy that line into the deploy notes as well; the rollback steps go back to this commit.
Before Stage 1 it should be `c5bff24`; before Stage 2, `b6e1342`.

**(c) Deploy window: a quiet time.**
- Pick the lowest-traffic hour from cPanel → Metrics → *Awstats* / *Visitors*. Google Tag Manager is off at the moment, so there is no GA data.
- Use a working day (Monday–Thursday) and **not** before a weekend, a holiday or a marketing campaign.
- The developer should be free for **2 hours afterwards** to watch `logs/errors.log` and to roll back if needed.
- The deploy itself takes about 15 minutes. The site is down only for the Passenger restart (a few seconds).
- Deploy Stage 2 on a different day from Stage 1, after Stage 1 has run cleanly for at least a day.

**(d) Who to call if something fails.** Fill this in before the deploy:

| Role | Name | Phone / Telegram | When |
|---|---|---|---|
| Developer (deploys, rolls back) |  |  | anything in the checks fails |
| Ahost support (server, nginx/Engintron, Passenger) |  | ticket in the Ahost client area | the site doesn't start after a restart; the cache problem in the Stage 2 check |
| Marketing / site owner (decides on a rollback, informs sales) |  |  | the site was down or a rollback was done |
| Sales (amoCRM leads) |  |  | leads stop arriving after the deploy |

If any check fails and the cause isn't obvious within 15 minutes, **roll back first and investigate afterwards** (each stage has its own Rollback section).

---

Two stages, deployed separately, each with its own rollback.

| Stage | Git | Contains | DB migrations | New packages |
|---|---|---|---|---|
| 1 | tag `deploy-stage1` (`b6e1342`) | tasks 1–13, plus four early TZ 14/15 commits (hreflang URL fixes, custom 404, 404 for unknown news) | `main` 0016–0022, `thumbnail` 0001 | pytz, sorl-thumbnail, Unidecode |
| 2 | last Task 14/15 commit (suggested tag `deploy-stage2`) | task 14 (languages), task 15 fixes | none | none |

Production today is `origin/main` (`c5bff24`, migrations up to `main.0015`).
`origin/main` is an ancestor of `deploy-stage1`, so `git pull` is a fast-forward.

Where the commands run:
- **Server**: cPanel → Terminal (bash), in the app folder `/home/autolig1/site`.
- **Checks**: Windows CMD on your own computer. `curl.exe` is built into Windows 10/11.
  - Paste the commands at the prompt as they are.
  - Inside a `.bat` file, write `%%{http_code}` instead of `%{http_code}`.

Activate the app's virtualenv before any `python`/`pip` command on the server.
cPanel → *Setup Python App* → the autoliga.uz app shows the exact command at the top:
`source /home/autolig1/virtualenv/<app>/<version>/bin/activate && cd /home/autolig1/site`.

---

## Stage 1 — `deploy-stage1` (tasks 1–13)

### 0. Before you start (on your computer)
- Merge the work into `main` so that `main` == `deploy-stage1`, then push the branch and the tag:
  `git push origin main` and `git push origin deploy-stage1`.
- Pick a quiet hour. Users won't notice anything; the only downtime is the Passenger restart.

### 1. Backup (server)
Run **"Before you start" (a) and (b)** at the top of this file: the DB dump, the site archive, the size checks and the live commit. Then:
```bash
cd /home/autolig1/site
git rev-parse HEAD > ~/backups/before_stage1_commit.txt   # code version to roll back to (c5bff24)
cp /home/autolig1/public_html/.htaccess ~/backups/public_html.htaccess.before_stage1
```
Media files are not changed by the deploy: originals are never touched, and new WebP copies go to `media/_resp/`.

### 2. Code (server)
```bash
cd /home/autolig1/site
git status                          # must be clean; if not, stop and check what was edited on the server
git pull --ff-only origin main
git log -1 --format=%h              # must print b6e1342
```

### 3. Packages (server, virtualenv active)
```bash
pip install "pytz>=2024.1" "sorl-thumbnail==13.1.0" "Unidecode>=1.3,<2.0"
```
The same pins are in both `requirements/django.txt` and `requirements.txt`.
`pip install -r <the file production uses>` gives the same result.

### 4. Migrations (server)
```bash
python manage.py showmigrations main thumbnail      # expect [ ] for 0016–0022 and thumbnail 0001
python manage.py migrate
python manage.py showmigrations main thumbnail      # all [X]
```
Every migration only adds columns or tables. There are no data migrations, and no existing row is changed.

| Migration | What it does |
|---|---|
| `main.0016_news_seo_description_…` | `seo_title` (max 65) and `seo_description` (max 160), uz/ru/en, on **News**, **Product** and **ProductCategory** (brand). Empty means automatic text. |
| `main.0017_dealer_seo_description_…` | Same `seo_title` / `seo_description` fields on **Dealer**. |
| `main.0018_producttrim` | New table **ProductTrim**: trims of a model (name, price UZS, engine, power, transmission, consumption, dimensions, order, active). Feeds the trim table and the Offer prices in JSON-LD. |
| `main.0019_brand_page` | On **ProductCategory**: `brand_text` (rich text, uz/ru/en) for `/brand/<slug>/`, plus `updated_at` for the sitemap `lastmod`. New table **BrandFAQ** (question/answer, uz/ru/en, per brand). |
| `main.0020_news_related_products` | On **News**: `preview_image_alt` (uz/ru/en) and `related_products` (many-to-many to Product), which feeds the model cards under a news item. |
| `main.0021_image_alt_text` | `alt_text` (uz/ru/en) on **Product**, **ProductGallery** and **NewsBlock** (image blocks). Empty means automatic alt text. |
| `main.0022_redirect` | New table **Redirect**: old path → model / brand / news / URL. 301s for old URLs, and slug changes are recorded automatically. |
| `thumbnail.0001_initial` | sorl-thumbnail's key-value table (`thumbnail_kvstore`) that remembers generated thumbnails. |

### 5. Static files (server)
```bash
python manage.py collectstatic --noinput     # never use --clear: it would delete static/.htaccess (post-deploy step B)
```

### 6. Restart (server)
cPanel → *Setup Python App* → **Restart**. From the terminal, this does the same:
```bash
mkdir -p /home/autolig1/site/tmp && touch /home/autolig1/site/tmp/restart.txt
```
Then:
```bash
python manage.py check --deploy 2>&1 | tail -3
tail -n 30 /home/autolig1/site/logs/errors.log       # no new tracebacks after the restart
```

### 7. Checks (Windows CMD)
Each line states its expected result. Replace `<model>` with a real model slug (e.g. `soueast`) and `<brand>` with a brand slug from the admin.
```bat
curl -s -o NUL -w "%{http_code}\n" https://autoliga.uz/
:: 200
curl -s -o NUL -w "%{http_code}\n" https://autoliga.uz/ru/products/
:: 200
curl -s -o NUL -w "%{http_code}\n" https://autoliga.uz/en/products/<model>/
:: 200
curl -s -o NUL -w "%{http_code}\n" https://autoliga.uz/brand/<brand>/
:: 200 (task 8 brand page)
curl -sI "https://autoliga.uz/products/?category=<brand>" | findstr /i "HTTP/ Location:"
:: 301, Location: /brand/<brand>/
curl -sI https://autoliga.uz/products | findstr /i "HTTP/ Location:"
:: 301, Location: /products/
curl -s -o NUL -w "%{http_code}\n" https://autoliga.uz/no-such-page/
:: 404 (custom page)
curl -s -o NUL -w "%{http_code} hops=%{num_redirects} %{url_effective}\n" -L http://www.autoliga.uz/
:: 200 hops=1 https://autoliga.uz/  (hops=2 means Ahost request item 4 is still open)
curl -s https://autoliga.uz/products/<model>/ | findstr /c:"application/ld+json" /c:"rel=\"canonical\"" /c:"<h1"
:: JSON-LD, canonical and one h1 are printed
curl -s https://autoliga.uz/sitemap.xml | findstr /c:"/brand/"
:: brand URLs are listed
curl -s https://autoliga.uz/robots.txt | findstr /i "Sitemap Disallow"
:: Sitemap: https://autoliga.uz/sitemap.xml and the Disallow lines
```
In a browser, at desktop and phone width:
- the menu and the brands dropdown open;
- a model page shows the gallery and the trims;
- the dealers page shows the map;
- the forms show no errors. Do **not** send a test lead unless sales knows about it: it goes to amoCRM.

### 8. Rollback (Stage 1)
Use this only if something is broken and can't be fixed quickly.
```bash
cd /home/autolig1/site
# 1) with the NEW code still in place, take the migrations back (drops the new columns/tables; data typed into them since the deploy is lost)
python manage.py migrate main 0015_remove_telegramuser_status
# 2) old code
git checkout --detach $(cat ~/backups/before_stage1_commit.txt)
# 3) restart (cPanel Restart, or:)
touch /home/autolig1/site/tmp/restart.txt
```
- **Step 1 is required before step 2.** Several new columns are NOT NULL, so the old code can't save News, Product or brand rows while they exist.
- If step 1 fails, restore the dump instead. Use the same `.env` reading loop as in "Before you start" (a), with this command in place of `pg_dump`:
  `PGPASSWORD="$DB_PASSWORD" pg_restore -h "${DB_HOST:-localhost}" -p "${DB_PORT:-5432}" -U "$DB_USER" -d "$DB_NAME" --clean --if-exists --no-owner ~/backups/autoliga_db_<STAMP>.dump`.
- The `thumbnail_kvstore` table and the packages can stay; the old code ignores them.
- Later, return `main` to the old commit on your computer, so the next `git pull` doesn't redeploy by accident.

---

## Stage 2 — Task 14 (languages) and Task 15 fixes

Deploy Stage 2 only once Stage 1 has run cleanly for a while (at least a day of normal traffic).
It has no migrations and no new packages.

What changes for visitors:
- The language comes only from the URL: no prefix is O'zbek, `/ru/` and `/en/` are the others.
- `/uz/...` → one 301 to the unprefixed URL.
- The language switcher is plain links.
- Pages that aren't translated stay open with `noindex,follow`.
- The sitemap lists each language with hreflang.
- Until **2027-01-31**, a visitor with the old `django_language=ru|en` cookie gets one uncacheable 302 from an unprefixed page to `/ru/...` or `/en/...`. Bots never get it, and neither do `/api/`, `/admin/`, `/static/`, `/media/`, the sitemap or robots.

### 1. Backup (server)
Run **"Before you start" (a) and (b)** again: a fresh dump and archive. Then:
```bash
cd /home/autolig1/site
git rev-parse HEAD > ~/backups/before_stage2_commit.txt      # should be b6e1342
```

### 2–6. Code, packages, migrations, static, restart
```bash
git status && git pull --ff-only origin main && git log -1 --format=%h      # the Stage 2 commit
python manage.py migrate --plan                                            # "No planned migration operations."
python manage.py collectstatic --noinput                                   # the switcher CSS changed
touch /home/autolig1/site/tmp/restart.txt                                  # or cPanel Restart
tail -n 30 /home/autolig1/site/logs/errors.log
```

### 7. Checks (Windows CMD)
Language URLs:
```bat
curl -sI https://autoliga.uz/products/ | findstr /i "HTTP/ Location: Vary: Content-Language:"
:: 200, Content-Language: uz, Vary contains Cookie, no Location
curl -sI https://autoliga.uz/uz/products/ | findstr /i "HTTP/ Location:"
:: 301, Location: /products/
curl -sI https://autoliga.uz/ru/products | findstr /i "HTTP/ Location:"
:: 301, Location: /ru/products/
curl -s -o NUL -w "%{http_code}\n" https://autoliga.uz/de/
:: 404
curl -s -o NUL -w "%{http_code}\n" https://autoliga.uz/test-utm/
:: 404 (was 500 before Task 15)
curl -s -o NUL -w "%{http_code}\n" "https://autoliga.uz/products/?brand=no-such-brand"
:: 404 (no redirect to a 404)
curl -s https://autoliga.uz/ru/products/ | findstr /c:"hreflang="
:: uz, ru, en and x-default links
curl -s https://autoliga.uz/sitemap.xml | findstr /c:"x-default"
:: hreflang alternates in the sitemap
curl -sI "https://autoliga.uz/set-language/?language=ru&next=/products/" | findstr /i "HTTP/ Location: Set-Cookie:"
:: 302, Location: /ru/products/, Set-Cookie: django_language=ru
```
Cookie redirect (transition until 2027-01-31):
```bat
curl -sI -H "Cookie: django_language=ru" https://autoliga.uz/products/ | findstr /i "HTTP/ Location: Cache-Control: Vary:"
:: 302, Location: /ru/products/, Cache-Control: private, no-store, max-age=0, Vary contains Cookie
curl -sI -H "Cookie: django_language=en" "https://autoliga.uz/news/?utm_source=test" | findstr /i "HTTP/ Location:"
:: 302, Location: /en/news/?utm_source=test  (query kept)
curl -sI -H "Cookie: django_language=ru" https://autoliga.uz/products | findstr /i "HTTP/ Location:"
:: one 302 straight to /ru/products/  (not 301 to /products/ first)
curl -sI -H "Cookie: django_language=ru" -A "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)" https://autoliga.uz/products/ | findstr /i "HTTP/ Location:"
:: 200, no Location (bots never get the cookie redirect)
curl -sI -H "Cookie: django_language=ru" https://autoliga.uz/sitemap.xml | findstr /i "HTTP/ Location:"
:: 200, no Location
curl -sI -H "Cookie: django_language=uz" https://autoliga.uz/products/ | findstr /i "HTTP/ Location:"
:: 200, no Location
```
The response also carries `X-Accel-Expires: 0`. nginx consumes that header, so it isn't visible from outside; the behavioural check below is what proves the 302 isn't cached.

**Engintron cache check.** Run these four in this order, against the same URL, within a minute:
```bat
curl -s -o NUL -w "%{http_code}\n" https://autoliga.uz/team/
:: 1) 200
curl -s -o NUL -w "%{http_code}\n" -H "Cookie: django_language=ru" https://autoliga.uz/team/
:: 2) 302   (a cached 200 from request 1 must NOT be served to a cookie visitor)
curl -s -o NUL -w "%{http_code}\n" https://autoliga.uz/team/
:: 3) 200   (the 302 from request 2 must NOT be served to a visitor without the cookie)
curl -s -o NUL -w "%{http_code}\n" -H "Cookie: django_language=ru" https://autoliga.uz/team/
:: 4) 302
```
Interpreting the results:
- **A 302 in step 3 is a real problem: roll back.** Engintron is caching the 302 and showing it to everybody. Ask Ahost to exclude responses with `Cache-Control: private` / `no-store` from the cache.
- **A 200 in step 2 or 4 is not harmful.** Engintron serves its cached uz page to cookie visitors, so those visitors see O'zbek and can use the switcher. Ask Ahost to bypass the cache when the `django_language` cookie is present.

In a browser:
- on `/ru/products/`, the switcher goes to English and then O'zbek, landing on the same page each time and staying there after a reload;
- an untranslated model in `/en/` opens with `noindex` (view source).

### 8. Rollback (Stage 2)
No database changes are involved, so code only. Roll back Task 14 as a whole, never a single group (see `docs/TASK14_CLEANUP.md`).
```bash
cd /home/autolig1/site
git checkout --detach $(cat ~/backups/before_stage2_commit.txt)     # b6e1342
touch /home/autolig1/site/tmp/restart.txt
```
Then point `main` back on your computer; locally use `git revert --no-commit deploy-stage1..<last Stage 2 commit>`.

---

## Hero slider desktop

Two commits: `feat(home): data for the desktop hero slider` and `feat(home): redesigned hero slider for screens >= 1200px`.
- **No migrations, no new packages.**
- **`collectstatic` IS required:** there are new files `css/hero_xl.css` and `js/hero_xl.js`, and `js/main-setting.js` changed.
- **What visitors see.**
  - At 1200px and wider, the home page shows the new model slider instead of the old FAW slider.
  - Below 1200px nothing changes.
  - The slider lists the models ticked "Показывать на главной" (at most 12). With none ticked, the old slider stays at all widths.

### 1. Backup (server)
```bash
cd /home/autolig1/site
git rev-parse HEAD > ~/backups/before_hero_commit.txt
```

### 2. Code, static, restart (server)
```bash
git status && git pull --ff-only origin main && git log -2 --oneline      # the two commits above
python manage.py migrate --plan                                          # "No planned migration operations."
python manage.py collectstatic --noinput                                 # required; never --clear (it would delete static/.htaccess)
touch /home/autolig1/site/tmp/restart.txt                                # or cPanel Restart
tail -n 30 /home/autolig1/site/logs/errors.log
```

### 3. Checks (Windows CMD)
```bat
curl -s https://autoliga.uz/ | findstr /c:"class=\"hero-xl\"" /c:"css/hero_xl.css" /c:"js/hero_xl.js" /c:"family=Unbounded"
:: 4 lines: the slider section, its stylesheet (media="(min-width: 1200px)"), its script (defer), the font link
curl -s https://autoliga.uz/ | find /c "<h1"
:: 1  (still exactly one H1; slide titles are h2)
curl -s https://autoliga.uz/ | findstr /c:"id=\"slider-data\""
:: 1 line: the old slider is still there for screens below 1200px
curl -s https://autoliga.uz/en/ | findstr /c:"Get the price"
:: the English button texts are there
curl -s -o NUL -w "%{http_code} %{content_type}\n" https://autoliga.uz/static/css/hero_xl.css
:: 200 text/css  (404 = collectstatic was not run)
curl -s -o NUL -w "%{http_code} %{content_type}\n" https://autoliga.uz/static/js/hero_xl.js
:: 200 and a javascript content type
curl -s https://autoliga.uz/static/js/main-setting.js | find /c "hxOn"
:: 1  (the new main-setting.js was collected; 0 = old file still served)
```
In a browser (private window):
- at 1440px wide, the new slider appears below the news block, and autoplay moves every 6s while it is on screen;
- at phone width, the old slider looks exactly as before;
- the console shows no errors.

Static files are cached for a day (`max-age=86400`), so a returning visitor can get the new page with yesterday's `main-setting.js`. The page still works, but on wide screens the hidden old slider also downloads its images until the cache expires. If the Engintron cache serves the old home page HTML, wait a few minutes or purge it.

### 4. Rollback
No database changes are involved, so code and static only:
```bash
cd /home/autolig1/site
git checkout --detach $(cat ~/backups/before_hero_commit.txt)
python manage.py collectstatic --noinput     # puts the previous main-setting.js back; the unused hero_xl.* files can stay
touch /home/autolig1/site/tmp/restart.txt
```
Then point `main` back on your computer. Locally, revert both commits with `git revert <design commit> <data commit>` (design first).

---

## After the deploy (manual steps)

### A. Soueast slug (after Stage 1 is live)
In admin → Products → **SOUEAST S09**, change the slug `soueast` to `soueast-s09` and save.
The old address gets a 301 automatically (slug history, task 13); nothing else needs to be added.
```bat
curl -sI https://autoliga.uz/products/soueast/ | findstr /i "HTTP/ Location:"
:: 301, Location: /products/soueast-s09/
curl -sI https://autoliga.uz/ru/products/soueast/ | findstr /i "HTTP/ Location:"
:: 301, Location: /ru/products/soueast-s09/
curl -s -o NUL -w "%{http_code}\n" https://autoliga.uz/products/soueast-s09/
:: 200
curl -s https://autoliga.uz/sitemap.xml | findstr /c:"/products/soueast"
:: only /products/soueast-s09/ URLs (a brand page /brand/soueast/, if the brand has that slug, is a different URL and does not change)
```
In admin → Redirects, an automatic row `/products/soueast/` → SOUEAST S09 now exists. Leave it there for good.

### B. `.htaccess` files (task 11)
Back up first: `cp /home/autolig1/public_html/.htaccess ~/backups/public_html.htaccess.$(date +%F)`.

| File in the repo | Copy to |
|---|---|
| `deploy/htaccess/static.htaccess` | `/home/autolig1/public_html/static/.htaccess` |
| `deploy/htaccess/media.htaccess` | `/home/autolig1/public_html/media/.htaccess` |
| `deploy/htaccess/public_html-root.snippet.htaccess` (optional) | paste into `/home/autolig1/public_html/.htaccess`, **outside** the `CLOUDLINUX PASSENGER CONFIGURATION` block |

```bat
curl -sI https://autoliga.uz/static/fonts/Phosphor/Phosphor.woff2 | findstr /i "Cache-Control"
:: max-age=31536000
curl -sI -H "Accept-Encoding: gzip" https://autoliga.uz/static/css/main_site.css | findstr /i "Content-Encoding Cache-Control"
:: gzip (or br), max-age=86400
curl -s -o NUL -w "%{http_code}\n" https://autoliga.uz/
:: 200: the site still works after the root .htaccess change; if not, put the backup back
```

### C. Ahost request
Send the text in `deploy/AHOST_REQUEST.md` from the autolig1 cPanel account. It asks for:
- Brotli/gzip;
- mod_deflate, mod_expires and mod_headers;
- HTTP/2;
- a one-hop http/www → https redirect;
- write access to `media/_resp/` and `media/cache/`.

When they answer, run the checks at the end of that file.

### D. Image conversion (task 11), after C item 5 is confirmed
The command writes WebP copies to `media/_resp/` and never changes or deletes originals.
```bash
python manage.py make_responsive_images --dry-run      # lists what it would do, writes nothing
python manage.py make_responsive_images --limit 20     # first 20 images; check a model page and the gallery in the browser
python manage.py make_responsive_images                # the rest; it can be stopped and run again (skips done images)
du -sh /home/autolig1/public_html/media/_resp/
```
```bat
curl -s https://autoliga.uz/products/<model>/ | findstr /c:"image/webp"
:: <source type="image/webp" ...> lines
```
For new uploads, run the command again (or schedule it as a cPanel cron, e.g. nightly).

### E. Google Search Console and Yandex.Webmaster
- Search Console (property `https://autoliga.uz/` or the domain property):
  - Sitemaps → submit `https://autoliga.uz/sitemap.xml`;
  - URL inspection → request indexing for `/`, `/products/`, the brand pages and the top models, in uz, `/ru/` and `/en/`;
  - after 1–2 weeks, look at Pages → "Duplicate without user-selected canonical", "Alternate page with proper canonical" and the 404 list.
- Yandex.Webmaster:
  - Indexing → Sitemap files → add the same sitemap;
  - Tools → robots.txt analysis (it shows the `Clean-param` line);
  - Reindex pages → the same key URLs;
  - check Site structure after a few days.

### F. PageSpeed
Test https://pagespeed.web.dev for `/`, `/products/`, `/brand/<brand>/`, `/products/<model>/` and `/dealers/`, on mobile and desktop.
- Record LCP, CLS and INP before image conversion (D) and after it.
- The footer Yandex map and the reCAPTCHA loading were left as they are on purpose. Decide about them from these numbers.

### G. Translation report (after Stage 2)
It is read-only: only SELECTs, inside a transaction that PostgreSQL marks READ ONLY.
```bash
python manage.py i18n_report          # first 30 untranslated items per list
python manage.py i18n_report --all    # everything; send the output to marketing (docs/MARKETING_LIST.md, item 12)
```
Its "Sitemap URLs per language" numbers must match the number of `<loc>` entries per language in `/sitemap.xml`.

### H. 2027-01-31
The cookie transition ends by itself. Do the tidy-up in `docs/TASK14_CLEANUP.md`.
