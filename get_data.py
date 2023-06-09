import config, csv
from binance.client import Client

client = Client(config.API_KEY, config.API_SECRET)

info= client.get_account()
balances = info['balances']
    

for i in balances:
    print(i)


# prices = client.get_all_tickers()

# for price in prices:
#     print(price)

csvfile = open('2020_15mins.csv', 'w', newline='') 
candlestick_writer = csv.writer(csvfile, delimiter=',')

candlesticks = client.get_historical_klines("BTCUSDT", Client.KLINE_INTERVAL_15MINUTE,"1 Jan 2020","14 Jul 2020")

for candlestick in  candlesticks:
    candlestick[0] = candlestick[0] / 1000
    candlestick_writer.writerow(candlestick)

csvfile.close()