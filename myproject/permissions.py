from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q


def setup_permissions():
    """Создание групп с правами доступа для FAW"""
    
    # ============================================
    # 1. ГЛАВНЫЕ АДМИНЫ (почти всё)
    # ============================================
    main_admins, created = Group.objects.get_or_create(name='Главные админы')
    if created or not main_admins.permissions.exists():
        # Все права на main и kg
        all_permissions = Permission.objects.filter(
            content_type__app_label__in=['main']
        )
        main_admins.permissions.set(all_permissions)
        
        # Права на пользователей (кроме удаления)
        user_permissions = Permission.objects.filter(
            Q(content_type__app_label='auth') &
            ~Q(codename='delete_user')
        )
        main_admins.permissions.add(*user_permissions)
    
    # ============================================
    # 2. КОНТЕНТ-АДМИНЫ (по странам)
    # ============================================
    
    # 2a. КОНТЕНТ UZ
    content_uz, created = Group.objects.get_or_create(name='Контент UZ')
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
    # 3. ЛИД-МЕНЕДЖЕРЫ (по странам)
    # ============================================
    
    # 3a. ЛИДЫ UZ
    lead_uz, created = Group.objects.get_or_create(name='Лиды UZ')
    if created or not lead_uz.permissions.exists():
        lead_permissions = Permission.objects.filter(
            content_type__model__in=[
                'contactform', 'jobapplication', 'becomeadealerapplication'
            ],
            content_type__app_label='main'
        ).exclude(codename__startswith='delete_')
        
        lead_uz.permissions.set(lead_permissions)
