import requests
import logging
import json
from django.conf import settings
import pytz

logger = logging.getLogger('django')


class TelegramNotificationSender:
    """Р В РЎвЂєР РЋРІР‚С™Р В РЎвЂ”Р РЋР вЂљР В Р’В°Р В Р вЂ Р В РЎвЂќР В Р’В° Р РЋРЎвЂњР В Р вЂ Р В Р’ВµР В РўвЂР В РЎвЂўР В РЎР В Р’В»Р В Р’ВµР В Р вЂ¦Р В РЎвЂР В РІвЂћвЂ“ Р В РЎвЂў Р В Р’В»Р В РЎвЂР В РўвЂР В Р’В°Р РЋРІР‚В¦ Р В Р вЂ  Telegram"""
    
    @classmethod
    def send_lead_notification(cls, contact_form):
        """Р В РЎвЂєР РЋРІР‚С™Р В РЎвЂ”Р РЋР вЂљР В Р’В°Р В Р вЂ Р В РЎвЂР РЋРІР‚С™Р РЋР Р‰ Р РЋРЎвЂњР В Р вЂ Р В Р’ВµР В РўвЂР В РЎвЂўР В РЎР В Р’В»Р В Р’ВµР В Р вЂ¦Р В РЎвЂР В Р’Вµ Р В РЎвЂў Р В Р вЂ¦Р В РЎвЂўР В Р вЂ Р В РЎвЂўР В РЎ Р В Р’В»Р В РЎвЂР В РўвЂР В Р’Вµ Р В Р вЂ  Telegram"""
        
        try:
            bot_token = settings.TELEGRAM_BOT_TOKEN
            chat_id = settings.TELEGRAM_CHAT_ID
            
            if not bot_token or not chat_id:
                logger.warning("Telegram Р В Р вЂ¦Р В Р’В°Р РЋР С“Р РЋРІР‚С™Р РЋР вЂљР В РЎвЂўР В РІвЂћвЂ“Р В РЎвЂќР В РЎвЂ Р В Р вЂ¦Р В Р’Вµ Р В Р’В·Р В Р’В°Р В РўвЂР В Р’В°Р В Р вЂ¦Р РЋРІР‚в„– Р В Р вЂ  .env")
                return
            
            # Р В Р’В¤Р В РЎвЂўР РЋР вЂљР В РЎР В РЎвЂР РЋР вЂљР РЋРЎвЂњР В Р’ВµР В РЎ Р РЋР С“Р В РЎвЂўР В РЎвЂўР В Р’В±Р РЋРІР‚В°Р В Р’ВµР В Р вЂ¦Р В РЎвЂР В Р’Вµ
            message = cls._format_message(contact_form)
            
            # Р В Р’В¤Р В РЎвЂўР РЋР вЂљР В РЎР В РЎвЂР РЋР вЂљР РЋРЎвЂњР В Р’ВµР В РЎ Р В РЎвЂќР В Р вЂ¦Р В РЎвЂўР В РЎвЂ”Р В РЎвЂќР В РЎвЂ
            reply_markup = cls._build_keyboard(contact_form)
            
            # Р В РЎвЂєР РЋРІР‚С™Р В РЎвЂ”Р РЋР вЂљР В Р’В°Р В Р вЂ Р В Р’В»Р РЋР РЏР В Р’ВµР В РЎ Р В Р вЂ  Telegram
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
                logger.info(f"Telegram Р РЋРЎвЂњР В Р вЂ Р В Р’ВµР В РўвЂР В РЎвЂўР В РЎР В Р’В»Р В Р’ВµР В Р вЂ¦Р В РЎвЂР В Р’Вµ Р В РЎвЂўР РЋРІР‚С™Р В РЎвЂ”Р РЋР вЂљР В Р’В°Р В Р вЂ Р В Р’В»Р В Р’ВµР В Р вЂ¦Р В РЎвЂў Р В РўвЂР В Р’В»Р РЋР РЏ Р В Р’В»Р В РЎвЂР В РўвЂР В Р’В° #{contact_form.id}")
            else:
                logger.error(
                    f"Р В РЎвЂєР РЋРІвЂљВ¬Р В РЎвЂР В Р’В±Р В РЎвЂќР В Р’В° Telegram {response.status_code} Р В РўвЂР В Р’В»Р РЋР РЏ Р В Р’В»Р В РЎвЂР В РўвЂР В Р’В° #{contact_form.id}: {response.text[:200]}"
                )
        
        except requests.exceptions.Timeout:
            logger.error(f"Telegram timeout Р В РўвЂР В Р’В»Р РЋР РЏ Р В Р’В»Р В РЎвЂР В РўвЂР В Р’В° #{contact_form.id}")
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Р В РЎвЂєР РЋРІвЂљВ¬Р В РЎвЂР В Р’В±Р В РЎвЂќР В Р’В° Р В Р’В·Р В Р’В°Р В РЎвЂ”Р РЋР вЂљР В РЎвЂўР РЋР С“Р В Р’В° Р В РЎвЂќ Telegram Р В РўвЂР В Р’В»Р РЋР РЏ Р В Р’В»Р В РЎвЂР В РўвЂР В Р’В° #{contact_form.id}: {str(e)}")
        
        except Exception as e:
            logger.error(f"Р В РЎв„ўР РЋР вЂљР В РЎвЂР РЋРІР‚С™Р В РЎвЂР РЋРІР‚РЋР В Р’ВµР РЋР С“Р В РЎвЂќР В Р’В°Р РЋР РЏ Р В РЎвЂўР РЋРІвЂљВ¬Р В РЎвЂР В Р’В±Р В РЎвЂќР В Р’В° Telegram Р В РўвЂР В Р’В»Р РЋР РЏ Р В Р’В»Р В РЎвЂР В РўвЂР В Р’В° #{contact_form.id}: {str(e)}", exc_info=True)
    
    @staticmethod
    def _format_message(contact_form):
        """Р В Р’В¤Р В РЎвЂўР РЋР вЂљР В РЎР В Р’В°Р РЋРІР‚С™Р В РЎвЂР РЋР вЂљР В РЎвЂўР В Р вЂ Р В Р’В°Р В Р вЂ¦Р В РЎвЂР В Р’Вµ Р РЋР С“Р В РЎвЂўР В РЎвЂўР В Р’В±Р РЋРІР‚В°Р В Р’ВµР В Р вЂ¦Р В РЎвЂР РЋР РЏ Р В РўвЂР В Р’В»Р РЋР РЏ Telegram"""
        
        # Р В РІР‚вЂќР В Р’В°Р В РЎвЂ“Р В РЎвЂўР В Р’В»Р В РЎвЂўР В Р вЂ Р В РЎвЂўР В РЎвЂќ
        if contact_form.amocrm_status == 'failed':
            header = f"РЎР‚РЎСџРЎв„ўРІР‚С” Р В РЎСљР В РЎвЂўР В Р вЂ Р В Р’В°Р РЋР РЏ Р В Р’В·Р В Р’В°Р РЋР РЏР В Р вЂ Р В РЎвЂќР В Р’В° FAW.UZ #{contact_form.id}\nР Р†РЎСљР Р‰ Р В РЎСљР В Р’Вµ Р В РЎвЂўР РЋРІР‚С™Р В РЎвЂ”Р РЋР вЂљР В Р’В°Р В Р вЂ Р В Р’В»Р В Р’ВµР В Р вЂ¦Р В РЎвЂў Р В Р вЂ  amoCRM\n"
        else:
            header = f"РЎР‚РЎСџРЎв„ўРІР‚С” Р В РЎСљР В РЎвЂўР В Р вЂ Р В Р’В°Р РЋР РЏ Р В Р’В·Р В Р’В°Р РЋР РЏР В Р вЂ Р В РЎвЂќР В Р’В° FAW.UZ #{contact_form.id}\n"
        
        # Р В РЎвЂєР РЋР С“Р В Р вЂ¦Р В РЎвЂўР В Р вЂ Р В Р вЂ¦Р В Р’В°Р РЋР РЏ Р В РЎвЂР В Р вЂ¦Р РЋРІР‚С›Р В РЎвЂўР РЋР вЂљР В РЎР В Р’В°Р РЋРІР‚В Р В РЎвЂР РЋР РЏ
        message = header
        message += f"\nРЎР‚РЎСџРІР‚Р’В¤ Р В РЎв„ўР В Р’В»Р В РЎвЂР В Р’ВµР В Р вЂ¦Р РЋРІР‚С™: {contact_form.name}"
        message += f"\nРЎР‚РЎСџРІР‚СљРЎвЂє Р В РЎС›Р В Р’ВµР В Р’В»Р В Р’ВµР РЋРІР‚С›Р В РЎвЂўР В Р вЂ¦: {contact_form.phone}"
        message += f"\nРЎР‚РЎСџРІР‚СљР РЉ Р В Р’В Р В Р’ВµР В РЎвЂ“Р В РЎвЂР В РЎвЂўР В Р вЂ¦: {contact_form.get_region_display()}"
        
        # Р В РЎС™Р В РЎвЂўР В РўвЂР В Р’ВµР В Р’В»Р РЋР Р‰ (Р В Р’ВµР РЋР С“Р В Р’В»Р В РЎвЂ Р В Р’ВµР РЋР С“Р РЋРІР‚С™Р РЋР Р‰)
        if contact_form.product:
            message += f"\nРЎР‚РЎСџРЎв„ўРІР‚вЂќ Р В РЎС™Р В РЎвЂўР В РўвЂР В Р’ВµР В Р’В»Р РЋР Р‰: {contact_form.product}"
        
        # Р В Р Р‹Р В РЎвЂўР В РЎвЂўР В Р’В±Р РЋРІР‚В°Р В Р’ВµР В Р вЂ¦Р В РЎвЂР В Р’Вµ (Р В Р’ВµР РЋР С“Р В Р’В»Р В РЎвЂ Р В Р’ВµР РЋР С“Р РЋРІР‚С™Р РЋР Р‰)
        if contact_form.message:
            msg = contact_form.message.strip()
            if len(msg) > 500:
                msg = msg[:497] + "..."
            message += f"\n\nРЎР‚РЎСџРІР‚в„ўР’В¬ Р В Р Р‹Р В РЎвЂўР В РЎвЂўР В Р’В±Р РЋРІР‚В°Р В Р’ВµР В Р вЂ¦Р В РЎвЂР В Р’Вµ:\n{msg}"
        
        # Р В Р РЋР С“Р РЋРІР‚С™Р В РЎвЂўР РЋРІР‚РЋР В Р вЂ¦Р В РЎвЂР В РЎвЂќ
        message += "\n\nРЎР‚РЎСџРІР‚СљР вЂ° Р В Р РЋР С“Р РЋРІР‚С™Р В РЎвЂўР РЋРІР‚РЋР В Р вЂ¦Р В РЎвЂР В РЎвЂќ:"
        
        # Referer
        if contact_form.referer:
            referer = contact_form.referer
            referer = referer.replace('https://', '').replace('http://', '').replace('www.', '')
            if '?' in referer:
                referer = referer.split('?')[0]
            if len(referer) > 80:
                referer = referer[:77] + "..."
            message += f"\nРЎР‚РЎСџРІР‚СњРІР‚вЂќ Referer: {referer}"
        
        # UTM Р В РЎР В Р’ВµР РЋРІР‚С™Р В РЎвЂќР В РЎвЂ
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
                    message += f"\nРЎР‚РЎСџР РЏР’В·Р С—РЎвЂР РЏ UTM: {' / '.join(utm_parts)}"
            except:
                pass
        
        # Form ID
        message += f"\nРЎР‚РЎСџРІР‚СљРЎСљ Form ID: Р В РІР‚вЂќР В Р’В°Р РЋР РЏР В Р вЂ Р В РЎвЂќР В Р’В° Р РЋР С“ Р РЋР С“Р В Р’В°Р В РІвЂћвЂ“Р РЋРІР‚С™Р В Р’В° FAW.UZ"
        
        # Visitor UID (Р В Р’ВµР РЋР С“Р В Р’В»Р В РЎвЂ Р В Р’ВµР РЋР С“Р РЋРІР‚С™Р РЋР Р‰)
        if contact_form.visitor_uid:
            uid = contact_form.visitor_uid[:20] + "..." if len(contact_form.visitor_uid) > 20 else contact_form.visitor_uid
            message += f"\nРЎР‚РЎСџРІР‚Р’В¤ Visitor UID: {uid}"
        
        # Р В РЎвЂєР РЋРІвЂљВ¬Р В РЎвЂР В Р’В±Р В РЎвЂќР В Р’В° amoCRM (Р В Р’ВµР РЋР С“Р В Р’В»Р В РЎвЂ Р В Р’ВµР РЋР С“Р РЋРІР‚С™Р РЋР Р‰)
        if contact_form.amocrm_status == 'failed' and contact_form.amocrm_error:
            error = contact_form.amocrm_error.strip()
            if len(error) > 200:
                error = error[:197] + "..."
            message += f"\n\nР Р†РЎв„ўР’В Р С—РЎвЂР РЏ Р В РЎвЂєР РЋРІвЂљВ¬Р В РЎвЂР В Р’В±Р В РЎвЂќР В Р’В° amoCRM: {error}"
        
        # Р В РІР‚в„ўР РЋР вЂљР В Р’ВµР В РЎР РЋР РЏ (Р В РЎвЂќР В РЎвЂўР В Р вЂ¦Р В Р вЂ Р В Р’ВµР РЋР вЂљР РЋРІР‚С™Р В РЎвЂР РЋР вЂљР РЋРЎвЂњР В Р’ВµР В РЎ Р В Р вЂ  Р В Р’В»Р В РЎвЂўР В РЎвЂќР В Р’В°Р В Р’В»Р РЋР Р‰Р В Р вЂ¦Р РЋРІР‚в„–Р В РІвЂћвЂ“ Р РЋРІР‚РЋР В Р’В°Р РЋР С“Р В РЎвЂўР В Р вЂ Р В РЎвЂўР В РІвЂћвЂ“ Р В РЎвЂ”Р В РЎвЂўР РЋР РЏР РЋР С“)
        tz = pytz.timezone(settings.TIME_ZONE)
        created_time_local = contact_form.created_at.astimezone(tz)
        created_time = created_time_local.strftime('%d.%m.%Y Р В Р вЂ  %H:%M')
        message += f"\n\nР Р†Р РЏР’В° {created_time}"
        
        return message
    
    @classmethod
    def send_test_drive_notification(cls, td):
        """Р В РЎвЂєР РЋРІР‚С™Р В РЎвЂ”Р РЋР вЂљР В Р’В°Р В Р вЂ Р В РЎвЂР РЋРІР‚С™Р РЋР Р‰ Р РЋРЎвЂњР В Р вЂ Р В Р’ВµР В РўвЂР В РЎвЂўР В РЎР В Р’В»Р В Р’ВµР В Р вЂ¦Р В РЎвЂР В Р’Вµ Р В РЎвЂў Р В Р вЂ¦Р В РЎвЂўР В Р вЂ Р В РЎвЂўР В РІвЂћвЂ“ Р В Р’В·Р В Р’В°Р РЋР РЏР В Р вЂ Р В РЎвЂќР В Р’Вµ Р В Р вЂ¦Р В Р’В° Р РЋРІР‚С™Р В Р’ВµР РЋР С“Р РЋРІР‚С™-Р В РўвЂР РЋР вЂљР В Р’В°Р В РІвЂћвЂ“Р В Р вЂ """
        try:
            bot_token = settings.TELEGRAM_BOT_TOKEN
            chat_id = settings.TELEGRAM_CHAT_ID

            if not bot_token or not chat_id:
                logger.warning("Telegram Р В Р вЂ¦Р В Р’В°Р РЋР С“Р РЋРІР‚С™Р РЋР вЂљР В РЎвЂўР В РІвЂћвЂ“Р В РЎвЂќР В РЎвЂ Р В Р вЂ¦Р В Р’Вµ Р В Р’В·Р В Р’В°Р В РўвЂР В Р’В°Р В Р вЂ¦Р РЋРІР‚в„– Р В Р вЂ  .env")
                return

            message = f"РЎР‚РЎСџР РЏР вЂ№ Р В РЎСљР В РЎвЂўР В Р вЂ Р В Р’В°Р РЋР РЏ Р В Р’В·Р В Р’В°Р РЋР РЏР В Р вЂ Р В РЎвЂќР В Р’В° Р В Р вЂ¦Р В Р’В° Р РЋРІР‚С™Р В Р’ВµР РЋР С“Р РЋРІР‚С™-Р В РўвЂР РЋР вЂљР В Р’В°Р В РІвЂћвЂ“Р В Р вЂ  #{td.id}\n"
            message += f"\nРЎР‚РЎСџРІР‚Р’В¤ Р В РЎв„ўР В Р’В»Р В РЎвЂР В Р’ВµР В Р вЂ¦Р РЋРІР‚С™: {td.name}"
            message += f"\nРЎР‚РЎСџРІР‚СљРЎвЂє Р В РЎС›Р В Р’ВµР В Р’В»Р В Р’ВµР РЋРІР‚С›Р В РЎвЂўР В Р вЂ¦: {td.phone}"

            if td.dealer:
                message += f"\nРЎР‚РЎСџР РЏРЎС› Р В РІР‚СњР В РЎвЂР В Р’В»Р В Р’ВµР РЋР вЂљ: {td.dealer.name}"
                if td.dealer.address:
                    message += f"\nРЎР‚РЎСџРІР‚СљР РЉ Р В РЎвЂ™Р В РўвЂР РЋР вЂљР В Р’ВµР РЋР С“: {td.dealer.address}"

            if td.product:
                message += f"\nРЎР‚РЎСџРЎв„ўРІР‚вЂќ Р В РЎС™Р В РЎвЂўР В РўвЂР В Р’ВµР В Р’В»Р РЋР Р‰: {td.product.title}"

            message += f"\nРЎР‚РЎСџРІР‚СљРІР‚В¦ Р В РІР‚СњР В Р’В°Р РЋРІР‚С™Р В Р’В°: {td.preferred_date.strftime('%d.%m.%Y')}"
            message += f"\nРЎР‚РЎСџРІР‚СћРЎвЂ™ Р В РІР‚в„ўР РЋР вЂљР В Р’ВµР В РЎР РЋР РЏ: {td.preferred_time}"

            tz = pytz.timezone(settings.TIME_ZONE)
            created_time = td.created_at.astimezone(tz).strftime('%d.%m.%Y Р В Р вЂ  %H:%M')
            message += f"\n\nР Р†Р РЏР’В° {created_time}"

            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            }

            response = requests.post(url, json=payload, timeout=5)

            if response.status_code == 200:
                logger.info(f"Telegram Р РЋРЎвЂњР В Р вЂ Р В Р’ВµР В РўвЂР В РЎвЂўР В РЎР В Р’В»Р В Р’ВµР В Р вЂ¦Р В РЎвЂР В Р’Вµ Р В РЎвЂўР РЋРІР‚С™Р В РЎвЂ”Р РЋР вЂљР В Р’В°Р В Р вЂ Р В Р’В»Р В Р’ВµР В Р вЂ¦Р В РЎвЂў Р В РўвЂР В Р’В»Р РЋР РЏ Р РЋРІР‚С™Р В Р’ВµР РЋР С“Р РЋРІР‚С™-Р В РўвЂР РЋР вЂљР В Р’В°Р В РІвЂћвЂ“Р В Р вЂ Р В Р’В° #{td.id}")
            else:
                logger.error(f"Р В РЎвЂєР РЋРІвЂљВ¬Р В РЎвЂР В Р’В±Р В РЎвЂќР В Р’В° Telegram {response.status_code} Р В РўвЂР В Р’В»Р РЋР РЏ Р РЋРІР‚С™Р В Р’ВµР РЋР С“Р РЋРІР‚С™-Р В РўвЂР РЋР вЂљР В Р’В°Р В РІвЂћвЂ“Р В Р вЂ Р В Р’В° #{td.id}: {response.text[:200]}")

        except Exception as e:
            logger.error(f"Р В РЎвЂєР РЋРІвЂљВ¬Р В РЎвЂР В Р’В±Р В РЎвЂќР В Р’В° Telegram Р В РўвЂР В Р’В»Р РЋР РЏ Р РЋРІР‚С™Р В Р’ВµР РЋР С“Р РЋРІР‚С™-Р В РўвЂР РЋР вЂљР В Р’В°Р В РІвЂћвЂ“Р В Р вЂ Р В Р’В° #{td.id}: {str(e)}", exc_info=True)

    @staticmethod
    def _build_keyboard(contact_form):
        """Р В Р Р‹Р В РЎвЂўР В Р’В·Р В РўвЂР В Р’В°Р В Р вЂ¦Р В РЎвЂР В Р’Вµ inline-Р В РЎвЂќР В Р вЂ¦Р В РЎвЂўР В РЎвЂ”Р В РЎвЂўР В РЎвЂќ"""
        buttons = []
        
        # Р В РЎв„ўР В Р вЂ¦Р В РЎвЂўР В РЎвЂ”Р В РЎвЂќР В Р’В° amoCRM (Р В Р’ВµР РЋР С“Р В Р’В»Р В РЎвЂ Р РЋРЎвЂњР РЋР С“Р В РЎвЂ”Р В Р’ВµР РЋРІвЂљВ¬Р В Р вЂ¦Р В РЎвЂў Р В РЎвЂўР РЋРІР‚С™Р В РЎвЂ”Р РЋР вЂљР В Р’В°Р В Р вЂ Р В Р’В»Р В Р’ВµР В Р вЂ¦Р В РЎвЂў)
        if contact_form.amocrm_status == 'sent' and contact_form.amocrm_lead_id:
            amocrm_url = f"https://fawtrucks.amocrm.ru/leads/detail/{contact_form.amocrm_lead_id}"
            buttons.append({
                "text": "РЎР‚РЎСџРІР‚СњРІР‚вЂќ Р В РЎвЂєР РЋРІР‚С™Р В РЎвЂќР РЋР вЂљР РЋРІР‚в„–Р РЋРІР‚С™Р РЋР Р‰ Р В Р вЂ  amoCRM",
                "url": amocrm_url
            })
        
        # Р В РЎв„ўР В Р вЂ¦Р В РЎвЂўР В РЎвЂ”Р В РЎвЂќР В Р’В° Р В Р’В°Р В РўвЂР В РЎР В РЎвЂР В Р вЂ¦-Р В РЎвЂ”Р В Р’В°Р В Р вЂ¦Р В Р’ВµР В Р’В»Р В РЎвЂ FAW
        admin_url = f"https://faw.uz/admin/main/contactform/{contact_form.id}/change/"
        buttons.append({
            "text": "Р Р†РЎв„ўРІвЂћСћР С—РЎвЂР РЏ Р В РЎвЂ™Р В РўвЂР В РЎР В РЎвЂР В Р вЂ¦-Р В РЎвЂ”Р В Р’В°Р В Р вЂ¦Р В Р’ВµР В Р’В»Р РЋР Р‰ FAW",
            "url": admin_url
        })
        
        if buttons:
            return {
                "inline_keyboard": [buttons]
            }
        
        return None