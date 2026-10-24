# Marketing nimalarni taqdim etishi kerak — SEO TZ (autoliga.uz)

*Asl nusxa: `MARKETING_LIST.md` (inglizcha). Ruscha: `MARKETING_LIST.ru.md`.*

Sayt kodi tayyor. Quyidagi har bir maydon bo‘sh bo‘lsa ham sayt ishlayveradi:
- blok yashiriladi;
- yoki avtomatik matn ishlatiladi;
- yoki maydon Google uchun ma'lumotlarga shunchaki qo‘shilmaydi.

Biznes kontentini (matnlar, narxlar, manzillar, koordinatalar, ish vaqti) biz o‘zimiz yozmaymiz. Quyidagilarning hammasi sizdan kelishi kerak.

Qayerga kiritiladi:
- **Admin**: autoliga.uz/admin/, o‘zingiz kiritishingiz mumkin.
- **Dasturchi**: bizga yuborasiz, biz kodga qo‘shamiz.

Har bir matn **uch tilda kerak: uz (asosiy), ru, en**.
- ru/en matni bo‘lmagan model, brend, yangilik yoki diler o‘sha tilda ochilaveradi, lekin Google'ga uni indekslamaslik aytiladi (`noindex`). U tarjima qilinmaguncha sitemap'ga ham kirmaydi.
- `python manage.py i18n_report --all` buyrug‘i aynan nima yetishmayotganini ko‘rsatadi (12-band).

Ustuvorlik: **P1** yaxshi indekslanishga to‘sqinlik qiladi, **P2** natijani yaxshilaydi, **P3** bo‘lsa yaxshi.

---

## 1. GEELY — P1 (qaror kerak)
GEELY **qanday bo‘lsa, shundayligicha qoldirildi**: matnlar, modellar, redirectlar va brend ma'lumotlari o‘zgartirilmadi.
- U Google uchun ishlatiladigan Organization tavsifida tilga olingan (9-band): "…JETOUR, SOUEAST, JAC va GEELY avtomobillari."

Iltimos, qaror qiling:
- Autoliga hozir GEELY sotadimi? Ha bo‘lsa, brend ma'lumotlarini yuboring (3- va 4-bandlar). Yo‘q bo‘lsa, uni o‘sha tavsifdan olib tashlaymiz va brend sahifasi faol bo‘lmaydi.

## 2. Bosh sahifadagi H1 — P1 (tasdiqlang yoki almashtiring)
Bosh sahifada endi bitta H1 bor. Hozirgi matn ishchi variant; iltimos, tasdiqlang yoki o‘zingiznikini yuboring (taxminan 70 belgidan kam):
- uz: AUTOLIGA — rasmiy avtosalonlar va servislar tarmog‘i
- ru: AUTOLIGA — сеть официальных автосалонов и сервисов
- en: AUTOLIGA — network of official car dealerships and services

Bosh sahifadagi ikki kichik matn faqat o‘zbekchada bor; ru/en variantlarini biz o‘ylab topmadik. Iltimos, ru va en tillarida yuboring:
- dumaloq nishondagi matn "Autoliga — Ishonch ✦ Barqarorlik ✦ Quvvat ✦";
- yashirin yorliq "{brand} narxi", uni ekran o‘quvchi dasturlar narx yonida o‘qiydi. Masalan "Цена {brand}" / "{brand} price"; iltimos, matnini tasdiqlang.

→ **Dasturchi**

## 3. Brend sahifalari `/brand/<slug>/` — P1
Har bir faol brend uchun (JETOUR, SOUEAST, JAC, … va 1-band "ha" desa GEELY): Admin → Brendlar (kategoriyalar):

| Maydon | Nima | Cheklovlar |
|---|---|---|
| Brend sahifasi matni (`brand_text`) | brend haqida 2–5 xatboshi, O‘zbekistondagi faoliyati: tarixi, kafolat, servis, nega Autoliga'dan sotib olish kerak | formatlangan matn; bo‘sh bo‘lsa blok yashiriladi |
| SEO sarlavha | Google natijalaridagi sarlavha | **ko‘pi bilan 65 belgi**; bo‘sh bo‘lsa avtomatik |
| SEO tavsif | Google natijalaridagi qisqa matn | **120–160 belgi** (maydon 160 da to‘xtaydi); bo‘sh bo‘lsa avtomatik |
| FAQ (Brend FAQ, ichki jadval) | xaridorlar beradigan 4–8 ta haqiqiy savol va javoblari | savol 255 belgigacha; javob formatlangan matn |

