import urllib.parse
import string
import re

from feeds.models import Filters
from full_feed_filter.settings import DOMAIN


class Snippets:
    def __init__(self, filtered_article) -> None:
        self.article = filtered_article
        self.feed = self.article.feed
        self.end_of_article_snippets = self.build_end_of_article_snippets()

    def get_end_of_article_snippets(self) -> str:
        return self.end_of_article_snippets

    def get_snippets_as_list(self) -> list:
        snippets = [
            self.build_snippet_active_filters(),
            self.build_snippet_quick_filters_by_keyword(),
            self.build_snippet_quick_filters_by_domain(),
            self.build_snippet_feed_management_links(),
        ]
        return snippets

    def build_end_of_article_snippets(self) -> str:
        title = '<br /><br /><br /><div align="left">' \
                '<hr style="margin: 0px; width: 100%; display: inline-block;">' \
                '<span style="display: block; margin: 0px; margin-left: 35%">FullFeedFilter</span>' \
                '<hr style="margin: 0px; width: 100%; display: inline-block;">' \
                '</div>'

        body = ''
        for snippet in self.get_snippets_as_list():
            if snippet:
                body += f"<p>{snippet}</p>"
        return ''.join([title, body])

    def build_filter_list_item(self, filter: Filters) -> str:
        link_base = f'http://{DOMAIN}'
        filter_link = f"{link_base}/feed/{self.feed.id}/filter/{filter.id}/edit/"
        return f"<li><a href='{filter_link}'>{filter}</a></li>"

    def build_snippet_active_filters(self) -> str:
        title = '<b><u>Active Filters</u></b>'
        body_items = []

        if self.article.active_show_filters:
            for filter in self.article.active_show_filters:
                body_items.append(self.build_filter_list_item(filter=filter))
        elif self.article.active_hide_filters:
            for filter in self.article.active_hide_filters:
                body_items.append(self.build_filter_list_item(filter=filter))
        else:
            body_items.append("<li>No Active Filters</li>")

        body = f"<ul>{''.join(body_items)}</ul>"
        return ''.join([title, body])

    def build_tag_links_from_list(self, tags_list: list) -> str:
        link_list = []

        for tag in tags_list:
            tag_encoded = urllib.parse.quote(tag)
            link = f'http://{DOMAIN}/feed/{self.feed.id}/filter/add/{tag_encoded}'
            link_list.append(f"<a href='{link}'>{tag}</a>")

        return ', '.join(link_list)

    def build_snippet_quick_filters_by_keyword(self) -> str:
        title = '<b><u>Quick Filters by Keyword</u></b>'

        article_title_as_list = re.sub(r'['+re.escape(string.punctuation)+']', '', self.article.title).split()

        article_tags = self.build_tag_links_from_list(self.article.tags)
        article_title_tags = self.build_tag_links_from_list(article_title_as_list)

        body = "<ul>"

        if article_tags:
            body += f"<li><b>Article Tags</b>: {article_tags}</li>"

        if article_title_tags:
            body += f"<li><b>Title Tags</b>: {article_title_tags}</li>"

        # TODO: Fixme self.article.additional_tags
        # if self.article.additional_tags:
        #     npl_tags = self.build_tag_links_from_list(self.article.additional_tags)
        #     body += f"<li><b>NPL Tags</b>: {npl_tags} </li>"

        body += "</ul>"

        return ''.join([title, body])

    def build_snippet_quick_filters_by_domain(self) -> (str, None):
        parsed_uri = urllib.parse.urlparse(self.article.link)
        article_domain = '.'.join([parsed_uri.netloc.split('.')[-2], parsed_uri.netloc.split('.')[-1]])

        if article_domain not in self.article.feed.url:
            title = '<b><u>Quick Filters by Domain</u></b>'

            article_domain_encoded = urllib.parse.quote(article_domain)
            link = f'http://{DOMAIN}/feed/{self.feed.id}/filter/add/domain/{article_domain_encoded}'

            body = f'<ul><li><a href="{link}">Hide articles from "{article_domain}"</a></li></ul>'

            return ''.join([title, body])
        else:
            return None

    def build_snippet_feed_management_links(self) -> str:
        title = '<b><u>Feed Management Links</u></b>'
        link_base = f'http://{DOMAIN}'
        body = f"<ul>" \
            f"<li><a href='{link_base}/feed/{self.feed.id}/edit/'>Edit Feed</a></li>" \
            f"<li><a href='{link_base}/feed/{self.feed.id}/filter/add/'>Add Filter</a></li>" \
            f"<li><a href='{link_base}/feed/{self.feed.id}'>View/Edit Filters</a></li>" \
            f"</ul>"
        return ''.join([title, body])
