# Generated by Django 2.2.1 on 2019-06-18 15:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('feeds', '0030_auto_20190618_0022'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='filters',
            unique_together={('feed', 'keyword', 'condition', 'source')},
        ),
    ]
