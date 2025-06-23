
import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import time

st.set_page_config(page_title="Crypto Terminal HF", layout="wide")

# Fungsi Ambil Data Binance Kline (Candlestick)
def get_binance_kline(symbol="BTCUSDT", interval="1m", limit=100):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    r = requests.get(url)
    data = r.json()
    df = pd.DataFrame(data, columns=[
        "timestamp", "open", "high", "low", "close", "volume",
        "close_time", "quote_asset_volume", "number_of_trades",
        "taker_buy_base_vol", "taker_buy_quote_vol", "ignore"
    ])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df[["open", "high", "low", "close", "volume"]] = df[["open", "high", "low", "close", "volume"]].astype(float)
    return df

# Fungsi Open Interest
def get_oi(symbol="BTCUSDT"):
    url = f"https://fapi.binance.com/futures/data/openInterestHist?symbol={symbol}&period=5m&limit=100"
    r = requests.get(url)
    data = r.json()
    df = pd.DataFrame(data)
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df["sumOpenInterest"] = df["sumOpenInterest"].astype(float)
    return df

# Fungsi Funding Rate
def get_funding(symbol="BTCUSDT"):
    url = f"https://fapi.binance.com/fapi/v1/fundingRate?symbol={symbol}&limit=50"
    r = requests.get(url)
    data = r.json()
    df = pd.DataFrame(data)
    df["fundingTime"] = pd.to_datetime(df["fundingTime"], unit="ms")
    df["fundingRate"] = df["fundingRate"].astype(float)
    return df

# Fungsi Orderbook Depth Heatmap Simulasi
def get_depth_heatmap(symbol="BTCUSDT"):
    url = f"https://api.binance.com/api/v3/depth?symbol={symbol}&limit=100"
    r = requests.get(url)
    data = r.json()
    bids = pd.DataFrame(data['bids'], columns=['price', 'qty'], dtype=float)
    asks = pd.DataFrame(data['asks'], columns=['price', 'qty'], dtype=float)
    return bids, asks

# Fungsi Long vs Short Simulasi (pakai OI naik/turun)
def get_long_short_ratio(df_oi):
    df = df_oi.copy()
    df["delta"] = df["sumOpenInterest"].diff().fillna(0)
    df["long_ratio"] = df["delta"].apply(lambda x: max(x, 0))
    df["short_ratio"] = df["delta"].apply(lambda x: abs(min(x, 0)))
    return df

# Fungsi Simulasi CVD dari Volume Candle
def compute_cvd(df_k):
    df = df_k.copy()
    df["deltaVol"] = df["volume"].diff().fillna(0)
    df["CVD"] = df["deltaVol"].cumsum()
    return df

# Sidebar
st.sidebar.title("HF Terminal Setup")
symbol = st.sidebar.text_input("Symbol", value="BTCUSDT")
interval = st.sidebar.selectbox("Interval", ["1m", "5m", "15m", "1h"], index=0)

# Fetch Data
with st.spinner("Mengambil data dari Binance..."):
    df_k = get_binance_kline(symbol, interval)
    df_oi = get_oi(symbol)
    df_funding = get_funding(symbol)
    bids, asks = get_depth_heatmap(symbol)
    df_ratio = get_long_short_ratio(df_oi)
    df_cvd = compute_cvd(df_k)

# Layout
col1, col2 = st.columns(2)

# Candlestick
with col1:
    st.subheader("📊 Candlestick Chart")
    fig = go.Figure(data=[go.Candlestick(x=df_k["timestamp"],
                    open=df_k["open"],
                    high=df_k["high"],
                    low=df_k["low"],
                    close=df_k["close"])])
    fig.update_layout(xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

# Open Interest
with col2:
    st.subheader("📈 Open Interest")
    st.line_chart(df_oi.set_index("timestamp")["sumOpenInterest"])

# Funding Rate
st.subheader("💰 Funding Rate")
st.line_chart(df_funding.set_index("fundingTime")["fundingRate"])

# Orderbook Heatmap Simulasi
st.subheader("🔥 Orderbook Depth (Heatmap Simulasi)")
st.write("📉 Bids")
st.bar_chart(bids.set_index("price")["qty"].sort_index(ascending=False).head(30))
st.write("📈 Asks")
st.bar_chart(asks.set_index("price")["qty"].sort_index().head(30))

# Long vs Short Ratio Simulasi
st.subheader("🟩 Long vs Short (Simulasi dari OI)")
st.area_chart(df_ratio.set_index("timestamp")[["long_ratio", "short_ratio"]])

# CVD Simulasi
st.subheader("📊 CVD (Simulasi dari Volume)")
st.line_chart(df_cvd.set_index("timestamp")["CVD"])

st.success("✅ Terminal berjalan. Siap untuk deploy ke Streamlit Cloud atau server sendiri.")
