# Generated by Django 2.2.1 on 2019-06-26 17:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feeds', '0036_auto_20190621_1634'),
    ]

    operations = [
        migrations.AddField(
            model_name='fullarticles',
            name='successful',
            field=models.BooleanField(default=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='fullarticles',
            name='tries',
            field=models.IntegerField(default=1),
        ),
    ]
