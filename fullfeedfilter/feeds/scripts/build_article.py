import email.utils
import html
import re
import time
import traceback
from datetime import datetime

import feedparser
import newspaper
from django.utils.timezone import now
from feeds.models import ArticleRecords, ArticleScrapers, Feeds, Filters
from feeds.scripts.build_snippets import Snippets
from feeds.scripts.scrapers import CraigslistScraper, RedditScraper, SimpleScraper
from full_feed_filter.settings import DOMAIN
from general.scripts import utils

""" markdown
# TODO:
    - Create Custom Exception Classes
    - Re-filter (similar to re-build)
    
"""


class FeedNotResolved(Exception):
    def __init__(self, message, value):
        super().__init__()
        self.message = message
        self.value = value

    def __str__(self):
        return f"FeedNotResolved: {self.message}: args={self.value}"


class Article:
    def __init__(
        self, feedparser_entry: feedparser, feed: Feeds, rebuild_full_article=False
    ) -> None:

        # Objects
        self.feed = feed
        self.errors = []

        # Article - Attributes
        self.title = None
        self.link = None
        self.pub_date = None

        self.scraper = None
        self.tags = []
        self.description = None

        self.active_hide_filters = None
        self.active_show_filters = None
        self.hidden = False
        self.hidden_date = None
        self.hidden_active_keywords = None

        self.full_article = False
        self.full_article_retries = 0

        # Article Objects
        self._rebuild_full_article = rebuild_full_article

        try:
            self._feedparser_article = FeedParserArticle(feedparser_article=feedparser_entry)
            self._url = self._feedparser_article.get_link()
        except FeedNotResolved as e:
            self._handle_exception(e, show_tb=False)
            return

        self._database_article = None
        self._scraper_article = ScraperArticle()

        # Build Article
        self._main()

    def _handle_exception(self, exception: Exception, show_tb=False) -> None:
        tb = traceback.format_exc() if show_tb else None
        self.errors.append(
            {
                "feed_id": self.feed.id,
                "feed_name": self.feed.name,
                "article_url": self.link,
                "article_title:": self.title,
                "exception": exception,
                "traceback": tb,
            }
        )

    def _main(self):
        db_record = ArticleRecords.objects.filter(url=self._url, feed=self.feed)

        # Load From Database
        if db_record.exists():
            self._database_article = db_record.first()
            self._update_article_attributes_from_database()
            if not self.hidden and self._update_article_attributes_from_scraper():

                self._sanitize_article_attributes()
                self._update_article_filter_attributes()
                self._append_article_snippets_to_description()

                self._update_or_create_record()

        # Load from RSS and/or Scraper
        else:
            self._update_article_attributes_from_feedparser()
            self._update_article_attributes_from_scraper()
            self._sanitize_article_attributes()
            self._update_article_filter_attributes()
            self._append_article_snippets_to_description()

            self._database_article = self._update_or_create_record()

    def _create_new_article_record(self):
        self._update_article_attributes_from_feedparser()
        self._update_article_attributes_from_scraper()
        self._sanitize_article_attributes()
        self._update_article_filter_attributes()
        self._append_article_snippets_to_description()

        return self._update_or_create_record()

    def _update_or_create_record(self):
        record = {
            "feed": self.feed,
            "url": self.link,
            "title": self.title,
            "pub_date": self.pub_date,
            "scraper": self.scraper,
            "description": self.description,
            "tags": utils.convert_list_to_string(self.tags),
            "full_article": self.full_article,
            "full_article_retries": self.full_article_retries,
            "hidden": self.hidden,
            "hidden_date": self.hidden_date,
            "hidden_active_keywords": self.hidden_active_keywords,
        }

        db_record = ArticleRecords.objects.filter(url=self._url, feed=self.feed)
        if db_record.exists():
            return db_record.update(**record)
        else:
            return ArticleRecords.objects.create(**record)

    def _update_article_attributes_from_database(self):
        self.link = self._database_article.url
        self.title = self._database_article.title
        self.pub_date = self._database_article.pub_date

        self.scraper = self._database_article
        self.description = self._database_article.description
        self.tags = utils.convert_string_to_list(self._database_article.tags)

        self.full_article = self._database_article.full_article
        self.full_article_retries = self._database_article.full_article_retries

        self.hidden = self._database_article.hidden
        self.hidden_date = self._database_article.hidden_date
        self.hidden_active_keywords = self._database_article.hidden_active_keywords

    def _update_article_attributes_from_feedparser(self):
        self._feedparser_article.load()

        self.link = self._feedparser_article.link
        self.title = self._feedparser_article.title
        self.pub_date = self._feedparser_article.pub_date

        self.scraper = self._feedparser_article.scraper
        self.description = self._feedparser_article.description
        self.tags = self._feedparser_article.tags

    def _update_article_attributes_from_scraper(self):
        if self.feed.scraper.id != 1:

            db_article_needs_updating = (
                self._database_article is None
                or self._database_article.scraper != self.feed.scraper
            )

            if db_article_needs_updating or self._rebuild_full_article:

                if (
                    self._database_article is not None
                    and self._database_article.full_article_retries > 10
                    and not self._rebuild_full_article
                ):
                    return False

                try:
                    self._scraper_article.load(url=self._url, scraper=self.feed.scraper)

                    # Update Article with Scraper Attributes
                    if self._scraper_article.title:
                        self.title = self._scraper_article.title
                    self.scraper = self.feed.scraper
                    self.description = self._scraper_article.description
                    self.tags += self._scraper_article.tags

                    self.full_article = True
                    self.full_article_retries += 1

                    return True

                except Exception as e:
                    self.full_article = False
                    self.full_article_retries += 1
                    self._handle_exception(e)
        return False

    def _update_article_filter_attributes(self):
        filter_results = ArticleFilter(self)
        filter_results.filter()

        self.active_hide_filters = filter_results.active_hide_filters
        self.active_show_filters = filter_results.active_show_filters
        self.hidden = filter_results.hidden
        self.hidden_date = filter_results.hidden_date
        self.hidden_active_keywords = filter_results.hidden_active_keywords

        if self.hidden:
            self.description = None
            self.tags = None

    def _sanitize_description(self):
        # Apply HTML Stop
        if self.feed.stop_html:
            self.description = self.description.split(self.feed.stop_html)[0]

        # Remove Text
        if self.feed.remove_text:
            text_to_remove = self.feed.remove_text.split(",")
            for text in text_to_remove:
                pattern = re.compile(text, re.IGNORECASE)
                self.description = pattern.sub("", self.description)
                self.title = pattern.sub("", self.title)

        # Sanitize HTML
        self.description = utils.sanitize_html(self.description)

    def _sanitize_article_attributes(self):
        self._sanitize_description()

    def _append_article_snippets_to_description(self):
        if self.hidden:
            return

        snippet_object = Snippets(filtered_article=self)

        snippets = snippet_object.get_end_of_article_snippets()

        self.description = "".join([self.description, snippets])


