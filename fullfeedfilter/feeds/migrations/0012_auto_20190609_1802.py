# Generated by Django 2.2.2 on 2019-06-09 18:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feeds', '0011_auto_20190609_1753'),
    ]

    operations = [
        migrations.AlterField(
            model_name='feeds',
            name='name',
            field=models.CharField(max_length=38),
        ),
    ]
