import asyncio

import ib_insync as ibi
import json
import configparser
import os
from kafka import KafkaProducer
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
        print("Configuration-file not found. Exiting.")
        exit(1)
    return config


def get_contracts():
    contracts_file = get_path_to_cwd("contracts.json")
    try:
        with open(contracts_file, "r") as f:
            contracts = json.load(f)
    except OSError as e:
        print("Contracts-file not found. Exiting.")
        exit(1)
    contracts_ibi = [
        ibi.Stock(symbol, contracts["exchange"], contracts["currency"])
        for symbol in contracts["symbols"]
    ]
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

    async def run(self):
        kafka_producer = KafkaProducer(
            bootstrap_servers=[self.kafka_broker_address]
        )
        with await self.ib.connectAsync(
                host=self.host, port=self.port, clientId=self.client_id
        ):
            for contract in get_contracts():
                self.ib.reqMktData(contract)

            async for tickers in self.ib.pendingTickersEvent:
                for ticker in tickers:
                    print(ticker)
                    kafka_producer.send(self.kafka_broker_topic, str(ticker).encode())

    def stop(self):
        self.ib.disconnect()


config_file = get_config("config.ini")
app = App()
try:
    asyncio.run(app.run())
except (KeyboardInterrupt, SystemExit):
    app.stop()