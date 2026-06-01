
# Yahoo Finance API → Python → SQLite DB → SQL Analytics


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
    """Real world business queries used at finance companies"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    print("\n" + "="*50)
    print(" REAL WORLD BUSINESS ANALYTICS")
    print("="*50)
    
    # Query 1: Latest price for each stock
    print("\n1️.  Current Market Snapshot (Latest Prices):")
    cursor.execute('''
        SELECT symbol, date, close_price, volume
        FROM stock_prices
        WHERE date = (SELECT MAX(date) FROM stock_prices)
        ORDER BY close_price DESC
    ''')
    for row in cursor.fetchall():
        print(f"   {row[0]:<12} ₹{row[2]:<10} Vol: {row[3]:,}")

    # Query 2: Price change % from first to last day
    print("\n2️.  30-Day Return % (Who gave best returns?):")
    cursor.execute('''
        SELECT 
            symbol,
            first_price,
            last_price,
            ROUND(((last_price - first_price) / first_price) * 100, 2) as return_pct
        FROM (
            SELECT 
                symbol,
                FIRST_VALUE(close_price) OVER (
                    PARTITION BY symbol ORDER BY date ASC
                ) as first_price,
                LAST_VALUE(close_price) OVER (
                    PARTITION BY symbol ORDER BY date ASC
                    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
                ) as last_price
            FROM stock_prices
        )
        GROUP BY symbol
        ORDER BY return_pct DESC
    ''')
    for row in cursor.fetchall():
        arrow = "📈" if row[3] > 0 else "📉"
        print(f"   {arrow} {row[0]:<12} {row[1]} → {row[2]}  "
              f"Return: {row[3]}%")

    # Query 3: Most volatile stock
    print("\n3️.  Most Volatile Stocks (Risk Analysis):")
    cursor.execute('''
        SELECT 
            symbol,
            ROUND(MAX(high_price) - MIN(low_price), 2) as price_range,
            ROUND(MAX(high_price), 2) as max_price,
            ROUND(MIN(low_price), 2) as min_price
        FROM stock_prices
        GROUP BY symbol
        ORDER BY price_range DESC
    ''')
    for row in cursor.fetchall():
        print(f"   {row[0]:<12} Range: ₹{row[1]:<10} "
              f"High: ₹{row[2]}  Low: ₹{row[3]}")

    # Query 4: Best and worst single day
    print("\n4️.  Best Single Day Gain per Stock:")
    cursor.execute('''
        SELECT 
            symbol,
            date,
            ROUND(close_price - open_price, 2) as day_gain,
            ROUND(((close_price - open_price) / open_price) * 100, 2) as gain_pct
        FROM stock_prices
        WHERE day_gain = (
            SELECT MAX(close_price - open_price)
            FROM stock_prices s2
            WHERE s2.symbol = stock_prices.symbol
        )
        ORDER BY gain_pct DESC
    ''')
    for row in cursor.fetchall():
        print(f"   {row[0]:<12} {row[1]}  "
              f"Gain: ₹{row[2]}  ({row[3]}%)")

    # Query 5: Worst single day loss
    print("\n5️.  Worst Single Day Loss per Stock:")
    cursor.execute('''
        SELECT 
            symbol,
            date,
            ROUND(close_price - open_price, 2) as day_loss,
            ROUND(((close_price - open_price) / open_price) * 100, 2) as loss_pct
        FROM stock_prices
        WHERE day_loss = (
            SELECT MIN(close_price - open_price)
            FROM stock_prices s2
            WHERE s2.symbol = stock_prices.symbol
        )
        ORDER BY loss_pct ASC
    ''')
    for row in cursor.fetchall():
        print(f"   {row[0]:<12} {row[1]}  "
              f"Loss: ₹{row[2]}  ({row[3]}%)")

    # Query 6: Volume spike detection
    print("\n6️.  Volume Spike Days (Unusual Trading Activity):")
    cursor.execute('''
        SELECT 
            symbol,
            date,
            volume,
            avg_volume,
            ROUND(CAST(volume AS REAL) / avg_volume, 2) as spike_ratio
        FROM (
            SELECT 
                symbol,
                date,
                volume,
                AVG(volume) OVER (PARTITION BY symbol) as avg_volume
            FROM stock_prices
        )
        WHERE spike_ratio > 1.5
        ORDER BY spike_ratio DESC
        LIMIT 10
    ''')
    for row in cursor.fetchall():
        print(f"   {row[0]:<12} {row[1]}  "
              f"Vol: {row[2]:,}  "
              f"({row[4]}x normal)")

    # Query 7: Weekly performance summary
    print("\n7️.  Weekly Performance (Last 4 Weeks):")
    cursor.execute('''
        SELECT 
            symbol,
            STRFTIME('%W', date) as week_num,
            ROUND(AVG(close_price), 2) as avg_close,
            ROUND(MAX(high_price), 2) as weekly_high,
            ROUND(MIN(low_price), 2) as weekly_low,
            SUM(volume) as total_volume
        FROM stock_prices
        GROUP BY symbol, week_num
        ORDER BY symbol, week_num
    ''')
    current_symbol = None
    for row in cursor.fetchall():
        if row[0] != current_symbol:
            print(f"\n   {row[0]}:")
            current_symbol = row[0]
        print(f"   Week {row[1]}: Avg ₹{row[2]}  "
              f"H:₹{row[3]} L:₹{row[4]}  "
              f"Vol:{row[5]:,}")

    # Query 8: Stock correlation — which stocks move together
    print("\n8️.  Highest vs Lowest Avg Price Comparison:")
    cursor.execute('''
        SELECT 
            symbol,
            ROUND(AVG(close_price), 2) as avg_price,
            ROUND(MIN(close_price), 2) as min_price,
            ROUND(MAX(close_price), 2) as max_price,
            COUNT(*) as trading_days
        FROM stock_prices
        GROUP BY symbol
        ORDER BY avg_price DESC
    ''')
    for row in cursor.fetchall():
        print(f"   {row[0]:<12} Avg:₹{row[1]:<10} "
              f"Min:₹{row[2]}  Max:₹{row[3]}  "
              f"Days:{row[4]}")

    # Query 9: Buy signal — close near 30-day low
    print("\n9️.  Potential Buy Signal (Price near 30-day Low):")
    cursor.execute('''
        SELECT 
            symbol,
            current_price,
            min_30d,
            ROUND(((current_price - min_30d) / min_30d) * 100, 2) as pct_above_low
        FROM (
            SELECT 
                symbol,
                LAST_VALUE(close_price) OVER (
                    PARTITION BY symbol ORDER BY date
                    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
                ) as current_price,
                MIN(close_price) OVER (PARTITION BY symbol) as min_30d
            FROM stock_prices
        )
        GROUP BY symbol
        ORDER BY pct_above_low ASC
    ''')
    for row in cursor.fetchall():
        signal = " BUY ZONE" if row[3] < 5 else " NEUTRAL"
        print(f"   {row[0]:<12} ₹{row[1]:<10} "
              f"{row[3]}% above 30d low  {signal}")

    # Query 10: Market summary dashboard
    print("\n10.  Executive Dashboard Summary:")
    cursor.execute('''
        SELECT COUNT(DISTINCT symbol) as stocks,
               COUNT(*) as total_records,
               MIN(date) as from_date,
               MAX(date) as to_date,
               ROUND(AVG(volume)) as avg_daily_volume
        FROM stock_prices
    ''')
    row = cursor.fetchone()
    print(f"   Stocks tracked    : {row[0]}")
    print(f"   Total records     : {row[1]}")
    print(f"   Date range        : {row[2]} → {row[3]}")
    print(f"   Avg daily volume  : {int(row[4]):,} shares")

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