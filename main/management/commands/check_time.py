# main/management/commands/check_time.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from main.models import AmoCRMToken
import requests
from django.conf import settings


class Command(BaseCommand):
    help = 'Р В РЎСџР РЋР вЂљР В РЎвЂўР В Р вЂ Р В Р’ВµР РЋР вЂљР В РЎвЂР РЋРІР‚С™Р РЋР Р‰ Р РЋР С“Р В РЎвЂР В Р вЂ¦Р РЋРІР‚В¦Р РЋР вЂљР В РЎвЂўР В Р вЂ¦Р В РЎвЂР В Р’В·Р В Р’В°Р РЋРІР‚В Р В РЎвЂР РЋР вЂ№ Р В Р вЂ Р РЋР вЂљР В Р’ВµР В РЎР В Р’ВµР В Р вЂ¦Р В РЎвЂ Django Р РЋР С“ amoCRM'

    def handle(self, *args, **options):
        # 1. Р В РІР‚в„ўР РЋР вЂљР В Р’ВµР В РЎР РЋР РЏ Django
        django_time = timezone.now()
        self.stdout.write(f"РЎР‚РЎСџРЎвЂ™Р РЉ Django Р В Р вЂ Р РЋР вЂљР В Р’ВµР В РЎР РЋР РЏ: {django_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        
        # 2. Р В РІР‚в„ўР РЋР вЂљР В Р’ВµР В РЎР РЋР РЏ Р РЋРІР‚С™Р В РЎвЂўР В РЎвЂќР В Р’ВµР В Р вЂ¦Р В Р’В°
        token_obj = AmoCRMToken.get_instance()
        self.stdout.write(f"Р Р†Р РЏР’В° Р В РЎС›Р В РЎвЂўР В РЎвЂќР В Р’ВµР В Р вЂ¦ Р В РЎвЂР РЋР С“Р РЋРІР‚С™Р В Р’ВµР В РЎвЂќР В Р’В°Р В Р’ВµР РЋРІР‚С™: {token_obj.expires_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 3. Р В РІР‚в„ўР РЋР вЂљР В Р’ВµР В РЎР РЋР РЏ amoCRM (Р РЋРІР‚РЋР В Р’ВµР РЋР вЂљР В Р’ВµР В Р’В· API)
        try:
            url = f"https://{settings.AMOCRM_SUBDOMAIN}.amocrm.ru/api/v4/account"
            headers = {'Authorization': f'Bearer {token_obj.access_token}'}
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # amoCRM Р В Р вЂ Р В РЎвЂўР В Р’В·Р В Р вЂ Р РЋР вЂљР В Р’В°Р РЋРІР‚В°Р В Р’В°Р В Р’ВµР РЋРІР‚С™ Unix timestamp Р В Р вЂ  Р В Р’В·Р В Р’В°Р В РЎвЂ“Р В РЎвЂўР В Р’В»Р В РЎвЂўР В Р вЂ Р В РЎвЂќР В Р’В°Р РЋРІР‚В¦
            server_time = response.headers.get('Date')
            self.stdout.write(f"Р Р†Р С“Р С—РЎвЂР РЏ  amoCRM Р В Р вЂ Р РЋР вЂљР В Р’ВµР В РЎР РЋР РЏ: {server_time}")
            
            self.stdout.write(self.style.SUCCESS("\nР Р†РЎС™РІР‚В¦ Р В РЎСџР РЋР вЂљР В РЎвЂўР В Р вЂ Р В Р’ВµР РЋР вЂљР В РЎвЂќР В Р’В° Р В Р’В·Р В Р’В°Р В Р вЂ Р В Р’ВµР РЋР вЂљР РЋРІвЂљВ¬Р В Р’ВµР В Р вЂ¦Р В Р’В°!"))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Р Р†РЎСљР Р‰ Р В РЎвЂєР РЋРІвЂљВ¬Р В РЎвЂР В Р’В±Р В РЎвЂќР В Р’В°: {str(e)}"))