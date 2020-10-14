import re
import requests
import datetime
import random
import time
from tqdm.notebook import tqdm
import pandas as pd
from selenium import webdriver
from pymongo import MongoClient
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from bs4 import BeautifulSoup

# chrome driver setting.
# driver_path = '../Driver/chromedriver'
driver_path = '/usr/local/bin/chromedriver'

options = webdriver.ChromeOptions()
options.add_argument('headless')
options.add_argument('window-size=1920x1080')
options.add_argument("disable-gpu")
options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.122 Safari/537.36")

driver = webdriver.Chrome(driver_path, chrome_options=options)
driver.implicitly_wait(3)

pattern_publisher = r"\s?[가-힣\s]{3,}기자"
pattern_email = r"([\w-]+)@([\w\.-]+)(\.[\w\.]+)"
url = "https://search.naver.com/search.naver?where=news&query={0}&sm=tab_opt&sort=0&photo=0&field=0&reporter_article=&pd=2&ds=&de=&docid=&nso=so%3Ar%2Cp%3A1m%2Ca%3Aall&mynews=0&refresh_start=0&related=0"

conn = MongoClient('192.168.0.12', 27017)
category_collection = conn['Changsung']['stock_category']
save_collection = conn['Changsung']['news']

comapny_infos = list(category_collection.find({}))
df = pd.DataFrame(comapny_infos)

company_info = list(zip(*map(df.get, df[['code', 'company', 'business_code', 'business']])))
print(comapny_infos)

tmp_df = pd.DataFrame(
    columns=['title', 'link', 'press', 'date', 'reporter', 'email', 'article', 'search_keyword', 'company',
             'company_code', 'business_code', 'business']
)

for idx, (code, company, business_code, business) in tqdm(enumerate(company_info), total=len(company_info)):
    page_num = 1
    search_url = url.format(company)
    driver.get(search_url)

    while page_num <= 50:
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        for urls in soup.select("._sp_each_url"):
            if urls["href"].startswith("https://news.naver.com"):
                driver.get(urls["href"])
                news_html = driver.page_source
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
                publisher_match = re.search(pattern_publisher, article)
                email_match = re.search(pattern_email, article)
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

                tmp_df = tmp_df.append({
                    'title': title, 'link': urls["href"], 'press': press,
                    'date': p_date, 'reporter': publisher, 'email': email,
                    'article': article, 'search_keyword': company,
                    'company': company, 'company_code': code,
                    'business_code': business_code, 'business': business
                }, ignore_index=True)
                print("title-{0}, date-{1}, press-{2}, company-{3}".format(title, p_date, press, company))
                time.sleep(random.randrange(3, 10))

        page_num += 1
        if len(driver.find_elements_by_class_name('next')) > 0:
            element = driver.find_element_by_class_name("next")
            element.click()
        else:
            break

    if len(tmp_df) > 0:
        save_collection.insert_many(tmp_df.to_dict('records'))
    driver.quit()
