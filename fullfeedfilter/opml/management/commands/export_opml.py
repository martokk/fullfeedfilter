from django.core.management.base import BaseCommand, CommandParser
from opml.scripts.opml import ExportOpml


class Command(BaseCommand):
    help = 'Builds OPML and saves the file.'

    def __init__(self) -> None:
        super().__init__(stdout=None, stderr=None, no_color=False, force_color=False)
        self.verbose = False

    def add_arguments(self, parser: CommandParser) -> None:
        # Optional argument
        parser.add_argument('-u', '--username', type=str, help='Username to run script against')
        parser.add_argument('-v2', '--verbose', action='store_true', help='Verbose output')

    def vprint(self, message: str) -> print:
        if self.verbose:
            return print(message)

    def handle(self, *args, **kwargs) -> print:
        username = kwargs['username']
        self.verbose = kwargs['verbose']

        opml = ExportOpml(username=username)
        opml.write_opml_to_file()

        return self.vprint(f"Completed.")
