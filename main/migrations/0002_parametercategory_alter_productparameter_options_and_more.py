# main/migrations/0002_parametercategory_alter_productparameter_options_and_more.py

import django.db.models.deletion
from django.db import migrations, models


def create_categories_and_migrate(apps, schema_editor):
    ParameterCategory = apps.get_model('main', 'ParameterCategory')
    ProductParameter = apps.get_model('main', 'ProductParameter')

    # Все 9 категорий — slug совпадает со старым CharField значением
    categories_data = [
        {'slug': 'main',          'name': 'Основные параметры',          'order': 1},
        {'slug': 'engine',        'name': 'Двигатель',                   'order': 2},
        {'slug': 'weight',        'name': 'Весовые параметры',           'order': 3},
        {'slug': 'transmission',  'name': 'Трансмиссия',                 'order': 4},
        {'slug': 'brakes',        'name': 'Система тормозов и шин',      'order': 5},
        {'slug': 'comfort',       'name': 'Удобства',                    'order': 6},
        {'slug': 'superstructure','name': 'Надстройка',                  'order': 7},
        {'slug': 'cabin',         'name': 'Кабина',                      'order': 8},
        {'slug': 'additional',    'name': 'Дополнительные параметры',    'order': 9},
    ]

    # Создаём все категории и запоминаем slug -> id
    slug_to_id = {}
    for data in categories_data:
        obj = ParameterCategory.objects.create(**data)
        slug_to_id[obj.slug] = obj.id

    # Переносим данные: старый текст category -> новый category_id
    for param in ProductParameter.objects.all():
        old_category = param.old_category  # старое CharField
        if old_category and old_category in slug_to_id:
            param.category_id = slug_to_id[old_category]
            param.save()


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_initial'),
    ]

    operations = [
        # 1. Создаём таблицу ParameterCategory
        migrations.CreateModel(
            name='ParameterCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='Nomi')),
                ('slug', models.SlugField(help_text='«Например: двигатель, вес, кабина. Только латинские буквы и тире».', max_length=100, unique=True, verbose_name='«Слуг (кодекс)»')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Порядок')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активен')),
            ],
            options={
                'verbose_name': 'Категория параметра',
                'verbose_name_plural': 'Категории параметров',
                'ordering': ['order', 'name'],
            },
        ),

        # 2. Переименовываем старое поле category -> old_category (чтобы не конфликтовало)
        migrations.RenameField(
            model_name='productparameter',
            old_name='category',
            new_name='old_category',
        ),

        # 3. Добавляем новое поле category как ForeignKey (пока null=True)
        migrations.AddField(
            model_name='productparameter',
            name='category',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='parameters',
                to='main.parametercategory',
                verbose_name='Категория параметра',
            ),
        ),

        # 4. Заполняем ParameterCategory и переносим данные
        migrations.RunPython(
            create_categories_and_migrate,
            reverse_code=migrations.RunPython.noop,
        ),

        # 5. Удаляем старое поле old_category
        migrations.RemoveField(
            model_name='productparameter',
            name='old_category',
        ),

        # 6. Обновляем Meta.ordering
        migrations.AlterModelOptions(
            name='productparameter',
            options={
                'ordering': ['category__order', 'order'],
                'verbose_name': 'Параметр',
                'verbose_name_plural': 'Параметры машины',
            },
        ),
    ]