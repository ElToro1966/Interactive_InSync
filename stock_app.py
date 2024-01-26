import asyncio

import ib_insync as ibi
import json
import configparser
import os
import logging
import logging.handlers


def get_path_to_cwd(filename):
    root_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(root_path, filename)


def get_config(cfg_file):
    config = configparser.ConfigParser()
    try:
        config.read(get_path_to_cwd(cfg_file))
    except OSError:
        print("Configuration-file not found. Exiting.")
        exit(1)
    return config


def get_contracts():
    contracts_file = get_path_to_cwd("contracts.json")
    with open(contracts_file, "r") as f:
        contracts = json.load(f)
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

    async def run(self, save_file=None):
        save_file = open(save_file, "w")
        with await self.ib.connectAsync(host=self.host, port=self.port, clientId=self.client_id):
            for contract in get_contracts():
                self.ib.reqMktData(contract)

            async for tickers in self.ib.pendingTickersEvent:
                for ticker in tickers:
                    print(ticker)
                    save_file.write(str(ticker))

    def stop(self):
        self.ib.disconnect()


config_file = get_config("config.ini")
data_store = config_file["database"]["save_file"]
app = App()
try:
    asyncio.run(app.run(data_store))
except (KeyboardInterrupt, SystemExit):
    app.stop()