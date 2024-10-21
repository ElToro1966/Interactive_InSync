import asyncio

import ib_insync as ibi
import json
import configparser
import os

from kafka import KafkaProducer
from kafka import errors as kafka_errors
import logger.custom_logger as cl


def get_path_to_cwd(filename):
    root_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(root_path, filename)


def get_config(cfg_file):
    config = configparser.ConfigParser()
    try:
        config.read(get_path_to_cwd(cfg_file))
    except OSError as e:
        e_msg: str = f"Configuration-file not found. Error: {e!s}. Exiting."
        logger.error(e_msg)
        exit(1)
    return config


def get_contracts():
    contracts_file = get_path_to_cwd(
        config_file["contracts"]["contracts_file"])
    try:
        with open(contracts_file, "r") as f:
            contracts = json.load(f)
    except OSError as e:
        e_msg: str = f"Contracts-file not found. Error: {e!s}. Exiting."
        logger.error(e_msg)
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
        self.kafka_broker_max_wait = (
            int(config_file["kafka_broker"]["maximum_wait_ms"]))
        self.kafka_broker_max_queue = (
            int(config_file["kafka_broker"]["queue_max_size"]))


    def ticker_to_json(self, ticker):
        '''
        Ticker(contract=Stock(symbol='NVDA', exchange='SMART', currency='USD'), time=datetime.datetime(2024, 10, 21, 11, 59, 48, 692059,
        tzinfo=datetime.timezone.utc), minTick=0.01, bid=137.07, bidSize=100.0, bidExchange='P', ask=137.12, askSize=900.0, askExchange='KPQZNU',
        last=137.07, lastSize=100.0, lastExchange='P', prevBid=137.11, prevBidSize=300.0, prevAsk=137.16, prevAskSize=700.0, prevLast=137.11, volume=24854.0,
        close=138.0, ticks=[TickData(time=datetime.datetime(2024, 10, 21, 11, 59, 48, 692059, tzinfo=datetime.timezone.utc), tickType=0, price=137.07,
        size=100.0)], bboExchange='9c0001', snapshotPermissions=3)

        '''
        ticks_data = []
        for tick in ticker.ticks:
            tick_data = {
                'stock_symbol': ticker.contract.symbol,
                'exchange': ticker.contract.exchange,
                'currency': ticker.contract.currency,
                'transaction_time': ticker.time.strftime('%Y-%m-%d %H:%M:%S.%f'),
                'min_tick': ticker.minTick,
                'bid': ticker.bid,
                'bid_size': ticker.bidSize,
                'bid_exchange': ticker.bidExchange,
                'ask': ticker.ask,
                'ask_size': ticker.askSize,
                'ask_exchange': ticker.askExchange,
                'last': ticker.last,
                'last_size': ticker.lastSize,
                'last_exchange': ticker.lastExchange,
                'prev_bid': ticker.prevBid,
                'prev_bid_size': ticker.prevBidSize,
                'prev_ask': ticker.prevAsk,
                'prev_ask_size': ticker.prevAskSize,
                'prev_last': ticker.prevLast,
                'volume': ticker.volume,
                'close': ticker.close,
                'tick_time': tick.time.strftime('%Y-%m-%d %H:%M:%S.%f'),
                'tick_type': tick.tickType,
                'tick_price': tick.price,
                'tic_size': tick.size,
                'bboExchange': ticker.bboExchange,
                'snapshot_permissions': ticker.snapshotPermissions
            }
            ticks_data.append(tick_data)
        return ticks_data


    async def run(self):
        try:
            kafka_producer = KafkaProducer(
                bootstrap_servers=[self.kafka_broker_address]
            )
        except kafka_errors.KafkaError as e:
            e_msg: str = f"Kafka broker failing. Error: {e!s}. Exiting."
            logger.error(e_msg)
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
                            for tick in self.ticker_to_json(ticker):
                                kafka_producer.send(self.kafka_broker_topic, json.dumps(tick).encode())
                        except kafka_errors.KafkaError as e:
                            e_msg: str = f"Kafka broker failing. Error: {e!s}. Exiting."
                            logger.error(e_msg)
                            exit(1)
        except OSError as e:
            e_msg: str = f"IB Gateway failing. Error: {e!s}. Exiting."
            logger.error(e_msg)
            exit(1)

    def stop(self):
        self.ib.disconnect()


logger = cl.get_custom_logger(__name__)
config_file = get_config("config.ini")
app = App()
try:
    asyncio.run(app.run())
except (KeyboardInterrupt, SystemExit):
    app.stop()