class FeedParserArticle:
    def __init__(self, feedparser_article: feedparser):
        # Init Objects
        self._feedparser_article = feedparser_article

        # Init Attributes
        self.link = None
        self.pub_date = None
        self.title = None
        self.scraper = None
        self.tags = []
        self.description = None

    def load(self):
        self.link = self._get_parsed_link()
        self.pub_date = self._get_pub_date()
        self.title = self._get_title()
        self.scraper = self._get_article_scraper()
        self.tags = self._get_tags()
        self.description = self._get_description()

    def get_link(self):
        return self._get_parsed_link()

    def _get_parsed_link(self) -> str:
        try:
            # Edit link for Indeed RSS
            return self._feedparser_article.link.split("&rtk")[0]
        except AttributeError as e:
            raise FeedNotResolved(e, self._feedparser_article)

    def _get_pub_date(self) -> datetime:
        published = self._feedparser_article.get("published_parsed")
        updated = self._feedparser_article.get("updated_parsed")

        if published:
            pub_date_dt = datetime.fromtimestamp(time.mktime(published))
        elif updated:
            pub_date_dt = datetime.fromtimestamp(time.mktime(updated))
        else:
            pub_date_dt = datetime.now()

        return email.utils.format_datetime(pub_date_dt)

    def _get_title(self):
        return html.escape(self._feedparser_article.title)

    def _get_tags(self) -> list:
        tags = []
        try:
            for tag in self._feedparser_article.tags:
                tags.append(tag.term)
        except AttributeError:
            pass
        return tags

    @staticmethod
    def _get_article_scraper():
        return ArticleScrapers.objects.get(name="Newspaper")

    def _get_content_value(self) -> (str, None):
        content = self._feedparser_article.get("content", None)

        if content:
            return content[0].get("value", None)
        else:
            return None

    def _get_description(self) -> (str, None):
        content_value = self._get_content_value()
        if content_value:
            return "<br /><p><b>FullFeedFilter: content_value</b><br />".join(
                [self._feedparser_article.description, content_value]
            )
        else:
            if self._feedparser_article.description == "":
                return "<p><b>FullFeedFilter Note:</b> No description of this article from RSS Feed</p>"
            else:
                return self._feedparser_article.description


