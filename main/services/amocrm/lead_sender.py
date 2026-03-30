import requests
import logging
from django.utils import timezone
from django.conf import settings
from main.models import AmoCRMToken
from main.services.amocrm.token_manager import TokenManager

logger = logging.getLogger('amocrm')


class LeadSender:

    @classmethod
    def send_lead(cls, contact_form):
        """Р В РЎвЂєР РЋРІР‚С™Р В РЎвЂ”Р РЋР вЂљР В Р’В°Р В Р вЂ Р В РЎвЂќР В Р’В° Р В Р’В»Р В РЎвЂР В РўвЂР В Р’В° Р В Р вЂ  amoCRM"""
        if contact_form.amocrm_status == 'sent' and contact_form.amocrm_lead_id:
            return

        try:
            token_obj = AmoCRMToken.get_instance()

            if token_obj.is_expired():
                TokenManager.refresh_token(token_obj)
                token_obj.refresh_from_db()

            pipeline_id = settings.AMOCRM_PIPELINE_ID
            editable_status = cls._get_editable_status_for_pipeline(token_obj.access_token, pipeline_id)
            
            if editable_status:
                status_to_use = editable_status
            else:
                status_to_use = settings.AMOCRM_STATUS_ID

            lead_data = cls._prepare_lead_data(contact_form, pipeline_id, status_to_use)

            headers = {
                'Authorization': f'Bearer {token_obj.access_token}',
                'Content-Type': 'application/json'
            }

            response = requests.post(
                f'https://{settings.AMOCRM_SUBDOMAIN}.amocrm.ru/api/v4/leads/complex',
                json=lead_data,
                headers=headers,
                timeout=10
            )
            if response.status_code in [200, 201]:
                result = response.json()
                lead_id = cls._extract_lead_id(result)

                if lead_id:
                    contact_form.amocrm_status = 'sent'
                    contact_form.amocrm_lead_id = lead_id
                    contact_form.amocrm_sent_at = timezone.now()
                    contact_form.amocrm_error = None
                    contact_form.save()
                else:
                    raise ValueError("ID Р В Р’В»Р В РЎвЂР В РўвЂР В Р’В° Р В Р вЂ¦Р В Р’Вµ Р В Р вЂ¦Р В Р’В°Р В РІвЂћвЂ“Р В РўвЂР В Р’ВµР В Р вЂ¦ Р В Р вЂ  Р В РЎвЂўР РЋРІР‚С™Р В Р вЂ Р В Р’ВµР РЋРІР‚С™Р В Р’Вµ amoCRM")
            else:
                error_text = cls._parse_error_response(response)
                logger.error(f"Р Р†РЎСљР Р‰ Р В РЎвЂєР РЋРІвЂљВ¬Р В РЎвЂР В Р’В±Р В РЎвЂќР В Р’В° amoCRM {response.status_code}: {error_text}")  
                contact_form.amocrm_status = 'failed'
                contact_form.amocrm_error = error_text[:500]
                contact_form.save()

        except requests.exceptions.Timeout:
            error_text = "Р В РЎС›Р В Р’В°Р В РІвЂћвЂ“Р В РЎР В Р’В°Р РЋРЎвЂњР РЋРІР‚С™ Р РЋР С“Р В РЎвЂўР В Р’ВµР В РўвЂР В РЎвЂР В Р вЂ¦Р В Р’ВµР В Р вЂ¦Р В РЎвЂР РЋР РЏ Р РЋР С“ amoCRM"
            logger.error(f"Р Р†Р РЏР’В±Р С—РЎвЂР РЏ {error_text}") 
            contact_form.amocrm_status = 'failed'
            contact_form.amocrm_error = error_text
            contact_form.save()

        except requests.exceptions.RequestException as e:
            error_text = f"Р В РЎвЂєР РЋРІвЂљВ¬Р В РЎвЂР В Р’В±Р В РЎвЂќР В Р’В° Р В Р’В·Р В Р’В°Р В РЎвЂ”Р РЋР вЂљР В РЎвЂўР РЋР С“Р В Р’В°: {str(e)}"
            logger.error(f"РЎР‚РЎСџР Р‰РЎвЂ™ {error_text}") 
            contact_form.amocrm_status = 'failed'
            contact_form.amocrm_error = error_text[:500]
            contact_form.save()

        except Exception as e:
            error_text = f"{type(e).__name__}: {str(e)}"
            logger.error(f"РЎР‚РЎСџРІР‚в„ўРўС’ Р В РЎв„ўР РЋР вЂљР В РЎвЂР РЋРІР‚С™Р В РЎвЂР РЋРІР‚РЋР В Р’ВµР РЋР С“Р В РЎвЂќР В Р’В°Р РЋР РЏ Р В РЎвЂўР РЋРІвЂљВ¬Р В РЎвЂР В Р’В±Р В РЎвЂќР В Р’В°: {error_text}", exc_info=True)  
            contact_form.amocrm_status = 'failed'
            contact_form.amocrm_error = error_text[:500]
            contact_form.save()

    @staticmethod
    def _get_editable_status_for_pipeline(access_token, pipeline_id):
        """Р В РІР‚в„ўР В РЎвЂўР В Р’В·Р В Р вЂ Р РЋР вЂљР В Р’В°Р РЋРІР‚В°Р В Р’В°Р В Р’ВµР РЋРІР‚С™ Р В РЎвЂ”Р В Р’ВµР РЋР вЂљР В Р вЂ Р РЋРІР‚в„–Р В РІвЂћвЂ“ is_editable=True status_id Р В РўвЂР В Р’В»Р РЋР РЏ pipeline"""
        try:
            url = f'https://{settings.AMOCRM_SUBDOMAIN}.amocrm.ru/api/v4/leads/pipelines/{pipeline_id}/statuses'
            headers = {'Authorization': f'Bearer {access_token}'}
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            statuses = data.get('_embedded', {}).get('statuses', [])
            for s in statuses:
                if s.get('is_editable', False):
                    return s.get('id')
            return None
        except Exception as e:
            logger.error(f"Р В РЎСљР В Р’Вµ Р РЋРЎвЂњР В РўвЂР В Р’В°Р В Р’В»Р В РЎвЂўР РЋР С“Р РЋР Р‰ Р В РЎвЂ”Р В РЎвЂўР В Р’В»Р РЋРЎвЂњР РЋРІР‚РЋР В РЎвЂР РЋРІР‚С™Р РЋР Р‰ Р РЋР С“Р РЋРІР‚С™Р В Р’В°Р РЋРІР‚С™Р РЋРЎвЂњР РЋР С“Р РЋРІР‚в„– pipeline {pipeline_id}: {e}") 
            return None

    @staticmethod
    def _extract_lead_id(result):
        """Р В Р В Р’В·Р В Р вЂ Р В Р’В»Р В Р’ВµР РЋРІР‚РЋР В Р’ВµР В Р вЂ¦Р В РЎвЂР В Р’Вµ ID Р В Р’В»Р В РЎвЂР В РўвЂР В Р’В° Р В РЎвЂР В Р’В· Р В РЎвЂўР РЋРІР‚С™Р В Р вЂ Р В Р’ВµР РЋРІР‚С™Р В Р’В° amoCRM"""
        try:
            if isinstance(result, list) and len(result) > 0:
                first_item = result[0]
                if 'id' in first_item:
                    return first_item['id']
                if '_embedded' in first_item and 'leads' in first_item['_embedded']:
                    leads = first_item['_embedded']['leads']
                    if len(leads) > 0:
                        return leads[0]['id']
            return None
        except (KeyError, IndexError, TypeError) as e:
            logger.error(f"Р Р†РЎСљР Р‰ Р В РЎвЂєР РЋРІвЂљВ¬Р В РЎвЂР В Р’В±Р В РЎвЂќР В Р’В° Р В РЎвЂ”Р В Р’В°Р РЋР вЂљР РЋР С“Р В РЎвЂР В Р вЂ¦Р В РЎвЂ“Р В Р’В° ID Р В Р’В»Р В РЎвЂР В РўвЂР В Р’В°: {str(e)}") 
            return None

    @staticmethod
    def _parse_error_response(response):
        """Р В РЎСџР В Р’В°Р РЋР вЂљР РЋР С“Р В РЎвЂР В Р вЂ¦Р В РЎвЂ“ Р РЋРІР‚С™Р В Р’ВµР В РЎвЂќР РЋР С“Р РЋРІР‚С™Р В Р’В° Р В РЎвЂўР РЋРІвЂљВ¬Р В РЎвЂР В Р’В±Р В РЎвЂќР В РЎвЂ Р В РЎвЂР В Р’В· Р В РЎвЂўР РЋРІР‚С™Р В Р вЂ Р В Р’ВµР РЋРІР‚С™Р В Р’В° amoCRM"""
        try:
            error_data = response.json()
            if 'validation-errors' in error_data:
                errors = error_data['validation-errors']
                if len(errors) > 0 and 'errors' in errors[0]:
                    first_error = errors[0]['errors'][0]
                    return f"{first_error.get('code')}: {first_error.get('detail')}"
            if 'detail' in error_data:
                return error_data['detail']
            if 'title' in error_data:
                return error_data['title']
            return response.text[:200]
        except Exception:
            return response.text[:200]

    @staticmethod
    def _prepare_lead_data(contact_form, pipeline_id, status_id):
        """Р В РЎСџР В РЎвЂўР В РўвЂР В РЎвЂ“Р В РЎвЂўР РЋРІР‚С™Р В РЎвЂўР В Р вЂ Р В РЎвЂќР В Р’В° Р В РўвЂР В Р’В°Р В Р вЂ¦Р В Р вЂ¦Р РЋРІР‚в„–Р РЋРІР‚В¦ Р В Р’В»Р В РЎвЂР В РўвЂР В Р’В° Р В РўвЂР В Р’В»Р РЋР РЏ Р В РЎвЂўР РЋРІР‚С™Р В РЎвЂ”Р РЋР вЂљР В Р’В°Р В Р вЂ Р В РЎвЂќР В РЎвЂ Р В Р вЂ  amoCRM"""
        name_parts = contact_form.name.strip().split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ''

        lead_custom_fields = []

        lead_custom_fields.append({
            "field_id": settings.AMOCRM_FIELD_REGION,
            "values": [{"value": contact_form.get_region_display()}]
        })

        if contact_form.message:
            msg = contact_form.message.strip()
            if len(msg) > 1000:
                msg = msg[:997] + "..."
            lead_custom_fields.append({
                "field_id": settings.AMOCRM_FIELD_MESSAGE,
                "values": [{"value": msg}]
            })

        if contact_form.product:
            lead_custom_fields.append({
                "field_id": settings.AMOCRM_FIELD_PRODUCT,
                "values": [{"value": contact_form.product}]
            })

        if contact_form.referer:
            lead_custom_fields.append({
                "field_id": settings.AMOCRM_FIELD_REFERER,
                "values": [{"value": contact_form.referer[:500]}]
            })

        if contact_form.utm_data:
            lead_custom_fields.append({
                "field_id": settings.AMOCRM_FIELD_UTM,
                "values": [{"value": contact_form.utm_data[:1000]}]
            })

        lead_custom_fields.append({
            "field_id": settings.AMOCRM_FIELD_FORMID,
            "values": [{"value": "Р В РІР‚вЂќР В Р’В°Р РЋР РЏР В Р вЂ Р В РЎвЂќР В Р’В° Р РЋР С“ Р РЋР С“Р В Р’В°Р В РІвЂћвЂ“Р РЋРІР‚С™Р В Р’В° FAW.UZ"}]
        })

        lead_name = f"{contact_form.product} Р Р†Р вЂљРІР‚Сњ {contact_form.name}" if contact_form.product else f"Р В РІР‚вЂќР В Р’В°Р РЋР РЏР В Р вЂ Р В РЎвЂќР В Р’В° Р РЋР С“ Р РЋР С“Р В Р’В°Р В РІвЂћвЂ“Р РЋРІР‚С™Р В Р’В°: {contact_form.name}"

        lead_dict = {
            "name": lead_name,
            "price": 0,
            "pipeline_id": pipeline_id,
            "status_id": status_id,
            "custom_fields_values": lead_custom_fields,
            "_embedded": {
                "tags": [{"name": "Р В Р Р‹Р В Р’В°Р В РІвЂћвЂ“Р РЋРІР‚С™"}, {"name": "FAW.UZ"}],
                "contacts": [{
                    "first_name": first_name,
                    "last_name": last_name,
                    "custom_fields_values": [{
                        "field_code": "PHONE",
                        "values": [{
                            "value": contact_form.phone,
                            "enum_code": "WORK"
                        }]
                    }]
                }]
            }
        }

        if contact_form.visitor_uid:
            lead_dict["visitor_uid"] = contact_form.visitor_uid

        if contact_form.product:
            lead_dict["_embedded"]["tags"].append({"name": contact_form.product[:30]})

        return [lead_dict]