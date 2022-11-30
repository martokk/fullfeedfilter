"""
General Utils for FullFeedFilter

"""
import email
import functools
import os
import sys
import time
import re
from html import unescape
import shutil

import pytz
from django.utils.html import strip_tags
from django.utils.timezone import now
from datetime import datetime

from termcolor import cprint

from full_feed_filter.settings import BASE_DIR, DOMAIN


# FULLFEEDFILTER HELPERS
def get_rss_folder(feed_id: int) -> os.path:
    return os.path.join(BASE_DIR, f"media/rss/{feed_id}/")


def get_rss_link(feed_id: int) -> str:
    link_base = f'http://{DOMAIN}'
    return f"{link_base}/feed/{feed_id}/rss/"


# GENERAL HELPERS
def mkdir_if_doesnt_exist(directory: str) -> None:
    if not os.path.exists(directory):
        os.makedirs(directory)


def rss_friendly_datetime(dt: datetime) -> datetime:
    return email.utils.format_datetime(dt)


def strip_special_characters(dirty_string: str, replace_with_space=False, ignore_space=True) -> str:
    if replace_with_space:
        replace_text = ' '
    else:
        replace_text = ''

    if ignore_space:
        regex = '[^A-Za-z0-9 ]+'
    else:
        regex = '[^A-Za-z0-9]+'

    return re.sub(regex, replace_text, dirty_string)


def sanitize_string(dirty_string: str, unescape_string=True, strip_html=True, strip_special_chars=True,
                    replace_special_chars_with_space=False, lowercase=False) -> str:
    """
    Unescaped Text
    Strips HTML Tags
    Remove Special Chars
    Converts to lowercase
    """
    sanitized_string = dirty_string

    if unescape_string:
        sanitized_string = unescape(sanitized_string)

    if strip_html:
        sanitized_string = strip_tags(sanitized_string)

    if strip_special_chars:
        if replace_special_chars_with_space:
            sanitized_string = strip_special_characters(sanitized_string, replace_with_space=True)
        else:
            sanitized_string = strip_special_characters(sanitized_string)

    if replace_special_chars_with_space:
        sanitized_string = strip_special_characters(sanitized_string, replace_with_space=True)

    if lowercase:
        sanitized_string = sanitized_string.lower()

    return sanitized_string.strip()


def now_cst() -> str:
    tz = pytz.timezone('US/Central')
    return datetime.strftime(tz.fromutc(now().replace(tzinfo=tz)), "%m-%d %H:%M")


def remove_folders(folder_dir: str) -> None:
    print(f"Deleting {folder_dir}")
    try:
        shutil.rmtree(folder_dir)
    except OSError as e:
        print("Error: %s - %s." % (e.filename, e.strerror))


def remove_files_modified_x_days_ago(folder_dir: str, days_ago: int) -> list:
    current_time = time.time()
    sec_ago = int(days_ago) * 86400
    files_deleted = []

    files_in_folder = [os.path.join(folder_dir, filename) for filename in os.listdir(folder_dir)]
    for filename in files_in_folder:
        file_modified = os.stat(filename).st_mtime
        modified_ago = current_time - file_modified
        if modified_ago > sec_ago:
            os.remove(filename)
            files_deleted.append(filename)
            print(f"File '{filename}' modified ({ int(modified_ago/86400) })"
                  f" days ago was deleted.")

    return files_deleted


def convert_string_to_list(_string: str) -> list:
    if _string:
        return _string.split(', ')
    else:
        return []


def convert_list_to_string(_list: list) -> (str, None):
    if _list:
        return ', '.join(_list)
    else:
        return None


def sanitize_html(dirty_html: str) -> str:
    from lxml.html.clean import Cleaner
    unescaped_html = unescape(dirty_html).replace("&", "&amp;")
    cleaner = Cleaner(embedded=False)
    return cleaner.clean_html(unescaped_html)


class main_wrapper(object):
    def __init__(self, title):
        self.title = title

    def __call__(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            command_title = self.title
            cprint(f"\n{command_title.upper()}\r", color="grey", on_color="on_magenta", attrs=['bold'])

            func_return = func(*args, **kwargs)

            cprint(f"Completed - {command_title.title()}.", color=None, attrs=['bold'])
            return func_return
        return wrapper

def remove_last_line():
    sys.stdout.write("\033[F")  # Cursor up one line
    print("                                                                                                                    ")
    sys.stdout.write("\033[F")