import asyncio

import ib_insync as ibi
import json
import configparser
import os

from kafka import KafkaProducer
from kafka import errors as kafka_errors
import logging
import logging.handlers


def get_path_to_cwd(filename):
    root_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(root_path, filename)


def get_config(cfg_file):
    config = configparser.ConfigParser()
    try:
        config.read(get_path_to_cwd(cfg_file))
    except OSError as e:
        print(f"Configuration-file not found. Error: {e!s}. Exiting.")
        exit(1)
    return config


def get_contracts():
    contracts_file = get_path_to_cwd(
        config_file["contracts"]["contracts_file"])
    try:
        with open(contracts_file, "r") as f:
            contracts = json.load(f)
    except OSError as e:
        logging.error(e)
        print(f"Contracts-file not found. Error: {e!s}. Exiting.")
        exit(1)
    contracts_ibi = []
    for contracts_per_exchange in contracts["exchanges"]:
        contracts_ibi.extend(
            [ibi.Stock(symbol, contracts_per_exchange["name"],
                       contracts_per_exchange["currency"])
             for symbol in contracts_per_exchange["symbols"]
            ]
        )
    return contracts_ibi


class App:

    def __init__(self):
        self.ib = ibi.IB()
        self.host = config_file["ib_gateway"]["host"]
        self.port = int(config_file["ib_gateway"]["port"])
        self.client_id = int(config_file["ib_gateway"]["client_id"])
        self.kafka_broker_address = config_file["kafka_broker"]["address"]
        self.kafka_broker_topic = config_file["kafka_broker"]["topic"]
        self.kafka_broker_max_wait = int(config_file["kafka_broker"]["maximum_wait_ms"])
        self.kafka_broker_max_queue = int(config_file["kafka_broker"]["queue_max_size"])
        self.log_file = get_path_to_cwd(config_file["logging"]["log_file"])
        self.log_level = config_file["logging"]["log_level"]
        logging.basicConfig(filename=self.log_file, encoding='utf-8', level=self.log_level)

    async def run(self):
        try:
            kafka_producer = KafkaProducer(
                bootstrap_servers=[self.kafka_broker_address]
            )
        except kafka_errors.KafkaError as e:
            logging.error(e)
            print(f"Kafka broker failing. Error: {e!s}. Exiting.")
            exit(1)
        try:
            with await self.ib.connectAsync(
                    host=self.host, port=self.port, clientId=self.client_id
            ):
                for contract in get_contracts():
                    self.ib.reqMktData(contract)

                async for tickers in self.ib.pendingTickersEvent:
                    for ticker in tickers:
                        print(ticker)
                        try:
                            kafka_producer.send(self.kafka_broker_topic, str(ticker).encode())
                        except kafka_errors.KafkaError as e:
                            logging.error(e)
                            print(f"Kafka broker failing. Error: {e!s} Exiting.")
                            exit(1)
        except OSError as e:
            logging.error(e)
            print(f"IB Gateway failing. Error: {e!s}. Exiting.")
            exit(1)

    def stop(self):
        self.ib.disconnect()


config_file = get_config("config.ini")
app = App()
try:
    asyncio.run(app.run())
except (KeyboardInterrupt, SystemExit):
    app.stop()