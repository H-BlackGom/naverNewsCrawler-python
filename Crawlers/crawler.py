from abc import ABC, abstractmethod
from Utils.utils import Log


class Crawler(ABC):
    def __init__(self, class_obj):
        self.log = Log(class_obj)

    @abstractmethod
    def execute_crawler(self, keywords, url):
        pass
