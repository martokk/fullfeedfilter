"""
"""
import os
from django.utils.timezone import now
from datetime import datetime

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandParser
from django.template.loader import render_to_string
from termcolor import cprint

from general.scripts import utils
from full_feed_filter.settings import BASE_DIR, DOMAIN
from general.scripts.utils import main_wrapper
from reports.scripts.hidden_articles import HiddenArticleViewer


class Command(BaseCommand):
    help = 'Exports hidden articles to RSS.'

    def __init__(self) -> None:
        super().__init__(stdout=None, stderr=None, no_color=False, force_color=False)
        self.verbose = False
        self.username = None
        self.users_to_export = None
        self.startTime = datetime.now()

    def init_kwargs(self, **kwargs) -> None:
        self.verbose = kwargs['verbose']
        self.username = kwargs['username']

        if self.username:
            self.users_to_export = User.objects.filter(username=self.username)
        else:
            self.users_to_export = User.objects.all()

    def add_arguments(self, parser: CommandParser) -> None:
        # Optional argument
        parser.add_argument('-u', '--username', type=str, help='Username to run script against')
        parser.add_argument('-v2', '--verbose', action='store_true', help='Verbose output')

    def vprint(self, message: str, color=None, on_color=None) -> print:
        if self.verbose:
            return cprint(message, color=color, on_color=on_color)

    @main_wrapper(title='Export Hidden to RSS')
    def handle(self, *args, **kwargs) -> print:
        self.init_kwargs(**kwargs)

        for user in self.users_to_export:
            rss = ExportHiddenRSS(user=user)
            rss.write_rss_to_file()
            self.vprint(f"Exported Hidden RSS for user '{user}'", 'green')

        return


class ExportHiddenRSS:
    def __init__(self, user: User) -> None:
        self.user = user
        self.username = self.user.username
        self.html_string = self.build_html_string()
        self.rss_string = self.build_rss_string()
        self.rss_folder = os.path.join(BASE_DIR, "media/hidden")
        self.rss_filename = self.build_rss_filename()

    def build_rss_string(self) -> str:
        article = {
            'title': f'Hidden Articles for {utils.now_cst()}',
            'link': f'http://{DOMAIN}/reports/hidden/{self.username}/{datetime.strftime(now(), "%m%d%H%M")}',
            'pub_date': utils.rss_friendly_datetime(datetime.now()),
            'description': self.html_string,
        }

        articles = [article]

        context = {
            'xml_link': f'http://{DOMAIN}/reports/hidden/{self.username}/rss/',
            'title': f'FullFeedFilter: Hidden Articles (8h)',
            'link': f'http://{DOMAIN}/reports/hidden/',
            'description': "Articles hidden during past 8 hours.",
            'articles': articles,
        }

        unformatted_string = render_to_string('rss/rss.xml', context)
        return str(unformatted_string.encode('ascii', 'ignore').decode())

    def build_html_string(self) -> str:
        _hidden_articles = HiddenArticleViewer(user=self.user,
                                               timedelta_hours=8)

        context = _hidden_articles.get_context()

        unformatted_string = render_to_string('reports/hidden_articles_rss.html', context)
        return str(unformatted_string.encode('ascii', 'ignore').decode())

    def build_rss_filename(self) -> str:
        return f"{self.username}.xml"

    def write_rss_to_file(self) -> None:
        utils.mkdir_if_doesnt_exist(self.rss_folder)
        with open(f'{self.rss_folder}/{self.rss_filename}', 'w') as fp:
            fp.write(self.rss_string)
