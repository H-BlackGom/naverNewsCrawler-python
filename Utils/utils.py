import yaml
import logging
import logging.handlers
yaml.warnings({'YAMLLoadWarning': False})

with open("config.yaml", "rt", encoding="utf-8") as stream:
    CONFIG = yaml.load(stream)['NewsCrawler']


class Log:
    def __init__(self, service_name):
        self.service_name = service_name
        self.default_massage = '/{0} :: '.format(self.service_name)
        self.logger = logging.getLogger('crumbs')

        # Check handler exists
        if len(self.logger.handlers) <= 0:
            if CONFIG['debug']:
                self.logger.setLevel(logging.DEBUG)
            else:
                self.logger.setLevel(logging.INFO)

            formatter = logging.Formatter('%(asctime)s %(levelname)s%(message)s')
            stream_handler = logging.StreamHandler()
            stream_handler.setFormatter(formatter)

            self.logger.addHandler(stream_handler)

    def debug(self, message):
        self.logger.debug(self.default_massage+message)

    def info(self, message):
        self.logger.info(self.default_massage+message)

    def warning(self, message):
        self.logger.warning(self.default_massage+message)

    def error(self, message):
        self.logger.error(self.default_massage+message)
