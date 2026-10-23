# main/templatetags/image_tags.py
"""{% responsive_img %}: <picture> with the WebP copies (main/images.py) and the
original as the <img> fallback, always with width/height when known (CLS).

    {% load image_tags %}
    {% responsive_img product.main_image alt=product.image_alt sizes="(max-width: 768px) 92vw, 420px" class="truck-image" %}
    {% responsive_img news.preview_image alt=... loading="eager" fetchpriority="high" %}

<picture> gets display:contents, so it adds no box: the <img> keeps the same
place in the layout and the same CSS selectors (descendant ones) as before.
"""

from django import template
from django.utils import translation
from django.utils.html import format_html, format_html_join

from main.images import image_info

register = template.Library()


@register.simple_tag
def responsive_img(file, alt='', sizes='100vw', loading='lazy', fetchpriority='', decoding='async', **attrs):
    info = image_info(file)
    if not info:
        return ''
    img_attrs = [('src', info['url']), ('alt', alt or '')]
    if info['width'] and info['height']:
        img_attrs += [('width', info['width']), ('height', info['height'])]
    if loading and loading != 'eager':
        img_attrs.append(('loading', loading))
    if fetchpriority:
        img_attrs.append(('fetchpriority', fetchpriority))
    if decoding:
        img_attrs.append(('decoding', decoding))
    for key, value in attrs.items():
        if value not in (None, ''):
            img_attrs.append(('class' if key in ('class', 'class_') else key.replace('_', '-'), value))
    # data-resp: lets the zero-specificity height:auto rule in site_menu.css keep the aspect ratio
    img = format_html('<img{} data-resp>', format_html_join('', ' {}="{}"', img_attrs))
    if not info['srcset']:
        return img
    return format_html('<picture style="display:contents"><source type="image/webp" srcset="{}" sizes="{}">{}</picture>',
                       info['srcset'], sizes, img)


@register.simple_tag
def webp_url(file):
    """The ~960px WebP copy (or the original) — for JS-built images such as the home slider."""
    info = image_info(file)
    return info['medium'] if info else ''


@register.simple_tag
def img_size_attrs(file):
    """' width="W" height="H" data-resp' for a hand-written <img> (e.g. one whose src JS swaps)."""
    info = image_info(file)
    if not info or not info['width'] or not info['height']:
        return ''
    return format_html(' width="{}" height="{}" data-resp', info['width'], info['height'])


@register.simple_tag
def webp_srcset(file):
    """srcset of the WebP copies ("" when there are none)."""
    info = image_info(file)
    return info['srcset'] if info else ''


@register.filter
def has_webp(file):
    info = image_info(file)
    return bool(info and info['srcset'])



GALLERY_WORD = {'uz': 'rasm', 'ru': 'изображение', 'en': 'image'}


@register.simple_tag
def gallery_alt(gallery_image, product, number):
    """Admin alt_text, else "{Brand} {Model}, rasm/изображение/image N" (task 12)."""
    text = ' '.join((gallery_image.alt_text or '').split())
    if text:
        return text
    word = GALLERY_WORD.get(translation.get_language(), GALLERY_WORD['uz'])
    return f'{product.display_name}, {word} {number}'
