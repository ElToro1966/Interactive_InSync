# Using IB Gateway and ib_insync to get market data and send it to a Kafka topic with faust

from ib_insync import *


def get_forex(ib_local):
    contract = Forex('EURUSD')
    bars = ib_local.reqHistoricalData(
        contract, endDateTime='', durationStr='30 D',
        barSizeSetting='1 hour', whatToShow='MIDPOINT', useRTH=True)

    # convert to pandas dataframe:
    df = util.df(bars)
    return df


def get_futures(ib_local):
    sub = ScannerSubscription(
        instrument='FUT.US',
        locationCode='FUT.GLOBEX',
        scanCode='TOP_PERC_GAIN')

    scan_data = ib.reqScannerSubscription(sub)
    scan_data.updateEvent += on_scan_data

    ib_local.sleep(60)
    ib_local.cancelScannerSubscription(scan_data)


def get_stocks(ib_local):
    sub = ScannerSubscription(
        instrument=""
    )


def on_scan_data(scandata):
    print(scandata[0])
    print(len(scandata))


if __name__ == '__main__':
    ib = IB()
    ib.connect("10.0.0.10", 4002, clientId=1)

    get_futures(ib)
