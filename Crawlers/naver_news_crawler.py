import re
import requests
import random
import time
import yaml
import datetime
import pandas as pd
from konlpy.tag import Mecab
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

        self.mecab = Mecab()
        self.data_handler = data_handler
        self.pattern_publisher = r"\s?[가-힣\s]{3,}기자"
        self.pattern_email = r"([\w-]+)@([\w\.-]+)(\.[\w\.]+)"
        driver_path = CONFIG['chromedriver_path']

        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
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

    # def _extract_publisher(self, article):
    #     publisher = None
    #     match = re.search(self.pattern_publisher, article)
    #     if match:
    #         publisher = match.group()
    #
    #     if publisher is not None:
    #         publisher = publisher.strip()
    #         tmp_publisher = publisher.split(" ")
    #
    #         if len(tmp_publisher) == 1:
    #             publisher = tmp_publisher[0].replace("기자", "")
    #         elif len(tmp_publisher) == 2:
    #             publisher = tmp_publisher[0]
    #         elif len(tmp_publisher) == 3:
    #             publisher = tmp_publisher[1]
    #
    #     self.log.debug("publisher - {0}".format(publisher))
    #     return publisher
    #
    # def _extract_publisher_email(self, article):
    #     email = None
    #     match = re.search(self.pattern_email, article)
    #     if match:
    #         email = match.group()
    #
    #     if email is not None:
    #         email = email.strip()
    #
    #     self.log.debug("publisher email - {0}".format(email))
    #     return email

    def execute_crawler(self, keywords, url):
        # ToDo: 기자가 많이 언급될 경우 다른 기자이름에 다른 이메일이 매칭 될 수 있음. 수정 필요
        self.log.debug("search keywords - {0}".format(keywords))
        self.log.debug("target url - {0}".format(url))

        for idx, (code, keyword, business_code, business) in tqdm(enumerate(keywords), total=len(keywords)):
            page_num = 1
            search_url = url.format(keyword)
            self.log.debug("search URL - {0}".format(search_url))

            self.driver.get(search_url)
            tmp_df = pd.DataFrame(
                columns=['title', 'link', 'press', 'date', 'reporter', 'email', 'article', 'search_keyword', 'company',
                         'company_code', 'business_code', 'business']
            )

            while page_num <= 10:
                html = self.driver.page_source
                soup = BeautifulSoup(html, 'html.parser')
                for urls in soup.select("a.info"):
                    if urls["href"].startswith("https://news.naver.com"):
                        self.log.debug("Get URL - {0}".format(urls['href']))
                        self.driver.get(urls["href"])
                        news_html = self.driver.page_source
                        news_html_soup = BeautifulSoup(news_html, 'html.parser')

                        tmp_title = news_html_soup.title(string=True)
                        tmp_date = news_html_soup.select('.t11')
                        tmp_article = news_html_soup.select('#articleBodyContents')
                        tmp_press = news_html_soup.select('#footer address')

                        title = tmp_title[0].replace(" : 네이버 뉴스", "")
                        if len(tmp_date) == 0:
                            tmp_date = news_html_soup.select('.article_info')[0].find('em')
                            p_date = tmp_date.get_text().split(" ")[0]
                        else:
                            p_date = tmp_date[0].get_text().split(" ")[0]
                        p_date = datetime.datetime.strptime(p_date, "%Y.%m.%d.")
                        if len(tmp_article) == 0:
                            tmp_article = news_html_soup.select('#articeBody')
                        article = tmp_article[0].get_text().replace('\n', "").replace('\t', "")
                        if not tmp_press[0].a:
                            tmp_press = news_html_soup.select(".article_footer")
                            press = tmp_press[0].a.get_text().replace("\n", "").replace("\t", "").split(" ")[0]
                        else:
                            press = tmp_press[0].a.get_text()

                        email = ""
                        publisher = ""
                        publisher_match = re.search(self.pattern_publisher, article)
                        email_match = re.search(self.pattern_email, article)
                        if publisher_match and email_match:
                            tmp_publisher = publisher_match.group()
                            tmp_publisher = tmp_publisher.strip().split(" ")

                            if len(tmp_publisher) == 1:
                                publisher = tmp_publisher[0].replace("기자", "")
                            elif len(tmp_publisher) == 2:
                                publisher = tmp_publisher[0]
                            elif len(tmp_publisher) == 3:
                                publisher = tmp_publisher[1]

                            tmp_email = email_match.group()
                            email = tmp_email.strip()

                        tokens = self.mecab.pos(str(article))
                        nouns_tokens = [word for word, tag in tokens if tag == 'NNG' or tag == 'NNP']
                        tokens_str = ' '.join(nouns_tokens)

                        tmp_df = tmp_df.append({
                            'title': title, 'link': urls["href"], 'press': press,
                            'date': p_date, 'reporter': publisher, 'email': email,
                            'article': article, 'search_keyword': keyword,
                            'company': keyword, 'company_code': code,
                            'business_code': business_code, 'business': business,
                            'tokens_split': nouns_tokens, 'tokens': tokens_str
                        }, ignore_index=True)
                        self.log.debug("title-{0}, date-{1}, press-{2}, company-{3}".format(title, p_date,
                                                                                            press, keyword))
                        time.sleep(random.randrange(3, 10))
                        self.driver.back()

                page_num += 1
                if len(self.driver.find_elements_by_class_name('next')) > 0:
                    element = self.driver.find_element_by_class_name("next")
                    element.click()
                else:
                    break

            self.log.debug("Save News data cnt - {0}".format(len(tmp_df)))
            if len(tmp_df) > 0:
                self.data_handler.save_db(tmp_df)
        self.driver.quit()
