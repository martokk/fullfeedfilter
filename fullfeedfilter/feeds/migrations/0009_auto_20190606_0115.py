# Generated by Django 2.2.1 on 2019-06-06 01:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feeds', '0008_auto_20190606_0045'),
    ]

    operations = [
        migrations.AlterField(
            model_name='filters',
            name='keyword',
            field=models.CharField(max_length=15),
        ),
    ]
