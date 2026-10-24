# What is left — after the SEO TZ code (tasks 1–16)

The code for all 16 tasks is written, tested locally and committed on branch `seo-task-5-ssr`. **Nothing has been pushed or deployed.**
This file lists everything that still has to happen, who does it, and where the details are.

| # | What | Who | Details |
|---|---|---|---|
| 1 | Deploy Stage 1 and Stage 2 | developer | `docs/DEPLOY_CHECKLIST.md` |
| 2 | Marketing content | marketing | `docs/MARKETING_LIST.md` (`.uz.md`, `.ru.md`) |
| 3 | Admin data entry | marketing / content manager | below |
| 4 | External checks and services | developer + Ahost | below |
| 5 | Open decisions | site owner / marketing | below |
| 6 | Broken project test suite | developer, separate task | below |
| 7 | Cleanup after 2027-01-31 | developer | `docs/TASK14_CLEANUP.md` |

---

## 1. Deploy (developer)
- **Git:**
  - merge the branch into `main`;
  - push `main` and the tag `deploy-stage1` (`b6e1342`);
  - create and push the tag `deploy-stage2` on the last commit when Stage 2 goes out.
- **Stage 1:** tag `deploy-stage1`, tasks 1–13. It also includes four early TZ-14/15 commits: the hreflang URL fixes, hreflang only for existing languages, the custom 404 page, and a 404 for unknown news.
  - Migrations `main` 0016–0022 and `thumbnail` 0001; packages pytz, sorl-thumbnail, Unidecode.
- **Stage 2:** Task 14 (language URLs, the cookie transition until 2027-01-31, switcher, sitemap per language, noindex for untranslated pages) and the Task 15 fixes.
  - No migrations, no packages.
  - The middleware-order commit `a506730` belongs to Stage 2 only.
- **Rollback:**
  - Stage 1 is migrations back to `0015`, *then* the old code.
  - Stage 2 is code only, and **always the whole Stage 2, never a single group**.

## 2. Marketing content (marketing)
Everything is in `docs/MARKETING_LIST.md` (12 items, with priorities, formats and limits). The P1 items:
- GEELY decision;
- home H1 approval, plus ru/en for the two home-page texts that exist only in Uzbek;
- brand texts and FAQ;
- model names, SEO titles (≤ 65) and descriptions (120–160), trims with prices and power units, alt texts;
- final legal texts for `/privacy/` and `/terms/`;
- head office address, coordinates and hours (09–19 or 09–20?);
- dealer data: coordinates, hours in the form `Du-Yak 9:00 - 20:00`, comma-separated phones;
- ru/en translations of all content.

Nothing of this was invented in the code. Empty fields hide the block or use an automatic text.

## 3. Admin data entry (after Stage 1 is live)
- **SOUEAST S09:** change the slug `soueast` → `soueast-s09`, then run the curl checks (`DEPLOY_CHECKLIST.md`, step A). The old URL keeps working with a 301.
- Enter what marketing delivers: brand pages and FAQ, models and trims, gallery alts, dealers and managers, news (title **and** body per language, related models).
- After Stage 2, run `python manage.py i18n_report --all` (read-only) and give the list of untranslated items to marketing. Run it again after they fill it in.

## 4. External checks and services (developer + Ahost)
- **Ahost request** (`deploy/AHOST_REQUEST.md`): Brotli/gzip, mod_deflate/expires/headers, HTTP/2, a one-hop http/www → https redirect, and write access to `media/_resp/` and `media/cache/`.
- **`.htaccess`** for `public_html/static/`, `public_html/media/` and (optionally) the root, from `deploy/htaccess/`.
- **Image conversion:** `make_responsive_images --dry-run`, then `--limit 20`, then all. It only adds WebP copies; originals are never changed.
- **Engintron cache check** after Stage 2: the 4-request sequence in the checklist.
- **Google Search Console and Yandex.Webmaster:** submit `sitemap.xml` and request indexing of the key pages. After 1–2 weeks, review the canonical, duplicate and 404 reports.
- **PageSpeed** (mobile and desktop) on the key pages, before and after image conversion.

## 5. Open decisions
| Decision | Options | Who |
|---|---|---|
| **GTM** | The loader was removed on 2026-02-02 (c64d777), so GTM, GA4 and pixels are **not running**. Restore it (container ID, tags, owner), or remove the leftover `<noscript>` parts. | marketing |
| GEELY | Sold or not: brand data, or removal from the Organization description | site owner |
| Availability in Google data | Currently not sent. Add it only if someone keeps it up to date. | marketing |
| Head office as a dealer page | Yes: entered as a dealer. No: stays in the footer and contacts only. | marketing |
| Footer Yandex map, reCAPTCHA loading | Left unchanged on purpose. Decide from the production PageSpeed numbers. | developer + owner |
| `/api/kg/` legacy rule | Kept unchanged. Remove only after the logs, the Telegram bot and any partner client show it is unused. | developer |

## 6. Broken project test suite (separate task)
`manage.py test` can't start at all:
- `main/tests/__init__.py` has had a SyntaxError (corrupted text) since commit `9454b36` (2026-03-30).

Run from a repaired copy, with all outgoing network blocked, the 40 tests give **16 pass and 24 fail**. The failures are identical on `origin/main`, `deploy-stage1` and the current branch, so they come from before the SEO work:
- 22 are errors in test setup, which still uses an old schema (`Product(category='tiger_vh')` as text);
- 2 are `POST /api/uz/contact/` returning 500 inside those tests.

What the task involves:
- repair `__init__.py`;
- update the fixtures to the current models;
- **mock amoCRM and Telegram**, so tests can never send real leads or messages;
- then add the SEO checks used during this work: 404, canonical, hreflang, sitemap, redirects, cookie transition. They exist today only as local scripts.

## 7. Cleanup after 2027-01-31 (developer)
The cookie transition switches itself off on that date. Then do the tidy-up in `docs/TASK14_CLEANUP.md`:
- remove the cookie redirect and its `Vary: Cookie`;
- make the switcher's O'zbek link a plain link;
- simplify or retire `/set-language/`;
- delete the unused `ForceRussianMiddleware`;
- remove the `/api/kg/` rule once it's confirmed unused.

Afterwards, run the checks listed there.

---

### Local leftovers (not in git)
- The local dev DB has no demo or test data left (only `jetour-t1` / `jetour`).
- There's a second worktree at `C:\Users\Salohiddin\Desktop\autoliga_stage1` (on `b6e1342`). It wasn't created during this work; remove it with `git worktree remove` when it's no longer needed.
