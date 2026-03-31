# main/templatetags/seo_tags.py

from django import template
from django.urls import reverse, NoReverseMatch
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag(takes_context=True)
def hreflang_tags(context):
    """
    Р В Р’В Р Р†Р вЂљРЎС™Р В Р’В Р вЂ™Р’ВµР В Р’В Р В РІР‚В¦Р В Р’В Р вЂ™Р’ВµР В Р Р‹Р В РІР‚С™Р В Р’В Р РЋРІР‚Р В Р Р‹Р В РІР‚С™Р В Р Р‹Р РЋРІР‚СљР В Р’В Р вЂ™Р’ВµР В Р Р‹Р Р†Р вЂљРЎв„ў hreflang Р В Р Р‹Р Р†Р вЂљРЎв„ўР В Р’В Р вЂ™Р’ВµР В Р’В Р РЋРІР‚вЂњР В Р’В Р РЋРІР‚ Р В Р’В Р СћРІР‚Р В Р’В Р вЂ™Р’В»Р В Р Р‹Р В Р РЏ Р В Р Р‹Р Р†Р вЂљРЎв„ўР В Р’В Р вЂ™Р’ВµР В Р’В Р РЋРІР‚СњР В Р Р‹Р РЋРІР‚СљР В Р Р‹Р Р†Р вЂљР’В°Р В Р’В Р вЂ™Р’ВµР В Р’В Р Р†РІР‚С›РІР‚вЂњ Р В Р Р‹Р В РЎвЂњР В Р Р‹Р Р†Р вЂљРЎв„ўР В Р Р‹Р В РІР‚С™Р В Р’В Р вЂ™Р’В°Р В Р’В Р В РІР‚В¦Р В Р’В Р РЋРІР‚Р В Р Р‹Р Р†Р вЂљР’В Р В Р Р‹Р Р†Р вЂљРІвЂћвЂ“.
    
    Р В Р’В Р В Р Р‹Р В РЎвЂњР В Р’В Р РЋРІР‚вЂќР В Р’В Р РЋРІР‚СћР В Р’В Р вЂ™Р’В»Р В Р Р‹Р В Р вЂ°Р В Р’В Р вЂ™Р’В·Р В Р’В Р РЋРІР‚СћР В Р’В Р В РІР‚В Р В Р’В Р вЂ™Р’В°Р В Р’В Р В РІР‚В¦Р В Р’В Р РЋРІР‚Р В Р’В Р вЂ™Р’Вµ Р В Р’В Р В РІР‚В  Р В Р Р‹Р Р†РІР‚С™Р’В¬Р В Р’В Р вЂ™Р’В°Р В Р’В Р вЂ™Р’В±Р В Р’В Р вЂ™Р’В»Р В Р’В Р РЋРІР‚СћР В Р’В Р В РІР‚В¦Р В Р’В Р вЂ™Р’Вµ:
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
        # Р В Р’В Р В РІвЂљВ¬Р В Р’В Р вЂ™Р’В·Р В Р’В Р вЂ™Р’В±Р В Р’В Р вЂ™Р’ВµР В Р’В Р РЋРІР‚СњР В Р Р‹Р В РЎвЂњР В Р’В Р РЋРІР‚СњР В Р’В Р РЋРІР‚Р В Р’В Р Р†РІР‚С›РІР‚вЂњ (Р В Р’В Р СћРІР‚Р В Р’В Р вЂ™Р’ВµР В Р Р‹Р Р†Р вЂљРЎвЂєР В Р’В Р РЋРІР‚СћР В Р’В Р вЂ™Р’В»Р В Р Р‹Р Р†Р вЂљРЎв„ўР В Р’В Р В РІР‚В¦Р В Р Р‹Р Р†Р вЂљРІвЂћвЂ“Р В Р’В Р Р†РІР‚С›РІР‚вЂњ, Р В Р’В Р вЂ™Р’В±Р В Р’В Р вЂ™Р’ВµР В Р’В Р вЂ™Р’В· Р В Р’В Р РЋРІР‚вЂќР В Р Р‹Р В РІР‚С™Р В Р’В Р вЂ™Р’ВµР В Р Р‹Р Р†Р вЂљРЎвЂєР В Р’В Р РЋРІР‚Р В Р’В Р РЋРІР‚СњР В Р Р‹Р В РЎвЂњР В Р’В Р вЂ™Р’В°)
        uz_url = reverse(url_name, kwargs=url_kwargs)
        tags.append(f'<link rel="alternate" hreflang="uz" href="{domain}{uz_url}" />')
        tags.append(f'<link rel="alternate" hreflang="x-default" href="{domain}{uz_url}" />')
        
        # Р В Р’В Р вЂ™Р’В Р В Р Р‹Р РЋРІР‚СљР В Р Р‹Р В РЎвЂњР В Р Р‹Р В РЎвЂњР В Р’В Р РЋРІР‚СњР В Р’В Р РЋРІР‚Р В Р’В Р Р†РІР‚С›РІР‚вЂњ (Р В Р Р‹Р В РЎвЂњ Р В Р’В Р РЋРІР‚вЂќР В Р Р‹Р В РІР‚С™Р В Р’В Р вЂ™Р’ВµР В Р Р‹Р Р†Р вЂљРЎвЂєР В Р’В Р РЋРІР‚Р В Р’В Р РЋРІР‚СњР В Р Р‹Р В РЎвЂњР В Р’В Р РЋРІР‚СћР В Р’В Р РЋ /ru/)
        ru_url = f"/ru{reverse(url_name, kwargs=url_kwargs)}"
        tags.append(f'<link rel="alternate" hreflang="ru" href="{domain}{ru_url}" />')
        
        # Р В Р’В Р РЋРІР‚в„ўР В Р’В Р В РІР‚В¦Р В Р’В Р РЋРІР‚вЂњР В Р’В Р вЂ™Р’В»Р В Р’В Р РЋРІР‚Р В Р’В Р Р†РІР‚С›РІР‚вЂњР В Р Р‹Р В РЎвЂњР В Р’В Р РЋРІР‚СњР В Р’В Р РЋРІР‚Р В Р’В Р Р†РІР‚С›РІР‚вЂњ (Р В Р Р‹Р В РЎвЂњ Р В Р’В Р РЋРІР‚вЂќР В Р Р‹Р В РІР‚С™Р В Р’В Р вЂ™Р’ВµР В Р Р‹Р Р†Р вЂљРЎвЂєР В Р’В Р РЋРІР‚Р В Р’В Р РЋРІР‚СњР В Р Р‹Р В РЎвЂњР В Р’В Р РЋРІР‚СћР В Р’В Р РЋ /en/)
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
    
    # Р В Р’В Р РЋРЎСџР В Р’В Р РЋРІР‚СћР В Р’В Р вЂ™Р’В»Р В Р Р‹Р РЋРІР‚СљР В Р Р‹Р Р†Р вЂљР Р‹Р В Р’В Р вЂ™Р’В°Р В Р’В Р вЂ™Р’ВµР В Р’В Р РЋ Р В Р Р‹Р Р†Р вЂљР Р‹Р В Р’В Р РЋРІР‚Р В Р Р‹Р В РЎвЂњР В Р Р‹Р Р†Р вЂљРЎв„ўР В Р Р‹Р Р†Р вЂљРІвЂћвЂ“Р В Р’В Р Р†РІР‚С›РІР‚вЂњ URL Р В Р’В Р вЂ™Р’В±Р В Р’В Р вЂ™Р’ВµР В Р’В Р вЂ™Р’В· Р В Р’В Р РЋРІР‚вЂќР В Р’В Р вЂ™Р’В°Р В Р Р‹Р В РІР‚С™Р В Р’В Р вЂ™Р’В°Р В Р’В Р РЋР В Р’В Р вЂ™Р’ВµР В Р Р‹Р Р†Р вЂљРЎв„ўР В Р Р‹Р В РІР‚С™Р В Р’В Р РЋРІР‚СћР В Р’В Р В РІР‚В 
    scheme = request.scheme  
    host = request.get_host()  
    path = request.path  
    
    canonical = f"{scheme}://{host}{path}"
    
    return mark_safe(f'<link rel="canonical" href="{canonical}" />')