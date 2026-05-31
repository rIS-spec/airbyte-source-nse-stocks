import yfinance as yf
from datetime import datetime, timedelta

def check_connection():
    """Test 1: Can we reach Yahoo Finance?"""
    try:
        ticker = yf.Ticker("TCS.NS")
        info = ticker.info
        if info:
            print("✅ Connection successful!")
            return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def discover():
    """Test 2: What data is available?"""
    fields = [
        "date",
        "open_price",
        "high_price", 
        "low_price",
        "close_price",
        "volume"
    ]
    print("📊 Available fields:", fields)
    return fields

def read_records():
    """Test 3: Get TCS stock data for last 30 days"""
    ticker = yf.Ticker("TCS.NS")
    end_date = datetime.today()
    start_date = end_date - timedelta(days=30)
    
    df = ticker.history(start=start_date, end=end_date)
    
    records = []
    for date, row in df.iterrows():
        record = {
            "date": str(date.date()),
            "open_price": round(row["Open"], 2),
            "high_price": round(row["High"], 2),
            "low_price": round(row["Low"], 2),
            "close_price": round(row["Close"], 2),
            "volume": int(row["Volume"])
        }
        records.append(record)
        print(f"📈 {record['date']} | Close: ₹{record['close_price']} | Volume: {record['volume']}")
    
    return records

# Run all 3 steps
print("=== TCS Stock Connector ===")
print("\nStep 1: Checking connection...")
check_connection()

print("\nStep 2: Discovering fields...")
discover()

print("\nStep 3: Reading TCS data...")
records = read_records()
print(f"\n✅ Total records fetched: {len(records)} days of TCS data")