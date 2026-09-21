"""腾讯财经实时行情采集器（HTTP 轮询）"""
import re
import time
import requests
from datetime import datetime

# 热门股票池：覆盖白酒/新能源/AI/医药/金融/消费/科技
STOCK_POOL = {
    # 白酒消费
    "sh600519": "贵州茅台", "sz000858": "五粮液", "sh600809": "山西汾酒",
    # 新能源
    "sz300750": "宁德时代", "sh601012": "隆基绿能", "sz002594": "比亚迪",
    # AI / 科技
    "sh688981": "中芯国际", "sz002230": "科大讯飞", "sh688256": "寒武纪",
    "sz300308": "中际旭创", "sh603019": "中科曙光",
    # 医药
    "sh600276": "恒瑞医药", "sz300760": "迈瑞医疗",
    # 金融
    "sh601318": "中国平安", "sh600036": "招商银行",
    # 军工
    "sh600760": "中航沈飞", "sz002179": "中航光电",
    # 汽车/机械
    "sh601127": "赛力斯", "sz002594": "比亚迪",
    # 券商
    "sh600030": "中信证券", "sz000776": "广发证券",
    # 房地产/基建
    "sz001979": "招商蛇口", "sh601668": "中国建筑",
    # 其他热门
    "sh601899": "紫金矿业", "sz002415": "海康威视",
    "sh600900": "长江电力", "sz300059": "东方财富",
    "sh601888": "中国中免", "sz002475": "立讯精密",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://gu.qq.com/",
}


def fetch_quotes(symbols=None):
    """批量获取行情，返回 {symbol: {name, price, pct_chg, volume, turnover, ...}}"""
    if symbols is None:
        symbols = list(STOCK_POOL.keys())
    # 腾讯接口一次最多约 60 只
    url = "http://qt.gtimg.cn/q=" + ",".join(symbols)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=5)
        resp.encoding = "gbk"
        text = resp.text
    except Exception as e:
        print(f"[tick_qq] fetch error: {e}")
        return {}

    result = {}
    for line in text.strip().split(";"):
        line = line.strip()
        if not line or "=" not in line:
            continue
        try:
            # v_sh600519="1~贵州茅台~600519~..."
            var_part, data_part = line.split("=", 1)
            sym = var_part.replace("v_", "").strip()
            data_part = data_part.strip().strip('"')
            fields = data_part.split("~")
            if len(fields) < 40:
                continue
            result[sym] = {
                "name": fields[1],
                "code": fields[2],
                "price": float(fields[3]) if fields[3] else 0.0,
                "prev_close": float(fields[4]) if fields[4] else 0.0,
                "open": float(fields[5]) if fields[5] else 0.0,
                "volume": float(fields[6]) if fields[6] else 0.0,  # 手
                "amount": float(fields[37]) if fields[37] else 0.0,  # 万元
                "high": float(fields[33]) if fields[33] else 0.0,
                "low": float(fields[34]) if fields[34] else 0.0,
                "pct_chg": float(fields[32]) if fields[32] else 0.0,  # 涨跌幅%
                "turnover": float(fields[38]) if fields[38] else 0.0,  # 换手率%
                "pe": float(fields[39]) if fields[39] else 0.0,
                "ts": datetime.now().strftime("%H:%M:%S"),
            }
        except Exception as e:
            continue
    return result


if __name__ == "__main__":
    # 测试
    data = fetch_quotes(["sh600519", "sz300750", "sz000001"])
    for sym, q in data.items():
        print(f"{q['name']}({sym}): {q['price']}  {q['pct_chg']:+.2f}%  换手{q['turnover']}%")
