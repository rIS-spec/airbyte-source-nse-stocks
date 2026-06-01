# Airbyte Source — NSE India Stock Data

A Python data connector that fetches real-time and historical 
stock data from NSE India (National Stock Exchange) using Yahoo Finance.

## What it does

- Connects to Yahoo Finance API (no API key needed)
- Fetches last 30 days of stock data for any NSE listed company
- Returns structured records with date, open, high, low, close, volume
- Currently supports: TCS, Reliance, Infosys, HDFC, and any NSE stock

## Tech stack

- Python 3.12
- yfinance
- airbyte-cdk

## Deployment Link : https://nse-stocks-analytics-dashboard.streamlit.app/

## How to run

```bash
# Clone the repo
git clone https://github.com/rIS-spec/airbyte-source-nse-stocks.git
cd airbyte-source-nse-stocks

# Create virtual environment
python -m venv env
env\Scripts\activate

# Install dependencies
pip install yfinance airbyte-cdk

# Run the connector
python source.py
```

## Sample output

#=== TCS Stock Connector ===
 Connection successful!
 2026-05-29 | Close: ₹2258.90 | Volume: 16331582
 Total records fetched: 21 days of TCS data



## Author

Arish Mahammad — [@rIS-spec](https://github.com/rIS-spec)
