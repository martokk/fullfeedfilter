import os
import sys

from django.core.management.base import BaseCommand, CommandParser
from django.template.loader import render_to_string
from django.utils.timezone import now
from termcolor import cprint

from feeds.models import Feeds, FeedValidation
from general.scripts import utils
from full_feed_filter.settings import DOMAIN, BASE_DIR
from datetime import datetime
from feeds.scripts.feed_validation import ValidateFeed
from general.scripts.utils import main_wrapper, remove_last_line


class Command(BaseCommand):
    help = 'Build a filtered feed and saves the file.'

    def __init__(self) -> None:
        super().__init__(stdout=None, stderr=None, no_color=False, force_color=False)
        self.verbose = False
        self.feed_id = None
        self.feeds_to_validate = None
        self.startTime = datetime.now()

    def add_arguments(self, parser: CommandParser) -> None:
        # Optional argument
        parser.add_argument('-f', '--feed_id', type=int, help='Feed ID to run script against')
        parser.add_argument('-v2', '--verbose', action='store_true', help='Verbose output')

    def vprint(self, message: str, color=None, on_color=None) -> print:
        if self.verbose:
            return cprint(message, color=color, on_color=on_color)

    def init_kwargs(self, **kwargs) -> None:
        self.feed_id = kwargs['feed_id']
        self.verbose = kwargs['verbose']

        if self.feed_id:
            self.feeds_to_validate = Feeds.objects.filter(id=self.feed_id)
            if not self.feeds_to_validate:
                raise LookupError(f"Feed ID ({self.feed_id}) not valid.")
        else:
            self.feeds_to_validate = Feeds.objects.all()

    @main_wrapper(title='Validate FFF Feed')
    def handle(self, *args, **kwargs) -> print:
        self.init_kwargs(**kwargs)

        self.loop_all_feeds_and_validate()

        rss = ExportRSS()
        rss.write_rss_to_file()

        return

    def loop_all_feeds_and_validate(self) -> None:
        invalid_feeds = []
        total_feeds = len(self.feeds_to_validate)

        for idx, feed in enumerate(self.feeds_to_validate):
            self.vprint(f"Validating ({idx} of {total_feeds}) feeds. Checking '{feed.name}' (id={feed.id}).")

            rss = self.validate_feed(feed=feed)
            if not rss.is_valid:
                invalid_feeds.append(rss)
            remove_last_line()

        self.print_results(invalid_feeds)
        self.vprint("")

    def validate_feed(self, feed: Feeds) -> ValidateFeed:
        rss_url = f"http://{DOMAIN}/feeds/{feed.id}/rss/"
        results = ValidateFeed(url=rss_url)

        if results.is_valid:
            self.handle_valid_feed(feed=feed)
        else:
            results.message = self.print_invalid_feed_message(rss_url, feed, results)
            self.handle_invalid_feed(feed=feed, errors_list=results.errors)

        return results

    def print_invalid_feed_message(self, rss_url: str, feed: Feeds, results: ValidateFeed) -> str:
        ignored_errors = [
            'guid values must not be duplicated within a feed',
            'Feeds should not be served with the "text/html" media type',
            'Self reference doesn\'t match document location',
        ]

        message = f"\nNOT VALID: {results.status} - ID: {feed.id} - Title: {feed.name} - URL: {rss_url}"

        for error in results.errors:
            ignored = False
            for ignored_error in ignored_errors:
                if ignored_error in error:
                    ignored = True
            if ignored:
                results.errors.remove(error)
                continue
            message += f"\n    - {error}"

        return message

    def print_results(self, invalid_feeds: list) -> None:
        self.vprint(f"Completed. Total time={datetime.now() - self.startTime}", 'blue')
        if invalid_feeds:
            total_invalid = len(invalid_feeds)
            self.vprint(f"A total of {total_invalid} invalid feeds were found:", 'red')

            for feed in invalid_feeds:
                self.vprint(f"  {feed.message}")

    @staticmethod
    def handle_valid_feed(feed: Feeds) -> FeedValidation:
        return FeedValidation.objects.filter(feed=feed).delete()

    @staticmethod
    def handle_invalid_feed(feed: Feeds, errors_list: list) -> None:
        ignored_errors = [
            'guid values must not be duplicated within a feed',
            'Feeds should not be served with the "text/html" media type',
            'Self reference doesn\'t match document location',
        ]

        for error in errors_list:
            ignored = False
            for ignored_error in ignored_errors:
                if ignored_error in error:
                    ignored = True
            if ignored:
                errors_list.remove(error)
                continue

        for error in errors_list:
            if not FeedValidation.objects.filter(feed=feed, error=error).exists():
                FeedValidation.objects.create(feed=feed,
                                              error=error,
                                              ignore=False)

        for record in FeedValidation.objects.filter(feed=feed):
            if not record.error in errors_list:
                FeedValidation.objects.filter(feed=feed, error=record.error).delete()
        return


class ExportRSS:
    def __init__(self) -> None:
        self.write_to_rss = False
        self.html_string = self.build_html_string()
        self.rss_string = self.build_rss_string()
        self.rss_folder = os.path.join(BASE_DIR, "media/invalid")
        self.rss_filename = self.build_rss_filename()

    def build_rss_string(self) -> str:
        article = {
            'title': f'Invalid Feeds {utils.now_cst()}',
            'link': f'http://{DOMAIN}/reports/invalid/{datetime.strftime(now(), "%m%d%H%M")}',
            'pub_date': utils.rss_friendly_datetime(datetime.now()),
            'description_with_snippets': self.html_string,
        }

        articles = [article]

        context = {
            'xml_link': f'http://{DOMAIN}/reports/invalid/rss/',
            'title': f'FullFeedFilter: Invalid Feeds',
            'link': f'http://{DOMAIN}/reports/invalid/rss/',
            'description': "Invalid Errors.",
            'articles': articles,
        }

        unformatted_string = render_to_string('rss/rss.xml', context)
        return str(unformatted_string.encode('ascii', 'ignore').decode())

    def build_html_string(self) -> str:
        invalid_feeds = FeedValidation.objects.values_list('feed', flat=True).distinct()

        feeds_errors = []
        for feed in invalid_feeds:
            feed = Feeds.objects.filter(pk=feed).first()

            errors = FeedValidation.objects.filter(feed=feed, ignore=False)

            if errors:
                feeds_errors.append({
                    'feed': feed,
                    'errors': errors,
                })
                self.write_to_rss = True

        context = {
            'feeds_errors': feeds_errors,
            # 'total_errors': total_errors,
            'build_date': utils.now_cst(),
        }

        unformatted_string = render_to_string('reports/validation_errors.html', context)
        return str(unformatted_string.encode('ascii', 'ignore').decode())

    @staticmethod
    def build_rss_filename() -> str:
        return f"invalid_feeds.xml"

    def write_rss_to_file(self) -> None:
        if self.write_to_rss:
            utils.mkdir_if_doesnt_exist(self.rss_folder)
            with open(f'{self.rss_folder}/{self.rss_filename}', 'w') as fp:
                fp.write(self.rss_string)
