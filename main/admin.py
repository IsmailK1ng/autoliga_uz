# main/admin.py

from django.conf import settings
from django.contrib import admin, messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q, Max
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, HttpResponseForbidden
from django.shortcuts import render, redirect
from django.urls import path
from django.utils import timezone
from django.utils.html import format_html
from django import forms

# ========== DJANGO THIRD-PARTY ==========
from modeltranslation.admin import TranslationTabularInline, TranslationStackedInline, TabbedTranslationAdmin, TranslationAdmin
from reversion.admin import VersionAdmin
from reversion.models import Version
from openpyxl.styles import Font, PatternFill, Alignment

# ========== PYTHON STANDARD LIBRARY ==========
import json
import logging
import openpyxl
import os
from datetime import datetime, timedelta
from urllib.parse import unquote

# ========== ЛОКАЛЬНЫЕ ИМПОРТЫ ==========
from .models import *
from main.services.amocrm.token_manager import TokenManager
logger = logging.getLogger('django')

# ========== НАСТРОЙКИ АДМИНКИ ==========
admin.site.site_header = "Панель управления Autoliga"
admin.site.site_title = "Autoliga Admin"
admin.site.index_title = "Управление сайтами Autoliga"

# ============ БАЗОВЫЕ МИКСИНЫ ============

class ContentAdminMixin:
    """Миксин для контент-админов"""
    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        

        if request.user.groups.filter(
            name__in=['Главные админы', 'Контент-админы', 'Контент UZ']
        ).exists():
            return True
        

        content_models = [
            'product', 'vacancy',
            'featureicon',
        ]
        for model in content_models:
            if request.user.has_perm(f'main.view_{model}'):
                return True
        
        return False
    
    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        
        if request.user.groups.filter(
            name__in=['Главные админы', 'Контент-админы', 'Контент UZ']
        ).exists():
            return True
        

        model_name = self.model._meta.model_name
        return request.user.has_perm(f'main.change_{model_name}')
    
    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        
        if request.user.groups.filter(name='Главные админы').exists():
            return True

        model_name = self.model._meta.model_name
        return request.user.has_perm(f'main.delete_{model_name}')

class LeadManagerMixin:
    """Миксин для лид-менеджеров"""
    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        

        if request.user.groups.filter(
            name__in=['Главные админы', 'Лид-менеджеры', 'Лиды UZ']
        ).exists():
            return True
        

        lead_models = ['contactform', 'jobapplication', 'becomeadealerapplication']
        for model in lead_models:
            if request.user.has_perm(f'main.view_{model}'):
                return True
        
        return False
    
    def has_add_permission(self, request):
        return False 
    
    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        
        if request.user.groups.filter(name='Главные админы').exists():
            return True
        

        model_name = self.model._meta.model_name
        return request.user.has_perm(f'main.delete_{model_name}')
        
class AmoCRMAdminMixin:
    """Миксин для управления amoCRM"""
    def has_module_permission(self, request):
        if request.user.is_superuser:
            return True
        
        if request.user.groups.filter(name='Главные админы').exists():
            return True
        
        return False
    
    def has_view_permission(self, request, obj=None):
        return self.has_module_permission(request)
    
    def has_change_permission(self, request, obj=None):
        return self.has_module_permission(request)
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False

class CustomReversionMixin:
    """Миксин для кастомного шаблона восстановления"""
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'recover/',
                self.admin_site.admin_view(self.custom_recover_list_view),
                name=f'{self.model._meta.app_label}_{self.model._meta.model_name}_recoverlist'
            ),
            path(
                'recover/<int:version_id>/', 
                self.admin_site.admin_view(self.recover_view),  
                name=f'{self.model._meta.app_label}_{self.model._meta.model_name}_recover'
            ),
        ]
        return custom_urls + urls
    
    def custom_recover_list_view(self, request):
        
        opts = self.model._meta
        deleted_versions = Version.objects.get_deleted(self.model)
        
        seen_objects = {}
        version_list_with_preview = []
        
        for version in deleted_versions.order_by('-revision__date_created'):
            obj_repr = version.object_repr
            if obj_repr not in seen_objects:
                seen_objects[obj_repr] = True
                
                preview_url = None
                try:
                    field_dict = version.field_dict
                    for field_name in ['preview_image', 'main_image', 'card_image', 'logo']:
                        if field_name in field_dict and field_dict[field_name]:
                            preview_url = f"{settings.MEDIA_URL}{field_dict[field_name]}"
                            break
                except Exception:
                    pass
                
                version_list_with_preview.append({
                    'version': version,
                    'preview_url': preview_url,
                    'object_repr': obj_repr,
                    'date': version.revision.date_created
                })
        
        context = {
            **self.admin_site.each_context(request),
            'opts': opts,
            'version_list': version_list_with_preview,
            'title': f'Восстановление: {opts.verbose_name_plural}',
            'has_view_permission': self.has_view_permission(request),
        }
        
        return render(request, 'admin/reversion/recover_list.html', context)
    
    def recover_view(self, request, version_id):
        
        opts = self.model._meta
        
        try:
            version = Version.objects.get(pk=version_id)
            
            if version.content_type.model_class() != self.model:
                raise Version.DoesNotExist
            
            version.revision.revert()
            
            messages.success(request, f'✅ Объект "{version.object_repr}" успешно восстановлен!')
            return redirect(f'admin:{opts.app_label}_{opts.model_name}_changelist')
            
        except Version.DoesNotExist:
            messages.error(request, '❌ Версия не найдена или уже восстановлена')
            return redirect(f'admin:{opts.app_label}_{opts.model_name}_recoverlist')
        except Exception as e:
            messages.error(request, f'❌ Ошибка восстановления: {str(e)}')
            return redirect(f'admin:{opts.app_label}_{opts.model_name}_recoverlist')

# ============ НОВОСТИ ============

