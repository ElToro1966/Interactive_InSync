import logging.config
import yaml


def get_custom_logger(name):
    with open("logger/logger_config.yaml", "r") as config_file:
        config = yaml.safe_load(config_file.read())
        logging.config.dictConfig(config)
    return logging.getLogger(name)