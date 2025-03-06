import streamlit as st
import yfinance as yf
import pandas as pd
import mplfinance as mpf
from datetime import date

def download_stock_data(ticker, start, end):
    """
    使用 yfinance 下載指定股票在指定期間的歷史數據
    """
    data = yf.download(ticker, start=start, end=end)
    # 若資料欄位為 MultiIndex，則扁平化為單一層
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    return data

def plot_bollinger_bands(data, window=20, num_std=2):
    """
    使用 mplfinance 繪製布林通道 (含 K 線圖與成交量)
    - data: DataFrame, 預期包含 'Open', 'High', 'Low', 'Close', 'Volume'
    - window: 移動平均線週期 (預設 20)
    - num_std: 標準差倍數 (預設 2)
    """
    # 預期的欄位名稱
    cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    
    # 檢查資料是否包含預期欄位
    if not set(cols).issubset(data.columns):
        st.error(f"下載的資料欄位不符合預期，實際欄位：{list(data.columns)}")
        return None

    # 轉換必要欄位為數值型態
    data[cols] = data[cols].apply(pd.to_numeric, errors='coerce')
    data.dropna(subset=cols, inplace=True)

    # 計算移動平均線 (MA) 與標準差 (STD)
    data['MA'] = data['Close'].rolling(window=window).mean()
    data['STD'] = data['Close'].rolling(window=window).std()

    # 計算布林通道上下軌
    data['Upper'] = data['MA'] + (num_std * data['STD'])
    data['Lower'] = data['MA'] - (num_std * data['STD'])

    # 自訂 mplfinance 風格 (黑色背景)
    my_style = mpf.make_mpf_style(
    base_mpl_style="dark_background",
    marketcolors=mpf.make_marketcolors(
        up='green',      # 上漲K棒改成綠色
        down='red',      # 下跌K棒改成紅色
        edge='inherit',
        wick='white',
        volume='inherit'
    ),
    mavcolors=['#ffffff','#787878'],
    facecolor='black',
    gridcolor='gray',
    figcolor='black',
    edgecolor='white',
    rc={
        'figure.facecolor':'black',
        'axes.facecolor':'black'
    }
)


    # 建立布林通道附加圖層
    apds = [
        mpf.make_addplot(data['MA'], color='white', linestyle='-', width=1),
        mpf.make_addplot(data['Upper'], color='red', linestyle='--', width=1),
        mpf.make_addplot(data['Lower'], color='red', linestyle='--', width=1),
    ]

    # 使用 mplfinance 畫圖，並回傳 fig 供 Streamlit 顯示
    fig, axes = mpf.plot(
        data,
        type='candle',
        addplot=apds,
        volume=True,
        style=my_style,
        datetime_format='%Y-%m-%d',
        returnfig=True,
        figsize=(10,6)
    )
    return fig

# ------------------ Streamlit 介面 ------------------
st.set_page_config(page_title="股票查詢", layout="wide")
st.title("股票查詢 - 布林通道示例")

# 1. 輸入股票代碼
ticker_input = st.text_input("輸入股票代碼 (美股如 AAPL；台股如 2330.TW)", value="NVDA")

# 2. 選擇市場 (如果需要簡單區分美股/台股)
market = st.selectbox("選擇市場", ["美股", "台股"])
if market == "台股":
    # 若使用者忘了加 .TW，可以自動補上
    if not ticker_input.endswith(".TW"):
        ticker_input += ".TW"

# 3. 選擇日期區間
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("開始日期", value=date(2023, 1, 1))
with col2:
    end_date = st.date_input("結束日期", value=date.today())

# 4. 布林通道參數
window = st.slider("布林通道中軌 (移動平均線) 天數", min_value=5, max_value=60, value=20, step=1)
num_std = st.slider("標準差倍數", min_value=1, max_value=3, value=2, step=1)

# 5. 查詢按鈕
if st.button("查詢"):
    with st.spinner("下載資料中..."):
        data = download_stock_data(ticker_input, start_date, end_date)
        if data.empty:
            st.error("無法取得此股票的歷史數據，請確認代碼或日期區間。")
        else:
            # 顯示下載到的資料筆數與部分資料（方便確認）
            st.write(f"資料筆數: {len(data)}")
            st.write(data.tail(5))
            
            # 繪製布林通道圖表
            fig = plot_bollinger_bands(data, window=window, num_std=num_std)
            if fig is None:
                st.error("資料不足或欄位不符，無法繪製圖表。")
            else:
                st.pyplot(fig)

                # 顯示最新一筆交易資料 (含布林通道值)
                latest_data = data.iloc[-1]
                st.subheader(f"最後交易日: {latest_data.name.date()}")
                st.write(f"**收盤價 (Close)**: {latest_data['Close']:.2f}")
                st.write(f"**布林通道上軌 (Upper)**: {latest_data['Upper']:.2f}")
                st.write(f"**布林通道中軌 (MA)**: {latest_data['MA']:.2f}")
                st.write(f"**布林通道下軌 (Lower)**: {latest_data['Lower']:.2f}")
