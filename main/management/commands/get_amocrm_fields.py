# main/management/commands/get_amocrm_fields.py

from django.core.management.base import BaseCommand
from main.services.amocrm.token_manager import TokenManager
import requests
from django.conf import settings


class Command(BaseCommand):
    help = 'Р В РЎСџР В РЎвЂўР В Р’В»Р РЋРЎвЂњР РЋРІР‚РЋР В РЎвЂР РЋРІР‚С™Р РЋР Р‰ Р РЋР С“Р В РЎвЂ”Р В РЎвЂР РЋР С“Р В РЎвЂўР В РЎвЂќ Р В Р вЂ Р РЋР С“Р В Р’ВµР РЋРІР‚В¦ Р В РЎвЂќР В Р’В°Р РЋР С“Р РЋРІР‚С™Р В РЎвЂўР В РЎР В Р вЂ¦Р РЋРІР‚в„–Р РЋРІР‚В¦ Р В РЎвЂ”Р В РЎвЂўР В Р’В»Р В Р’ВµР В РІвЂћвЂ“ Р В Р вЂ  amoCRM'

    def handle(self, *args, **options):
        try:
            access_token = TokenManager.get_valid_token()
            
            # Р В РЎСџР РЋР вЂљР РЋР РЏР В РЎР В РЎвЂўР В РІвЂћвЂ“ Р В Р’В·Р В Р’В°Р В РЎвЂ”Р РЋР вЂљР В РЎвЂўР РЋР С“ Р В Р вЂ Р В РЎР В Р’ВµР РЋР С“Р РЋРІР‚С™Р В РЎвЂў AmoCRMClient
            url = f"https://{settings.AMOCRM_SUBDOMAIN}.amocrm.ru/api/v4/leads/custom_fields"
            headers = {'Authorization': f'Bearer {access_token}'}
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            fields = response.json().get('_embedded', {}).get('custom_fields', [])
            
            self.stdout.write("\n" + "="*60)
            self.stdout.write("Р В РЎв„ўР В РЎвЂ™Р В Р Р‹Р В РЎС›Р В РЎвЂєР В РЎС™Р В РЎСљР В Р’В«Р В РІР‚Сћ Р В РЎСџР В РЎвЂєР В РІР‚С”Р В Р вЂЎ Р В РІР‚С”Р В Р В РІР‚СњР В РЎвЂєР В РІР‚в„ў Р В РІР‚в„ў amoCRM:")
            self.stdout.write("="*60)
            
            for field in fields:
                field_id = field['id']
                field_name = field['name']
                field_type = field['type']
                
                self.stdout.write(f"\nID: {field_id}")
                self.stdout.write(f"Р В РЎСљР В Р’В°Р В Р’В·Р В Р вЂ Р В Р’В°Р В Р вЂ¦Р В РЎвЂР В Р’Вµ: {field_name}")
                self.stdout.write(f"Р В РЎС›Р В РЎвЂР В РЎвЂ”: {field_type}")
                self.stdout.write("-" * 60)
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Р Р†РЎСљР Р‰ Р В РЎвЂєР РЋРІвЂљВ¬Р В РЎвЂР В Р’В±Р В РЎвЂќР В Р’В°: {str(e)}"))