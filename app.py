"""实时金融热点监控 MVP —— Streamlit 主页面

运行方式：
    cd hotspot-mvp
    streamlit run app.py
"""
import time
import pandas as pd
import streamlit as st
from datetime import datetime

from collectors.tick_qq import fetch_quotes, STOCK_POOL
from collectors.news_cls import fetch_latest_news
from collectors.kline_qq import calc_indicators, classify_volume, classify_ma
from engines.hotspot import HotspotEngine

st.set_page_config(
    page_title="实时金融热点监控",
    page_icon="📈",
    layout="wide",
)

# 初始化 session state
if "engine" not in st.session_state:
    st.session_state.engine = HotspotEngine()
if "last_data" not in st.session_state:
    st.session_state.last_data = []
if "last_news" not in st.session_state:
    st.session_state.last_news = []
if "alerts" not in st.session_state:
    st.session_state.alerts = []

st.title("📈 实时金融热点监控 MVP")
st.caption("数据源：腾讯财经行情 + 财联社快讯 | 热度分 = 涨跌幅40% + 换手率30% + 量比30%")

# 侧边栏：控制
with st.sidebar:
    st.header("控制面板")
    refresh_interval = st.slider("刷新间隔（秒）", 3, 30, 5)
    top_n = st.slider("显示 Top N", 10, 50, 20)
    alert_threshold = st.slider("告警阈值", 50, 95, 70)
    auto_refresh = st.toggle("自动刷新", value=True)

# 顶部：时间和状态
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("当前时间", datetime.now().strftime("%H:%M:%S"))
with col2:
    st.metric("监控股票数", len(STOCK_POOL))
with col3:
    st.metric("累计告警数", len(st.session_state.alerts))

# 手动刷新按钮
if st.button("🔄 立即刷新"):
    auto_refresh = False

# 采集 + 计算
quotes = fetch_quotes()
if quotes:
    ranked = st.session_state.engine.score(quotes)
    st.session_state.last_data = ranked

    # 检查告警
    for item in ranked:
        if st.session_state.engine.should_alert(item, threshold=alert_threshold):
            msg = f"🚨 **{item['name']}**({item['symbol']}) 热度 {item['score']} | 涨跌 {item['pct_chg']:+.2f}% | 换手 {item['turnover']}% | 量比 {item['vol_ratio']}"
            st.session_state.alerts.insert(0, f"[{item['ts']}] {msg}")
            if len(st.session_state.alerts) > 20:
                st.session_state.alerts.pop()
else:
    ranked = st.session_state.last_data

# 获取新闻
news = fetch_latest_news(15)
if news:
    st.session_state.last_news = news

# 左侧：热点榜单
st.subheader("🔥 实时热点榜")
if ranked:
    # 用 markdown 表格显示，兼容性更好
    lines = ["| 名称 | 代码 | 现价 | 涨跌幅% | 换手率% | 量比 | 量价关系 | 均线位置 | 热度分 |",
             "|---|---|---|---|---|---|---|---|---|"]
    for item in ranked[:top_n]:
        # 计算均线和量价关系（有缓存，每天只算一次）
        ind = calc_indicators(item["symbol"])
        vol_cls = classify_volume(item["pct_chg"], ind["today_vol"], ind["avg_vol_5"])
        ma_cls = classify_ma(item["price"], ind["ma5"], ind["ma20"])
        lines.append(
            f"| {item['name']} | {item['symbol']} | {item['price']} "
            f"| {item['pct_chg']:+.2f} | {item['turnover']} "
            f"| {item['vol_ratio']} | {vol_cls} | {ma_cls} | **{item['score']}** |"
        )
    st.markdown("\n".join(lines))
else:
    st.info("暂无行情数据")

# 右侧：快讯
st.subheader("📰 最新快讯")
if st.session_state.last_news:
    for n in st.session_state.last_news[:15]:
        with st.expander(f"[{n['time']}] {n['title']}"):
            st.write(n["content"])

# 告警记录
if st.session_state.alerts:
    st.subheader("🚨 告警记录")
    for a in st.session_state.alerts[:10]:
        st.markdown(a)

# 自动刷新
if auto_refresh:
    time.sleep(refresh_interval)
    st.rerun()
