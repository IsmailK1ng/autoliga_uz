# GA4 / GTM dataLayer events — developer part (part 1 of `autoliga_GA4_eventlar.docx`)

The site pushes events to `window.dataLayer`, and GTM (`GTM-K2LCFZJG`) turns them into GA4 events.
No analytics tag (gtag, ym) was added to the code for this task. The GTM setup (part 2) and the GA4 settings (part 3) are done in the GTM and GA4 web interfaces, not in this repository.

## Events the site pushes

| Event | When | Keys |
|---|---|---|
| `lead_submit` | After the server answers 2xx to a form. Never on a validation error or a server error. Once per submission. | `form_type`, `car_model`, `car_brand`, `dealer`, `page_type` |
| `form_start` | The first time the visitor focuses or types in a form, once per page load. | `form_type`, `car_model`, `page_type` |
| `view_model` | When a model page `/products/<slug>/` loads, right after the GTM snippet. | `car_model`, `car_brand`, `price_from` (number in UZS, `0` when the model has no trim price) |

Every key is always present. A key with no value is the empty string `""`.
`car_model` is the product slug. `car_brand` is the brand (`ProductCategory`) slug.

**No personal data.** `lead_submit` and `form_start` go through one helper, `window.autoligaTrack` in `main/templates/main/includes/datalayer_events.html`. The helper copies only the five keys above, so the name, phone, message and region never reach the dataLayer, even if a caller passes them by mistake.

## Forms

| Form | Page | `form_type` | `page_type` | `car_model` / `car_brand` | `dealer` |
|---|---|---|---|---|---|
| `#testDriveForm` | `/test-drive/` | `test_drive` | `test_drive` | the selected model's slugs | slug of the selected dealer |
| `#faw-contact-form` ("Narxini bilish" modal) | `/products/<slug>/` | `price` | `product` | the current model | `""` |
| `#contactForm` | home page `/` | `contact` | `home` | `""` | `""` |
| `#contactForm` | `/contact/` | `contact` | `contact` | `""` | `""` |
| `#reviewForm` (review modal) | home page `/` | `review` | `home` | `""` | `""` |

There are no other lead forms. The API has only `contact`, `test-drive` and `reviews` endpoints. A `dealer-applications` form does not exist in this codebase.

**Dealer value.** The `Dealer` model has no slug field. The value is made from the dealer's base (uz) name, for example "Jetour Yunusobod" → `jetour-yunusobod`, so it is the same in every site language. If the name is empty, the dealer id is used. The value comes from `dealer_card()` in `main/dealer_info.py` (key `slug`).

**Duplicate pushes.** Each form already blocks a second submission while one is in flight: the test-drive form uses `isSubmitting` and a disabled button, the price and contact forms use `isSubmitting`, and the review form uses a disabled button. So one submission pushes `lead_submit` once.

**"Narxini bilish" modal.** When the modal opens, the script puts the cursor in the message box. The helper's `quietFocus()` does this without counting it as `form_start`. The event fires when the visitor actually clicks a field or types, including typing straight into the already-focused message box.

**Replaced events.** The old pushes `test_drive_submitted` (test-drive form) and `lead_form_submitted` (price and contact forms) were removed, and `lead_submit` replaces them. If a GTM trigger still listens for an old name, move it to `CE - lead_submit`.

## `data-track` attributes (for GTM click triggers only)

These attributes add no styles and no JavaScript.

| Element | Attributes |
|---|---|
| "Narxini bilish" button on the model page (`product_detail.html`) | `data-track="price_button" data-model="<slug>"` |
| "Narxini bilish" button in the desktop hero slider (`hero_xl_body.html`) | `data-track="price_button" data-model="<slug>"` |
| "Test-drayvga yozilish" button on the model page | `data-track="test_drive_button" data-model="<slug>"` |
| "Test-drayvga yozilish" link in the desktop hero slider | `data-track="test_drive_button" data-model="<slug>"` |
| "Test-drayv" link in the header menu, the footer and the 404 page | `data-track="test_drive_button"` (no model) |

The model cards on `/products/` and on the brand pages have only a "Batafsil" (details) link, so they get no attribute.
The header, footer and 404 links are counted as `test_drive_click` too. Use `page_path` and `data-model` to tell them apart from the model-page buttons.

## Files changed

| File | Change |
|---|---|
| `main/templates/main/includes/datalayer_events.html` | **New.** The `window.autoligaTrack` helper with `leadSubmit`, `watchFormStart` and `quietFocus`. |
| `templates/base.html` | Includes the helper right after `gtm_head.html`. |
| `main/templates/main/product_detail.html` | Includes the helper and pushes `view_model` after the GTM snippet. The price form gets `data-car-model` and `data-car-brand` and pushes `form_start` and `lead_submit`. The modal focus uses `quietFocus`. The price and test-drive buttons get `data-track`. |
| `main/views.py` | `product_detail` passes `price_from`, the lowest active trim price from `seo.min_trim_price`. |
| `main/templates/main/test_drive.html` | The model options get `data-model` and `data-brand`, and the dealer options get `data-slug`. The form pushes `form_start` and `lead_submit`. |
| `main/dealer_info.py` | `dealer_card()` returns `slug`. |
| `main/templates/main/index.html` | The contact form (`contact`/`home`) and the review form (`review`/`home`) push `form_start` and `lead_submit`. |
| `main/templates/main/contact.html` | The contact form (`contact`/`contact`) pushes `form_start` and `lead_submit`. |
| `main/templates/main/includes/hero_xl_body.html` | `data-track` on the price and test-drive links. |
| `main/templates/main/includes/header.html`, `main/templates/main/includes/footer.html`, `templates/404.html` | `data-track="test_drive_button"` on the test-drive link. |
| `main/tests/test_datalayer_events.py` | **New.** Checks the helper, `view_model`, the option slugs, the `data-track` attributes and that no PII keys are in the helper. |

## Checks

- `python manage.py check`: no issues.
- `main/tests/test_datalayer_events.py`: 7 tests, all pass.
  - The `main/tests` package cannot be imported right now, because `main/tests/__init__.py` has broken encoding (SyntaxError on line 34). This was already broken before this change.
  - The new module was run on its own (copied outside the package) until `__init__.py` is fixed.
- Not done: checking in a browser with GTM Preview. That needs a deploy with `DEBUG=False`, because GTM loads only when `ANALYTICS_ENABLED` is true. Use the acceptance list below once deployed.

## Acceptance (GTM Preview, incognito, no extensions)

1. Send each form with valid test data. The Data Layer tab shows `lead_submit` once, with the right `form_type`.
2. Send a form with a short phone number, or while the server returns an error. No `lead_submit` appears.
3. Click into a form for the first time. `form_start` appears once. Opening the "Narxini bilish" modal by itself does not push it.
4. Open `/products/jetour-t1/`. `view_model` appears with `car_model: "jetour-t1"`.
5. No pushed object contains a name, phone number or message.

## Note on GA4 page views

`main/templates/main/includes/analytics.html` still loads gtag.js directly for `G-VHDEDRT6PE` when `GA_DIRECT_ENABLED=True` (the default). The new GA4 event tags in GTM work alongside it. However, if a **Google tag** (page view) for the same ID is also added in GTM, page views are counted twice. Choose one:

- keep the direct gtag and add no page-view Google tag in GTM; or
- add the Google tag in GTM, then set `GA_DIRECT_ENABLED=False` in `.env`.
