# Generated by Django 2.2.1 on 2019-06-17 22:56

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('feeds', '0025_hiddenarticles'),
    ]

    operations = [
        migrations.AlterField(
            model_name='hiddenarticles',
            name='date_hidden',
            field=models.DateTimeField(default=datetime.datetime(2019, 6, 17, 22, 56, 2, 270740, tzinfo=utc)),
        ),
    ]
