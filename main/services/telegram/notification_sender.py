import requests
import logging
import json
from django.conf import settings
import pytz

logger = logging.getLogger('django')


class TelegramNotificationSender:
    """Отправка уведомлений о лидах в Telegram"""
    
    @classmethod
    def send_lead_notification(cls, contact_form):
        """Отправить уведомление о новом лиде в Telegram"""
        
        try:
            bot_token = settings.TELEGRAM_BOT_TOKEN
            chat_id = settings.TELEGRAM_CHAT_ID
            
            if not bot_token or not chat_id:
                logger.warning("Telegram настройки не заданы в .env")
                return
            
            # Формируем сообщение
            message = cls._format_message(contact_form)
            
            # Формируем кнопки
            reply_markup = cls._build_keyboard(contact_form)
            
            # Отправляем в Telegram
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            }
            
            if reply_markup:
                payload["reply_markup"] = reply_markup
            
            response = requests.post(url, json=payload, timeout=5)
            
            if response.status_code == 200:
                logger.info(f"Telegram уведомление отправлено для лида #{contact_form.id}")
            else:
                logger.error(
                    f"Ошибка Telegram {response.status_code} для лида #{contact_form.id}: {response.text[:200]}"
                )
        
        except requests.exceptions.Timeout:
            logger.error(f"Telegram timeout для лида #{contact_form.id}")
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка запроса к Telegram для лида #{contact_form.id}: {str(e)}")
        
        except Exception as e:
            logger.error(f"Критическая ошибка Telegram для лида #{contact_form.id}: {str(e)}", exc_info=True)
    
    @staticmethod
    def _format_message(contact_form):
        """Форматирование сообщения для Telegram"""
        
        # Заголовок
        if contact_form.amocrm_status == 'failed':
            header = f"🚛 Новая заявка FAW.UZ #{contact_form.id}\n❌ Не отправлено в amoCRM\n"
        else:
            header = f"🚛 Новая заявка FAW.UZ #{contact_form.id}\n"
        
        # Основная информация
        message = header
        message += f"\n👤 Клиент: {contact_form.name}"
        message += f"\n📞 Телефон: {contact_form.phone}"
        message += f"\n📍 Регион: {contact_form.get_region_display()}"
        
        # Модель (если есть)
        if contact_form.product:
            message += f"\n🚗 Модель: {contact_form.product}"
        
        # Сообщение (если есть)
        if contact_form.message:
            msg = contact_form.message.strip()
            if len(msg) > 500:
                msg = msg[:497] + "..."
            message += f"\n\n💬 Сообщение:\n{msg}"
        
        # Источник
        message += "\n\n📊 Источник:"
        
        # Referer
        if contact_form.referer:
            referer = contact_form.referer
            referer = referer.replace('https://', '').replace('http://', '').replace('www.', '')
            if '?' in referer:
                referer = referer.split('?')[0]
            if len(referer) > 80:
                referer = referer[:77] + "..."
            message += f"\n🔗 Referer: {referer}"
        
        # UTM метки
        if contact_form.utm_data:
            try:
                utm = json.loads(contact_form.utm_data)
                utm_parts = []
                if 'utm_source' in utm:
                    utm_parts.append(utm['utm_source'])
                if 'utm_medium' in utm:
                    utm_parts.append(utm['utm_medium'])
                if 'utm_campaign' in utm:
                    utm_parts.append(utm['utm_campaign'])
                
                if utm_parts:
                    message += f"\n🏷️ UTM: {' / '.join(utm_parts)}"
            except:
                pass
        
        # Form ID
        message += f"\n📝 Form ID: Заявка с сайта FAW.UZ"
        
        # Visitor UID (если есть)
        if contact_form.visitor_uid:
            uid = contact_form.visitor_uid[:20] + "..." if len(contact_form.visitor_uid) > 20 else contact_form.visitor_uid
            message += f"\n👤 Visitor UID: {uid}"
        
        # Ошибка amoCRM (если есть)
        if contact_form.amocrm_status == 'failed' and contact_form.amocrm_error:
            error = contact_form.amocrm_error.strip()
            if len(error) > 200:
                error = error[:197] + "..."
            message += f"\n\n⚠️ Ошибка amoCRM: {error}"
        
        # Время (конвертируем в локальный часовой пояс)
        tz = pytz.timezone(settings.TIME_ZONE)
        created_time_local = contact_form.created_at.astimezone(tz)
        created_time = created_time_local.strftime('%d.%m.%Y в %H:%M')
        message += f"\n\n⏰ {created_time}"
        
        return message
    
    @classmethod
    def send_test_drive_notification(cls, td):
        """Отправить уведомление о новой заявке на тест-драйв"""
        try:
            bot_token = settings.TELEGRAM_BOT_TOKEN
            chat_id = settings.TELEGRAM_CHAT_ID

            if not bot_token or not chat_id:
                logger.warning("Telegram настройки не заданы в .env")
                return

            message = f"🏎 Новая заявка на тест-драйв #{td.id}\n"
            message += f"\n👤 Клиент: {td.name}"
            message += f"\n📞 Телефон: {td.phone}"

            if td.dealer:
                message += f"\n🏢 Дилер: {td.dealer.name}"
                if td.dealer.address:
                    message += f"\n📍 Адрес: {td.dealer.address}"

            if td.product:
                message += f"\n🚗 Модель: {td.product.title}"

            message += f"\n📅 Дата: {td.preferred_date.strftime('%d.%m.%Y')}"
            message += f"\n🕐 Время: {td.preferred_time}"

            tz = pytz.timezone(settings.TIME_ZONE)
            created_time = td.created_at.astimezone(tz).strftime('%d.%m.%Y в %H:%M')
            message += f"\n\n⏰ {created_time}"

            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            }

            response = requests.post(url, json=payload, timeout=5)

            if response.status_code == 200:
                logger.info(f"Telegram уведомление отправлено для тест-драйва #{td.id}")
            else:
                logger.error(f"Ошибка Telegram {response.status_code} для тест-драйва #{td.id}: {response.text[:200]}")

        except Exception as e:
            logger.error(f"Ошибка Telegram для тест-драйва #{td.id}: {str(e)}", exc_info=True)

    @staticmethod
    def _build_keyboard(contact_form):
        """Создание inline-кнопок"""
        buttons = []
        
        # Кнопка amoCRM (если успешно отправлено)
        if contact_form.amocrm_status == 'sent' and contact_form.amocrm_lead_id:
            amocrm_url = f"https://fawtrucks.amocrm.ru/leads/detail/{contact_form.amocrm_lead_id}"
            buttons.append({
                "text": "🔗 Открыть в amoCRM",
                "url": amocrm_url
            })
        
        # Кнопка админ-панели FAW
        admin_url = f"https://faw.uz/admin/main/contactform/{contact_form.id}/change/"
        buttons.append({
            "text": "⚙️ Админ-панель FAW",
            "url": admin_url
        })
        
        if buttons:
            return {
                "inline_keyboard": [buttons]
            }
        
        return None