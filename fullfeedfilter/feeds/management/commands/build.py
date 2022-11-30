"""
./manage.py build
./manage.py build -f 2
"""
import threading
import traceback
from datetime import datetime

from django.core.management.base import BaseCommand

from feeds.models import Feeds
from feeds.scripts.build_feed import BuildFeed
from termcolor import colored, cprint


# noinspection PyUnusedLocal
class Command(BaseCommand):
    help = 'Build a filtered feed and saves the file.'

    def __init__(self):
        super().__init__()
        self.verbose = False
        self.verbose_article = False
        self.rebuild_full_articles = False
        self.no_threading = False
        self.feed_id = None
        self.article_id = None
        self.article_url = None
        self.max_articles = None
        self.feeds_to_build = None
        self.build_type = None
        self.errors = []

        self.startTime = datetime.now()
        self.total_seconds = None

    def init_kwargs(self, *args, **kwargs):
        self.feed_id = kwargs['feed_id']
        self.article_id = kwargs['article_id']
        self.article_url = kwargs['article_url']
        self.max_articles = kwargs['max_articles']
        self.verbose = kwargs['verbose']

        # TODO: Disabled threading until sqlite locking bug can get resolved.
        # self.no_threading = kwargs['no_threading']
        self.no_threading = True

        self.verbose_article = kwargs['verbose_article']
        self.rebuild_full_articles = kwargs['rebuild_full_articles']

        if self.feed_id:
            self.feeds_to_build = Feeds.objects.filter(id=self.feed_id)
            if not self.feeds_to_build:
                raise LookupError(f"Feed ID ({self.feed_id}) not valid.")
        else:
            self.feeds_to_build = Feeds.objects.all()

        if self.rebuild_full_articles:
            self.build_type = "Re-build Full Articles"
        else:
            self.build_type = "Re-filter Articles"

    def add_arguments(self, parser):
        # Optional argument
        parser.add_argument('-f', '--feed_id', type=int, help='Feed ID to run script against')
        parser.add_argument('-a', '--article_id', type=int, help='Article ID to run script against')
        parser.add_argument('-m', '--max_articles', type=int, help='Max Articles per feed')
        parser.add_argument('-aurl', '--article_url', type=str, help='Article ID to run script against')
        parser.add_argument('-v2', '--verbose', action='store_true', help='Verbose output')
        parser.add_argument('-v3', '--verbose_article', action='store_true', help='Verbose output')
        parser.add_argument('-nt', '--no-threading', action='store_true', help='No Threading')
        parser.add_argument('-r', '--rebuild_full_articles', action='store_true', help='Force Rebuild of Full Articles')

    def vprint(self, message, color=None, on_color=None, *args, **kwargs):
        if self.verbose:
            return cprint(message, color, on_color, *args, **kwargs)

    def handle(self, *args, **kwargs) -> None:
        self.init_kwargs(*args, **kwargs)

        # Start
        self.print_start_options()
        self.loop_all_feeds_and_build()

        # Complete
        total_time = datetime.now() - self.startTime
        self.total_seconds = int(total_time.total_seconds())
        self.print_total_time()
        self.print_errors()
        self.print_total_time()

    def loop_all_feeds_and_build(self) -> None:
        total_feeds = len(self.feeds_to_build)
        thread_list = []

        if self.no_threading:
            for idx, feed in enumerate(self.feeds_to_build, start=1):
                self.build_filtered_feed(feed=feed, idx=idx, total_feeds=total_feeds, threaded=False)
        else:
            for idx, feed in enumerate(self.feeds_to_build, start=1):
                t = threading.Thread(target=self.build_filtered_feed, args=(feed, idx, total_feeds))
                thread_list.append(t)

            for i, thread in enumerate(thread_list):
                thread.start()

            for i, thread in enumerate(thread_list):
                thread.join()

            # if success is False:
            #     self.handle_error(Exception("self.build_filtered_feed(feed=feed) = FALSE"), feed)
            #     # self.errors.append(feed)
        pass

    def build_filtered_feed(self, feed, idx, total_feeds, threaded=True) -> bool:
        # Build Filtered Feeds Object

        try:
            start_time = datetime.now()
            filtered_feed = BuildFeed(feed=feed,
                                      article_id=self.article_id,
                                      article_url=self.article_url,
                                      max_articles=self.max_articles,
                                      verbose=self.verbose,
                                      verbose_article=self.verbose_article,
                                      rebuild_full_articles=self.rebuild_full_articles,
                                      threaded=threaded)

            if filtered_feed.errors:
                self.errors.append(filtered_feed.errors)

            # Save filtered feeds to file
            if filtered_feed.feedparser.is_valid:
                filtered_feed.write_feeds_to_file()

                total_time = datetime.now() - start_time
                seconds = int(total_time.total_seconds())
                self.vprint(f"Completed - {idx}/{total_feeds} - {feed.name} - ({seconds} seconds)")
                return True
            else:
                self.vprint(f"ERROR: Feed could not be parsed. Ignored building/saving file. (feed_id={feed.id}).")
                return False
        except Exception as e:
            self.handle_error(e, feed)

    def handle_error(self, e: Exception, feed: Feeds) -> None:
        tb = traceback.format_exc()
        self.errors.append([{
            'feed_id': feed.id,
            'feed_name': feed.name,
            'article_url': '',
            'article_title:': '',
            'exception': e,
            'traceback': tb,
        }])

    def print_total_time(self) -> None:

        self.vprint(f"\nCompleted in {self.total_seconds} seconds.", 'cyan')
        self.vprint("---------------------------------------\n")

    def print_start_options(self) -> None:
        self.vprint("---------------------------------------", color='grey', on_color='on_grey')
        self.vprint("build.py: Starting\n")
        self.vprint(f"{self.build_type} Options:", color='yellow')

        if self.feed_id:
            self.vprint(f"\tFeed ID: \t\t{self.feed_id}")
            self.vprint(f"\tFeed Name: \t\t{self.feeds_to_build.first().name}")
        self.vprint(f"\tTotal Feeds: \t{len(self.feeds_to_build)}")
        if self.article_id:
            self.vprint(f"\tArticle ID: \t{self.article_id}")
        if self.article_url:
            self.vprint(f"\tArticle URL: \t{self.article_url}")

        self.vprint("---------------------------------------", color='grey', on_color='on_grey')

    def print_errors(self) -> None:
        if len(self.errors) > 0:
            self.vprint(f"\nTotal of ({len(self.errors)}) feeds contained errors:")

            for feed in self.errors:
                top_feed = feed[0]

                self.vprint(
                    colored(f"\n\nNAME: {top_feed['feed_name']} (ID={top_feed['feed_id']})", 'grey', 'on_red'))

                for error in feed:
                    error_text, tb = self.replace_error_text(str(error['exception']), error['traceback'])
                    self.vprint(f"EXCEPTION: {error_text}")
                    self.vprint(f"URL: {error['article_url']}", 'cyan')
                    if tb:
                        self.vprint(f"{tb}", 'red')
                    else:
                        self.vprint("")

    @staticmethod
    def replace_error_text(error_text: str, error_traceback: str) -> tuple:

        if "failed with 403 Client Error: Forbidden" in error_text:
            error_text = "Article `download()` failed with 403 Client Error: Forbidden"
            error_traceback = None
        elif "failed with 404 Client Error: Not Found" in error_text:
            error_text = "Article `download()` failed with 404 Client Error: Not Found"
            error_traceback = None
        elif "(connect timeout=7)'" in error_text:
            error_text = "Connection timed out. (connect timeout=7)'"
            error_traceback = None

        return error_text, error_traceback
