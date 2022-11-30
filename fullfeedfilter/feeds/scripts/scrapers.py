import os
from html import unescape

import requests
import yaml
from bs4 import BeautifulSoup
from full_feed_filter.settings import BASE_DIR
from newspaper import Article


class Scraper:
    def __init__(self, url: str) -> None:
        self.url = url
        self.config = self.get_url_config()
        self.soup = self.get_soup()

        self.additional_images = None
        self.top_image = None
        self.tags = []
        self.article_html = None
        self.movies = None
        self.title = None

    def get_url_config(self) -> dict:
        yml = yaml.load(
            open(os.path.join(BASE_DIR, "feeds/scripts/scrapers.yaml")), Loader=yaml.BaseLoader
        )
        result = None
        for site, config in yml.items():
            for item in config:
                if item["url"] in self.url:
                    result = item
        if result:
            return result
        else:
            raise AttributeError("URL not found in scrapers.yaml")

    def get_soup(self) -> BeautifulSoup:
        resp = requests.get(self.url, timeout=5)
        if resp.status_code == 200:
            return BeautifulSoup(resp.content, "html.parser")
        else:
            raise Exception(f"Status code: {resp.status_code}")

    def get_html_from_selector(self, selector: str, raw=False, remove=None) -> (str, None):
        if selector is None:
            return None

        raw_html = self.soup.select_one(selector)

        if raw_html is None:
            return None

        if raw:
            return raw_html
        else:
            html_string = raw_html.__str__()
            if remove:
                html_string = html_string.replace(str(remove), "")
            return html_string

    def get_article_p_html(
        self, article_selector: str, article_stop_div_classname=None, remove=None
    ) -> (None, str):
        raw_html = self.soup.select_one(article_selector)

        if raw_html is None:
            return None

        p_soup = raw_html.find_all("p")

        html_string = ""
        for p in p_soup:

            # ARTICLE STOP CLASS
            if article_stop_div_classname:
                if p.find_parents("div", article_stop_div_classname):
                    continue

            html_string += p.__str__()

        if remove:
            html_string = html_string.replace(str(remove), "")
        return html_string

    def get_tags(self, tags_selector: str) -> (list, None):
        raw_html = self.soup.select_one(tags_selector)

        if raw_html is None:
            return None

        try:
            li_soup = list(raw_html.findAll("li"))
        except AttributeError:
            raise AttributeError(
                f"Could not get tags -- url={self.url}; tags_classname={tags_selector}"
            )

        tags = []
        for li in li_soup:
            tags.append(li.text.strip())

        return tags

    def get_top_image(self) -> (None, str):
        all_images = self.additional_images
        if all_images:
            return all_images[0]
        else:
            return None

    def get_all_images(self, images_selector: str) -> (list, None):
        raw_html = self.soup.select_one(images_selector)

        if raw_html is None:
            return None

        try:
            images = []
            img_soup = raw_html.find_all("img")

            if img_soup:
                for img in img_soup:
                    img_src = img.get("src")
                    if "http" in img_src:
                        images.append(img_src)
                return images
            else:
                return None
        except TypeError:
            return None
        except AttributeError:
            return None


class SimpleScraper(Scraper):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        if self.config.get("images"):
            self.additional_images = self.get_all_images(self.config.get("images"))
            self.top_image = self.get_top_image()
        if self.config.get("tags"):
            self.tags = self.get_tags(self.config["tags"])
        if self.config.get("article"):
            self.article_html = self.get_article_p_html(
                article_selector=self.config["article"],
                article_stop_div_classname=self.config.get("article_stop", None),
            )


class CraigslistScraper(SimpleScraper):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        # self.additional_images = self.get_all_images()
        # self.top_image = self.get_top_image('')
        self.additional_details = self.get_html_from_selector(self.config.get("additional_details"))
        self.map = self.get_html_from_selector(self.config.get("map"))

        old_article_html = self.get_html_from_selector(
            self.config.get("article"), remove=self.config.get("remove")
        )
        self.article_html = self.append_to_article_html(old_article_html=old_article_html)

    def get_top_image(self) -> (None, str):
        if self.additional_images:
            return self.additional_images[0]
        else:
            return None

    def get_all_images(self, images_selector: str) -> (list, None):
        raw_html = self.soup.select_one(images_selector)

        if raw_html is None:
            return None

        try:
            images = []
            img_soup = raw_html.find_all("a")

            if img_soup:
                for img in img_soup:
                    images.append(img.get("href"))
                return images
            else:
                img_soup = raw_html.find_all("img")

                if img_soup:
                    for img in img_soup:
                        images.append(img.get("src"))
                    return images
                else:
                    return None
        except TypeError:
            return None
        except AttributeError:
            return None

    def append_to_article_html(self, old_article_html: str) -> str:
        article_html = old_article_html

        if self.additional_details:
            article_html += f"<p>{self.additional_details}</p>"
        if self.map:
            article_html += f"<p><b><u>Address:</b></u> {self.map}</p>"

        return article_html


