# main/management/commands/get_amocrm_fields.py

from django.core.management.base import BaseCommand
from main.services.amocrm.token_manager import TokenManager
import requests
from django.conf import settings


class Command(BaseCommand):
    help = "amoCRM custom fields olish uchun command"

    def handle(self, *args, **options):
        try:
            access_token = TokenManager.get_valid_token()
            
            url = f"https://{settings.AMOCRM_SUBDOMAIN}.amocrm.ru/api/v4/leads/custom_fields"
            headers = {'Authorization': f'Bearer {access_token}'}
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            fields = response.json().get('_embedded', {}).get('custom_fields', [])
            
            self.stdout.write("\n" + "="*60)
            self.stdout.write("amoCRM custom fields:")
            for field in fields:
                self.stdout.write(f"{field.get('name')} ({field.get('id')})")
            self.stdout.write("="*60 + "\n")
            
        except Exception as e:
            self.stderr.write(f"Xatolik: {e}")