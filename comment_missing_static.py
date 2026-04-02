"""
Django static CSS fayllarida yo‘q fayllarni avtomatik comment qiladi.
"""

import os
import re

# CSS fayllaringiz joylashgan papka
CSS_DIR = "static/css"
# Static images papkasi
STATIC_DIR = "static/images"

# Barcha CSS fayllarni tekshirish
for root, dirs, files in os.walk(CSS_DIR):
    for file in files:
        if file.endswith(".css"):
            path = os.path.join(root, file)
            with open(path, "r+", encoding="utf-8") as f:
                content = f.read()
                # url(...) ichidagi fayllarni topadi
                urls = re.findall(r'url\(["\']?(.*?)["\']?\)', content)
                new_content = content
                for url in urls:
                    # /static/ prefiksini olib tashlash
                    rel_path = url.replace("/static/", "")
                    full_path = os.path.join("static", rel_path)
                    if not os.path.exists(full_path):
                        # Yo‘q faylni comment qilish
                        pattern = re.escape(f"url('{url}')")
                        new_content = re.sub(pattern, f"url('{url}') /* FILE NOT FOUND */", new_content)
                        print(f"Commented missing file in {file}: {url}")
                # CSS faylini yozib qo‘yish
                f.seek(0)
                f.write(new_content)
                f.truncate()