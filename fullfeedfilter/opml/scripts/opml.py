from datetime import datetime

from django.contrib.auth.models import User
import os
from full_feed_filter.settings import BASE_DIR, DOMAIN
from django.template.loader import render_to_string
from feeds.models import Feeds
from xml.etree import ElementTree
import warnings


class ExportOpml:
    def __init__(self, username: str, remote_rss_feeds=False) -> None:
        self.user = User.objects.filter(username=username).first()
        self.username = self.user.username
        self.remote_rss_feeds = remote_rss_feeds
        self.opml_string = self.build_opml_string()
        self.opml_folder = os.path.join(BASE_DIR, "media/opml")
        self.opml_filename = self.build_opml_filename()

    def build_folders_feeds_dict(self) -> dict:
        users_feed_folders = list(Feeds.objects.filter(user=self.user).values_list('folder', flat=True).distinct())

        folders_feeds_dict = {}
        for folder in users_feed_folders:
            feed_list = []

            folders_feeds = Feeds.objects.filter(user=self.user, folder=folder)
            for feed in folders_feeds:

                if self.remote_rss_feeds:
                    url = feed.url
                    title = feed.name
                else:
                    url = f"http://{DOMAIN}/feeds/{feed.id}/rss/"
                    title = f"{feed.name} - (Filtered)"

                feed_list.append({
                    'title': title,
                    'url': url,
                })
            folders_feeds_dict.update({folder: feed_list})

        return folders_feeds_dict

    def build_opml_string(self) -> str:
        if self.remote_rss_feeds:
            title = f"Remote RSS Feeds for { self.username } (Not Filtered)"
        else:
            title = f"FullFeedFilter Subscriptions for { self.username }"

        context = {
            'title': title,
            'folders': self.build_folders_feeds_dict(),
        }
        unformatted_string = render_to_string('opml/opml.xml', context)
        return str(unformatted_string.encode('ascii', 'ignore').decode())

    def build_opml_filename(self) -> str:
        stamp = datetime.strftime(datetime.now(), '%Y%m%d_%H%M%S')
        if self.remote_rss_feeds:
            return f"{self.username}_remote_rss_{stamp}.opml"
        else:
            return f"{self.username}_fullfeedfilter_{stamp}.opml"

    def write_opml_to_file(self) -> None:
        with open(f'{self.opml_folder}/{self.opml_filename}', 'w') as fp:
            fp.write(self.opml_string)


class ImportOpml:
    def __init__(self, file: str, user: User) -> None:
        self.file = file
        self.user = user
        self.username = self.user.username
        self.feeds_to_import = self.parse_raw_opml()

    def parse_raw_opml(self) -> list:
        feeds_to_import = []

        tree = ElementTree.parse(self.file)
        for node in tree.findall('./body/outline'):
            import_url = node.attrib.get('xmlUrl')

            if import_url:
                feeds_to_import.append({'folder': 'None', 'url': import_url, 'name': node.attrib.get('title')})
            else:
                for child_node in node:
                    feeds_to_import.append({'folder': node.attrib.get('title'),
                                            'url': child_node.attrib.get('xmlUrl'),
                                            'name': child_node.attrib.get('title')})
        return feeds_to_import

    def get_feed_record_from_database(self, url: str) -> (None, Feeds):

        # Lookup by URL
        if Feeds.objects.filter(url=url).exists():
            return Feeds.objects.filter(url=url).first()

        # Check if 'fullfeedfilter' url
        else:
            if f"{DOMAIN}/feed" in url:
                split_url = url.split("/")
                fff_index = split_url.index(DOMAIN)
                feed_slug = split_url[fff_index + 2]

                if Feeds.objects.filter(user=self.user, slug=feed_slug).exists():
                    return Feeds.objects.filter(user=self.user, slug=feed_slug).first()
                else:
                    warnings.warn(f'Feed is FFF feed, but could not get located in database. Check url username and '
                                  f'slug. url={url}')
                    return None
            else:
                return None

    def create_feed_record(self, parsed_feed: dict) -> Feeds:
        return Feeds.objects.create(url=parsed_feed['url'],
                                    user=self.user,
                                    name=parsed_feed['name'],
                                    folder=parsed_feed['folder'])

    def update_feed_record_folder(self, parsed_feed: dict) -> Feeds:
        feed_record = self.get_feed_record_from_database(url=parsed_feed['url'])
        feed_record.folder = parsed_feed['folder']
        return feed_record.save()

    def import_opml(self) -> None:
        for parsed_feed in self.feeds_to_import:
            feed_record = self.get_feed_record_from_database(url=parsed_feed['url'])

            if feed_record:
                self.update_feed_record_folder(parsed_feed=parsed_feed)
            else:
                self.create_feed_record(parsed_feed=parsed_feed)
        return
