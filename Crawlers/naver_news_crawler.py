import re
import requests
import random
import time
import yaml
import pandas as pd
from tqdm import tqdm
from bs4 import BeautifulSoup
from selenium import webdriver
from Crawlers.crawler import Crawler
yaml.warnings({'YAMLLoadWarning': False})

with open("config.yaml", "rt", encoding="utf-8") as stream:
    CONFIG = yaml.load(stream)['NewsCrawler']


class NaverNewsCrawler(Crawler):
    def __init__(self, data_handler):
        super(NaverNewsCrawler, self).__init__(NaverNewsCrawler)

        self.data_handler = data_handler
        self.pattern_publisher = r"\s?[가-힣\s]{3,}기자"
        self.pattern_email = r"([\w-]+)@([\w\.-]+)(\.[\w\.]+)"
        driver_path = CONFIG['chromedriver_path']

        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        options.add_argument('window-size=1920x1080')
        options.add_argument("disable-gpu")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.122 Safari/537.36"
        )

        self.driver = webdriver.Chrome(driver_path, chrome_options=options)
        self.driver.implicitly_wait(3)

    def _change_date_format(self, s_date, e_date):
        s_from = s_date.replace(".", "")
        e_to = e_date.replace(".", "")
        self.log.debug("re-formatting s_date - {0}, e_date - {1}".format(s_from, e_to))

        return s_from, e_to

    def get_target_url(self, s_date, e_date):
        s_from, e_to = self._change_date_format(s_date, e_date)

        if CONFIG['iterate']:
            url = "https://search.naver.com/search.naver?&where=news&query={0}" + \
                  "&sm=tab_pge&sort=0&photo=0&field=0&reporter_article=&pd=7&ds=" + s_date + "&de=" + e_date + \
                  "&docid=&nso=so:r,p:1h,a:all&mynews=0&cluster_rank=29&start=1&refresh_start=0"

        else:
            url = "https://search.naver.com/search.naver?where=news&query={0}" + \
                  "&sort=0&ds=" + s_date + "&de=" + e_date + \
                  "&nso=so%3Ar%2Cp%3Afrom" + s_from + "to" + e_to + "%2Ca%3A"

        self.log.debug("URL according to conditions - {0}".format(url))
        return url

    def _extract_publisher(self, article):
        publisher = None
        match = re.search(self.pattern_publisher, article)
        if match:
            publisher = match.group()

        if publisher is not None:
            publisher = publisher.strip()
            tmp_publisher = publisher.split(" ")

            if len(tmp_publisher) == 1:
                publisher = tmp_publisher[0].replace("기자", "")
            elif len(tmp_publisher) == 2:
                publisher = tmp_publisher[0]
            elif len(tmp_publisher) == 3:
                publisher = tmp_publisher[1]

        self.log.debug("publisher - {0}".format(publisher))
        return publisher

    def _extract_publisher_email(self, article):
        email = None
        match = re.search(self.pattern_email, article)
        if match:
            email = match.group()

        if email is not None:
            email = email.strip()

        self.log.debug("publisher email - {0}".format(email))
        return email

    def execute_crawler(self, keywords, url):
        # ToDo: 기자가 많이 언급될 경우 다른 기자이름에 다른 이메일이 매칭 될 수 있음. 수정 필요
        self.log.debug("search keywords - {0}".format(keywords))
        self.log.debug("target url - {0}".format(url))

        for idx, keyword in tqdm(enumerate(keywords), total=len(keywords)):
            page_num = 1
            search_url = url.format(keyword)
            self.log.debug("search URL - {0}".format(search_url))

            self.driver.get(search_url)
            tmp_df = pd.DataFrame(
                columns=['title', 'link', 'press', 'date', 'reporter', 'email', 'article', 'search_keyword']
            )

            while True:
                html = self.driver.page_source
                soup = BeautifulSoup(html, 'html.parser')

                for urls in soup.select("._sp_each_url"):
                    try:
                        if urls["href"].startswith("https://news.naver.com"):
                            detail_news_req = requests.get(urls["href"])
                            detail_news_soup = BeautifulSoup(detail_news_req.content, 'html.parser')

                            title = detail_news_soup.select('h3#articleTitle')[0].text
                            publish_date = detail_news_soup.select('.t11')[0].get_text()[:11]
                            _text = detail_news_soup.select('#articleBodyContents')[0].get_text().replace('\n', " ")
                            article = _text.replace("// function _flash_removeCallback() {}", "")
                            company = detail_news_soup.select('#footer address')[0].a.get_text()
                            publisher = self._extract_publisher(article)
                            email = self._extract_publisher_email(article)

                            if publisher is None or email is None:
                                continue

                            tmp_df = tmp_df.append({
                                'title': title, 'link': urls["href"], 'press': company,
                                'date': publish_date, 'reporter': publisher, 'email': email,
                                'article': article, 'search_keyword': keyword
                            }, ignore_index=True)

                            time.sleep(random.randrange(3, 10))
                    except Exception as e:
                        self.log.warning(e.__traceback__)
                        continue

                page_num += 1
                if page_num > 50:
                    break

                if len(self.driver.find_elements_by_class_name('next')) > 0:
                    element = self.driver.find_element_by_class_name("next")
                    element.click()
                else:
                    break

            if len(tmp_df) > 0:
                self.data_handler.save_file(tmp_df, keyword, len(tmp_df))
                self.data_handler.save_db(tmp_df)
        self.driver.quit()
