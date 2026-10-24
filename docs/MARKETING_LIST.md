# What marketing needs to provide — SEO TZ (autoliga.uz)

The site code is ready. Each field below is built so that, while it is empty, the site still works:
- the block is hidden;
- or an automatic text is used;
- or the field is simply left out of the data for Google.

We do not write business content (texts, prices, addresses, coordinates, hours) ourselves. Everything below has to come from you.

Where it goes:
- **Admin** means autoliga.uz/admin/; you can type it in yourselves.
- **Developer** means send it to us and we put it in the code.

Each text is needed in **three languages: uz (main), ru, en**.
- A model, brand, news item or dealer without a ru/en text still opens in that language, but Google is told not to index it (`noindex`). It also stays out of the sitemap until it is translated.
- `python manage.py i18n_report --all` lists exactly what is missing (item 12).

Priority: **P1** blocks good indexing, **P2** improves results, **P3** is nice to have.

---

## 1. GEELY — P1 (a decision)
GEELY was **left exactly as it is**: no texts, models, redirects or brand data were changed.
- It is mentioned in the Organization description used for Google (item 9): "…JETOUR, SOUEAST, JAC va GEELY avtomobillari."

Please decide:
- Does Autoliga sell GEELY now? If yes, send the brand data (items 3 and 4). If no, we remove it from that description and the brand page stays inactive.

## 2. Home page H1 — P1 (approve or replace)
The home page now has one H1. The current wording is a working text; please approve it or send your own (under about 70 characters):
- uz: AUTOLIGA — rasmiy avtosalonlar va servislar tarmog‘i
- ru: AUTOLIGA — сеть официальных автосалонов и сервисов
- en: AUTOLIGA — network of official car dealerships and services

Two small home-page texts exist only in O'zbek; we did not invent ru/en versions. Please send ru and en for:
- the round badge text "Autoliga — Ishonch ✦ Barqarorlik ✦ Quvvat ✦";
- the hidden label "{brand} narxi", read by screen readers next to the price. For example "Цена {brand}" / "{brand} price"; please confirm the wording.
→ **Developer**

## 3. Brand pages `/brand/<slug>/` — P1
For each active brand (JETOUR, SOUEAST, JAC, … and GEELY if item 1 says yes), go to Admin → Brands (categories):

| Field | What | Limits |
|---|---|---|
| Brand page text (`brand_text`) | 2–5 paragraphs about the brand in Uzbekistan: history, warranty, service, why buy from Autoliga | rich text; empty means the block is hidden |
| SEO title | the title in Google results | **max 65 characters**; empty means automatic |
| SEO description | the snippet in Google results | **120–160 characters** (the field stops at 160); empty means automatic |
| FAQ (Brand FAQ, inline) | 4–8 real questions buyers ask, with answers | question up to 255 characters; answer is rich text |

FAQ answers must be true and current (warranty years, service intervals, credit terms). Google shows them as-is.

## 4. Models — P1
Admin → Products, for every active model:

| Field | What | Limits |
|---|---|---|
| Title / name | the model name exactly as the brand writes it: capitals and spaces, e.g. "JETOUR T1", not "jetour-t1" | short; it is the H1 |
| SEO title | e.g. "JETOUR T1 — narxi va komplektatsiyalari \| AUTOLIGA" | **max 65 characters** |
| SEO description | price from, key specs, where to buy | **120–160 characters** |
| Alt text (main photo) | what is in the photo, e.g. "JETOUR T1 oq rangda, old tomondan" | up to 255 characters; empty means "{Brand} {Model}" |
| Trims (inline) | trim name, price in UZS (digits only), engine, power **with unit** (e.g. "150 hp" / "150 ot kuchi"), transmission, consumption, dimensions | the price feeds Google's "price from" data |
| Gallery photos, alt text per photo | one short description per photo (exterior / interior / detail) | empty means automatic "{Brand} {Model}, rasm N" |

