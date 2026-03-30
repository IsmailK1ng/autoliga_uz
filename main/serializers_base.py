# main/serializers_base.py

from django.utils.translation import get_language


class LanguageSerializerMixin:
    """
    Serializer-larda tilni aniqlash uchun asosiy mixin.
    
    URL-ni tahlil qilish o'rniga Django translation tizimidan foydalanadi.
    ForceRussianMiddleware bilan mos keladi.
    """
    
    def get_current_language(self):
        """
        Django translation tizimidan joriy tilni qaytaradi.
        
        Returns:
            str: Til kodi ('uz', 'ru', 'en')
        
        Example:
            >>> self.get_current_language()
            'uz'
        """
        return get_language() or 'uz'