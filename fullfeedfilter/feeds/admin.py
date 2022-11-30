from django.contrib import admin
from .models import Feeds, Filters, ArticleScrapers, FeedValidation, ArticleRecords


class FeedsAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'folder', 'name', 'url', 'scraper']


class FiltersAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'feed', 'keyword', '__str__']


class FeedValidationAdmin(admin.ModelAdmin):
    list_display = ['feed', 'error', 'ignore']


class ArticleRecordsAdmin(admin.ModelAdmin):
    list_display = ['feed', 'title', 'scraper', 'full_article', 'full_article_retries', 'hidden']


admin.site.register(Feeds, FeedsAdmin)
admin.site.register(Filters, FiltersAdmin)
admin.site.register(ArticleScrapers)
admin.site.register(FeedValidation, FeedValidationAdmin)
admin.site.register(ArticleRecords, ArticleRecordsAdmin)
