import django.db.models.deletion
from django.db import migrations, models


def create_categories_and_migrate(apps, schema_editor):
    ParameterCategory = apps.get_model('main', 'ParameterCategory')
    ProductParameter = apps.get_model('main', 'ProductParameter')

    categories_data = [
        {'slug': 'main',          'name': 'Asosiy xarakteristikalar', 'order': 1},
        {'slug': 'engine',        'name': 'Dvigatel',                  'order': 2},
        {'slug': 'weight',        'name': "Og'irlik va o'lchamlar",    'order': 3},
        {'slug': 'transmission',  'name': 'Transmissiya',              'order': 4},
        {'slug': 'brakes',        'name': 'Tormoz tizimi',             'order': 5},
        {'slug': 'comfort',       'name': 'Qulaylik',                  'order': 6},
        {'slug': 'superstructure','name': 'Ustki qism',                'order': 7},
        {'slug': 'cabin',         'name': 'Kabina',                    'order': 8},
        {'slug': 'additional',    'name': "Qo'shimcha xususiyatlar",   'order': 9},
    ]

    slug_to_id = {}
    for data in categories_data:
        obj = ParameterCategory.objects.create(**data)
        slug_to_id[obj.slug] = obj.id

    for param in ProductParameter.objects.all():
        old_category = param.old_category
        if old_category and old_category in slug_to_id:
            param.category_id = slug_to_id[old_category]
            param.save()


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_initial'),
    ]

    operations = [
        # 1. ParameterCategory modelini yaratish
        migrations.CreateModel(
            name='ParameterCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Nomi')),
                ('slug', models.SlugField(
                    help_text='Unikal identifikator: lotin harflari, raqamlar, tire. Masalan: engine, main-params.',
                    max_length=100,
                    unique=True,
                    verbose_name='Slug (identifikator)'
                )),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Tartib raqami')),
                ('is_active', models.BooleanField(default=True, verbose_name='Faolmi')),
            ],
            options={
                'verbose_name': 'Parametr kategoriyasi',
                'verbose_name_plural': 'Parametr kategoriyalari',
                'ordering': ['order', 'name'],
            },
        ),

        # 2. ProductParameter modelidagi category -> old_category
        migrations.RenameField(
            model_name='productparameter',
            old_name='category',
            new_name='old_category',
        ),

        # 3. Yangi category ForeignKey qo'shish (null=True)
        migrations.AddField(
            model_name='productparameter',
            name='category',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='parameters',
                to='main.parametercategory',
                verbose_name='Parametr kategoriyasi',
            ),
        ),

        # 4. ParameterCategory larni yaratish va ma'lumotlarni ko'chirish
        migrations.RunPython(
            create_categories_and_migrate,
            reverse_code=migrations.RunPython.noop,
        ),

        # 5. old_category ustunini o'chirish
        migrations.RemoveField(
            model_name='productparameter',
            name='old_category',
        ),

        # 6. Meta.ordering yangilash
        migrations.AlterModelOptions(
            name='productparameter',
            options={
                'ordering': ['category__order', 'order'],
                'verbose_name': 'Mahsulot parametri',
                'verbose_name_plural': 'Mahsulot parametrlari',
            },
        ),
    ]