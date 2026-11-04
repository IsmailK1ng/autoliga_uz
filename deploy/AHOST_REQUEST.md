# Request to Ahost support (SEO TZ task 11)

Send the text below from the cPanel account of autoliga.uz (account `autolig1`).

---

Здравствуйте!

Сайт autoliga.uz (аккаунт autolig1, Python-приложение через Passenger в cPanel).
Просим проверить и, если возможно, включить на уровне сервера:

1. Сжатие ответов: Brotli (если доступно) и gzip для text/html, text/css,
   application/javascript, application/json, image/svg+xml, а также для HTML-страниц,
   которые отдаёт Passenger-приложение.
2. Работу модулей mod_deflate, mod_expires и mod_headers для .htaccess
   (мы добавим заголовки Cache-Control в public_html/static/ и public_html/media/).
3. HTTP/2 (или HTTP/3) для домена autoliga.uz.
4. Один редирект без цепочки: http://autoliga.uz, http://www.autoliga.uz и
   https://www.autoliga.uz -> https://autoliga.uz (301, сразу на конечный адрес).
5. Права на запись для приложения в папку public_html/media/ (в том числе новые
   подпапки media/_resp/ и media/cache/) — там создаются уменьшенные копии изображений.
6. Чтобы приложение не останавливалось при простое: PassengerMinInstances 1 для
   autoliga.uz (или, если это невозможно, увеличить PassengerPoolIdleTime). Сейчас первый
   запрос после паузы попадает на холодный старт приложения и ждёт заметно дольше.

Конфигурацию nginx мы сами не меняем. Если что-то из этого включается только вами —
пожалуйста, включите или подскажите, как сделать это через cPanel.

Спасибо!

---

## English summary (for us)

1. Brotli/gzip at server level, including the HTML that Passenger returns.
2. mod_deflate / mod_expires / mod_headers allowed in .htaccess.
3. HTTP/2 (or HTTP/3).
4. One-hop 301 from http / www to https://autoliga.uz.
5. The app user can write to public_html/media/ (incl. media/_resp/ and media/cache/).
6. PassengerMinInstances 1 (or a longer PassengerPoolIdleTime), so the first request after
   idle time is not a cold start of the app.

## Check after they answer

```
curl -sI -H "Accept-Encoding: br, gzip" https://autoliga.uz/ | grep -iE "^HTTP|content-encoding"
curl -sI -H "Accept-Encoding: gzip" https://autoliga.uz/static/css/main_site.css | grep -iE "content-encoding|cache-control"
curl -sI https://autoliga.uz/static/fonts/Phosphor/Phosphor.woff2 | grep -i cache-control      # max-age=31536000
curl -s -o /dev/null -w "%{http_code} hops=%{num_redirects} %{url_effective}\n" -L http://www.autoliga.uz/   # 200 hops=1 https://autoliga.uz/
curl -s -o /dev/null -w "ttfb=%{time_starttransfer}\n" https://autoliga.uz/      # first request after a quiet period (e.g. early morning): about the same as a repeat request, no cold-start delay
```
