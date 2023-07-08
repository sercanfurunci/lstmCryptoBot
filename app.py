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
""" 
SOCKET = "wss://testnet.binance.vision/ws/ethusdt@kline_1m"
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
TRADE_SYMBOL = 'ethusdt' """
""" TRADE_QUANTITY = 0.05
 """
closes = []
in_position = False

@app.route("/")
def index():
    print(request.form)
    title = "CoinTrade"
    account= client.get_account()
    balances = account['balances']
    exchange_info = client.get_exchange_info()
    symbols=exchange_info['symbols']
    return render_template("index.html",title=title,my_balances=balances,symbols=symbols)

@app.route("/buy",methods=['POST'])
def buy():
    print(request.form)
    try:
        symbol = request.form['symbol']
        quantity = request.form['quantity']
        order = client.create_order(symbol=request.form['symbol'], 
            side=SIDE_BUY,
            type=ORDER_TYPE_MARKET,
            quantity=request.form['quantity'])
        flash(f"Bought {quantity} of {symbol} successfully.", "success")
    except Exception as e:
        flash(e.message, "error")
    
    return redirect('/')

@app.route("/sell",methods=['POST'])
def sell():
    print(request.form)
    try:
        symbol = request.form['symbol']
        quantity = request.form['quantity']
        order = client.create_order(symbol=request.form['symbol'], 
            side=SIDE_SELL,
            type=ORDER_TYPE_MARKET,
            quantity=request.form['quantity'])
        flash(f"Sold {quantity} of {symbol} successfully.", "success")
    except Exception as e:
        flash(e.message, "error")
    return redirect('/')

@app.route("/settings")
def settings():
    return "settings"

@app.route("/history")
def history():
    symbol = request.args.get('symbol', 'ETHUSDT')  
    candlesticks = client.get_historical_klines(symbol, Client.KLINE_INTERVAL_1MINUTE, "1 day ago UTC")
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

@app.route("/current_price")
def current_price():
    symbol = request.args.get('symbol')
    ticker = client.get_symbol_ticker(symbol=symbol)
    price = ticker['price']
    return jsonify({'price': price})


@app.route("/bot",methods=['POST'])
def bot():
    TRADE_SYMBOL = request.form.get('symbol')
    TRADE_QUANTITY = request.form.get('trade_quantity')
    RSI_PERIOD = int(request.form.get('rsi_length'))
    RSI_OVERBOUGHT = float(request.form.get('rsi_overbought'))
    RSI_OVERSOLD = float(request.form.get('rsi_oversold'))
    SOCKET = f"wss://testnet.binance.vision/ws/{TRADE_SYMBOL.lower()}@kline_1m"
    # Display the received values
    print("Symbol:", TRADE_SYMBOL)
    print("Trade quantity:",TRADE_QUANTITY)
    print("RSI Length:", RSI_PERIOD)
    print("RSI Overbought:", RSI_OVERBOUGHT)
    print("RSI Oversold:", RSI_OVERSOLD)
    print("Socket:",SOCKET)
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
                        flash("Overbought! Sell! Sell! Sell!")
                        
                        order_succeeded = order(SIDE_SELL, TRADE_QUANTITY, TRADE_SYMBOL)
                        if order_succeeded:
                            in_position = False
                    else:
                        #print("It is overbought, but we don't own any. Nothing to do.")
                        flash("It is overbought, but we don't own any. Nothing to do.")
            
                if last_rsi < RSI_OVERSOLD:
                    if in_position:
                        print("It is oversold, but you already own it, nothing to do.")
                        flash("It is oversold, but you already own it, nothing to do.")
                    else:
                        print("Oversold! Buy! Buy! Buy!")
                        flash("Oversold! Buy! Buy! Buy!")
                        
                        order_succeeded = order(SIDE_BUY, TRADE_QUANTITY, TRADE_SYMBOL)
                        if order_succeeded:
                            in_position = True

                
    ws = websocket.WebSocketApp(SOCKET, on_open=on_open, on_close=on_close, on_message=on_message)
    ws.run_forever()
    return redirect('/')

@app.route('/run_python_script', methods=['POST'])
def run_python_script():
    TRADE_SYMBOL = request.form.get('symbol')
    TRADE_QUANTITY = request.form.get('trade_quantity')
    # print("Symbol:", TRADE_SYMBOL)
    # print("Trade quantity:",TRADE_QUANTITY)
    os.system('python lstmbot.py')
    return 'Python script executed' 
    #return redirect('/')

@app.route("/trade_history")
def trade_history():
    # Get all symbols
    exchange_info = client.get_exchange_info()
    symbols = [symbol['symbol'] for symbol in exchange_info['symbols']]

    # Get user trades for each symbol
    processed_trades = []

    for symbol in symbols:
        trades = client.get_my_trades(symbol=symbol)

        for trade in trades:
            processed_trade = {
                "symbol": trade['symbol'],
                "orderId": trade['orderId'],
                "price": trade['price'],
                "quantity": trade['qty'],
                "time": datetime.datetime.fromtimestamp(trade['time'] / 1000).strftime('%Y-%m-%d %H:%M:%S'),
                "isBuyer": trade['isBuyer'],
                "isMaker": trade['isMaker']
            }

            processed_trades.append(processed_trade)

    # Sort trades by timestamp in descending order (newest to oldest)
    processed_trades = sorted(processed_trades, key=lambda x: x['time'], reverse=True)

    return render_template("trade_history.html", trades=processed_trades)




    
