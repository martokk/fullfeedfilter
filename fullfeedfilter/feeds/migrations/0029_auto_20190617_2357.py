# Generated by Django 2.2.1 on 2019-06-17 23:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('feeds', '0028_auto_20190617_2303'),
    ]

    operations = [
        migrations.RenameField(
            model_name='hiddenarticles',
            old_name='active_hidden_filters_ul',
            new_name='active_hidden_filters_keywords',
        ),
    ]
