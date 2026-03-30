# main/templatetags/seo_tags.py

from django import template
from django.urls import reverse, NoReverseMatch
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag(takes_context=True)
def hreflang_tags(context):
    """
    Р В РІР‚СљР В Р’ВµР В Р вЂ¦Р В Р’ВµР РЋР вЂљР В РЎвЂР РЋР вЂљР РЋРЎвЂњР В Р’ВµР РЋРІР‚С™ hreflang Р РЋРІР‚С™Р В Р’ВµР В РЎвЂ“Р В РЎвЂ Р В РўвЂР В Р’В»Р РЋР РЏ Р РЋРІР‚С™Р В Р’ВµР В РЎвЂќР РЋРЎвЂњР РЋРІР‚В°Р В Р’ВµР В РІвЂћвЂ“ Р РЋР С“Р РЋРІР‚С™Р РЋР вЂљР В Р’В°Р В Р вЂ¦Р В РЎвЂР РЋРІР‚В Р РЋРІР‚в„–.
    
    Р В Р РЋР С“Р В РЎвЂ”Р В РЎвЂўР В Р’В»Р РЋР Р‰Р В Р’В·Р В РЎвЂўР В Р вЂ Р В Р’В°Р В Р вЂ¦Р В РЎвЂР В Р’Вµ Р В Р вЂ  Р РЋРІвЂљВ¬Р В Р’В°Р В Р’В±Р В Р’В»Р В РЎвЂўР В Р вЂ¦Р В Р’Вµ:
    {% load seo_tags %}
    {% hreflang_tags %}
    """
    request = context.get('request')
    if not request:
        return ''
    
    url_name = request.resolver_match.url_name if request.resolver_match else None
    if not url_name:
        return ''
    
    domain = request.build_absolute_uri('/').rstrip('/')
    url_kwargs = request.resolver_match.kwargs if request.resolver_match else {}
    
    tags = []
    
    try:
        # Р В Р в‚¬Р В Р’В·Р В Р’В±Р В Р’ВµР В РЎвЂќР РЋР С“Р В РЎвЂќР В РЎвЂР В РІвЂћвЂ“ (Р В РўвЂР В Р’ВµР РЋРІР‚С›Р В РЎвЂўР В Р’В»Р РЋРІР‚С™Р В Р вЂ¦Р РЋРІР‚в„–Р В РІвЂћвЂ“, Р В Р’В±Р В Р’ВµР В Р’В· Р В РЎвЂ”Р РЋР вЂљР В Р’ВµР РЋРІР‚С›Р В РЎвЂР В РЎвЂќР РЋР С“Р В Р’В°)
        uz_url = reverse(url_name, kwargs=url_kwargs)
        tags.append(f'<link rel="alternate" hreflang="uz" href="{domain}{uz_url}" />')
        tags.append(f'<link rel="alternate" hreflang="x-default" href="{domain}{uz_url}" />')
        
        # Р В Р’В Р РЋРЎвЂњР РЋР С“Р РЋР С“Р В РЎвЂќР В РЎвЂР В РІвЂћвЂ“ (Р РЋР С“ Р В РЎвЂ”Р РЋР вЂљР В Р’ВµР РЋРІР‚С›Р В РЎвЂР В РЎвЂќР РЋР С“Р В РЎвЂўР В РЎ /ru/)
        ru_url = f"/ru{reverse(url_name, kwargs=url_kwargs)}"
        tags.append(f'<link rel="alternate" hreflang="ru" href="{domain}{ru_url}" />')
        
        # Р В РЎвЂ™Р В Р вЂ¦Р В РЎвЂ“Р В Р’В»Р В РЎвЂР В РІвЂћвЂ“Р РЋР С“Р В РЎвЂќР В РЎвЂР В РІвЂћвЂ“ (Р РЋР С“ Р В РЎвЂ”Р РЋР вЂљР В Р’ВµР РЋРІР‚С›Р В РЎвЂР В РЎвЂќР РЋР С“Р В РЎвЂўР В РЎ /en/)
        en_url = f"/en{reverse(url_name, kwargs=url_kwargs)}"
        tags.append(f'<link rel="alternate" hreflang="en" href="{domain}{en_url}" />')
        
    except NoReverseMatch:
        return ''
    
    return mark_safe('\n    '.join(tags))


@register.simple_tag(takes_context=True)
def canonical_url(context):

    request = context.get('request')
    if not request:
        return ''
    
    # Р В РЎСџР В РЎвЂўР В Р’В»Р РЋРЎвЂњР РЋРІР‚РЋР В Р’В°Р В Р’ВµР В РЎ Р РЋРІР‚РЋР В РЎвЂР РЋР С“Р РЋРІР‚С™Р РЋРІР‚в„–Р В РІвЂћвЂ“ URL Р В Р’В±Р В Р’ВµР В Р’В· Р В РЎвЂ”Р В Р’В°Р РЋР вЂљР В Р’В°Р В РЎР В Р’ВµР РЋРІР‚С™Р РЋР вЂљР В РЎвЂўР В Р вЂ 
    scheme = request.scheme  
    host = request.get_host()  
    path = request.path  
    
    canonical = f"{scheme}://{host}{path}"
    
    return mark_safe(f'<link rel="canonical" href="{canonical}" />')