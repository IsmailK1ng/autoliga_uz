from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q


def setup_permissions():
    """Р В Р Р‹Р В РЎвЂўР В Р’В·Р В РўвЂР В Р’В°Р В Р вЂ¦Р В РЎвЂР В Р’Вµ Р В РЎвЂ“Р РЋР вЂљР РЋРЎвЂњР В РЎвЂ”Р В РЎвЂ” Р РЋР С“ Р В РЎвЂ”Р РЋР вЂљР В Р’В°Р В Р вЂ Р В Р’В°Р В РЎР В РЎвЂ Р В РўвЂР В РЎвЂўР РЋР С“Р РЋРІР‚С™Р РЋРЎвЂњР В РЎвЂ”Р В Р’В° Р В РўвЂР В Р’В»Р РЋР РЏ FAW"""
    
    # ============================================
    # 1. Р В РІР‚СљР В РІР‚С”Р В РЎвЂ™Р В РІР‚в„ўР В РЎСљР В Р’В«Р В РІР‚Сћ Р В РЎвЂ™Р В РІР‚СњР В РЎС™Р В Р В РЎСљР В Р’В« (Р В РЎвЂ”Р В РЎвЂўР РЋРІР‚РЋР РЋРІР‚С™Р В РЎвЂ Р В Р вЂ Р РЋР С“Р РЋРІР‚)
    # ============================================
    main_admins, created = Group.objects.get_or_create(name='Р В РІР‚СљР В Р’В»Р В Р’В°Р В Р вЂ Р В Р вЂ¦Р РЋРІР‚в„–Р В Р’Вµ Р В Р’В°Р В РўвЂР В РЎР В РЎвЂР В Р вЂ¦Р РЋРІР‚в„–')
    if created or not main_admins.permissions.exists():
        # Р В РІР‚в„ўР РЋР С“Р В Р’Вµ Р В РЎвЂ”Р РЋР вЂљР В Р’В°Р В Р вЂ Р В Р’В° Р В Р вЂ¦Р В Р’В° main Р В РЎвЂ kg
        all_permissions = Permission.objects.filter(
            content_type__app_label__in=['main']
        )
        main_admins.permissions.set(all_permissions)
        
        # Р В РЎСџР РЋР вЂљР В Р’В°Р В Р вЂ Р В Р’В° Р В Р вЂ¦Р В Р’В° Р В РЎвЂ”Р В РЎвЂўР В Р’В»Р РЋР Р‰Р В Р’В·Р В РЎвЂўР В Р вЂ Р В Р’В°Р РЋРІР‚С™Р В Р’ВµР В Р’В»Р В Р’ВµР В РІвЂћвЂ“ (Р В РЎвЂќР РЋР вЂљР В РЎвЂўР В РЎР В Р’Вµ Р РЋРЎвЂњР В РўвЂР В Р’В°Р В Р’В»Р В Р’ВµР В Р вЂ¦Р В РЎвЂР РЋР РЏ)
        user_permissions = Permission.objects.filter(
            Q(content_type__app_label='auth') &
            ~Q(codename='delete_user')
        )
        main_admins.permissions.add(*user_permissions)
    
    # ============================================
    # 2. Р В РЎв„ўР В РЎвЂєР В РЎСљР В РЎС›Р В РІР‚СћР В РЎСљР В РЎС›-Р В РЎвЂ™Р В РІР‚СњР В РЎС™Р В Р В РЎСљР В Р’В« (Р В РЎвЂ”Р В РЎвЂў Р РЋР С“Р РЋРІР‚С™Р РЋР вЂљР В Р’В°Р В Р вЂ¦Р В Р’В°Р В РЎ)
    # ============================================
    
    # 2a. Р В РЎв„ўР В РЎвЂєР В РЎСљР В РЎС›Р В РІР‚СћР В РЎСљР В РЎС› UZ
    content_uz, created = Group.objects.get_or_create(name='Р В РЎв„ўР В РЎвЂўР В Р вЂ¦Р РЋРІР‚С™Р В Р’ВµР В Р вЂ¦Р РЋРІР‚С™ UZ')
    if created or not content_uz.permissions.exists():
        content_models = [
            'news', 'newsblock', 'product', 'productparameter',
            'productfeature', 'productgallery', 'productcardspec',
            'vacancy', 'vacancyresponsibility', 'vacancyrequirement',
            'vacancycondition', 'vacancyidealcandidate',
            'dealer', 'dealerservice', 'featureicon',
            'becomeadealerpage', 'dealerrequirement'
        ]
        
        content_permissions = Permission.objects.filter(
            content_type__model__in=content_models,
            content_type__app_label='main'
        ).exclude(codename__startswith='delete_')
        
        content_uz.permissions.set(content_permissions)

    # ============================================
    # 3. Р В РІР‚С”Р В Р В РІР‚Сњ-Р В РЎС™Р В РІР‚СћР В РЎСљР В РІР‚СћР В РІР‚СњР В РІР‚вЂњР В РІР‚СћР В Р’В Р В Р’В« (Р В РЎвЂ”Р В РЎвЂў Р РЋР С“Р РЋРІР‚С™Р РЋР вЂљР В Р’В°Р В Р вЂ¦Р В Р’В°Р В РЎ)
    # ============================================
    
    # 3a. Р В РІР‚С”Р В Р В РІР‚СњР В Р’В« UZ
    lead_uz, created = Group.objects.get_or_create(name='Р В РІР‚С”Р В РЎвЂР В РўвЂР РЋРІР‚в„– UZ')
    if created or not lead_uz.permissions.exists():
        lead_permissions = Permission.objects.filter(
            content_type__model__in=[
                'contactform', 'jobapplication', 'becomeadealerapplication'
            ],
            content_type__app_label='main'
        ).exclude(codename__startswith='delete_')
        
        lead_uz.permissions.set(lead_permissions)