FAQ javoblari to‘g‘ri va dolzarb bo‘lishi kerak (kafolat yillari, servis oraliqlari, kredit shartlari). Google ularni o‘zgartirmasdan ko‘rsatadi.

## 4. Modellar — P1
Admin → Mahsulotlar, har bir faol model uchun:

| Maydon | Nima | Cheklovlar |
|---|---|---|
| Nomi | brend qanday yozsa, model nomi aynan shunday: bosh harflar va bo‘shliqlar bilan, masalan "JETOUR T1", "jetour-t1" emas | qisqa; bu H1 |
| SEO sarlavha | masalan "JETOUR T1 — narxi va komplektatsiyalari \| AUTOLIGA" | **ko‘pi bilan 65 belgi** |
| SEO tavsif | narxi (dan boshlab), asosiy xususiyatlar, qayerdan sotib olish mumkin | **120–160 belgi** |
| Alt matn (asosiy rasm) | rasmda nima borligi, masalan "JETOUR T1 oq rangda, old tomondan" | 255 belgigacha; bo‘sh bo‘lsa "{Brend} {Model}" |
| Komplektatsiyalar (ichki jadval) | komplektatsiya nomi, narxi UZS da (faqat raqam), dvigatel, quvvat **o‘lchov birligi bilan** (masalan "150 hp" / "150 ot kuchi"), uzatmalar qutisi, yoqilg‘i sarfi, o‘lchamlari | narx Google'dagi "narxi …dan" ma'lumotiga ketadi |
| Galereya rasmlari, har bir rasmga alt matn | har bir rasmga bitta qisqa tavsif (tashqi ko‘rinish / salon / detal) | bo‘sh bo‘lsa avtomatik "{Brend} {Model}, rasm N" |

Izohlar:
- **Juda uzun sarlavhalar** Google natijalarida kesiladi. 65 belgidan uzun har qanday SEO sarlavhani qisqartirish kerak; maydon ko‘prog‘ini qabul qilmaydi.
- **SOUEAST S09**: deploydan keyin uning manzili `/products/soueast/` dan `/products/soueast-s09/` ga o‘zgaradi. Slug'ni biz o‘zgartiramiz; eski havola 301 redirect orqali ishlashda davom etadi. Reklamalar, ijtimoiy tarmoqlardagi profil matnlari va bosma QR kodlardagi havolani qulay vaqtda yangilang.
- **Mavjudlik** ("sotuvda bor" / "buyurtma asosida") hozir Google'ga **ko‘rsatilmaydi**, chunki ishonchli ma'lumot yo‘q edi. Kerak bo‘lsa ayting va uni kim yangilab turishini bildiring.

## 5. Huquqiy sahifalar `/privacy/` va `/terms/` — P1
- Ikkala sahifa ham qisqa neytral matn bilan mavjud va `noindex`, ya'ni ular qidiruv uchun mo‘ljallanmagan.
- Iltimos, yuristingizdan maxfiylik siyosati va foydalanish shartlarining **yakuniy huquqiy matnini** uz, ru va en tillarida, yuridik shaxs nomi va sanasi bilan yuboring. → **Dasturchi**

## 6. Ijtimoiy tarmoq profillari — P2
Footer'dagi ikonkalar va Google'dagi Organization ma'lumotlari (`sameAs`) aynan shu uchtasini ishlatadi. Iltimos, rasmiy va dolzarb ekanini tasdiqlang, yetishmayotganlarini yuboring (Facebook, TikTok, ikkinchi Telegram, …). → **Dasturchi**
- https://www.instagram.com/autoliga.uz/
- https://t.me/avtoligauz
- https://youtube.com/@autoligauz

## 7. Bosh ofis — P1
Saytdagi yagona telefon raqami **+998 78 555 73 77**, email info@autoliga.uz. Iltimos, ikkalasini tasdiqlang, keyin yuboring:
- bosh ofisning aniq manzili (uz/ru/en) va xaritadagi koordinatalari (kenglik, uzunlik; Google yoki Yandex xaritasidan "nuqta qo‘yish → nusxa olish");
- ish vaqti: **saytda hozir har kuni 09:00–20:00 deb yozilgan; boshqa manbada 09:00–19:00 deyilgan.** Qaysi biri to‘g‘ri?
- bosh ofis Dilerlar sahifasida alohida sahifasi bor filial sifatida chiqishi kerakmi (unda u 8-banddagi kabi kiritiladi).

