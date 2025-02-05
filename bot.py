import os
import alpaca_trade_api as tradeapi
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from datetime import datetime, timedelta
import time
import pytz

# טוען משתנים מקובץ .env
load_dotenv()
API_KEY = os.getenv("APCA_API_KEY_ID")
API_SECRET = os.getenv("APCA_API_SECRET_KEY")
BASE_URL = os.getenv("APCA_API_BASE_URL")

# חיבור ל-Alpaca API
api = tradeapi.REST(API_KEY, API_SECRET, BASE_URL, api_version='v2')

# משתנה גלובלי לבדיקת ריצה
running = False

def stop_bot():
    global running
    running = False

def get_bars(symbol):
    try:
        now = datetime.now(pytz.UTC)
        start_time = now - timedelta(minutes=15)

        bars = api.get_bars(symbol, tradeapi.TimeFrame.Minute, start=start_time.isoformat(), end=now.isoformat(), feed="iex").df

        if bars.empty:
            print(f"❌ No new data available for {symbol}.")
            return None

        bars['timestamp'] = bars.index
        return bars

    except Exception as e:
        print(f"❌ Error fetching bars: {e}")
        return None

def calculate_indicators(bars):
    prices = bars["close"].values
    volume = bars["volume"].values

    # חישוב VWAP
    vwap_numerator = sum(volume[i] * prices[i] for i in range(len(prices)))
    vwap_denominator = sum(volume)
    vwap = vwap_numerator / vwap_denominator if vwap_denominator != 0 else 0

    # חישוב MACD
    prices_series = pd.Series(prices)
    ema12 = prices_series.ewm(span=12, adjust=False).mean()
    ema26 = prices_series.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    histogram = macd - signal

    # חישוב ATR (מתוקן)
    high_low = bars["high"] - bars["low"]
    high_close = np.abs(bars["high"] - bars["close"].shift())
    low_close = np.abs(bars["low"] - bars["close"].shift())
    tr = np.maximum(high_low, np.maximum(high_close, low_close))

    if len(tr) >= 14:
        atr = tr.rolling(window=14).mean().iloc[-1]
    elif len(tr) > 0:
        atr = tr.mean()
    else:
        atr = 0.1

    return {
        "current_price": prices[-1],
        "vwap": vwap,
        "macd": macd.iloc[-1],
        "signal": signal.iloc[-1],
        "histogram": histogram.iloc[-1],
        "atr": atr if not np.isnan(atr) else 0.1
    }

def has_open_order(symbol):
    open_orders = api.list_orders(status="open", symbols=[symbol])
    return len(open_orders) > 0

def get_position(symbol):
    try:
        position = api.get_position(symbol)
        return int(position.qty)
    except:
        return 0

def place_order(symbol, side, current_price, position_qty):
    print(f"📌 Placing {side.upper()} order for {symbol} at {current_price:.2f}...")
    try:
        if side == 'buy':
            take_profit = round(current_price * 1.02, 2)
            stop_loss = round(current_price * 0.98, 2)
        else:
            take_profit = round(current_price * 0.98, 2)
            stop_loss = round(current_price * 1.02, 2)

        if position_qty == 0:
            api.submit_order(
                symbol=symbol,
                qty=1,
                side=side,
                type='market',
                time_in_force='gtc',
                order_class='bracket',
                take_profit={'limit_price': take_profit},
                stop_loss={'stop_price': stop_loss}
            )
            print(f"✅ Entry Order placed: {side.upper()} 1 {symbol} at {current_price:.2f}")
        else:
            api.submit_order(
                symbol=symbol,
                qty=position_qty,
                side=side,
                type='market',
                time_in_force='gtc'
            )
            print(f"✅ Exit Order placed: {side.upper()} {position_qty} {symbol} at market price.")
    except Exception as e:
        print(f"❌ Error placing order: {e}")

def run_trading_bot(symbol, update_ui_callback):
    global running
    running = True
    print(f"🚀 Starting trading bot for {symbol}...")

    while running:
        bars = get_bars(symbol)
        if bars is None:
            time.sleep(5)
            continue
        
        indicators = calculate_indicators(bars)
        
        print(f"\n📊 Last 10 bars for {symbol}:")
        for _, row in bars.iterrows():
            print(f"Time: {row['timestamp']}, Close: {row['close']}, Volume: {row['volume']}")

        print(f"\n💡 Current Price: {indicators['current_price']} | VWAP: {indicators['vwap']:.4f} | ATR: {indicators['atr']:.4f}")
        print(f"📈 MACD: {indicators['macd']:.4f} | Signal Line: {indicators['signal']:.4f} | Histogram: {indicators['histogram']:.4f}")

        position_qty = get_position(symbol)
        order_message = ""

        if indicators['macd'] > indicators['signal'] and not has_open_order(symbol):
            order_message = place_order(symbol, 'buy', indicators['current_price'], position_qty)
        elif indicators['macd'] < indicators['signal']:
            order_message = place_order(symbol, 'sell', indicators['current_price'], max(1, position_qty))

        update_ui_callback(f"\n💡 Current Price: {indicators['current_price']:.2f} | VWAP: {indicators['vwap']:.4f} | ATR: {indicators['atr']:.4f}\n"
                           f"📈 MACD: {indicators['macd']:.4f} | Signal Line: {indicators['signal']:.4f} | Histogram: {indicators['histogram']:.4f}\n"
                           f"{order_message}")
        
        time.sleep(10)
