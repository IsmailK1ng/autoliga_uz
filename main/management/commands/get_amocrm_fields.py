# main/management/commands/get_amocrm_fields.py

from django.core.management.base import BaseCommand
from main.services.amocrm.token_manager import TokenManager
import requests
from django.conf import settings


class Command(BaseCommand):
    help = 'Р В Р’В Р РЋРЎСџР В Р’В Р РЋРІР‚СћР В Р’В Р вЂ™Р’В»Р В Р Р‹Р РЋРІР‚СљР В Р Р‹Р Р†Р вЂљР Р‹Р В Р’В Р РЋРІР‚Р В Р Р‹Р Р†Р вЂљРЎв„ўР В Р Р‹Р В Р вЂ° Р В Р Р‹Р В РЎвЂњР В Р’В Р РЋРІР‚вЂќР В Р’В Р РЋРІР‚Р В Р Р‹Р В РЎвЂњР В Р’В Р РЋРІР‚СћР В Р’В Р РЋРІР‚Сњ Р В Р’В Р В РІР‚В Р В Р Р‹Р В РЎвЂњР В Р’В Р вЂ™Р’ВµР В Р Р‹Р Р†Р вЂљР’В¦ Р В Р’В Р РЋРІР‚СњР В Р’В Р вЂ™Р’В°Р В Р Р‹Р В РЎвЂњР В Р Р‹Р Р†Р вЂљРЎв„ўР В Р’В Р РЋРІР‚СћР В Р’В Р РЋР В Р’В Р В РІР‚В¦Р В Р Р‹Р Р†Р вЂљРІвЂћвЂ“Р В Р Р‹Р Р†Р вЂљР’В¦ Р В Р’В Р РЋРІР‚вЂќР В Р’В Р РЋРІР‚СћР В Р’В Р вЂ™Р’В»Р В Р’В Р вЂ™Р’ВµР В Р’В Р Р†РІР‚С›РІР‚вЂњ Р В Р’В Р В РІР‚В  amoCRM'

    def handle(self, *args, **options):
        try:
            access_token = TokenManager.get_valid_token()
            
            # Р В Р’В Р РЋРЎСџР В Р Р‹Р В РІР‚С™Р В Р Р‹Р В Р РЏР В Р’В Р РЋР В Р’В Р РЋРІР‚СћР В Р’В Р Р†РІР‚С›РІР‚вЂњ Р В Р’В Р вЂ™Р’В·Р В Р’В Р вЂ™Р’В°Р В Р’В Р РЋРІР‚вЂќР В Р Р‹Р В РІР‚С™Р В Р’В Р РЋРІР‚СћР В Р Р‹Р В РЎвЂњ Р В Р’В Р В РІР‚В Р В Р’В Р РЋР В Р’В Р вЂ™Р’ВµР В Р Р‹Р В РЎвЂњР В Р Р‹Р Р†Р вЂљРЎв„ўР В Р’В Р РЋРІР‚Сћ AmoCRMClient
            url = f"https://{settings.AMOCRM_SUBDOMAIN}.amocrm.ru/api/v4/leads/custom_fields"
            headers = {'Authorization': f'Bearer {access_token}'}
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            fields = response.json().get('_embedded', {}).get('custom_fields', [])
            
            self.stdout.write("\n" + "="*60)
            self.stdout.write("Р В Р’В Р РЋРІвЂћСћР В Р’В Р РЋРІР‚в„ўР В Р’В Р В Р вЂ№Р В Р’В Р РЋРЎвЂєР В Р’В Р РЋРІР‚С”Р В Р’В Р РЋРЎв„ўР В Р’В Р РЋРЎС™Р В Р’В Р вЂ™Р’В«Р В Р’В Р Р†Р вЂљРЎС› Р В Р’В Р РЋРЎСџР В Р’В Р РЋРІР‚С”Р В Р’В Р Р†Р вЂљРЎвЂќР В Р’В Р В РІР‚РЋ Р В Р’В Р Р†Р вЂљРЎвЂќР В Р’В Р В Р’В Р Р†Р вЂљРЎСљР В Р’В Р РЋРІР‚С”Р В Р’В Р Р†Р вЂљРІвЂћСћ Р В Р’В Р Р†Р вЂљРІвЂћСћ amoCRM:")
            self.stdout.write("="*60)
            
            for field in fields:
                field_id = field['id']
                field_name = field['name']
                field_type = field['type']
                
                self.stdout.write(f"\nID: {field_id}")
                self.stdout.write(f"Р В Р’В Р РЋРЎС™Р В Р’В Р вЂ™Р’В°Р В Р’В Р вЂ™Р’В·Р В Р’В Р В РІР‚В Р В Р’В Р вЂ™Р’В°Р В Р’В Р В РІР‚В¦Р В Р’В Р РЋРІР‚Р В Р’В Р вЂ™Р’Вµ: {field_name}")
                self.stdout.write(f"Р В Р’В Р РЋРЎвЂєР В Р’В Р РЋРІР‚Р В Р’В Р РЋРІР‚вЂќ: {field_type}")
                self.stdout.write("-" * 60)
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Р В Р вЂ Р РЋРЎС™Р В Р вЂ° Р В Р’В Р РЋРІР‚С”Р В Р Р‹Р Р†РІР‚С™Р’В¬Р В Р’В Р РЋРІР‚Р В Р’В Р вЂ™Р’В±Р В Р’В Р РЋРІР‚СњР В Р’В Р вЂ™Р’В°: {str(e)}"))