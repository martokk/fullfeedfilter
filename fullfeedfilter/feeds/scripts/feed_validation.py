import feedparser as feedparser
import requests
from bs4 import BeautifulSoup

from feeds.models import Feeds


class Feedparser:
    def __init__(self, url: str) -> None:
        self.url = url
        self.feedparser = None
        self.title = None
        self.link = None
        self.description = None

        self.is_valid = self.validate()

    def validate(self) -> bool:
        try:
            self.feedparser = feedparser.parse(self.url)
            status = self.feedparser.status

            # If feed url changed, update in database
            changed_status = [
                301,  # 301 Moved Permanently
                302,  # 302 Found (Previously "Moved temporarily")
            ]
            if status in changed_status:
                new_url = self.feedparser.href
                feed = Feeds.objects.filter(url=self.url).first()
                feed.url = new_url
                feed.save()

            allowed_status = [
                200, # OK
            ]

            if status in (allowed_status + changed_status):
                self.title = self.feedparser.feed.title
                try:
                    self.link = self.feedparser.feed.link
                except AttributeError:
                    self.link = self.feedparser.feed.url
                try:
                    self.description = self.feedparser.feed.description
                except AttributeError:
                    self.description = ""
                return True
            else:
                raise Exception(f"Server status = {status}")
        except Exception as e:
            raise e


class ValidateFeed:
    def __init__(self, url: str) -> None:
        self.url = url
        self.status = None
        self.errors = []
        self.improvements = []
        self.is_valid = None

        self.check_feed_url()

    def check_feed_url(self) -> requests:
        payload = {'url': self.url}
        response = requests.post('https://validator.w3.org/feed/check.cgi', data=payload)

        return self.parse_response(response=response)

    @staticmethod
    def get_soup(content: str) -> BeautifulSoup:
        return BeautifulSoup(content, 'html.parser')

    def parse_response(self, response: requests) -> None:
        soup = self.get_soup(response.content)
        self.status = self.build_status(soup)
        self.is_valid = self.is_status_valid(self.status)

        if not self.is_valid:
            self.errors = self.build_errors(soup)

        return

    @staticmethod
    def build_status(soup: BeautifulSoup) -> str:
        all_p = soup.find_all('p')
        return all_p[2].text.strip()

    def build_errors(self, soup: BeautifulSoup) -> list:
        errors = []
        error_ul = soup.find_all('ul')

        for ul in error_ul:
            ul_class = ul.attrs.get('class', None)
            if ul_class:
                return errors
            error_li = ul.find_all('li')
            for li in error_li:
                li_text = li.text.replace("[help]", "")

                error_text = self.format_error(li_text)
                errors.append(error_text)
        return errors

    @staticmethod
    def is_status_valid(status: str) -> bool:
        if status == "This is a valid RSS feed.":
            return True
        else:
            return False

    @staticmethod
    def format_error(error_text: str) -> str:
        if "line" in error_text:
            error_list = error_text.split(":")
            error_list.pop(0)
            error_text = ''.join(error_list)
        return error_text