class ScraperArticle:
    def __init__(self):
        self._url = None
        self._scraper = None
        self._scraper_article = None

        # Article Attributes
        self.title = None
        self.description = ""
        self.tags = []

    def load(self, url: str, scraper: ArticleScrapers):
        self._url = url
        self._scraper = scraper

        if self._scraper.name == "Newspaper":
            self._scraper_article = self._get_article_from_newspaper()
        elif self._scraper.name == "Simple Scraper":
            self._scraper_article = SimpleScraper(url=self._url)
        elif self._scraper.name == "Craigslist Scraper":
            self._scraper_article = CraigslistScraper(url=self._url)
        elif self._scraper.name == "Reddit Scraper":
            self._scraper_article = RedditScraper(url=self._url)
        else:
            raise AttributeError(
                f"Scraper Name '{self._scraper.name} not found in update_from_scraper()."
            )

        self._validate_article_contents()
        self._update_attributes_from_scraper_article()

    def _update_attributes_from_scraper_article(self):
        if self._scraper_article.title:
            self.title = html.escape(self._scraper_article.title)
        self.description += self._build_description_with_additional_details()
        self.tags = self._scraper_article.tags

    def _get_article_from_newspaper(self) -> (newspaper.Article, None):
        article = newspaper.Article(url=self._url, keep_article_html=True)

        article.download()
        article.parse()
        article.nlp()

        article.tags = article.keywords + article.meta_keywords
        article.additional_images = None

        return article

    def _validate_article_contents(self) -> None:
        error_text = (
            "<br /><br /><hr><i><small>FullFeedFilter could not generate the full article text for this link. "
            "Consider joining as a Pro (Gold) member to get a custom scraper created for "
            "this website.</small></i>"
        )

        if self._scraper_article is None:
            error_text += "<br /><small>(Error: article is None)</small>"
            self.description += error_text
            raise ValueError(f"article is None. Needs a custom parser.")

        if self._scraper_article.article_html == "":
            if self._scraper_article.article_html == "":
                error_text += "<br /><small>(Error: article.article_html == '')</small>"
            self.description += error_text
            raise ValueError(f"Could not get article_html or title. Needs a custom parser.")

    def _build_description_with_additional_details(self) -> str:
        description = ""

        # Append Top Image
        if self._scraper_article.top_image:
            description = f"<img src='{self._scraper_article.top_image}' /><br /><br />"

        # Append Article HTML
        description += self._scraper_article.article_html

        # Append Youtube Videos
        if self._scraper_article.movies:
            for video_src in self._scraper_article.movies:
                description += (
                    f'<p class="youtube">'
                    f'<iframe width="560" height="315" src="{video_src}" frameborder="0" allowfullscreen>'
                    f"</iframe></p>"
                )

        # Append Additional Images
        if self._scraper_article.additional_images:
            if len(self._scraper_article.additional_images) > 1:
                for img_src in self._scraper_article.additional_images:
                    description += f"<p><a href='{img_src}'><img src='{img_src}' /></a></p>"

        return description


