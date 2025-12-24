from modeltranslation.translator import register, TranslationOptions
from .models import (
    News, NewsBlock, Vacancy, 
    VacancyResponsibility, VacancyRequirement, VacancyCondition, VacancyIdealCandidate,
    Product, ProductFeature, ProductCardSpec, ProductParameter,
    ProductCategory,  # ✅ НОВОЕ
    FeatureIcon,
)

# ========== НОВОСТИ ==========
@register(News)
class NewsTranslationOptions(TranslationOptions):
    fields = ('title', 'desc')


@register(NewsBlock)
class NewsBlockTranslationOptions(TranslationOptions):
    fields = ('title', 'text')


# ========== ВАКАНСИИ ==========
@register(Vacancy)
class VacancyTranslationOptions(TranslationOptions):
    fields = ('title', 'short_description', 'contact_info')


@register(VacancyResponsibility)
class VacancyResponsibilityTranslationOptions(TranslationOptions):
    fields = ('title', 'text')


@register(VacancyRequirement)
class VacancyRequirementTranslationOptions(TranslationOptions):
    fields = ('text',)


@register(VacancyCondition)
class VacancyConditionTranslationOptions(TranslationOptions):
    fields = ('text',)


@register(VacancyIdealCandidate)
class VacancyIdealCandidateTranslationOptions(TranslationOptions):
    fields = ('text',)



# ========== КАТЕГОРИИ ПРОДУКТОВ ==========
@register(ProductCategory)
class ProductCategoryTranslationOptions(TranslationOptions):
    fields = ('name', 'description')

# ========== ПРОДУКТЫ ==========
@register(Product)
class ProductTranslationOptions(TranslationOptions):
    fields = (
        'title',
        'slider_price',
        'slider_power',
        'slider_fuel_consumption',
    )

@register(ProductFeature)
class ProductFeatureTranslationOptions(TranslationOptions):
    fields = ('name',)


@register(ProductCardSpec)
class ProductCardSpecTranslationOptions(TranslationOptions):
    fields = ('value',)


@register(ProductParameter)
class ProductParameterTranslationOptions(TranslationOptions):
    fields = ('text',)
