import os
import json
import csv
import datetime
import requests
from bs4 import BeautifulSoup
import yfinance as yf
from tqdm import tqdm
from colorama import Fore, Style, init

# Setup
init(autoreset=True)
stocks = ['AAPL', 'TSLA', 'NVDA', 'GOOGL', 'AMZN', 'MSFT', 'META', 'NFLX']
stock_data = []
monthly_data = {symbol: [] for symbol in stocks}
summary_data = []

now = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
output_dir = "output"
os.makedirs(output_dir, exist_ok=True)

def getData(symbol):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        url = f'https://finance.yahoo.com/quote/{symbol}'
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')

        price = soup.find('fin-streamer', {'data-field': 'regularMarketPrice'})
        change = soup.find('fin-streamer', {'data-field': 'regularMarketChange'})

        return {
            'symbol': symbol,
            'price': float(price.text.replace(',', '')) if price else None,
            'change': float(change.text.replace(',', '')) if change else None
        }
    except Exception as e:
        print(Fore.RED + f"Error fetching {symbol}: {e}")
        return {'symbol': symbol, 'price': None, 'change': None}

def getPastData(symbol):
    try:
        stock = yf.Ticker(symbol)
        hist = stock.history(period="1mo")
        prices = []

        for date, row in hist.iterrows():
            prices.append(row['Close'])
            monthly_data[symbol].append({
                'date': date.strftime('%Y-%m-%d'),
                'price': round(row['Close'], 2),
                'change': round(row['Close'] - row['Open'], 2)
            })

        if prices:
            summary_data.append({
                'symbol': symbol,
                'min': round(min(prices), 2),
                'max': round(max(prices), 2),
                'avg': round(sum(prices) / len(prices), 2)
            })

    except Exception as e:
        print(Fore.RED + f"Error pulling history for {symbol}: {e}")

def saveFiles():
    today_path = os.path.join(output_dir, f"stock_data_today_{now}.json")
    month_path = os.path.join(output_dir, f"stock_data_month_{now}.json")
    summary_json_path = os.path.join(output_dir, f"stock_summary_{now}.json")
    summary_csv_path = os.path.join(output_dir, f"stock_summary_{now}.csv")

    with open(today_path, 'w') as f:
        json.dump(stock_data, f, indent=4)
    with open(month_path, 'w') as f:
        json.dump(monthly_data, f, indent=4)
    with open(summary_json_path, 'w') as f:
        json.dump(summary_data, f, indent=4)

    with open(summary_csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['symbol', 'min', 'max', 'avg'])
        writer.writeheader()
        writer.writerows(summary_data)

    return [today_path, month_path, summary_json_path, summary_csv_path]

# Main
for stock in tqdm(stocks, desc="Processing stocks"):
    data = getData(stock)
    getPastData(stock)
    stock_data.append(data)

    if data['price'] is not None:
        color = Fore.GREEN if data['change'] > 0 else Fore.RED if data['change'] < 0 else Fore.YELLOW
        print(color + f"{stock}: ${data['price']} ({data['change']:+.2f})")
    else:
        print(Fore.MAGENTA + f"{stock}: Price unavailable")

saveFiles()
print(Style.BRIGHT + Fore.GREEN + "Done! Data saved to 'output' folder.")
