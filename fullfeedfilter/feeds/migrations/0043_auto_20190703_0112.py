# Generated by Django 2.2.3 on 2019-07-03 01:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('feeds', '0042_auto_20190701_1836'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='hiddenarticles',
            name='feed',
        ),
        migrations.DeleteModel(
            name='FullArticles',
        ),
        migrations.DeleteModel(
            name='HiddenArticles',
        ),
    ]