Notes:
- **Titles that are too long** get cut in Google results. Any SEO title over 65 characters must be shortened; the field won't accept more.
- **SOUEAST S09**: after the deploy, its address changes from `/products/soueast/` to `/products/soueast-s09/`. We do the slug change; the old link keeps working through a 301 redirect. Update the link in ads, social bios and printed QR codes when convenient.
- **Availability** ("in stock" / "on order") is **not** shown to Google now, because there was no reliable data. Tell us if you want it and who keeps it up to date.

## 5. Legal pages `/privacy/` and `/terms/` — P1
- Both pages exist with a short neutral text and are `noindex`, so they are not meant for search.
- Please send the **final legal text** from your lawyer for the privacy policy and the terms of use, in uz, ru and en, with the legal entity name and the date. → **Developer**

## 6. Social profiles — P2
The footer icons and Google's Organization data (`sameAs`) use exactly these three. Please confirm they are official and current, and send any missing ones (Facebook, TikTok, a second Telegram, …). → **Developer**
- https://www.instagram.com/autoliga.uz/
- https://t.me/avtoligauz
- https://youtube.com/@autoligauz

## 7. Head office — P1
The only phone number on the site is **+998 78 555 73 77**, with the email info@autoliga.uz. Please confirm both, then send:
- the head office's exact address (uz/ru/en) and the map coordinates (latitude, longitude, from Google or Yandex maps; "drop pin → copy");
- the opening hours: **the site currently says 09:00–20:00 every day; another source said 09:00–19:00.** Which is right?
- whether the head office should appear on the Dealers page as a branch with its own page (then it is entered like item 8).

## 8. Dealers / branches — P1
Admin → Dealers, for every branch:

| Field | Format |
|---|---|
| Name (uz/ru/en) | e.g. "Autoliga Yunusobod" |
| Address (uz/ru/en) | street, house, district, city |
| Coordinates | latitude and longitude, e.g. 41.3111 / 69.2797 (needed for the map pin and Google) |
| Phones | one or more, **comma-separated**: `+998 78 555 73 77, +998 XX XXX XX XX` |
| Working hours | exactly in the form **`Du-Yak 9:00 - 20:00`**. Only this form is passed to Google; other forms are shown on the page but not sent to Google. |
| Photos and their captions (uz/ru/en) | the showroom from outside and inside |
| Managers (inline) | full name and position (uz/ru/en), photo |
| SEO title / description | max 65 / 120–160 characters (optional; automatic if empty) |

## 9. Organization description for Google — P2
The short "about us" sentence in Google's Organization data exists only in O'zbek (see item 1). Please send the same sentence in **ru** and **en**, about 150–250 characters. → **Developer**

## 10. News — P2
Admin → News, for every news item:
- **Title and body text in each language.** A news item counts as translated only when it has both a title **and** body text in that language.
- **Preview image alt** (uz/ru/en), and alt text on every image block.
- **Related models** ("Модели в новости"): pick the models the news is about, so a model card with its price appears under the news.
- SEO title / description: max 65 / 120–160 characters (optional).

## 11. Google Tag Manager — P2 (a decision)
- The GTM loader script was removed from the site on 2026-02-02 (commit c64d777). Only the `<noscript>` part is left on some pages, which does nothing for normal visitors.
- So **GTM and anything inside it (GA4, Meta Pixel, …) is not running now.**

Please decide:
- Restore GTM? Then confirm the container ID, which tags are inside it, and who manages it. We put it back in one place for all pages.
- Or not needed? Then we remove the leftover `<noscript>` parts.

→ **Developer**

## 12. ru / en translations of everything — P1
After the deploy, we run the read-only translation report and send you the output. It lists every model, brand, news item, dealer, manager and brand FAQ that is missing ru or en.
- Trim names and prices are not translated; they are shown as entered.
- Fill these in Admin (the `_ru` / `_en` tabs of each field).
- After that, the pages become indexable in that language and enter the sitemap automatically; nothing else needs to be done.

---

### Length cheat sheet
| Text | Length |
|---|---|
| SEO title | up to **65** characters (the field limit) |
| SEO description | **120–160** characters (the field stops at 160) |
| H1 / model name | short, the real name |
| Alt text | one sentence, up to 255 characters, describes what is in the photo; no need to start with "rasm" / "фото" |
| FAQ question | up to 255 characters |
