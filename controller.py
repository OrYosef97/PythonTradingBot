import tkinter as tk
from tkinter import ttk
from threading import Thread
import bot

class TradingBotUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Trading Bot Controller")
        self.running = False

        
        ttk.Label(root, text="Trading Bot", font=("Arial", 16, "bold")).pack(pady=10)

        # Stock selecting
        self.symbol_label = ttk.Label(root, text="Select Symbol:")
        self.symbol_label.pack()
        self.symbol_entry = ttk.Entry(root)
        self.symbol_entry.pack()

        # Start button
        self.start_button = ttk.Button(root, text="Start Bot", command=self.start_bot)
        self.start_button.pack(pady=5)

        # Stop button
        self.stop_button = ttk.Button(root, text="Stop Bot", command=self.stop_bot, state=tk.DISABLED)
        self.stop_button.pack(pady=5)

        # status 
        self.status_text = tk.Text(root, height=15, width=60)
        self.status_text.pack(pady=10)

    def start_bot(self):
        symbol = self.symbol_entry.get().upper()
        if not symbol:
            return
        self.running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.symbol_entry.config(state=tk.DISABLED)
        self.bot_thread = Thread(target=bot.run_trading_bot, args=(symbol, self.update_status), daemon=True)
        self.bot_thread.start()

    def stop_bot(self):
        bot.stop_bot()
        self.running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.symbol_entry.config(state=tk.NORMAL)

    def update_status(self, message):
        self.status_text.insert(tk.END, message + "\n")
        self.status_text.see(tk.END)

root = tk.Tk()
app = TradingBotUI(root)
root.mainloop()
