import os
import shutil
from datetime import timedelta, datetime

from django.core.management.base import BaseCommand
from termcolor import cprint

from feeds.models import Feeds, ArticleRecords
from general.scripts import utils
from full_feed_filter.settings import BASE_DIR
from general.scripts.utils import main_wrapper

FULL_ARTICLE_AGING_DAYS = 60
OPML_AGING_DAYS = 1


class Command(BaseCommand):
    help = 'Build a filtered feed and saves the file.'

    def __init__(self) -> None:
        super().__init__(stdout=None, stderr=None, no_color=False, force_color=False)
        self.verbose = False

    def add_arguments(self, parser) -> None:
        # Optional argument
        parser.add_argument('-v2', '--verbose', action='store_true', help='Verbose output')

    def vprint(self, message: str, color=None, on_color=None) -> print:
        if self.verbose:
            return cprint(message, color=color, on_color=on_color)

    @main_wrapper(title="Cleanup Script")
    def handle(self, *args, **kwargs):
        self.verbose = kwargs['verbose']

        # Cleanup Actions
        self.remove_lingering_rss_folders()
        self.remove_aging_full_articles()
        self.remove_opml_files()
        return

    def remove_lingering_rss_folders(self) -> None:
        """ Removes RSS folders for Feed ID's that no longer exist in database. """

        rss_folder = os.scandir(os.path.join(BASE_DIR, 'media/rss'))
        feeds = Feeds.objects.all()
        total_removed = 0

        # self.vprint(f"Deleting lingering rss folders.")

        for folder in rss_folder:
            if folder is not int:
                continue
            folder_id = folder.name

            if not feeds.filter(id=folder_id).exists():
                folder_path = os.path.join(BASE_DIR, f"media/rss/{folder_id}")
                self.vprint(f"Feed #{folder_id} does not exist. Deleting '{folder_path}' folder.")
                shutil.rmtree(folder_path)
                total_removed += 1

        self.vprint(f"Removed ({total_removed}) Lingering RSS Folders", 'green')

    def remove_aging_full_articles(self) -> None:

        # Build Objects
        object_name = "Full Articles"
        objects_aging_days = FULL_ARTICLE_AGING_DAYS
        record_timedelta = datetime.now() - timedelta(days=objects_aging_days)

        # Delete Records
        # self.vprint(f"Deleting '{object_name}' records over '{ objects_aging_days }' Days.")
        aging_records = ArticleRecords.objects.filter(date_added=record_timedelta)
        total_aging_records = aging_records.count()
        aging_records.delete()

        self.vprint(f"Removed ({total_aging_records}) aging '{object_name}' records.", 'green')

    def remove_opml_files(self):
        object_name = "OPML Files"
        objects_aging_days = OPML_AGING_DAYS

        # Delete Records
        # self.vprint(f"Deleting '{object_name}' files over '{objects_aging_days}' Days.")
        opml_folder = os.path.join(BASE_DIR, 'media/opml')
        deleted_files = utils.remove_files_modified_x_days_ago(folder_dir=opml_folder,
                                                               days_ago=objects_aging_days)
        total_aging_records = len(deleted_files)

        self.vprint(f"Removed ({total_aging_records}) aging '{object_name}' files.", 'green')
