# Generated by Django 2.2.16 on 2022-03-02 16:51

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0008_comment'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='comment',
            options={'ordering': ('created',)},
        ),
    ]
