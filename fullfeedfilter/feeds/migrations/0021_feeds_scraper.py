# Generated by Django 2.2.1 on 2019-06-13 02:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('feeds', '0020_articlescrapers'),
    ]

    operations = [
        migrations.AddField(
            model_name='feeds',
            name='scraper',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.SET_DEFAULT, to='feeds.ArticleScrapers'),
        ),
    ]
