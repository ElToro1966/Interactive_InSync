import asyncio

import ib_insync as ibi


class App:

    async def run(self):
        self.ib = ibi.IB()
        with await self.ib.connectAsync("10.0.0.10", 4002, clientId=1):
            contracts = [
                ibi.Stock(symbol, 'SMART', 'USD')
                for symbol in ['BHP', 'DECK', 'INVH', 'LMT', 'MA', 'NSC', 'ORCL',
                               'PFE', 'RTX', 'UNP', 'VMW', 'WM']]
            for contract in contracts:
                self.ib.reqMktData(contract)

            async for tickers in self.ib.pendingTickersEvent:
                for ticker in tickers:
                    print(ticker)

    def stop(self):
        self.ib.disconnect()


app = App()
try:
    asyncio.run(app.run())
except (KeyboardInterrupt, SystemExit):
    app.stop()