## 8. Dilerlar / filiallar — P1
Admin → Dilerlar, har bir filial uchun:

| Maydon | Format |
|---|---|
| Nomi (uz/ru/en) | masalan "Autoliga Yunusobod" |
| Manzil (uz/ru/en) | ko‘cha, uy, tuman, shahar |
| Koordinatalar | kenglik va uzunlik, masalan 41.3111 / 69.2797 (xaritadagi belgi va Google uchun kerak) |
| Telefonlar | bitta yoki bir nechta, **vergul bilan ajratilgan**: `+998 78 555 73 77, +998 XX XXX XX XX` |
| Ish vaqti | aynan **`Du-Yak 9:00 - 20:00`** ko‘rinishida. Google'ga faqat shu ko‘rinish uzatiladi; boshqa ko‘rinishlar sahifada chiqadi, lekin Google'ga yuborilmaydi. |
| Rasmlar va ularning izohlari (uz/ru/en) | salonning tashqi va ichki ko‘rinishi |
| Menejerlar (ichki jadval) | to‘liq ismi va lavozimi (uz/ru/en), rasmi |
| SEO sarlavha / tavsif | ko‘pi bilan 65 / 120–160 belgi (ixtiyoriy; bo‘sh bo‘lsa avtomatik) |

## 9. Google uchun Organization tavsifi — P2
Google'dagi Organization ma'lumotlaridagi qisqa "biz haqimizda" jumlasi faqat o‘zbekchada bor (1-bandga qarang). Iltimos, xuddi shu jumlani **ru** va **en** tillarida, taxminan 150–250 belgida yuboring. → **Dasturchi**

## 10. Yangiliklar — P2
Admin → Yangiliklar, har bir yangilik uchun:
- **Har bir tilda sarlavha va asosiy matn.** Yangilik o‘sha tilda faqat sarlavhasi **va** asosiy matni bo‘lsagina tarjima qilingan hisoblanadi.
- **Asosiy rasm alt matni** (uz/ru/en), va har bir rasm blokiga alt matn.
- **Bog‘liq modellar** ("Модели в новости"): yangilik qaysi modellar haqida bo‘lsa, o‘shalarni tanlang, shunda yangilik ostida narxi bilan model kartochkasi chiqadi.
- SEO sarlavha / tavsif: ko‘pi bilan 65 / 120–160 belgi (ixtiyoriy).

## 11. Google Tag Manager — P2 (qaror kerak)
- GTM yuklovchi skripti saytdan 2026-02-02 da olib tashlangan (commit c64d777). Ba'zi sahifalarda faqat `<noscript>` qismi qolgan, u oddiy tashrif buyuruvchilar uchun hech narsa qilmaydi.
- Demak, **GTM va uning ichidagi hamma narsa (GA4, Meta Pixel, …) hozir ishlamayapti.**

Iltimos, qaror qiling:
- GTM'ni qaytaramizmi? Unda konteyner ID'sini, ichida qaysi teglar borligini va uni kim boshqarishini tasdiqlang. Biz uni barcha sahifalar uchun bitta joyga qaytaramiz.
- Yoki kerak emasmi? Unda qolgan `<noscript>` qismlarini olib tashlaymiz.

→ **Dasturchi**

## 12. Hamma narsaning ru / en tarjimalari — P1
Deploydan keyin biz faqat o‘qiydigan tarjima hisobotini ishga tushirib, natijasini sizga yuboramiz. Unda ru yoki en tarjimasi yo‘q har bir model, brend, yangilik, diler, menejer va brend FAQ ro‘yxati bo‘ladi.
- Komplektatsiya nomlari va narxlari tarjima qilinmaydi; ular kiritilganidek ko‘rsatiladi.
- Ularni Admin'da to‘ldiring (har bir maydonning `_ru` / `_en` yorliqlari).
- Shundan keyin sahifalar o‘sha tilda indekslanadigan bo‘ladi va sitemap'ga avtomatik kiradi; boshqa hech narsa qilish shart emas.

---

### Uzunliklar bo‘yicha qisqa jadval
| Matn | Uzunlik |
|---|---|
| SEO sarlavha | **65** belgigacha (maydon chegarasi) |
| SEO tavsif | **120–160** belgi (maydon 160 da to‘xtaydi) |
| H1 / model nomi | qisqa, haqiqiy nomi |
| Alt matn | bitta jumla, 255 belgigacha, rasmda nima borligini tasvirlaydi; "rasm" / "фото" so‘zi bilan boshlash shart emas |
| FAQ savoli | 255 belgigacha |
