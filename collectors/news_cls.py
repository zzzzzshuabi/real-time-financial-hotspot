"""财联社快讯采集器（HTTP）"""
import time
import requests
from datetime import datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.cls.cn/telegraph",
}


def fetch_latest_news(limit=20):
    """获取财联社最新电报，返回 [{title, time, content}]"""
    url = (
        "https://www.cls.cn/nodeapi/telegraphList"
        "?app=CailianpressWeb&os=web&sv=8.4.6&category="
    )
    try:
        resp = requests.get(url, headers=HEADERS, timeout=8)
        data = resp.json()
        items = data.get("data", {}).get("roll_data", [])
    except Exception as e:
        print(f"[news_cls] fetch error: {e}")
        return []

    result = []
    for item in items[:limit]:
        title = item.get("title") or item.get("brief", "")
        content = item.get("content", "")
        # 去除HTML标签
        if content:
            import re
            content = re.sub(r"<[^>]+>", "", content)
        ctime = item.get("ctime", 0)
        try:
            t_str = datetime.fromtimestamp(ctime).strftime("%H:%M:%S")
        except Exception:
            t_str = datetime.now().strftime("%H:%M:%S")
        result.append({
            "title": title[:80] if title else content[:80],
            "content": content[:200],
            "time": t_str,
        })
    return result


if __name__ == "__main__":
    news = fetch_latest_news(10)
    for n in news:
        print(f"[{n['time']}] {n['title']}")