class NewsBlockInline(TranslationStackedInline): 
    model = NewsBlock
    extra = 1
    fields = ('block_type', 'title', 'text', 'image', 'youtube_url', 'video_file', 'order')

    class Media:
        js = ('js/admin/news_block_dynamic.js',) 
        css = {
            'all': ('css/news_block_custom.css',)  
            
        }

@admin.register(News)
class NewsAdmin(ContentAdminMixin, CustomReversionMixin, VersionAdmin, TabbedTranslationAdmin):
    list_display = ['preview_image_tag', 'title', 'author', 'is_active', 'order', 'created_at', 'action_buttons']
    list_editable = ['is_active', 'order']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'desc']
    readonly_fields = ['preview_image_tag', 'author_photo_tag', 'slug', 'updated_at']
    prepopulated_fields = {}
    inlines = [NewsBlockInline]
    history_latest_first = True
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'slug', 'created_at', 'is_active', 'order'),
        }),
        ('Карточка новости', {
            'fields': ('desc', 'preview_image', 'preview_image_tag'),
        }),
        ('Автор', {
            'fields': ('author', 'author_photo', 'author_photo_tag')
        }),
        ('Техническая информация', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        }),
    )

    def preview_image_tag(self, obj):
        if obj.preview_image:
            return format_html('<img src="{}" width="100" style="border-radius:8px;"/>', obj.preview_image.url)
        return "—"
    preview_image_tag.short_description = "Превью"

    def author_photo_tag(self, obj):
        if obj.author_photo:
            return format_html('<img src="{}" width="50" style="border-radius:50%;">', obj.author_photo.url)
        return "—"
    author_photo_tag.short_description = "Фото автора"
    
    def action_buttons(self, obj):
        return format_html('''
            <div style="display: flex; gap: 8px;">
                <a href="{}" title="Редактировать">
                    <img src="/static/media/icon-adminpanel/pencil.png" width="24" height="24">
                </a>
                <a href="/news/{}/" title="Просмотр" target="_blank">
                    <img src="/static/media/icon-adminpanel/eyes.png" width="24" height="24">
                </a>
                <a href="{}" title="Удалить" onclick="return confirm('Удалить?')">
                    <img src="/static/media/icon-adminpanel/recycle-bin.png" width="24" height="24">
                </a>
            </div>
        ''', f'/admin/main/news/{obj.id}/change/', obj.slug, f'/admin/main/news/{obj.id}/delete/')
    action_buttons.short_description = "Действия"
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        deleted_count = Version.objects.get_deleted(self.model).count()
        if deleted_count > 0:
            extra_context['show_recover_button'] = True
            extra_context['deleted_count'] = deleted_count
        return super().changelist_view(request, extra_context)
    
# ============ ЗАЯВКИ ============

