from modeltranslation.translator import register, TranslationOptions
from main.models import *

# ========== Р В РЎСљР В РЎвЂєР В РІР‚в„ўР В РЎвЂєР В Р Р‹Р В РЎС›Р В  ==========
@register(News)
class NewsTranslationOptions(TranslationOptions):
    fields = ('title', 'desc')


@register(NewsBlock)
class NewsBlockTranslationOptions(TranslationOptions):
    fields = ('title', 'text')


# ========== Р В РІР‚в„ўР В РЎвЂ™Р В РЎв„ўР В РЎвЂ™Р В РЎСљР В Р Р‹Р В Р В  ==========
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



# ========== Р В РЎв„ўР В РЎвЂ™Р В РЎС›Р В РІР‚СћР В РІР‚СљР В РЎвЂєР В Р’В Р В Р В  Р В РЎСџР В Р’В Р В РЎвЂєР В РІР‚СњР В Р в‚¬Р В РЎв„ўР В РЎС›Р В РЎвЂєР В РІР‚в„ў ==========
@register(ProductCategory)
class ProductCategoryTranslationOptions(TranslationOptions):
    fields = ('name', 'description')

# ========== Р В РЎСџР В Р’В Р В РЎвЂєР В РІР‚СњР В Р в‚¬Р В РЎв„ўР В РЎС›Р В Р’В« ==========
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

@register(ParameterCategory)
class ParameterCategoryTranslationOptions(TranslationOptions):
    fields = ('name',)      

# ========== DILERLAR ==========
@register(Dealer)
class DealerTranslationOptions(TranslationOptions):
    fields = ('name', 'address', 'working_hours', 'description')

@register(DealerImage)
class DealerImageTranslationOptions(TranslationOptions):
    fields = ('caption',)

# ========== Р В РЎв„ўР В РЎвЂєР В РЎС™Р В РЎвЂ™Р В РЎСљР В РІР‚СњР В РЎвЂ™ ==========
@register(BranchManager)
class BranchManagerTranslationOptions(TranslationOptions):
    fields = ('full_name', 'position')