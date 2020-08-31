import yaml
from Utils.utils import Log
from Handlers.data_handler import DataHandler
from Crawlers.naver_news_crawler import NaverNewsCrawler
yaml.warnings({'YAMLLoadWarning': False})
with open("config.yaml", "rt", encoding="utf-8") as stream:
    CONFIG = yaml.load(stream)['NewsCrawler']


if __name__ == '__main__':
    log = Log(__name__)
    data_handler = DataHandler()
    naver_crawler = NaverNewsCrawler(data_handler)

    if CONFIG['is_input_keywords']:
        search_keywords = CONFIG['keywords']
    else:
        search_keywords = data_handler.get_search_keywords()

    if CONFIG['iterate']:
        s_date, e_date = data_handler.get_range_search_date()
    else:
        s_date = CONFIG['start_date']
        e_date = CONFIG['end_date']

    url = naver_crawler.get_target_url(s_date, e_date)
    naver_crawler.execute_crawler(search_keywords, url)
