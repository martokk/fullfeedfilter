import html
import threading
import traceback
from html import unescape

from django.template.loader import render_to_string

from feeds.models import Feeds
from general.scripts import utils
from feeds.scripts.feed_validation import Feedparser
from full_feed_filter.settings import DOMAIN
from .build_article import Article


class BuildFeed:
    def __init__(self, feed: Feeds, verbose=False, rebuild_full_articles=False, article_id=None, article_url=None,
                 max_articles=None, verbose_article=False, threaded=True) -> None:
        # Objects
        self.feed = feed
        self.article_id_limit = article_id
        self.article_url_limit = article_url
        self.max_articles_limit = max_articles
        self.errors = []
        self.threaded = threaded
        try:
            self.feedparser = Feedparser(url=self.feed.url)
        except AttributeError as e:
            self.handle_exception(e)
            return
        self.rebuild_full_articles = rebuild_full_articles

        # Attributes
        self.verbose = verbose
        self.verbose_article = verbose_article
        self.rss_folder = utils.get_rss_folder(feed_id=self.feed.id)

        # Filter Articles
        self.all_articles = []
        self.show_articles = []
        self.hide_articles = []
        self.articles = self.build_articles_object()
        self.filter_articles()

    def vprint(self, message: str) -> print:
        if self.verbose:
            return print(message)

    def handle_exception(self, exception: Exception) -> None:
        tb = traceback.format_exc()
        self.errors.append({
            'feed_id': self.feed.id,
            'feed_name': self.feed.name,
            'article_url': '',
            'article_title:': '',
            'exception': exception,
            'traceback': tb,
        })

    def build_article(self, i, feedparser_entry, entries, articles):

        # Check Article Limits
        if self.article_id_limit:
            if i != self.article_id_limit:
                return
        if self.article_url_limit:
            if feedparser_entry.link not in self.article_url_limit and self.article_url_limit not in feedparser_entry.link:
                return
        if self.max_articles_limit:
            if i > self.max_articles_limit:
                return

        # Build Article
        if self.verbose_article:
            self.vprint(f"  - ({i} of {len(entries)}) URL:{feedparser_entry.link}")

        full_filtered_article = Article(feedparser_entry=feedparser_entry,
                                        feed=self.feed,
                                        rebuild_full_article=self.rebuild_full_articles)

        if full_filtered_article.errors:
            self.errors += full_filtered_article.errors

        articles.append(full_filtered_article)

    def build_articles_object(self) -> list:
        entries = self.feedparser.feedparser['entries']
        thread_list = []
        articles = []

        if self.threaded:
            for i, feedparser_entry in enumerate(entries, start=1):
                t = threading.Thread(target=self.build_article, args=(i, feedparser_entry, entries, articles))
                thread_list.append(t)

            for thread in thread_list:
                thread.start()

            for thread in thread_list:
                thread.join()
        else:
            for i, feedparser_entry in enumerate(entries, start=1):
                self.build_article(i, feedparser_entry, entries, articles)

        return articles

    def filter_articles(self) -> None:
        for article in self.articles:
            if not article.hidden:
                self.show_articles.append(article)

    def print_hidden_and_shown_articles(self) -> None:
        self.vprint("")
        self.vprint("")
        self.vprint("HIDDEN")
        for article in self.hide_articles:
            self.vprint(f"{article.title}")
            if article.hide_filters:
                for hide_filter in article.hide_filters:
                    self.vprint(f"    -- HIDE: '{hide_filter.keyword}' {hide_filter.condition} {hide_filter.source}")

        self.vprint("")
        self.vprint("")
        self.vprint("SHOWN")
        for article in self.show_articles:
            self.vprint(f"{article.title}")
            if article.show_filters:
                for show_filter in article.show_filters:
                    self.vprint(f"    -- SHOW: '{show_filter.keyword}' {show_filter.condition} {show_filter.source}")

    def write_feeds_to_file(self) -> None:
        # self.vprint(f"Saving filtered feed for feed (feed_id={self.feed.id}).")
        utils.mkdir_if_doesnt_exist(directory=self.rss_folder)

        feed_title = f"{self.feed.name} - (Filtered)"
        self.write_feed_to_file(filename='rss.xml', feed_title=feed_title, articles=self.show_articles)

    def write_feed_to_file(self, filename, articles, feed_title=None) -> None:
        xml_link = f"http://{DOMAIN}/{self.feed.user.username}/{self.feed.slug}/"''
        feed_title = self.feed.name if feed_title is None else feed_title

        context = {
            'xml_link': html.escape(xml_link),
            'title': html.escape(feed_title),
            'link': html.escape(self.feed.url),
            'description': html.escape(self.feedparser.description),
            'articles': articles,
        }

        rss_string = render_to_string('rss/rss.xml', context)

        rss_string = unescape(rss_string)
        with open(f'{self.rss_folder}{filename}', 'w') as fp:
            fp.write(str(rss_string.encode('ascii', 'ignore').decode()))
