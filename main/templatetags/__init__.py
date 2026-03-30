# main/serializers.py



from rest_framework import serializers

import logging



logger = logging.getLogger('django')

from main.serializers_base import LanguageSerializerMixin



from .models import (

    News, NewsBlock, ContactForm, JobApplication,

    Product, FeatureIcon, ProductCardSpec, ProductParameter, ProductFeature, ProductGallery, ProductCategory,

    Vacancy, VacancyResponsibility, VacancyRequirement, VacancyCondition, VacancyIdealCandidate,

    Review, TestDriveRequest

)





# ========== Р В Р’В Р РЋРЎС™Р В Р’В Р РЋРІР‚С”Р В Р’В Р Р†Р вЂљРІвЂћСћР В Р’В Р РЋРІР‚С”Р В Р’В Р В Р вЂ№Р В Р’В Р РЋРЎвЂєР В Р’В 