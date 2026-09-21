"""热点打分引擎：基于涨跌幅、换手率、量比等行情信号"""
from collections import deque
from datetime import datetime


class HotspotEngine:
    """维护每个 symbol 的历史行情，计算热度分"""

    def __init__(self, window=30):
        # 每个 symbol 保留最近 N 个采样点的成交量
        self.vol_history = {}
        self.window = window
        # 去重：已推送过的高热度 symbol 记录
        self.pushed = {}  # symbol -> (score, ts)

    def _vol_ratio(self, sym, current_volume):
        """计算量比：当前成交量 / 历史平均"""
        hist = self.vol_history.setdefault(sym, deque(maxlen=self.window))
        if len(hist) < 5:
            hist.append(current_volume)
            return 1.0
        avg = sum(hist) / len(hist)
        hist.append(current_volume)
        if avg == 0:
            return 1.0
        return current_volume / avg

    def score(self, quotes):
        """对一批行情数据打分，返回按热度降序的列表"""
        scored = []
        for sym, q in quotes.items():
            pct = abs(q.get("pct_chg", 0))
            turnover = q.get("turnover", 0)
            vr = self._vol_ratio(sym, q.get("volume", 0))

            # 归一化打分（0~100）
            # 涨跌幅：10% 满分
            s_pct = min(pct / 10.0, 1.0) * 40
            # 换手率：10% 满分
            s_turnover = min(turnover / 10.0, 1.0) * 30
            # 量比：5倍满分
            s_vr = min(vr / 5.0, 1.0) * 30

            score = round(s_pct + s_turnover + s_vr, 1)

            scored.append({
                "symbol": sym,
                "name": q["name"],
                "price": q["price"],
                "pct_chg": q["pct_chg"],
                "turnover": turnover,
                "vol_ratio": round(vr, 2),
                "score": score,
                "ts": q["ts"],
            })

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored

    def should_alert(self, item, threshold=70, cooldown_sec=180):
        """判断是否需要告警：高分 + 冷却期"""
        sym = item["symbol"]
        now = datetime.now().timestamp()
        last = self.pushed.get(sym)
        if item["score"] < threshold:
            return False
        if last and now - last < cooldown_sec:
            return False
        self.pushed[sym] = (item["score"], now)
        return True
