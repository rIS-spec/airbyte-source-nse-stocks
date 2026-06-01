import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# === PAGE CONFIG ===
st.set_page_config(
    page_title="NSE India Stock Dashboard",
    page_icon="📈",
    layout="wide"
)

DB_NAME = "nse_stocks.db"

def get_data(query):
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# === HEADER ===
st.title("📈 NSE India Stock Dashboard")
st.markdown("**Real-time analytics on TCS, Reliance, Infosys, HDFC, Wipro**")
st.divider()

# === ROW 1: KPI CARDS ===
latest = get_data('''
    SELECT symbol, close_price, volume
    FROM stock_prices
    WHERE date = (SELECT MAX(date) FROM stock_prices)
    ORDER BY close_price DESC
''')

cols = st.columns(5)
for i, row in latest.iterrows():
    with cols[i]:
        st.metric(
            label=row['symbol'],
            value=f"₹{row['close_price']:,.2f}",
            delta=f"Vol: {int(row['volume']):,}"
        )

st.divider()

# === ROW 2: PRICE CHART + RETURNS ===
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📊 30-Day Price Movement")
    
    selected_stocks = st.multiselect(
        "Select stocks:",
        ["TCS", "RELIANCE", "INFY", "HDFCBANK", "WIPRO"],
        default=["TCS", "RELIANCE", "INFY"]
    )
    
    if selected_stocks:
        placeholders = ','.join(['?' for _ in selected_stocks])
        conn = sqlite3.connect(DB_NAME)
        price_df = pd.read_sql_query(
            f"SELECT symbol, date, close_price FROM stock_prices WHERE symbol IN ({placeholders}) ORDER BY date",
            conn,
            params=selected_stocks
        )
        conn.close()
        
        fig = px.line(
            price_df,
            x='date',
            y='close_price',
            color='symbol',
            title='Closing Price (Last 30 Days)',
            labels={'close_price': 'Price (₹)', 'date': 'Date'}
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("🏆 30-Day Returns")
    
    returns_df = get_data('''
        SELECT 
            symbol,
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
    
    colors = ['green' if x > 0 else 'red' for x in returns_df['return_pct']]
    fig2 = go.Figure(go.Bar(
        x=returns_df['symbol'],
        y=returns_df['return_pct'],
        marker_color=colors,
        text=[f"{x}%" for x in returns_df['return_pct']],
        textposition='outside'
    ))
    fig2.update_layout(
        title='Return %',
        yaxis_title='Return (%)',
        height=400
    )
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

# === ROW 3: VOLUME + VOLATILITY ===
col3, col4 = st.columns(2)

with col3:
    st.subheader("📊 Volume Analysis")
    
    vol_df = get_data('''
        SELECT symbol, date, volume,
               AVG(volume) OVER (PARTITION BY symbol) as avg_vol
        FROM stock_prices
        ORDER BY date
    ''')
    
    fig3 = px.bar(
        vol_df,
        x='date',
        y='volume',
        color='symbol',
        title='Daily Trading Volume',
        labels={'volume': 'Volume', 'date': 'Date'}
    )
    fig3.update_layout(height=350)
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    st.subheader("⚡ Volatility (Price Range)")
    
    vol2_df = get_data('''
        SELECT 
            symbol,
            ROUND(MAX(high_price) - MIN(low_price), 2) as price_range,
            ROUND(MAX(high_price), 2) as max_price,
            ROUND(MIN(low_price), 2) as min_price
        FROM stock_prices
        GROUP BY symbol
        ORDER BY price_range DESC
    ''')
    
    fig4 = px.bar(
        vol2_df,
        x='symbol',
        y='price_range',
        color='symbol',
        title='30-Day Price Range (Volatility)',
        labels={'price_range': 'Price Range (₹)'},
        text='price_range'
    )
    fig4.update_layout(height=350)
    st.plotly_chart(fig4, use_container_width=True)

st.divider()

# === ROW 4: BUY SIGNALS + VOLUME SPIKES ===
col5, col6 = st.columns(2)

with col5:
    st.subheader("🟢 Buy Signal Detector")
    
    buy_df = get_data('''
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
    
    for _, row in buy_df.iterrows():
        signal = "🟢 BUY ZONE" if row['pct_above_low'] < 5 else "⚪ NEUTRAL"
        st.markdown(
            f"**{row['symbol']}** — ₹{row['current_price']} "
            f"({row['pct_above_low']}% above 30d low) {signal}"
        )

with col6:
    st.subheader("🚨 Volume Spike Alerts")
    
    spike_df = get_data('''
        SELECT symbol, date, volume, avg_volume,
               ROUND(CAST(volume AS REAL) / avg_volume, 2) as spike_ratio
        FROM (
            SELECT symbol, date, volume,
                   AVG(volume) OVER (PARTITION BY symbol) as avg_volume
            FROM stock_prices
        )
        WHERE spike_ratio > 1.5
        ORDER BY spike_ratio DESC
        LIMIT 8
    ''')
    
    for _, row in spike_df.iterrows():
        st.warning(
            f"⚠️ **{row['symbol']}** on {row['date']} — "
            f"{row['spike_ratio']}x normal volume"
        )

st.divider()

# === ROW 5: CANDLESTICK CHART ===
st.subheader("🕯️ Candlestick Chart")

stock_choice = st.selectbox(
    "Select stock for candlestick:",
    ["TCS", "RELIANCE", "INFY", "HDFCBANK", "WIPRO"]
)

conn = sqlite3.connect(DB_NAME)
candle_df = pd.read_sql_query(
    "SELECT * FROM stock_prices WHERE symbol = ? ORDER BY date",
    conn,
    params=[stock_choice]
)
conn.close()

fig5 = go.Figure(data=[go.Candlestick(
    x=candle_df['date'],
    open=candle_df['open_price'],
    high=candle_df['high_price'],
    low=candle_df['low_price'],
    close=candle_df['close_price']
)])
fig5.update_layout(
    title=f'{stock_choice} Candlestick Chart',
    yaxis_title='Price (₹)',
    height=450
)
st.plotly_chart(fig5, use_container_width=True)

st.divider()

# === FOOTER ===
total = get_data("SELECT COUNT(*) as total FROM stock_prices")
st.caption(
    f"📦 Database: {total['total'][0]} records | "
    f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | "
    f"Data: Yahoo Finance (NSE India)"
)