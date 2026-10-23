# main/images.py
"""
Responsive WebP copies of uploaded images (SEO TZ task 11).

For an uploaded image   media/products/main/t1.png
the copies are          media/_resp/products/main/t1-<hash>-480.webp  (and -960, -1600)
plus a small sidecar    media/_resp/products/main/t1.json  {"width", "height", "hash", "variants": {...}}

* WebP, quality 80, widths 480 / 960 / 1600 (never larger than the original;
  a smaller original gets one copy at its own width). Transparency is kept.
* Originals are never changed or deleted. Without copies the page simply
  shows the original (the <img> src is always the original).
* <hash> comes from the original's name and size, so a replaced picture gets
  new file names: copies can be cached for a year without going stale.
* New uploads get copies on save (main/signals.py); existing files with
  `manage.py make_responsive_images [--dry-run] [--limit N] [--force]`.
"""

import hashlib
import io
import json
import logging
import os
import posixpath
import threading

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

logger = logging.getLogger('django')

WIDTHS = (480, 960, 1600)
QUALITY = 80
PREFIX = '_resp'
# Fields that get copies: (app_label.Model, field names)
IMAGE_FIELDS = {
    'main.Product': ('main_image', 'card_image', 'slider_image'),
    'main.ProductGallery': ('image',),
    'main.News': ('preview_image',),
    'main.NewsBlock': ('image',),
}
RASTER_EXT = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp', '.tif', '.tiff'}

_meta_cache = {}
_lock = threading.Lock()


def _base(name):
    stem, _ext = posixpath.splitext(name)
    return posixpath.join(PREFIX, stem)


def sidecar_name(name):
    return _base(name) + '.json'


def source_hash(name, size):
    return hashlib.sha1(f'{name}:{size}'.encode()).hexdigest()[:8]


def is_supported(name):
    return bool(name) and posixpath.splitext(name)[1].lower() in RASTER_EXT and not name.startswith(PREFIX + '/')


def load_meta(name):
    """Sidecar data for an original (cached per process, re-read when the sidecar changes), or None."""
    if not is_supported(name):
        return None
    path = sidecar_name(name)
    try:
        mtime = os.path.getmtime(default_storage.path(path))
    except (OSError, NotImplementedError, ValueError):
        return None
    cached = _meta_cache.get(name)
    if cached and cached[0] == mtime:
        return cached[1]
    try:
        with default_storage.open(path) as fh:
            meta = json.loads(fh.read().decode('utf-8'))
    except (OSError, ValueError):
        return None
    with _lock:
        _meta_cache[name] = (mtime, meta)
    return meta


def is_current(name):
    """True when copies exist for this exact original (same name and size)."""
    meta = load_meta(name)
    if not meta:
        return False
    try:
        size = default_storage.size(name)
    except OSError:
        return False
    return meta.get('hash') == source_hash(name, size) and all(default_storage.exists(v) for v in meta.get('variants', {}).values())


def generate(name, force=False, dry_run=False):
    """Create the WebP copies for one original. Returns 'created', 'skipped', 'missing' or 'error: ...'."""
    from PIL import Image, ImageOps

    if not is_supported(name):
        return 'skipped'
    if not default_storage.exists(name):
        return 'missing'
    if not force and is_current(name):
        return 'skipped'
    if dry_run:
        return 'created'
    try:
        size = default_storage.size(name)
        digest = source_hash(name, size)
        # Memory: one image at a time, decoded straight from the file (no extra copy of
        # the file in memory); big JPEG photos are decoded at a reduced scale that is
        # still >= 1600px (a 6000x4000 photo needs ~1/4 of the memory).
        with default_storage.open(name, 'rb') as fh:
            image = Image.open(fh)
            width, height = image.size
            if image.getexif().get(0x0112, 1) in (5, 6, 7, 8):  # EXIF-rotated: shown size is swapped
                width, height = height, width
            if image.format == 'JPEG' and max(width, height) > WIDTHS[-1]:
                image.draft('RGB', (WIDTHS[-1], WIDTHS[-1]))
            image.load()
        image = ImageOps.exif_transpose(image)
        if image.mode not in ('RGB', 'RGBA'):
            image = image.convert('RGBA' if 'A' in image.getbands() or image.mode == 'P' else 'RGB')
        # every target width below the original, plus the original width (at most 1600): never upscaled
        widths = sorted({w for w in WIDTHS if w < width} | {min(width, WIDTHS[-1])})
        old = load_meta(name) or {}
        variants = {}
        for w in widths:
            h = max(1, round(height * w / width))
            copy = image if image.size == (w, h) else image.resize((w, h), Image.LANCZOS)
            buffer = io.BytesIO()
            copy.save(buffer, 'WEBP', quality=QUALITY, method=6)
            del copy
            target = f'{_base(name)}-{digest}-{w}.webp'
            if default_storage.exists(target):
                default_storage.delete(target)
            default_storage.save(target, ContentFile(buffer.getvalue()))
            variants[str(w)] = target
        image.close()
        meta = {'width': width, 'height': height, 'hash': digest, 'variants': variants, 'source': name}
        side = sidecar_name(name)
        if default_storage.exists(side):
            default_storage.delete(side)
        default_storage.save(side, ContentFile(json.dumps(meta).encode('utf-8')))
        # copies of an earlier version of this original (same name, different file)
        for target in (old.get('variants') or {}).values():
            if target not in variants.values() and default_storage.exists(target):
                default_storage.delete(target)
        with _lock:
            _meta_cache.pop(name, None)
        return 'created'
    except Exception as exc:  # never break an admin save because of a picture
        logger.warning('responsive image failed for %s: %s', name, exc)
        return f'error: {exc}'


def generate_for_instance(instance):
    """Signal helper: copies for every image field of a saved object (missing or outdated only)."""
    key = f'{instance._meta.app_label}.{instance.__class__.__name__}'
    for field in IMAGE_FIELDS.get(key, ()):
        file = getattr(instance, field, None)
        if file and file.name:
            generate(file.name)


_size_cache = {}


def original_size(file):
    """(width, height) of an original without copies yet (read once per process), or (None, None)."""
    if file.name in _size_cache:
        return _size_cache[file.name]
    try:
        from django.core.files.images import get_image_dimensions
        with default_storage.open(file.name, 'rb') as fh:
            size = get_image_dimensions(fh) or (None, None)
    except Exception:
        size = (None, None)
    with _lock:
        _size_cache[file.name] = size
    return size


def image_info(file):
    """For templates: dict(url, width, height, srcset) of an ImageField file, or None."""
    if not file or not getattr(file, 'name', None):
        return None
    try:
        url = file.url
    except ValueError:
        return None
    meta = load_meta(file.name)
    if not meta:
        width, height = original_size(file)
        return {'url': url, 'width': width, 'height': height, 'srcset': '', 'medium': url}
    srcset = ', '.join(f"{default_storage.url(path)} {w}w" for w, path in sorted(meta['variants'].items(), key=lambda kv: int(kv[0])))
    return {'url': url, 'width': meta['width'], 'height': meta['height'], 'srcset': srcset,
            'medium': default_storage.url(meta['variants'].get('960') or sorted(meta['variants'].items(), key=lambda kv: int(kv[0]))[-1][1])}