class RedditScraper:
    def __init__(self, url: str) -> None:
        self.url = url
        self.config = self.get_url_config()
        self.json = self.get_json_dump()

        # JSON Objects
        self.selftext_html = self.json["selftext_html"]
        self._url = self.json["url"]
        self.media = self.json["media"]
        self.score = self.json["score"]
        self.spoiler = self.json["spoiler"]
        self.subreddit = self.json["subreddit"]
        self.is_reddit_media_domain = self.json["is_reddit_media_domain"]
        self.is_self = self.json["is_self"]
        self.thumbnail = self.json["thumbnail"]
        self.domain = self.json["domain"]
        self.post_hint = self.json.get("post_hint", "")
        self.link_flair_text = self.json["link_flair_text"]

        # Article Objects
        self.post_type = self.get_post_type()
        self.title = self.build_title()
        self.additional_images = None
        self.movies = None
        self.top_image = self.get_top_image()
        self.tags = []
        self.article_html = self.build_article_html()
        pass

    def get_url_config(self) -> str:
        yml = yaml.load(
            open(os.path.join(BASE_DIR, "feeds/scripts/scrapers.yaml")), Loader=yaml.BaseLoader
        )
        result = None
        for site, config in yml.items():
            for item in config:
                if item["url"] in self.url:
                    result = item
        if result:
            return result
        else:
            raise AttributeError("URL not found in simple_scraper.yaml")

    def get_json_dump(self) -> requests:
        r = requests.get(f"{self.url}.json", headers={"user-agent": "Mozilla/5.0"})
        return r.json()[0]["data"]["children"][0]["data"]

    def build_title(self) -> str:
        title = self.json["title"]
        pre_title = None

        # Build Pre-Title
        if self.post_type == "video":
            pre_title = "VIDEO"
        elif self.post_type == "image":
            pre_title = "IMG"
        elif self.post_type == "tweet":
            pre_title = "TWEET"
        elif self.post_type == "article":
            pre_title = "ARTICLE"

        if pre_title:
            title = f"{pre_title}: {title}"

        # Build Spoiler Pre-Title
        if self.spoiler:
            if self.link_flair_text:
                title = f"[[ SPOILER - {self.link_flair_text.upper()} ]] -- {title}"
            else:
                title = f"[[ SPOILER ]] -- {title}"

        return title

    def is_img(self):
        if self.is_reddit_media_domain:
            return True
        if "image" in self.post_hint:
            return True
        if (
            ".jpg" in self._url
            or ".jpeg" in self._url
            or ".png" in self._url
            or ".gif" in self._url
        ):
            return True
        return False

    def get_post_type(self) -> str:
        if self.is_self:
            return "self"
        elif self.is_img():
            return "image"
        elif self.media or "video" in self.post_hint:
            return "video"
        elif "twitter" in self._url:
            return "tweet"
        elif self._url:
            return "article"
        else:
            return "unknown"

    def get_top_image(self) -> str:
        if self.post_type == "image":
            return self._url

    def get_tags(self) -> list:
        if self.link_flair_text:
            return [self.link_flair_text]
        else:
            return []

    def build_article_html(self) -> str:
        article_html = ""

        # Spoilers
        if self.spoiler:
            article_html += (
                '<div align="left">'
                '<hr style="margin: 0px; width: 100%; display: inline-block;">'
                '<span style="display: block; margin: 0px; margin-left: 40%">SPOILERS</span>'
                '<hr style="margin: 0px; width: 100%; display: inline-block;">'
                "</div><br /><br />"
            )

        # Self
        if self.post_type == "self":
            if self.selftext_html:
                html = unescape(self.selftext_html)
                article_html += f"<p>{html}</p>"
            else:
                article_html += f"<p>{self.title}</p>"

        # Image
        elif self.post_type == "image":
            article_html += f"<p></p>"

        # Video / Article / Tweet
        else:
            if self._url:
                article_html += self.handle_other_url()

        return article_html

    def handle_other_url(self) -> str:
        try:
            article_html = ""

            # Download & Parse via Newspaper
            article = Article(url=self._url, keep_article_html=True)
            article.download()
            article.parse()
            article.nlp()

            # Append Top Image
            if article.top_image:
                article_html += f'<p><img src="{article.top_image}" /><p/>'

            # Handle if Tweet or Article/Video
            if self.post_type == "tweet":
                article_html += self.handle_twitter()
            else:
                article_html += self.handle_newspaper_full_article(article=article)

            # Append Tags
            self.tags += article.keywords
            self.tags += article.meta_keywords
            self.tags += article.tags

            return article_html

        except Exception as e:
            raise e

    def handle_twitter(self) -> str:
        article_html = ""
        article_html += f"<h3>Tweet</h3>"
        article_html += f"<p>URL: <a href='{self._url}'>{self._url}</a></p>"

        resp = requests.get(self._url, timeout=5)
        soup = BeautifulSoup(resp.content, "html.parser")

        raw_html = soup.select_one("div.js-tweet-text-container")
        html_string = raw_html.__str__()

        article_html += f"{html_string}"

        return article_html

    def handle_newspaper_full_article(self, article) -> str:
        article_html = ""

        # Append Article Title & Text
        article_html += f"<h2><a href='{self._url}'>{article.title}</a></h2>"
        article_html += f"<p>{article.article_html}</p>"
        article_html += f"<p>Article URL: <a href='{self._url}'>{self._url}</a></p>"

        # Append Embedded Video
        if self.media:
            try:
                html = unescape(self.json["media"]["oembed"]["html"])
            except KeyError as e:
                html = (
                    f"Unable to get html for embedded video ({e.__str__()}).<br />"
                    f"<a href='{self._url}'>Click Here</a> to view the video."
                )

            article_html += f'<p class="embedded-video">{ html }</p>'

        if article.movies:
            self.movies = article.movies

        return article_html
