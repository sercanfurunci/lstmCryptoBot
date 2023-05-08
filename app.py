from flask import Flask, render_template, request, flash, redirect, jsonify
import websocket, json, pprint, talib, numpy
import config, csv, datetime
from binance.client import Client
from binance.enums import *
import os
import subprocess   

app = Flask(__name__)
app.secret_key = b'asdasfazamazqwezayraz'
client = Client(config.API_KEY,config.API_SECRET,testnet=True)

SOCKET = "wss://testnet.binance.vision/ws/ethusdt@kline_15m"
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
TRADE_SYMBOL = 'ethusdt'
TRADE_QUANTITY = 100

@app.route("/")
def index():
    print(request.form)
    title = "CoinView"
    account= client.get_account()
    balances = account['balances']
    exchange_info = client.get_exchange_info()
    symbols=exchange_info['symbols']
    return render_template("index.html",title=title,my_balances=balances,symbols=symbols)

@app.route("/buy",methods=['POST'])
def buy():
    print(request.form)
    try:
        order = client.create_order(symbol=request.form['symbol'], 
            side=SIDE_BUY,
            type=ORDER_TYPE_MARKET,
            quantity=request.form['quantity'])
    except Exception as e:
        flash(e.message, "error")

    return redirect('/')

@app.route("/sell",methods=['POST'])
def sell():
    print(request.form)
    try:
        order = client.create_order(symbol=request.form['symbol'], 
            side=SIDE_SELL,
            type=ORDER_TYPE_MARKET,
            quantity=request.form['quantity'])
    except Exception as e:
        flash(e.message, "error")

    return redirect('/')

@app.route("/settings")
def settings():
    return "settings"

@app.route("/history")
def history():
    symbol = "ETHUSDT"
    candlesticks = client.get_historical_klines(symbol,Client.KLINE_INTERVAL_1MINUTE, "1 day ago UTC")
    processed_candlesticks = []

    for data in candlesticks:
        candlestick = { 
            "time": data[0] / 1000, 
            "open": data[1],
            "high": data[2], 
            "low": data[3], 
            "close": data[4]
        }

        processed_candlesticks.append(candlestick)

    return jsonify(processed_candlesticks)

@app.route("/bot",methods=['POST'])
def bot():
    
    RSI_PERIOD = request.form["rsi_length"]
    RSI_OVERBOUGHT = request.form["rsi_overbought"]
    RSI_OVERSOLD = request.form["rsi_oversold"]
    
    closes = []
    in_position = False

    def order(side, quantity, symbol,order_type=ORDER_TYPE_MARKET):
        try:
            print("sending order")
            order = client.create_order(symbol=symbol, side=side, type=order_type, quantity=quantity)
            print(order)
        except Exception as e:
            print("an exception occured - {}".format(e))
            return False

        return True

    
    def on_open(ws):
        print('opened connection')

    def on_close(ws):
        print('closed connection')

    def on_message(ws, message):
        global closes, in_position
    
        print('received message')
        json_message = json.loads(message)
        pprint.pprint(json_message)

        candle = json_message['k']

        is_candle_closed = candle['x']
        close = candle['c']

        if is_candle_closed:
            print("candle closed at {}".format(close))
            closes.append(float(close))
            print("closes")
            print(closes)

            if len(closes) > RSI_PERIOD:
                np_closes = numpy.array(closes)
                rsi = talib.RSI(np_closes, RSI_PERIOD)
                print("all rsis calculated so far")
                print(rsi)
                last_rsi = rsi[-1]
                print("the current rsi is {}".format(last_rsi))

                if last_rsi > RSI_OVERBOUGHT:
                    if in_position:
                        print("Overbought! Sell! Sell! Sell!")
                        # put binance sell logic here
                        order_succeeded = order(SIDE_SELL, TRADE_QUANTITY, TRADE_SYMBOL)
                        if order_succeeded:
                            in_position = False
                    else:
                        print("It is overbought, but we don't own any. Nothing to do.")
            
                if last_rsi < RSI_OVERSOLD:
                    if in_position:
                        print("It is oversold, but you already own it, nothing to do.")
                    else:
                        print("Oversold! Buy! Buy! Buy!")
                        # put binance buy order logic here
                        order_succeeded = order(SIDE_BUY, TRADE_QUANTITY, TRADE_SYMBOL)
                        if order_succeeded:
                            in_position = True

                
    ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message)
    ws.run_forever()
    return redirect('/')

@app.route('/run_python_script', methods=['POST'])
def run_python_script():
    os.system('python lstmbot.py')
    return 'Python script executed'


    
