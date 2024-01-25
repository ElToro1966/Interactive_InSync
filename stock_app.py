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


class App:

    def __init__(self):
        self.ib = ibi.IB()
        self.host = config_file["ib_gateway"]["host"]
        self.port = int(config_file["ib_gateway"]["port"])
        self.client_id = int(config_file["ib_gateway"]["client_id"])

    async def run(self, save_file=None):
        save_file = open(save_file, "w")
        print(self.host, self.port, self.client_id)
        with await self.ib.connectAsync(host=self.host, port=self.port, clientId=self.client_id):
            '''
            contracts = [
                ibi.Stock(symbol, 'SMART', 'USD')
                for symbol in ['BHP', 'DECK', 'INVH', 'LMT', 'MA', 'NSC', 'ORCL',
                               'PFE', 'RTX', 'UNP', 'WM']]
            '''
            contracts = [
                ibi.Stock(symbol, 'SMART', 'CAD')
                for symbol in ['AC','RCI.A','RCI.B']
            ]
            for contract in contracts:
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