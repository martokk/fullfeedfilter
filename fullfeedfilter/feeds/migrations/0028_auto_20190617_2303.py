# Generated by Django 2.2.1 on 2019-06-17 23:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feeds', '0027_auto_20190617_2256'),
    ]

    operations = [
        migrations.AlterField(
            model_name='hiddenarticles',
            name='date_hidden',
            field=models.DateTimeField(),
        ),
    ]
