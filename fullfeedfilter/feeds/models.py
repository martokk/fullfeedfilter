from django.contrib.auth.models import User
from django.db import models
from django.template.defaultfilters import slugify
from django.urls import reverse, reverse_lazy


class ArticleScrapers(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class Feeds(models.Model):
    name = models.CharField(max_length=150)
    url = models.URLField()
    slug = models.SlugField(default="", editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    scraper = models.ForeignKey(ArticleScrapers, on_delete=models.SET_DEFAULT, default=1)
    folder = models.CharField(max_length=50, default="None")
    remove_text = models.CharField(max_length=250, blank=True)
    stop_html = models.CharField(max_length=250, blank=True)
    report_hidden_articles = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Feeds, self).save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("feed_view", args=(self.pk,))


class Filters(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    feed = models.ForeignKey(Feeds, on_delete=models.CASCADE)
    keyword = models.CharField(max_length=50)
    condition = models.CharField(
        max_length=10,
        choices=(
            ("in", "in"),
            ("not_in", "not in"),
        ),
    )
    source = models.CharField(
        max_length=10,
        choices=(
            ("feed", "Feed"),
            ("title", "Title"),
            ("body", "Body"),
            ("link", "Link"),
            ("tag", "Tags"),
        ),
    )
    action = models.CharField(
        max_length=10,
        choices=(
            ("hide", "Hide Article"),
            ("show", "Show Article"),
        ),
    )

    class Meta:
        unique_together = ("feed", "keyword", "condition", "source")

    def save(self, *args, **kwargs):
        self.keyword = self.keyword.lower()
        return super(Filters, self).save(*args, **kwargs)

    def __str__(self):
        return f"IF [{self.keyword}] [{self.condition}] [{self.source}]; THEN [{self.action}]"

    def get_absolute_url(self):
        return reverse_lazy("feed_view", kwargs={"pk": self.feed_id}, current_app="feeds")


class FeedValidation(models.Model):
    feed = models.ForeignKey(Feeds, on_delete=models.CASCADE)
    error = models.CharField(max_length=250)
    ignore = models.BooleanField(default=False)


class ArticleRecords(models.Model):
    feed = models.ForeignKey(Feeds, on_delete=models.CASCADE)
    url = models.URLField()
    title = models.CharField(max_length=250)
    pub_date = models.CharField(max_length=50)
    date_added = models.DateTimeField(auto_now_add=True)

    scraper = models.ForeignKey(ArticleScrapers, on_delete=models.CASCADE, default=None)
    description = models.TextField(blank=True, null=True)
    tags = models.TextField(blank=True, null=True)

    full_article = models.BooleanField(default=False)
    full_article_retries = models.IntegerField(default=0)

    hidden = models.BooleanField(default=False)
    hidden_date = models.DateTimeField(blank=True, null=True)
    hidden_active_keywords = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.title
