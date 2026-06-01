import yfinance as yf
from datetime import datetime, timedelta
import sqlite3
import os

# === CONFIGURATION ===
STOCKS = [
    "TCS.NS",
    "RELIANCE.NS",
    "INFY.NS",
    "HDFCBANK.NS",
    "WIPRO.NS"
]
DAYS = 30
DB_NAME = "nse_stocks.db"

def create_database():
    """Create SQLite database and table"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            date TEXT NOT NULL,
            open_price REAL,
            high_price REAL,
            low_price REAL,
            close_price REAL,
            volume INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol, date)
        )
    ''')
    
    conn.commit()
    conn.close()
    print(" Database created: nse_stocks.db")

def save_to_database(records):
    """Save records to SQLite database"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    inserted = 0
    skipped = 0
    
    for record in records:
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO stock_prices 
                (symbol, date, open_price, high_price, 
                 low_price, close_price, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                record['symbol'],
                record['date'],
                record['open_price'],
                record['high_price'],
                record['low_price'],
                record['close_price'],
                record['volume']
            ))
            if cursor.rowcount > 0:
                inserted += 1
            else:
                skipped += 1
        except Exception as e:
            print(f"Error inserting {record}: {e}")
    
    conn.commit()
    conn.close()
    return inserted, skipped

def fetch_stock_data(symbol):
    """Fetch stock data from Yahoo Finance"""
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

def run_analytics():
    """Run SQL queries on your data — like your Netflix project!"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    print("\n" + "="*50)
    print(" ANALYTICS ON YOUR STOCK DATA")
    print("="*50)
    
    # Query 1: Latest price for each stock
    print("\n1️.  Latest closing price per stock:")
    cursor.execute('''
        SELECT symbol, date, close_price, volume
        FROM stock_prices
        WHERE date = (SELECT MAX(date) FROM stock_prices)
        ORDER BY close_price DESC
    ''')
    for row in cursor.fetchall():
        print(f"   {row[0]:<12} ₹{row[2]:<10} Volume: {row[3]:,}")
    
    # Query 2: Highest price in last 30 days
    print("\n2️.  Highest price in last 30 days:")
    cursor.execute('''
        SELECT symbol, MAX(high_price) as max_price, date
        FROM stock_prices
        GROUP BY symbol
        ORDER BY max_price DESC
    ''')
    for row in cursor.fetchall():
        print(f"   {row[0]:<12} ₹{row[1]:<10} on {row[2]}")
    
    # Query 3: Average volume per stock
    print("\n3️.  Average daily volume per stock:")
    cursor.execute('''
        SELECT symbol, ROUND(AVG(volume)) as avg_volume
        FROM stock_prices
        GROUP BY symbol
        ORDER BY avg_volume DESC
    ''')
    for row in cursor.fetchall():
        print(f"   {row[0]:<12} {int(row[1]):,} shares/day")
    
    # Query 4: Total records in database
    cursor.execute('SELECT COUNT(*) FROM stock_prices')
    total = cursor.fetchone()[0]
    print(f"\n Total records in database: {total}")
    
    conn.close()

def run_pipeline():
    """Main pipeline"""
    print("="*50)
    print("   NSE India Stock Data Pipeline v2.0")
    print("   Now with SQLite Database!")
    print("="*50)
    
    # Step 1: Create database
    print("\n Setting up database...")
    create_database()
    
    # Step 2: Fetch and store data
    total_inserted = 0
    total_skipped = 0
    
    for symbol in STOCKS:
        print(f"\n Processing {symbol}...")
        
        try:
            records = fetch_stock_data(symbol)
            inserted, skipped = save_to_database(records)
            total_inserted += inserted
            total_skipped += skipped
            print(f"   Inserted: {inserted} | Skipped: {skipped}")
        except Exception as e:
            print(f"   Error: {e}")
    
    print(f"\n Pipeline complete!")
    print(f"   New records: {total_inserted}")
    print(f"   Already existed: {total_skipped}")
    
    # Step 3: Run analytics
    run_analytics()

# Run the pipeline
run_pipeline()