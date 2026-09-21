"""腾讯日K线采集：用于计算均线和量能"""
import requests
from datetime import datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://gu.qq.com/",
}

_cache = {}  # symbol -> {"ma5": float, "ma20": float, "avg_vol_5": float, "updated": str}
CACHE_TTL = 3600  # 缓存1小时，日线不需要太频繁更新


def get_kline(symbol, count=30):
    """获取日K线数据，返回 [[date, open, close, high, low, volume], ...]"""
    url = f"http://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={symbol},day,,,{count},qfq"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=8)
        data = resp.json()
        klines = data["data"][symbol].get("qfqday") or data["data"][symbol].get("day")
        return klines or []
    except Exception as e:
        print(f"[kline_qq] {symbol} error: {e}")
        return []


def calc_indicators(symbol):
    """计算MA5、MA20、5日均量，返回字典，带缓存"""
    today = datetime.now().strftime("%Y-%m-%d")
    if symbol in _cache and _cache[symbol]["updated"] == today:
        return _cache[symbol]

    klines = get_kline(symbol, 30)
    if len(klines) < 20:
        return {"ma5": None, "ma20": None, "avg_vol_5": None, "close": None}

    closes = [float(k[2]) for k in klines]
    vols = [float(k[5]) for k in klines]

    ma5 = sum(closes[-5:]) / 5
    ma20 = sum(closes[-20:]) / 20
    avg_vol_5 = sum(vols[-6:-1]) / 5  # 前5日平均量（不含今天）
    today_close = closes[-1]
    today_vol = vols[-1]

    result = {
        "ma5": round(ma5, 2),
        "ma20": round(ma20, 2),
        "avg_vol_5": round(avg_vol_5, 0),
        "close": today_close,
        "today_vol": today_vol,
        "updated": today,
    }
    _cache[symbol] = result
    return result


def classify_volume(price_chg, today_vol, avg_vol_5):
    """判断量价关系：增量上涨/缩量上涨/增量下跌/缩量下跌"""
    if not avg_vol_5 or avg_vol_5 == 0:
        return "—"
    vol_ratio = today_vol / avg_vol_5
    if price_chg > 0:
        if vol_ratio > 1.2:
            return "放量上涨"
        elif vol_ratio < 0.8:
            return "缩量上涨"
        else:
            return "平量上涨"
    else:
        if vol_ratio > 1.2:
            return "放量下跌"
        elif vol_ratio < 0.8:
            return "缩量下跌"
        else:
            return "平量下跌"


def classify_ma(price, ma5, ma20):
    """判断均线位置"""
    if not ma5 or not ma20:
        return "—"
    above5 = price > ma5
    above20 = price > ma20
    if above5 and above20:
        return "站上5日/20日线"
    elif above5 and not above20:
        return "站上5日线"
    elif not above5 and above20:
        return "站上20日线"
    else:
        return "5日/20日线下方"


if __name__ == "__main__":
    # 测试
    for sym in ["sh600519", "sz300750", "sh600276"]:
        ind = calc_indicators(sym)
        print(f"{sym}: MA5={ind['ma5']}, MA20={ind['ma20']}, avgVol5={ind['avg_vol_5']}")
        vol_cls = classify_volume(1.5, ind["today_vol"], ind["avg_vol_5"])
        ma_cls = classify_ma(ind["close"], ind["ma5"], ind["ma20"])
        print(f"  -> {vol_cls} | {ma_cls}")
