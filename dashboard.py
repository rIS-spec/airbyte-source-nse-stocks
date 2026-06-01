import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# === PAGE CONFIG ===
st.set_page_config(
    page_title="NSE India Stock Dashboard",
    page_icon="📈",
    layout="wide"
)

STOCKS = {
    "TCS": "TCS.NS",
    "RELIANCE": "RELIANCE.NS",
    "INFY": "INFY.NS",
    "HDFCBANK": "HDFCBANK.NS",
    "WIPRO": "WIPRO.NS"
}

@st.cache_data(ttl=3600)
def fetch_all_data():

    symbols = list(STOCKS.values())

    data = yf.download(
        tickers=symbols,
        period="1mo",
        group_by="ticker",
        auto_adjust=True,
        threads=False
    )

    all_data = []

    for name, symbol in STOCKS.items():

        stock_df = data[symbol].copy()

        stock_df = stock_df.reset_index()

        stock_df["symbol"] = name

        stock_df = stock_df.rename(columns={
            "Date": "date",
            "Open": "open_price",
            "High": "high_price",
            "Low": "low_price",
            "Close": "close_price",
            "Volume": "volume"
        })

        stock_df["date"] = pd.to_datetime(stock_df["date"]).dt.date

        all_data.append(stock_df)

    return pd.concat(all_data, ignore_index=True)


# === LOAD DATA ===
with st.spinner("Fetching live NSE data..."):
    df = fetch_all_data()

# === HEADER ===
st.title("📈 NSE India Stock Dashboard")
st.markdown("**Live analytics on TCS, Reliance, Infosys, HDFC, Wipro**")
st.divider()

# === ROW 1: KPI CARDS ===
latest_df = df.groupby('symbol').last().reset_index()

cols = st.columns(5)
for i, row in latest_df.iterrows():
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
    selected = st.multiselect(
        "Select stocks:",
        list(STOCKS.keys()),
        default=["TCS", "RELIANCE", "INFY"]
    )
    if selected:
        filtered = df[df['symbol'].isin(selected)]
        fig = px.line(
            filtered,
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
    returns = []
    for symbol in STOCKS.keys():
        stock_df = df[df['symbol'] == symbol].sort_values('date')
        if len(stock_df) > 0:
            first = stock_df.iloc[0]['close_price']
            last = stock_df.iloc[-1]['close_price']
            ret = round(((last - first) / first) * 100, 2)
            returns.append({'symbol': symbol, 'return_pct': ret})
    
    ret_df = pd.DataFrame(returns).sort_values('return_pct', ascending=False)
    colors = ['green' if x > 0 else 'red' for x in ret_df['return_pct']]
    
    fig2 = go.Figure(go.Bar(
        x=ret_df['symbol'],
        y=ret_df['return_pct'],
        marker_color=colors,
        text=[f"{x}%" for x in ret_df['return_pct']],
        textposition='outside'
    ))
    fig2.update_layout(title='Return %', height=400)
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

# === ROW 3: VOLUME + VOLATILITY ===
col3, col4 = st.columns(2)

with col3:
    st.subheader("📊 Volume Analysis")
    fig3 = px.bar(
        df, x='date', y='volume', color='symbol',
        title='Daily Trading Volume'
    )
    fig3.update_layout(height=350)
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    st.subheader("⚡ Volatility")
    vol_df = df.groupby('symbol').agg(
        price_range=('high_price', lambda x: round(x.max() - df.loc[x.index, 'low_price'].min(), 2))
    ).reset_index()
    
    fig4 = px.bar(
        vol_df, x='symbol', y='price_range',
        color='symbol', title='30-Day Price Range',
        text='price_range'
    )
    fig4.update_layout(height=350)
    st.plotly_chart(fig4, use_container_width=True)

st.divider()

# === ROW 4: BUY SIGNALS + VOLUME SPIKES ===
col5, col6 = st.columns(2)

with col5:
    st.subheader("🟢 Buy Signal Detector")
    for symbol in STOCKS.keys():
        stock_df = df[df['symbol'] == symbol]
        current = stock_df.iloc[-1]['close_price']
        min_price = stock_df['low_price'].min()
        pct = round(((current - min_price) / min_price) * 100, 2)
        signal = "🟢 BUY ZONE" if pct < 5 else "⚪ NEUTRAL"
        st.markdown(f"**{symbol}** — ₹{current} ({pct}% above 30d low) {signal}")

with col6:
    st.subheader("🚨 Volume Spike Alerts")
    for symbol in STOCKS.keys():
        stock_df = df[df['symbol'] == symbol].copy()
        avg_vol = stock_df['volume'].mean()
        spikes = stock_df[stock_df['volume'] > avg_vol * 1.5].sort_values('volume', ascending=False).head(2)
        for _, row in spikes.iterrows():
            ratio = round(row['volume'] / avg_vol, 2)
            st.warning(f"⚠️ **{symbol}** on {row['date']} — {ratio}x normal volume")

st.divider()

# === CANDLESTICK ===
st.subheader("🕯️ Candlestick Chart")
stock_choice = st.selectbox("Select stock:", list(STOCKS.keys()))
candle_df = df[df['symbol'] == stock_choice].sort_values('date')

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
st.caption(
    f"📦 {len(df)} records | "
    f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | "
    f"Data: Yahoo Finance (NSE India)"
)