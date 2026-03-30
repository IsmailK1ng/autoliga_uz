# main/management/commands/save_amocrm_tokens.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from main.models import AmoCRMToken


class Command(BaseCommand):
    help = 'Р В Р Р‹Р В РЎвЂўР РЋРІР‚В¦Р РЋР вЂљР В Р’В°Р В Р вЂ¦Р В РЎвЂР РЋРІР‚С™Р РЋР Р‰ Р РЋРІР‚С™Р В РЎвЂўР В РЎвЂќР В Р’ВµР В Р вЂ¦Р РЋРІР‚в„– amoCRM Р В РЎвЂР В Р’В· Postman Р В Р вЂ  Р В РІР‚Р В РІР‚Сњ'

    def handle(self, *args, **options):
        self.stdout.write("РЎР‚РЎСџРІР‚СљРЎСљ Р В РІР‚в„ўР В Р вЂ Р В Р’ВµР В РўвЂР В РЎвЂР РЋРІР‚С™Р В Р’Вµ Р РЋРІР‚С™Р В РЎвЂўР В РЎвЂќР В Р’ВµР В Р вЂ¦Р РЋРІР‚в„–:\n")
        
        access_token = input("Access Token: ").strip()
        refresh_token = input("Refresh Token: ").strip()
        
        if not access_token or not refresh_token:
            self.stdout.write(self.style.ERROR("Р Р†РЎСљР Р‰ Р В РЎС›Р В РЎвЂўР В РЎвЂќР В Р’ВµР В Р вЂ¦Р РЋРІР‚в„– Р В Р вЂ¦Р В Р’Вµ Р В РЎР В РЎвЂўР В РЎвЂ“Р РЋРЎвЂњР РЋРІР‚С™ Р В Р’В±Р РЋРІР‚в„–Р РЋРІР‚С™Р РЋР Р‰ Р В РЎвЂ”Р РЋРЎвЂњР РЋР С“Р РЋРІР‚С™Р РЋРІР‚в„–Р В РЎР В РЎвЂ!"))
            return
        
        # Р В Р Р‹Р В РЎвЂўР РЋРІР‚В¦Р РЋР вЂљР В Р’В°Р В Р вЂ¦Р РЋР РЏР В Р’ВµР В РЎ
        token_obj = AmoCRMToken.get_instance()
        token_obj.access_token = access_token
        token_obj.refresh_token = refresh_token
        token_obj.expires_at = timezone.now() + timedelta(hours=24)
        token_obj.save()
        
        self.stdout.write(self.style.SUCCESS(
            f"Р Р†РЎС™РІР‚В¦ Р В РЎС›Р В РЎвЂўР В РЎвЂќР В Р’ВµР В Р вЂ¦Р РЋРІР‚в„– Р РЋРЎвЂњР РЋР С“Р В РЎвЂ”Р В Р’ВµР РЋРІвЂљВ¬Р В Р вЂ¦Р В РЎвЂў Р РЋР С“Р В РЎвЂўР РЋРІР‚В¦Р РЋР вЂљР В Р’В°Р В Р вЂ¦Р В Р’ВµР В Р вЂ¦Р РЋРІР‚в„–!\n"
            f"Р В Р РЋР С“Р РЋРІР‚С™Р В Р’ВµР В РЎвЂќР В Р’В°Р РЋР вЂ№Р РЋРІР‚С™: {token_obj.expires_at.strftime('%d.%m.%Y %H:%M')}"
        ))