class ArticleFilter:
    def __init__(self, article_to_filter: Article):
        self._article_to_filter = article_to_filter

        # Search Helpers
        self._filters = None
        self._search_feed_text = None
        self._search_tags_text = None

        # Filter Results
        self.active_hide_filters = []
        self.active_show_filters = []
        self.hidden = False
        self.hidden_date = None
        self.hidden_active_keywords = None

    def filter(self):
        self._filters = Filters.objects.filter(feed=self._article_to_filter.feed)
        self._search_feed_text = self._get_search_feed_text()
        self._search_tags_text = self._get_search_tags_text()

        show_filters = self._filters.filter(action="show")
        hide_filters = self._filters.filter(action="hide")

        # Check Show Filters
        for filter in show_filters:
            if self._filter_is_true(filter=filter):
                self.active_show_filters.append(filter)

        # Check Hide Filtershttps://youtube.com/playlist?list=PL9jess9jFHgkYTOiPate1PQpMVSHrFzxl
        for filter in hide_filters:
            if self._filter_is_true(filter=filter):
                self.active_hide_filters.append(filter)

        if self.active_show_filters:
            self.hidden_date = None
            self.hidden = False
            self.hidden_active_keywords = None
            return

        if self.active_hide_filters:
            self.hidden_date = now()
            self.hidden = True
            self.hidden_active_keywords = self.build_hidden_active_keywords()
            return

    def _get_search_tags_text(self) -> str:
        return " ".join(self._article_to_filter.tags).lower()

    def _get_search_feed_text(self) -> str:
        search_list = [
            self._article_to_filter.title,
            self._article_to_filter.link,
            self._article_to_filter.description,
        ]
        search_list += self._article_to_filter.tags

        return " ".join(search_list).lower()

    def _get_mapped_filter_source_as_string(self, source: str) -> str:
        if source == "title":
            return self._article_to_filter.title
        elif source == "body":
            return self._article_to_filter.description
        elif source == "link":
            return self._article_to_filter.link
        elif source == "tag":
            return self._search_tags_text
        else:
            return self._search_feed_text

    @staticmethod
    def _word_in_string(word: str, string: str) -> bool:
        return f" {word} " in f" {string} "

    @staticmethod
    def _word_not_in_string(word: str, string: str) -> bool:
        result = True
        if f" {word} " in f" {string} ":
            result = False
        return result

    def _filter_is_true(self, filter: Filters) -> bool:
        filter_source_string = self._get_mapped_filter_source_as_string(filter.source)

        filter_keyword = utils.sanitize_string(
            dirty_string=filter.keyword,
            strip_html=True,
            unescape_string=True,
            strip_special_chars=True,
            replace_special_chars_with_space=True,
            lowercase=True,
        )

        filter_source = utils.sanitize_string(
            dirty_string=filter_source_string,
            strip_html=True,
            unescape_string=True,
            strip_special_chars=True,
            replace_special_chars_with_space=True,
            lowercase=True,
        )

        if filter.condition == "in":
            return self._word_in_string(word=filter_keyword, string=filter_source)
        else:
            return self._word_not_in_string(word=filter_keyword, string=filter_source)

    def build_filter_keyword_link(self, filter: Filters) -> str:
        filter_link = (
            f"http://{DOMAIN}/feed/{self._article_to_filter.feed.id}/filter/{filter.id}/edit/"
        )
        return f"<a href='{filter_link}'>{filter.keyword}</a>"

    def build_hidden_active_keywords(self) -> str:
        body_items = []

        if self.active_hide_filters:
            for filter in self.active_hide_filters:
                body_items.append(self.build_filter_keyword_link(filter=filter))

        body = f"{', '.join(body_items)}"
        return body