@admin.register(ContactForm)
class ContactFormAdmin(LeadManagerMixin, admin.ModelAdmin):
    change_list_template = 'main/contactform/change_list.html'
    preserve_filters = True
    

    list_select_related = ['manager']
    list_per_page = 50
    show_full_result_count = False
    
    list_display = [
        'name', 'phone', 'product_display', 'region', 
        'priority', 'status', 'amocrm_badge', 
        'manager', 'created_at', 'action_buttons'
    ]
    list_editable = ['priority', 'status', 'manager']  
    list_filter = ['status', 'priority', 'region']
    search_fields = ['name', 'phone', 'amocrm_lead_id']
    readonly_fields = ['created_at', 'amocrm_sent_at', 'amocrm_lead_link']
    autocomplete_fields = ['manager']
    actions = ['retry_failed_leads', 'export_to_excel']

    fieldsets = (
        ('Информация о клиенте', {
            'fields': ('name', 'phone', 'region', 'message', 'created_at')
        }),
        ('Управление', {
            'fields': ('status', 'priority', 'manager', 'admin_comment')
        }),
        ('amoCRM', {
            'fields': ('amocrm_status', 'amocrm_lead_link', 'amocrm_sent_at', 'amocrm_error'),
            'classes': ('collapse',)
        }),
    )
    
    class Media:
        css = {'all': ('css/amocrm_modal.css', 'css/contactform_admin.css')}
        js = ('js/amocrm_modal.js', 'js/contactform_admin.js')
    
    # ==================== ОТОБРАЖЕНИЕ ====================
    
    def product_display(self, obj):
        if not obj.product:
            return "—"
        return format_html(
            '<span style="color:#1976d2;font-weight:600;">{}</span>',
            obj.product[:30]
        )
        return format_html('<span style="color:#999;">—</span>')
    
    product_display.short_description = "Модель"
    product_display.admin_order_field = 'product'
    
    def amocrm_badge(self, obj):
        """Бейдж статуса amoCRM"""
        if obj.amocrm_status == 'sent':
            return format_html(
                '<span style="background:#10b981;color:white;padding:5px 12px;border-radius:6px;font-weight:600;font-size:12px;">Отправлено</span>'
            )
        elif obj.amocrm_status == 'failed':
            error_text = (obj.amocrm_error or 'Неизвестная ошибка').replace('"', '&quot;').replace("'", '&#39;')
            return format_html(
                '<span class="amocrm-error-badge" data-error="{}" style="background:#ef4444;color:white;padding:5px 12px;border-radius:6px;font-weight:600;font-size:12px;cursor:pointer;" title="Нажмите для просмотра ошибки">Ошибка</span>',
                error_text
            )
        return format_html(
            '<span style="background:#f59e0b;color:white;padding:5px 12px;border-radius:6px;font-weight:600;font-size:12px;">Ожидает</span>'
        )

    amocrm_badge.short_description = "amoCRM"
    amocrm_badge.admin_order_field = 'amocrm_status'
    
    def action_buttons(self, obj):
        """Кнопки действий"""
        view_url = f"https://fawtrucks.amocrm.ru/leads/detail/{obj.amocrm_lead_id}" if obj.amocrm_lead_id else f"/admin/main/contactform/{obj.id}/change/"
        view_title = "Открыть в amoCRM" if obj.amocrm_lead_id else "Просмотр заявки"
        
        return format_html('''
            <div style="display:flex;gap:8px;">
                <a href="{}" title="Редактировать" style="padding:6px;border-radius:6px;display:inline-block;transition:transform 0.2s;" onmouseover="this.style.transform='translateY(-2px)'" onmouseout="this.style.transform='translateY(0)'">
                    <img src="/static/media/icon-adminpanel/pencil.png" width="20" height="20">
                </a>
                <a href="{}" title="{}" target="_blank" style="padding:6px;border-radius:6px;display:inline-block;transition:transform 0.2s;" onmouseover="this.style.transform='translateY(-2px)'" onmouseout="this.style.transform='translateY(0)'">
                    <img src="/static/media/icon-adminpanel/eyes.png" width="20" height="20">
                </a>
                <a href="{}" title="Удалить" onclick="return confirm('Удалить заявку?')" style="padding:6px;border-radius:6px;display:inline-block;transition:transform 0.2s;" onmouseover="this.style.transform='translateY(-2px)'" onmouseout="this.style.transform='translateY(0)'">
                    <img src="/static/media/icon-adminpanel/recycle-bin.png" width="20" height="20">
                </a>
            </div>
        ''', f'/admin/main/contactform/{obj.id}/change/', view_url, view_title, f'/admin/main/contactform/{obj.id}/delete/')
    
    action_buttons.short_description = "Действия"
    
    def amocrm_lead_link(self, obj):
        """Ссылка на лид в amoCRM"""
        if obj.amocrm_lead_id:
            # url = f"https://fawtrucks.amocrm.ru/leads/detail/{obj.amocrm_lead_id}"
            return format_html(
                '<a href="{}" target="_blank" style="color:#3b82f6;font-weight:600;">Открыть в amoCRM (ID: {})</a>',
                url, obj.amocrm_lead_id
            )
        return "—"
    
    amocrm_lead_link.short_description = "Ссылка на лид"
    
    # ==================== ДЕЙСТВИЯ ====================
    
    def retry_failed_leads(self, request, queryset):
        """Повторная отправка ошибочных заявок"""
        logger = logging.getLogger('django')
        
        failed_leads = queryset.filter(amocrm_status='failed')
        
        if not failed_leads.exists():
            self.message_user(request, 'Нет ошибочных заявок для повторной отправки', level=messages.WARNING)
            return
        
        success_count = 0
        fail_count = 0
        
        for lead in failed_leads:
            try:
                lead.amocrm_status = 'pending'
                lead.amocrm_error = None
                lead.save()
                
                LeadSender.send_lead(lead)
                lead.refresh_from_db()
                
                if lead.amocrm_status == 'sent':
                    success_count += 1
                else:
                    fail_count += 1
            except Exception as e:
                logger.error(f"Error retrying lead {lead.id}: {str(e)}", exc_info=True)
                fail_count += 1
        
        if success_count > 0:
            self.message_user(request, f'Успешно отправлено: {success_count}', level=messages.SUCCESS)
        if fail_count > 0:
            self.message_user(request, f'Ошибка отправки: {fail_count}', level=messages.ERROR)
    
    retry_failed_leads.short_description = 'Повторно отправить ошибочные заявки'
    
    def export_to_excel(self, request, queryset):
        """Экспорт в Excel"""
        logger = logging.getLogger('django')
        
        try:
            if request.POST.get('select_across') == '1':
                queryset = self.get_queryset(request)
            
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Заявки AutoLiga"
            
            headers = [
                'Номер', 'ФИО', 'Телефон', 'Модель', 'Регион', 'Сообщение', 
                'Статус', 'Приоритет', 'Менеджер', 'Дата',
                'amoCRM Статус', 'amoCRM ID', 'amoCRM Дата', 'amoCRM Ошибка'
            ]
            ws.append(headers)
            
            header_fill = PatternFill(start_color='366092', end_color='366092', fill_type='solid')
            header_font = Font(bold=True, color='FFFFFF')
            
            for cell in ws[1]:
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = Alignment(horizontal='center', vertical='center')
            
            for idx, contact in enumerate(queryset, start=1):
                ws.append([
                    idx,
                    contact.name,
                    contact.phone,
                    contact.product[:30] if contact.product else '-',
                    contact.get_region_display(),
                    contact.message[:100] if contact.message else '-',
                    contact.get_status_display(),
                    contact.get_priority_display(),
                    contact.manager.username if contact.manager else '-',
                    contact.created_at.strftime('%d.%m.%Y %H:%M'),
                    contact.get_amocrm_status_display(),
                    contact.amocrm_lead_id or '-',
                    contact.amocrm_sent_at.strftime('%d.%m.%Y %H:%M') if contact.amocrm_sent_at else '-',
                    contact.amocrm_error[:100] if contact.amocrm_error else '-'
                ])
            
            for column in ws.columns:
                max_length = max(len(str(cell.value)) for cell in column)
                ws.column_dimensions[column[0].column_letter].width = min(max_length + 2, 50)
            
            response = HttpResponse(
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            # response['Content-Disposition'] = f'attachment; filename="faw_uz_contacts_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
            wb.save(response)
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Error exporting to Excel: {str(e)}", exc_info=True)
            self.message_user(request, f'Ошибка экспорта: {str(e)}', level=messages.ERROR)
            return redirect(request.path)
    
    export_to_excel.short_description = 'Экспорт в Excel'
    
    # ==================== QUERYSET ====================
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Отключаем управление менеджерами"""
        formfield = super().formfield_for_foreignkey(db_field, request, **kwargs)
        if db_field.name == "manager":
            formfield.widget.can_add_related = False
            formfield.widget.can_change_related = False
            formfield.widget.can_delete_related = False
            formfield.widget.can_view_related = False
        return formfield
    
    def get_queryset(self, request):
        """Фильтрация queryset"""
        qs = super().get_queryset(request)
        
        # Поиск
        if search_query := request.GET.get('q', '').strip():
            qs = qs.filter(
                Q(name__icontains=search_query) | 
                Q(phone__icontains=search_query) | 
                Q(amocrm_lead_id__icontains=search_query)
            )

        if status := request.GET.get('status', '').strip():
            qs = qs.filter(status=status)
        
        if amocrm_status := request.GET.get('amocrm_status', '').strip():
            qs = qs.filter(amocrm_status=amocrm_status)
        
        if priority := request.GET.get('priority', '').strip():
            qs = qs.filter(priority=priority)
        
        if region := request.GET.get('region', '').strip():
            qs = qs.filter(region=region)
        
        if product := request.GET.get('product', '').strip():
            qs = qs.filter(product__icontains=product)
        

        if date_from := request.GET.get('date_from', '').strip():
            try:
                parsed_date = datetime.strptime(date_from, '%Y-%m-%d')
                date_from_aware = timezone.make_aware(
                    parsed_date.replace(hour=0, minute=0, second=0, microsecond=0)
                )
                qs = qs.filter(created_at__gte=date_from_aware)
            except ValueError:
                pass
        
        if date_to := request.GET.get('date_to', '').strip():
            try:
                parsed_date = datetime.strptime(date_to, '%Y-%m-%d')
                date_to_aware = timezone.make_aware(
                    parsed_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                )
                qs = qs.filter(created_at__lte=date_to_aware)
            except ValueError:
                pass
        
        return qs

    def get_changelist(self, request, **kwargs):
        """Переопределяем ChangeList чтобы игнорировать date_from/date_to"""
        from django.contrib.admin.views.main import ChangeList
        
        class CustomChangeList(ChangeList):
            def get_filters_params(self, params=None):
                """Убираем date_from и date_to из lookup параметров"""
                lookup_params = super().get_filters_params(params)
                

                lookup_params.pop('date_from', None)
                lookup_params.pop('date_to', None)
                
                return lookup_params
        
        return CustomChangeList
    
    def changelist_view(self, request, extra_context=None):
        """Контекст для фильтров"""
        extra_context = extra_context or {}
        
        from main.models import REGION_CHOICES
        extra_context['regions'] = REGION_CHOICES
        
        products = ContactForm.objects.exclude(
            product__isnull=True
        ).exclude(
            product=''
        ).values_list('product', flat=True).distinct().order_by('product')
        
        extra_context['products'] = list(products)
        
        return super().changelist_view(request, extra_context)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:object_id>/quick-update/', self.admin_site.admin_view(self.quick_update_view), name='contactform_quick_update'),
        ]
        return custom_urls + urls

    def quick_update_view(self, request, object_id):
        """AJAX автосохранение статуса/приоритета/менеджера"""
        import json
        from django.http import JsonResponse
        
        if request.method != 'POST':
            return JsonResponse({'error': 'Method not allowed'}, status=405)
        
        try:
            obj = ContactForm.objects.get(pk=object_id)
            data = json.loads(request.body)
            
            if 'status' in data:
                obj.status = data['status']
            if 'priority' in data:
                obj.priority = data['priority']
            if 'manager' in data:
                obj.manager_id = data['manager'] if data['manager'] else None
            
            obj.save()
            
            return JsonResponse({'success': True})
        
        except ContactForm.DoesNotExist:
            return JsonResponse({'error': 'Object not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
# ============ ВАКАНСИИ ============

class VacancyResponsibilityInline(TranslationStackedInline):
    model = VacancyResponsibility
    extra = 2
    fields = (('title', 'order'), 'text')

class VacancyRequirementInline(TranslationTabularInline):
    model = VacancyRequirement
    extra = 3
    fields = ('text', 'order')

class VacancyConditionInline(TranslationTabularInline):
    model = VacancyCondition
    extra = 3
    fields = ('text', 'order')

class VacancyIdealCandidateInline(TranslationTabularInline):
    model = VacancyIdealCandidate
    extra = 3
    fields = ('text', 'order')

@admin.register(Vacancy)
class VacancyAdmin(ContentAdminMixin, CustomReversionMixin, VersionAdmin, TabbedTranslationAdmin):
    list_display = ['title', 'is_active', 'applications_count', 'order', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'short_description']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_at', 'updated_at', 'applications_count']
    inlines = [VacancyResponsibilityInline, VacancyRequirementInline, VacancyIdealCandidateInline, VacancyConditionInline]
    history_latest_first = True
    
    fieldsets = (
        ('Основная информация', {'fields': ('title', 'slug', 'short_description', 'is_active', 'order')}),
        ('Контакты', {'fields': ('contact_info',)}),
        ('Статистика', {'fields': ('applications_count', 'created_at', 'updated_at'), 'classes': ('collapse',)}),
    )
    
    def applications_count(self, obj):
        count = obj.get_applications_count()
        if count > 0:
            return format_html(
                '<a href="/admin/main/jobapplication/?vacancy__id__exact={}" style="color:#007bff;font-weight:bold;"> {} Заявок</a>',
                obj.id, count
            )
        return '0 заявок'
    applications_count.short_description = 'Заявки'

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        deleted_count = Version.objects.get_deleted(self.model).count()
        if deleted_count > 0:
            extra_context['show_recover_button'] = True
            extra_context['deleted_count'] = deleted_count
        return super().changelist_view(request, extra_context)

@admin.register(JobApplication)
class JobApplicationAdmin(LeadManagerMixin, admin.ModelAdmin):
    list_display = ['vacancy', 'region', 'applicant_name', 'resume_link', 'file_size_display', 'created_at', 'is_processed_badge']
    list_filter = ['is_processed', 'vacancy', 'region', 'created_at']
    search_fields = ['applicant_name', 'applicant_phone', 'applicant_email', 'vacancy__title']
    readonly_fields = ['created_at', 'file_size_display', 'resume_preview']
    date_hierarchy = 'created_at'
    autocomplete_fields = ['vacancy']
    
    fieldsets = (
        ('Информация', {'fields': ('vacancy', 'region', 'created_at')}),
        ('Резюме', {'fields': ('resume', 'file_size_display', 'resume_preview')}),
        ('Контакты', {'fields': ('applicant_name', 'applicant_phone', 'applicant_email')}),
        ('Обработка', {'fields': ('is_processed', 'admin_comment')}),
    )
    
    def resume_link(self, obj):
        if obj.resume:
            return format_html('<a href="{}" target="_blank" style="color:#007bff;font-weight:bold;"> Скачать</a>', obj.resume.url)
        return "—"
    resume_link.short_description = 'Резюме'
    
    def file_size_display(self, obj):
        size = obj.get_file_size()
        return f"{size} MB" if size else "—"
    file_size_display.short_description = 'Размер'
    
    def resume_preview(self, obj):
        if obj.resume:
            file_ext = obj.resume.name.split('.')[-1].lower()
            if file_ext in ['jpg', 'jpeg', 'png']:
                return format_html('<img src="{}" width="300" style="border-radius:8px;">', obj.resume.url)
            return format_html('<p style="color:#888;"> {}</p>', obj.resume.name)
        return "—"
    resume_preview.short_description = 'Превью'
    
    def is_processed_badge(self, obj):
        if obj.is_processed:
            return format_html('<span style="color:green;font-weight:bold;"> Рассмотрено</span>')
        return format_html('<span style="color:orange;font-weight:bold;"> Новая</span>')
    is_processed_badge.short_description = 'Статус'

# ============ ИКОНКИ ============

@admin.register(FeatureIcon)
class FeatureIconAdmin(ContentAdminMixin, admin.ModelAdmin):
    list_display = ['icon_preview', 'name', 'order']
    list_editable = ['name', 'order']
    search_fields = ['name']
    
    def icon_preview(self, obj):
        if obj.icon:
            return format_html('<img src="{}" width="30" height="30"/>', obj.icon.url)
        return "—"
    icon_preview.short_description = "Превью"

# ============ ПРОДУКТЫ ============

@admin.register(ProductCategory)
class ProductCategoryAdmin(ContentAdminMixin, TabbedTranslationAdmin):
    list_display = ['icon_preview', 'name', 'slug', 'products_count', 'is_active', 'order']
    list_editable = ['is_active', 'order']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['products_count', 'created_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'slug', 'description', 'is_active', 'order')
        }),
        ('Изображения', {
            'fields': ('icon', 'hero_image')
        }),
        ('Статистика', {
            'fields': ('products_count', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def icon_preview(self, obj):
        if obj.icon:
            return format_html('<img src="{}" width="30" height="30"/>', obj.icon.url)
        return "—"
    icon_preview.short_description = "Иконка"
    
    def products_count(self, obj):
        count = obj.get_products_count()
        if count > 0:
            return format_html(
                '<a href="/admin/main/product/?category__id__exact={}" style="color:#007bff;font-weight:bold;">{} товаров</a>',
                obj.id, count
            )
        return '0 товаров'
    products_count.short_description = 'Продуктов'

# ========== ПРОДУКТЫ (ОБНОВЛЕННЫЙ) ==========

# ========== ПРОДУКТЫ (ОБНОВЛЕННЫЙ) ==========

class ProductCategoryFilter(admin.SimpleListFilter):
    """Фильтр по марке автомобиля"""
    title = 'Марка автомобиля'
    parameter_name = 'category_filter'
    
    def lookups(self, request, model_admin):
        categories = ProductCategory.objects.filter(is_active=True).order_by('order', 'name')
        return [(cat.id, cat.name) for cat in categories]
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(category__id=self.value())
        return queryset


class ParameterCategoryFilter(admin.SimpleListFilter):
    """Фильтр параметров по категории (для ProductAdmin)"""
    title = 'Категория параметра'
    parameter_name = 'param_category'

    def lookups(self, request, model_admin):
        cats = ParameterCategory.objects.filter(is_active=True).order_by('order', 'name')
        return [(cat.id, cat.name) for cat in cats]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(parameters__category__id=self.value()).distinct()
        return queryset


# class ProductParameterInline(admin.TabularInline):
#     """
#     Параметры продукта.
#     ✅ TranslationTabularInline эмас — category энди ForeignKey (tarjima йўқ).
#     """
#     model = ProductParameter
#     extra = 0
#     fields = ('category', 'text', 'order')
#     verbose_name = "Параметр"
#     verbose_name_plural = "📋 Параметры (выберите категорию для фильтрации)"
#     # category dropdown учун autocomplete (ParameterCategoryAdmin да search_fields бўлиши керак)
#     autocomplete_fields = ['category']


    # class Media:
    #     js = ('js/admin/parameter_filter.js',)
    #     css = {'all': ('css/admin/parameter_filter.css',)}    

class ProductParameterInline(TranslationTabularInline):
    """Параметры с фильтрацией по категории"""
    model = ProductParameter
    extra = 0
    fields = ('category', 'text', 'order')
    verbose_name = "Параметр"
    verbose_name_plural = "📋 Параметры (выберите категорию для фильтрации)"
    
    class Media:
        js = ('js/admin/parameter_filter.js',)
        css = {'all': ('css/admin/parameter_filter.css',)}




@admin.register(ParameterCategory)
class ParameterCategoryAdmin(TranslationAdmin):
    """
    Параметр категориялари — тўлиқ CRUD, 3 тилда.
    """
    list_display = ('name', 'slug', 'order', 'is_active', 'get_parameters_count')
    list_editable = ('order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'name_uz', 'name_ru', 'name_en', 'slug')
    prepopulated_fields = {'slug': ('name',)}

    fieldsets = (
        (None, {
            'fields': ('slug', 'order', 'is_active')
        }),
        ("🇺🇿 O'zbek", {
            'fields': ('name_uz',),
            'classes': ('collapse',),
        }),
        ("🇷🇺 Русский", {
            'fields': ('name_ru',),
            'classes': ('collapse',),
        }),
        ("🇬🇧 English", {
            'fields': ('name_en',),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description="Параметрлар сони")
    def get_parameters_count(self, obj):
        count = obj.parameters.count()
        return f"{count} та"

class ProductFeatureInline(TranslationTabularInline):
    model = ProductFeature
    extra = 0
    max_num = 8
    fields = ('icon', 'name', 'order')
    verbose_name = "Характеристика"
    verbose_name_plural = "🔹 Характеристики с иконками"


class ProductCardSpecInline(TranslationTabularInline):
    model = ProductCardSpec
    extra = 0
    max_num = 4
    fields = ('icon', 'value', 'order')
    verbose_name = "Спецификация"
    verbose_name_plural = "📄 Характеристики карточки"


class ProductGalleryInline(admin.TabularInline):
    model = ProductGallery
    extra = 1
    fields = ('image', 'order')
    verbose_name = "Фото"
    verbose_name_plural = "🖼️ Галерея"


@admin.register(Product)
class ProductAdmin(ContentAdminMixin, CustomReversionMixin, VersionAdmin, TabbedTranslationAdmin):
    list_display = ['thumbnail', 'title', 'category_display', 'is_active', 'is_featured', 'slider_order', 'order']
    list_filter = [ProductCategoryFilter, 'is_active', 'is_featured']
    search_fields = ['title', 'slug']
    list_editable = ['is_active', 'is_featured', 'slider_order', 'order']
    prepopulated_fields = {'slug': ('title',)}
    history_latest_first = True
    actions = ['add_to_slider', 'remove_from_slider']
    
    list_per_page = 15
    show_full_result_count = False
    
    fieldsets = (
        ('Основная информация', {
            'fields': (
                ('title', 'slug'),
                'category',  # ✅ Теперь обычный select
                ('order', 'is_active', 'is_featured'),
                ('main_image', 'card_image')
            )
        }),
        ('⭐ Настройки главного слайдера', {
            'classes': ('collapse',),
            'fields': (
                'slider_image',
                ('slider_year', 'slider_order'),
                'slider_price',
                ('slider_power', 'slider_fuel_consumption'),
            ),
        }),
    )
    
    inlines = [ProductParameterInline, ProductFeatureInline, ProductCardSpecInline, ProductGalleryInline]
    
    def thumbnail(self, obj):
        img = obj.card_image or obj.main_image
        if img:
            return format_html(
                '<img src="{}" width="80" height="50" style="object-fit:cover;border-radius:4px;"/>',
                img.url
            )
        return "—"
    thumbnail.short_description = "Фото"

    def category_display(self, obj):
        """✅ НОВОЕ: Отображение одной категории"""
        if obj.category:
            return format_html(
                '<span style="background:#1976d2;color:white;padding:4px 8px;border-radius:4px;font-size:11px;font-weight:600;">{}</span>',
                obj.category.name
            )
        return format_html('<span style="color:#999;">Без категории</span>')
    category_display.short_description = "Категория"
    
    def add_to_slider(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'✅ {updated} продуктов добавлено в слайдер')
    add_to_slider.short_description = '⭐ Добавить в слайдер'
    
    def remove_from_slider(self, request, queryset):
        updated = queryset.update(is_featured=False)
        self.message_user(request, f'❌ {updated} продуктов убрано из слайдера')
    remove_from_slider.short_description = '❌ Убрать из слайдера'

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        deleted_count = Version.objects.get_deleted(self.model).count()
        if deleted_count > 0:
            extra_context['show_recover_button'] = True
            extra_context['deleted_count'] = deleted_count
        featured_count = Product.objects.filter(is_featured=True, is_active=True).count()
        extra_context['featured_count'] = featured_count
        extra_context['show_slider_info'] = True
        return super().changelist_view(request, extra_context)
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'api/parameter-suggestions/',
                self.admin_site.admin_view(self.parameter_suggestions_api),
                name='parameter_suggestions_api'
            ),
        ]
        return custom_urls + urls

    def parameter_suggestions_api(self, request):
        """API для получения подсказок параметров по категории"""
        category = request.GET.get('category', '')
        
        if not category:
            return JsonResponse({'suggestions': []})
        
        from django.db.models import Count
        
        suggestions = ProductParameter.objects.filter(
            category=category
        ).values('text').annotate(
            usage_count=Count('id')
        ).order_by('-usage_count')[:20]
        
        result = []
        seen = set()
        
        for item in suggestions:
            text = item['text']
            if text and text not in seen:
                seen.add(text)
                result.append({
                    'text': text,
                    'count': item['usage_count']
                })
        
        return JsonResponse({'suggestions': result})

@admin.register(AmoCRMToken)
class AmoCRMTokenAdmin(AmoCRMAdminMixin, admin.ModelAdmin):
    list_display = ['token_status', 'expires_display', 'time_left_display', 'action_buttons']
    
    # ========== ОТОБРАЖЕНИЕ ==========
    def token_status(self, obj):
        """Статус токена"""
        
        if not obj.access_token:
            return format_html(
                '<span style="background:#dc3545;color:white;padding:6px 12px;border-radius:6px;font-weight:600;">Не настроен</span>'
            )
        
        if obj.is_expired():
            return format_html(
                '<span style="background:#ffc107;color:#000;padding:6px 12px;border-radius:6px;font-weight:600;">Истекает скоро</span>'
            )
        
        return format_html(
            '<span style="background:#28a745;color:white;padding:6px 12px;border-radius:6px;font-weight:600;">Валиден</span>'
        )
    
    token_status.short_description = "Статус"
    
    def expires_display(self, obj):
        """Дата истечения"""
        if obj.expires_at:
            return obj.expires_at.strftime('%d.%m.%Y %H:%M')
        return "—"
    
    expires_display.short_description = "Истекает"
    
    def time_left_display(self, obj):
        """Оставшееся время"""
        
        if not obj.expires_at:
            return "—"
        
        time_left = obj.expires_at - timezone.now()
        
        if time_left.total_seconds() < 0:
            return format_html('<span style="color:#dc3545;font-weight:600;">Истёк</span>')
        
        days = time_left.days
        hours = int(time_left.seconds / 3600)
        minutes = int((time_left.seconds % 3600) / 60)
        
        if time_left.total_seconds() < 3600:
            color = '#dc3545'
        elif time_left.total_seconds() < 7200:
            color = '#ffc107'
        else:
            color = '#28a745'
        
        if days > 0:
            text = f"{days} дн. {hours} ч."
        elif hours > 0:
            text = f"{hours} ч. {minutes} мин."
        else:
            text = f"{minutes} мин."
        
        return format_html('<span style="color:{};font-weight:600;">{}</span>', color, text)
    
    time_left_display.short_description = "Осталось"
    
    def action_buttons(self, obj):
        """Кнопки действий"""
        return format_html('''
            <div style="display:flex;gap:8px;flex-wrap:wrap;">
                <a href="/admin/main/amocrmtoken/refresh/" 
                   class="button" 
                   style="background:#007bff;color:white;padding:6px 12px;border-radius:4px;text-decoration:none;white-space:nowrap;">
                    Обновить токен
                </a>
                <a href="/admin/main/amocrmtoken/logs/" 
                   class="button" 
                   style="background:#dc3545;color:white;padding:6px 12px;border-radius:4px;text-decoration:none;white-space:nowrap;">
                    Логи ошибок
                </a>
                <a href="/admin/main/amocrmtoken/instructions/" 
                   class="button" 
                   style="background:#6c757d;color:white;padding:6px 12px;border-radius:4px;text-decoration:none;white-space:nowrap;">
                    Инструкция
                </a>
            </div>
        ''')
    
    action_buttons.short_description = "Действия"
    
    # ========== МАРШРУТЫ ==========
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('refresh/', self.admin_site.admin_view(self.refresh_token_view), name='amocrm_refresh'),
            path('logs/', self.admin_site.admin_view(self.logs_view), name='amocrm_logs'),
            path('instructions/', self.admin_site.admin_view(self.instructions_view), name='amocrm_instructions'),
        ]
        return custom_urls + urls
    
    # ========== ОБРАБОТЧИКИ ==========
    def refresh_token_view(self, request):
        """Обновить токен вручную"""
        try:
            token_obj = AmoCRMToken.get_instance()
            
            if not token_obj.refresh_token:
                messages.error(request, 'Refresh token не найден. Настройте токены заново.')
                return redirect('/admin/main/amocrmtoken/')
            
            TokenManager.refresh_token(token_obj)
            messages.success(request, f'Токен успешно обновлён. Истекает: {token_obj.expires_at.strftime("%d.%m.%Y %H:%M")}')
            
        except Exception as e:
            messages.error(request, f'Ошибка обновления: {str(e)}')
        
        return redirect('/admin/main/amocrmtoken/')
    
    def logs_view(self, request):
        """Показать логи ошибок amoCRM"""

        
        amocrm_log_path = os.path.join(settings.BASE_DIR, 'logs', 'amocrm.log')
        errors_log_path = os.path.join(settings.BASE_DIR, 'logs', 'errors.log')
        
        amocrm_logs = []
        errors_logs = []
        
        if os.path.exists(amocrm_log_path):
            try:
                with open(amocrm_log_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    amocrm_logs = [line.strip() for line in lines if line.strip()][-100:]
            except Exception as e:
                amocrm_logs = [f"Ошибка чтения amocrm.log: {str(e)}"]
        
        if os.path.exists(errors_log_path):
            try:
                with open(errors_log_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    errors_logs = [line.strip() for line in lines if line.strip()][-50:]
            except Exception as e:
                errors_logs = [f"Ошибка чтения errors.log: {str(e)}"]
        
        context = {
            **self.admin_site.each_context(request),
            'title': 'Логи ошибок amoCRM',
            'amocrm_logs': amocrm_logs,
            'errors_logs': errors_logs,
        }
        return render(request, 'main/amocrm_logs.html', context)
    
    def instructions_view(self, request):
        """Показать инструкцию"""
        
        token_obj = AmoCRMToken.get_instance()
        time_left_text = None
        
        if token_obj.expires_at:
            time_left = token_obj.expires_at - timezone.now()
            
            if time_left.total_seconds() < 0:
                time_left_text = "Токен истёк"
            else:
                days = time_left.days
                hours = int(time_left.seconds / 3600)
                minutes = int((time_left.seconds % 3600) / 60)
                
                parts = []
                if days > 0:
                    parts.append(f"{days} дн.")
                if hours > 0:
                    parts.append(f"{hours} ч.")
                if minutes > 0:
                    parts.append(f"{minutes} мин.")
                
                time_left_text = " ".join(parts) if parts else "Менее минуты"
        
        context = {
            **self.admin_site.each_context(request),
            'title': 'Инструкция: Обновление токенов amoCRM',
            'token': token_obj,
            'time_left_text': time_left_text,
        }
        return render(request, 'main/amocrm_instructions.html', context)
    
# ========== DILERLAR ==========

class DealerImageInline(admin.TabularInline):
    model = DealerImage
    extra = 1
    fields = ('image', 'caption_uz', 'caption_ru', 'caption_en', 'order')
    ordering = ('order',)


@admin.register(Dealer)
class DealerAdmin(ContentAdminMixin, TabbedTranslationAdmin):
    list_display = ('name', 'region', 'phone', 'is_active', 'order')
    list_filter = ('region', 'is_active')
    list_editable = ('is_active', 'order')
    search_fields = ('name', 'address', 'phone')
    ordering = ('order', 'name')
    inlines = [DealerImageInline]
    fieldsets = (
        ("Asosiy ma'lumotlar", {
            'fields': (
                'name_uz', 'name_ru', 'name_en',
                'region',
                'address_uz', 'address_ru', 'address_en',
                'phone',
                'working_hours_uz', 'working_hours_ru', 'working_hours_en',
                'logo',
            )
        }),
        ("Tavsif", {
            'fields': ('description_uz', 'description_ru', 'description_en'),
            'classes': ('collapse',),
        }),
        ("Xarita koordinatalari", {
            'fields': ('latitude', 'longitude'),
            'description': '📍 Google Maps da diler manzilini toping → "joylashuvni koordinatalarini toping" → nusxa oling.',
        }),
        ("Ijtimoiy tarmoqlar", {
            'fields': ('instagram', 'telegram', 'facebook', 'youtube'),
            'classes': ('collapse',),
        }),
        ("Sozlamalar", {
            'fields': ('is_active', 'order'),
        }),
    )


# ========== ОТЗЫВЫ КЛИЕНТОВ ==========

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('name', 'rating_stars', 'status_badge', 'is_verified', 'created_at', 'moderated_at')
    list_filter = ('status', 'rating', 'is_verified', 'created_at')
    list_editable = ('is_verified',)
    search_fields = ('name', 'text')
    readonly_fields = ('ip_address', 'created_at', 'moderated_at', 'avatar_preview')
    ordering = ('-created_at',)
    actions = ['approve_reviews', 'reject_reviews']
    list_per_page = 30

    fieldsets = (
        ("Информация об отзыве", {
            'fields': ('name', 'rating', 'text', 'avatar', 'avatar_preview')
        }),
        ("Модерация", {
            'fields': ('status', 'is_verified', 'admin_comment'),
            'description': '⚠️ Только одобренные отзывы отображаются на сайте'
        }),
        ("Системная информация", {
            'fields': ('ip_address', 'created_at', 'moderated_at'),
            'classes': ('collapse',),
        }),
    )

    def rating_stars(self, obj):
        return format_html(
            '<span style="color:#F7941D;font-size:16px;">{}</span>',
            '★' * obj.rating + '☆' * (5 - obj.rating)
        )
    rating_stars.short_description = "Оценка"

    def status_badge(self, obj):
        colors = {'pending': '#FF9800', 'approved': '#4CAF50', 'rejected': '#f44336'}
        labels = {'pending': 'На модерации', 'approved': 'Одобрен', 'rejected': 'Отклонён'}
        return format_html(
            '<span style="background:{};color:#fff;padding:3px 10px;border-radius:12px;font-size:12px;">{}</span>',
            colors.get(obj.status, '#999'),
            labels.get(obj.status, obj.status)
        )
    status_badge.short_description = "Статус"

    def avatar_preview(self, obj):
        if obj.avatar:
            return format_html('<img src="{}" style="max-width:150px;max-height:150px;border-radius:50%;">', obj.avatar.url)
        return "Нет фото"
    avatar_preview.short_description = "Превью аватара"

    def approve_reviews(self, request, queryset):
        count = queryset.update(status='approved', is_verified=True, moderated_at=timezone.now())
        self.message_user(request, f"✅ Одобрено отзывов: {count}", messages.SUCCESS)
    approve_reviews.short_description = "✅ Одобрить выбранные отзывы"

    def reject_reviews(self, request, queryset):
        count = queryset.update(status='rejected', moderated_at=timezone.now())
        self.message_user(request, f"❌ Отклонено отзывов: {count}", messages.WARNING)
    reject_reviews.short_description = "❌ Отклонить выбранные отзывы"

    def save_model(self, request, obj, form, change):
        if change and 'status' in form.changed_data:
            obj.moderated_at = timezone.now()
        super().save_model(request, obj, form, change)


# ========== ТЕСТ-ДРАЙВ ==========

@admin.register(TestDriveRequest)
class TestDriveRequestAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'product', 'dealer', 'preferred_date', 'preferred_time', 'status', 'created_at']
    list_filter = ['status', 'dealer', 'preferred_date', 'created_at']
    search_fields = ['name', 'phone']
    list_editable = ['status']
    readonly_fields = ['ip_address', 'referer', 'utm_data', 'visitor_uid', 'created_at', 'updated_at']
    ordering = ['-created_at']

    fieldsets = (
        ('Клиент', {
            'fields': ('name', 'phone', 'dealer', 'product')
        }),
        ('Дата и время', {
            'fields': ('preferred_date', 'preferred_time')
        }),
        ('Статус', {
            'fields': ('status', 'admin_comment')
        }),
        ('Техническая информация', {
            'classes': ('collapse',),
            'fields': ('ip_address', 'referer', 'utm_data', 'visitor_uid', 'created_at', 'updated_at')
        }),
    )

    actions = ['mark_confirmed', 'mark_completed', 'mark_cancelled']

    def mark_confirmed(self, request, queryset):
        count = queryset.update(status='confirmed')
        self.message_user(request, f"Подтверждено: {count}", messages.SUCCESS)
    mark_confirmed.short_description = "Подтвердить выбранные"

    def mark_completed(self, request, queryset):
        count = queryset.update(status='completed')
        self.message_user(request, f"Завершено: {count}", messages.SUCCESS)
    mark_completed.short_description = "Отметить как завершённые"

    def mark_cancelled(self, request, queryset):
        count = queryset.update(status='cancelled')
        self.message_user(request, f"Отменено: {count}", messages.WARNING)
    mark_cancelled.short_description = "Отменить выбранные"


# ========== КОМАНДА — МЕНЕДЖЕРЫ ==========

@admin.register(BranchManager)
class BranchManagerAdmin(TabbedTranslationAdmin):
    list_display = ['full_name', 'position', 'dealer', 'phone', 'is_active', 'order']
    list_filter = ['dealer', 'is_active']
    list_editable = ['is_active', 'order']
    search_fields = ['full_name', 'phone']
    ordering = ['dealer__order', 'order']

    fieldsets = (
        (None, {
            'fields': ('full_name', 'position', 'photo', 'dealer', 'phone')
        }),
        ('Настройки', {
            'fields': ('is_active', 'order')
        }),
    )


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ['telegram_id', 'username', 'first_name', 'phone', 'region', 'language', 'age', 'created_at']
    list_filter = ['region', 'language', 'created_at']
    search_fields = ['username', 'first_name', 'phone', 'telegram_id']
    readonly_fields = ['telegram_id', 'username', 'first_name', 'phone', 'region', 'language', 'age', 'created_at']
    ordering = ['-created_at']
    list_per_page = 50





    