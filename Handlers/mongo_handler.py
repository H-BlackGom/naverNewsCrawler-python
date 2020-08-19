import yaml
from pymongo import MongoClient
from Utils.utils import Log
yaml.warnings({'YAMLLoadWarning': False})

with open("config.yaml", "rt", encoding="utf-8") as stream:
    CONFIG = yaml.load(stream)['NewsCrawler']


class MongoHandler:
    def __init__(self):
        self.log = Log(MongoHandler)
        conn = MongoClient(CONFIG['DB_ip'], CONFIG['DB_port'])

        self.save_collection = conn[CONFIG['DB_name']][CONFIG['collection_name']]
        self.log.info("MongoDB connection to {0} collection. - {1}".format(
            CONFIG['collection_name'], self.save_collection
        ))

        if not CONFIG['is_input_keywords']:
            self.category_collection = conn[CONFIG['DB_name']]['stock_category']
            self.log.info("MongoDB connection to category collection. - {0}".format(
                self.category_collection
            ))

    def get_search_keywords(self):
        if CONFIG['is_input_keywords']:
            raise self.log.warning("Check is_input_keywords option")

        query = {}
        category_info = list(self.category_collection.find(query))
        return category_info

    def add_news_data(self, news_dict):
        self.save_collection.insert_many(news_dict)
