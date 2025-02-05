import tkinter as tk
from tkinter import ttk
import alpaca_trade_api as tradeapi
import pandas as pd
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
import numpy as np

# טוען משתנים מה-ENV
load_dotenv()
API_KEY = os.getenv("APCA_API_KEY_ID")
API_SECRET = os.getenv("APCA_API_SECRET_KEY")
BASE_URL = os.getenv("APCA_API_BASE_URL")

# התחברות ל-Alpaca API
api = tradeapi.REST(API_KEY, API_SECRET, BASE_URL, api_version='v2')

# פונקציה לשליפת נתוני מניה
def get_stock_data():
    symbol = stock_var.get()
    start = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%SZ')
    bars = api.get_bars(symbol, tradeapi.TimeFrame.Minute, start=start, limit=50).df

    if bars.empty:
        result_label.config(text=f"❌ No data for {symbol}")
        return

    # חישוב VWAP
    vwap = (bars['high'] + bars['low'] + bars['close']).mean() / 3

    # חישוב MACD
    ema12 = bars['close'].ewm(span=12, adjust=False).mean()
    ema26 = bars['close'].ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()

    # ATR
    bars['range'] = bars['high'] - bars['low']
    atr = bars['range'].rolling(window=14).mean().iloc[-1]

    # הצגת הנתונים בממשק
    latest_price = bars['close'].iloc[-1]
    result_label.config(text=f"📊 {symbol} Price: {latest_price:.2f}\n"
                             f"VWAP: {vwap:.2f} | ATR: {atr:.2f}\n"
                             f"MACD: {macd.iloc[-1]:.4f} | Signal: {signal.iloc[-1]:.4f}")

# יצירת חלון Tkinter
root = tk.Tk()
root.title("Trading Bot Dashboard")
root.geometry("400x300")

# בחירת מניה
ttk.Label(root, text="בחר מניה:").pack(pady=5)
stock_var = tk.StringVar()
stock_dropdown = ttk.Combobox(root, textvariable=stock_var, values=["AAPL", "MSFT", "NVDA", "META", "AMZN", "TSLA"])
stock_dropdown.pack(pady=5)
stock_dropdown.current(0)

# כפתור עדכון
update_button = ttk.Button(root, text="📈 קבל נתונים", command=get_stock_data)
update_button.pack(pady=10)

# תווית להצגת נתונים
result_label = ttk.Label(root, text="", font=("Arial", 12))
result_label.pack(pady=10)

# הפעלת הממשק
root.mainloop()
