import os
import time

from django.core.management.base import BaseCommand
from termcolor import cprint

from general.scripts.utils import main_wrapper, remove_last_line

MANAGE_PY = '~/full_feed_filter/manage.py'
COMMAND_TITLE = 'Admin Helper'


def static_input(func):
    def wrapper(text):
        userinput = input(f"{text}: ")
        remove_last_line()
        remove_last_line()
        if userinput == "y":
            cprint(f"{text}: YES", 'green')
            rtn = func()
        else:
            # cprint(f"{text}: NO", 'red',)
            rtn = None
        return rtn
    return wrapper


def self_input(func):
    def wrapper(self, text):
        userinput = input(f"{text}: ")
        remove_last_line()
        remove_last_line()
        if userinput == "y":
            cprint(f"{text}: YES", 'green')
            rtn = func(self)
        else:
            # cprint(f"{text}: NO", 'red')
            rtn = None
        return rtn
    return wrapper


def arg_input(func):
    def wrapper(text, flag, boolean=False):
        flag_value = input(f"\t- {text}: ")
        remove_last_line()
        if flag_value != "n" and flag_value != '':
            if boolean:
                cprint(f"\t- {text}: YES", 'blue')
                rtn = func(flag=flag)
            else:
                cprint(f"\t- {text}: {flag_value}", 'blue')
                rtn = func(flag=flag, value=flag_value)
        else:
            # cprint(f"\t- {text}: NO", 'red')
            rtn = None
        return rtn
    return wrapper


def press_special_key_to_continue(key=None):
    if key:
        v_key = f'" {key} "'
    else:
        v_key = 'Any'
    while True:
        key_press = input(f"Press {v_key} key to continue.")
        remove_last_line()
        if key:
            if key == "'":
                break
        else:
            break
    print("")


class Command(BaseCommand):
    help = 'Admin Helper Commands'\


    @main_wrapper(title='Admin Helper')
    def handle(self, *args, **kwargs):
        print("")
        cmd_list = [
            self.build_cmd(func=self.cmd_restart_apache, text="Restart Apache"),
            self.build_cmd(func=self.cmd_build_rss_feed, text="Build RSS Feeds"),
            self.build_cmd(func=self.cmd_cleanup, text="Cleanup Script"),
            self.build_cmd(func=self.cmd_export_hidden_to_rss, text="Export Hidden to RSS"),
            self.build_cmd(func=self.cmd_validate_feed, text="Validate FFF Feed"),
        ]
        cmd_list = list(filter(None, cmd_list))
        time.sleep(1)
        cprint("RUNNING CMD", color="grey", on_color="on_cyan", attrs=['bold'])
        cmd_list_nl = '\n\t- '.join(cmd_list)
        cprint(f"\t- {cmd_list_nl}")

        press_special_key_to_continue(key="'")
        for cmd in cmd_list:
            os.system(cmd)
            time.sleep(1)
        return

    @staticmethod
    def build_cmd(func, text):
        rtn = func(text=text)
        print("")
        press_special_key_to_continue()
        remove_last_line()
        remove_last_line()
        print("")
        return rtn

    @staticmethod
    @arg_input
    def arg_return(flag, value=None):
        return f"{flag} {value}" if value else f"{flag}"

    # COMMANDS
    @staticmethod
    @static_input
    def cmd_restart_apache():
        return "sudo service apache2 restart"

    @self_input
    def cmd_build_rss_feed(self):
        cmd_list = [
            MANAGE_PY,
            'build',
            '-v2',
            self.arg_return(text="Single Feed ID", flag='-f'),
            self.arg_return(text="Single Article ID", flag='-a'),
            self.arg_return(text="Single Article URL", flag='-aurl'),
            self.arg_return(text="Max # of Articles", flag='-m'),
            self.arg_return(text="Rebuild Full Articles", flag='-r', boolean=True),
            self.arg_return(text="Verbose for each Article", flag='-v3', boolean=True),
            self.arg_return(text="No Threading", flag='-nt', boolean=True),
        ]
        cmd_list = list(filter(None, cmd_list))
        return " ".join(cmd_list)

    @self_input
    def cmd_cleanup(self):
        cmd_list = [
            MANAGE_PY,
            'cleanup',
            '-v2',
        ]
        cmd_list = list(filter(None, cmd_list))
        return " ".join(cmd_list)

    @self_input
    def cmd_export_hidden_to_rss(self):
        cmd_list = [
            MANAGE_PY,
            'export_hidden_to_rss',
            '-v2',
            self.arg_return(text="Single Username", flag='-u'),
        ]
        cmd_list = list(filter(None, cmd_list))
        return " ".join(cmd_list)

    @self_input
    def cmd_validate_feed(self):
        cmd_list = [
            MANAGE_PY,
            'validate_feed',
            '-v2',
            self.arg_return(text="Single Feed ID", flag='-f'),
        ]
        cmd_list = list(filter(None, cmd_list))
        return " ".join(cmd_list)




