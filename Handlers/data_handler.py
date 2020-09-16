import os
import yaml
import pandas as pd
from datetime import datetime
from datetime import timedelta
from Utils.utils import Log
from Handlers.mongo_handler import MongoHandler
yaml.warnings({'YAMLLoadWarning': False})

with open("config.yaml", "rt", encoding="utf-8") as stream:
    CONFIG = yaml.load(stream)['NewsCrawler']


class DataHandler:
    def __init__(self):
        self.log = Log(DataHandler)
        self.mongo_handler = MongoHandler()

    def get_search_keywords(self):
        df = pd.DataFrame(self.mongo_handler.get_search_keywords())
        search_keywords = df['company'].unique()
        self.log.debug("search keywords count - {0}".format(len(search_keywords)))

        return search_keywords

    def get_range_search_date(self):
        now_date = datetime.now()
        e_date = now_date.strftime('%Y.%m.%d.%H.%M')
        s_date = (now_date - timedelta(hours=1)).strftime('%Y.%m.%d.%H.%M')
        self.log.debug("start date - {0}, end date - {1}".format(s_date, e_date))

        return s_date, e_date

    def save_file(self, df, keyword, size):
        path = CONFIG['save_file_path']
        if not os.path.exists(path):
            os.makedirs(path)

        self.log.debug("save file name - {0}_{1}.csv".format(keyword, size))
        df.to_csv(path + '/{0}_{1}.csv'.format(keyword, size), sep=',', na_rep='NaN')

    def save_db(self, df):
        self.mongo_handler.add_news_data(df.to_dict('records'))

