import os
import re


def sanitize_name(text: str) -> str | None:
    """Ism validatsiyasi: faqat harflar, 2-30 belgi."""
    if not isinstance(text, str):
        return None
    text = text.strip()
    if len(text) < 2 or len(text) > 30:
        return None
    if not re.fullmatch(r"[A-Za-zА-Яа-яЁёЎўҚқҒғҲҳ\s\-'`]{2,30}", text):
        return None
    return text


def get_image_path(relative_url: str, media_root: str) -> str | None:
    """Rasm URL ni to'liq fayl yo'liga aylantiradi."""
    if not relative_url or not media_root:
        return None
    path = relative_url
    if path.startswith("/media/"):
        path = path[7:]
    elif path.startswith("media/"):
        path = path[6:]
    safe_path = os.path.normpath(path).lstrip("/\\")
    full_path = os.path.join(media_root, safe_path)
    if not full_path.startswith(os.path.abspath(media_root)):
        return None
    return full_path if os.path.exists(full_path) else None


def format_phone(phone: str) -> str | None:
    """Telefon raqamini +998XXXXXXXXX formatiga tekshiradi."""
    if not phone:
        return None
    phone = phone.strip().replace(" ", "").replace("-", "")
    if re.fullmatch(r"\+998\d{9}", phone):
        return phone
    return None