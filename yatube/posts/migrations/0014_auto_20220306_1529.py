# Generated by Django 2.2.16 on 2022-03-06 15:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0013_auto_20220305_1400'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='image',
            field=models.ImageField(blank=True, help_text='Загрузите изображение', upload_to='posts/', verbose_name='Изображение'),
        ),
    ]