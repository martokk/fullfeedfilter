from datetime import timedelta

from django.contrib.auth.models import User
from django.utils.timezone import now

from feeds.models import Feeds, ArticleRecords
from general.scripts import utils


class HiddenArticleViewer:

    def __init__(self, user: User, timedelta_hours: int, feed_id=None) -> None:
        self.user = user
        self.timedelta_hours = timedelta_hours
        self.total_hidden_count = 0

        if feed_id:
            self.feeds_to_retrieve_hidden_articles_from = \
                Feeds.objects.filter(id=feed_id)
        else:
            self.feeds_to_retrieve_hidden_articles_from = \
                Feeds.objects.filter(user=user).order_by('-report_hidden_articles', 'name')

    def get_single_feed_hidden_articles(self, feed: Feeds) -> dict:
        """ Returns a dict with all hidden articles for a single feed. """

        # Build Objects
        date_hidden_timedelta = now() - timedelta(hours=self.timedelta_hours)
        feeds_hidden_articles = {}
        hidden_articles = ArticleRecords.objects.filter(feed=feed,
                                                        hidden=True,
                                                        hidden_date__gte=date_hidden_timedelta)

        # Build Return
        if hidden_articles:
            self.total_hidden_count += hidden_articles.count()
            feeds_hidden_articles = {
                'feed': feed,
                'articles': hidden_articles,
                'count': hidden_articles.count(),
            }
        return feeds_hidden_articles

    def get_feeds_with_hidden_articles(self, feeds_to_check: Feeds.objects) -> list:
        """ Returns a list of feeds containing hidden articles """
        feeds_with_hidden_articles = []

        # Loop through all user's feeds
        for feed in feeds_to_check:
            single_feed_hidden_articles = self.get_single_feed_hidden_articles(feed)

            if single_feed_hidden_articles:
                feeds_with_hidden_articles.append(single_feed_hidden_articles)

        return feeds_with_hidden_articles

    def get_total_hidden_count(self) -> int:
        """ Returns a total of hidden articles for all feeds """
        return self.total_hidden_count

    def get_context(self) -> dict:
        """ Generates and returns the context data for all feeds with hidden articles. """
        return {
            'hidden_articles': self.get_feeds_with_hidden_articles(self.feeds_to_retrieve_hidden_articles_from),
            'total_hidden': self.get_total_hidden_count(),
            'build_date': utils.now_cst(),
            'user': self.user.username,
            'timedelta_hours': self.timedelta_hours,
        }
