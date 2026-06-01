# Code Snippet source.py

import yfinance as yf
from datetime import datetime, timedelta
import csv
import os

# === CONFIGURATION ===
# Add any NSE stock symbol here — just add .NS at the end
STOCKS = [
    "TCS.NS",
    "RELIANCE.NS", 
    "INFY.NS",
    "HDFCBANK.NS",
    "WIPRO.NS"
]
DAYS = 30  # How many days of history to fetch

def check_connection(symbol):
    """Test: Can we reach Yahoo Finance for this stock?"""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        if info:
            print(f" Connected to {symbol}")
            return True
    except Exception as e:
        print(f" Failed for {symbol}: {e}")
        return False

def fetch_stock_data(symbol):
    """Fetch last N days of stock data"""
    ticker = yf.Ticker(symbol)
    end_date = datetime.today()
    start_date = end_date - timedelta(days=DAYS)
    
    df = ticker.history(start=start_date, end=end_date)
    
    records = []
    for date, row in df.iterrows():
        record = {
            "symbol": symbol.replace(".NS", ""),
            "date": str(date.date()),
            "open_price": round(row["Open"], 2),
            "high_price": round(row["High"], 2),
            "low_price": round(row["Low"], 2),
            "close_price": round(row["Close"], 2),
            "volume": int(row["Volume"])
        }
        records.append(record)
    
    return records

def save_to_csv(all_records):
    """Save all records to a CSV file"""
    filename = f"nse_stocks_{datetime.today().strftime('%Y%m%d')}.csv"
    
    with open(filename, 'w', newline='') as f:
        fieldnames = ["symbol", "date", "open_price", "high_price", 
                     "low_price", "close_price", "volume"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_records)
    
    print(f"\n Data saved to: {filename}")
    return filename

def run_pipeline():
    """Main pipeline — runs all steps"""
    print("=" * 50)
    print("   NSE India Stock Data Pipeline")
    print("=" * 50)
    
    all_records = []
    
    for symbol in STOCKS:
        print(f"\n Processing {symbol}...")
        
        # Step 1: Check connection
        if not check_connection(symbol):
            continue
            
        # Step 2: Fetch data
        records = fetch_stock_data(symbol)
        all_records.extend(records)
        
        # Step 3: Show latest price
        if records:
            latest = records[-1]
            print(f"   Latest: {latest['date']} | "
                  f"Close: ₹{latest['close_price']} | "
                  f"Volume: {latest['volume']:,}")
            print(f"   Records fetched: {len(records)} days")
    
    # Step 4: Save everything to CSV
    print("\n" + "=" * 50)
    print(f" Total records: {len(all_records)}")
    save_to_csv(all_records)
    print(" Pipeline completed successfully!")

# Run the pipeline
run_pipeline()