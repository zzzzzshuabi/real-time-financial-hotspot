# 05 · 存储设计

## 1. 存储选型总览

| 存储 | 用途 | 选型理由 |
|---|---|---|
| Redis ZSet | 实时热点榜单 Top 100 | 毫秒级排序、自动过期 |
| TDengine / InfluxDB | tick、K线、分钟线时序 | 高写入、高压缩、SQL 查询 |
| PostgreSQL | 股票元数据、板块映射、热点日表 | 事务、关系查询 |
| Elasticsearch | 新闻/公告全文检索 | 中文分词、模糊搜索 |
| MinIO / S3 | 原始 JSON 报文归档 | 冷数据、可重放计算 |

## 2. Redis（热数据）

### Key 设计
- `hotspot:top:symbol` —— ZSet，member=symbol, score=hot_score，存 Top 500
- `hotspot:top:sector` —— 板块热度榜
- `hotspot:top:topic` —— 话题热度榜
- `hotspot:detail:{symbol}` —— Hash，存最新四路分数、触发时间
- `news:dedup:{hash}` —— String，去重指纹，TTL 72h
- `collector:offset:{source}` —— String，记录断点

### 要点
- 所有 key 设 TTL，防止内存膨胀
- ZSet 定期裁剪到 Top 500

## 3. 时序库（温数据）

### TDengine 建表示例

```sql
CREATE STABLE tick (
  ts TIMESTAMP, price DOUBLE, volume BIGINT, amount DOUBLE,
  bid1 DOUBLE, ask1 DOUBLE
) TAGS (symbol BINARY(16), market BINARY(8));

CREATE STABLE kline_1min (
  ts TIMESTAMP, open DOUBLE, high DOUBLE, low DOUBLE, close DOUBLE,
  volume BIGINT
) TAGS (symbol BINARY(16));
```

- 每个 symbol 一个子表
- 保留策略：tick 留 7 天，分钟线留 1 年，日线永久

## 4. PostgreSQL（元数据）

### 核心表

```sql
CREATE TABLE stock (
  symbol VARCHAR(16) PRIMARY KEY,
  name VARCHAR(32), sector VARCHAR(32), industry VARCHAR(32),
  list_date DATE
);

CREATE TABLE hotspot_daily (
  id BIGSERIAL PRIMARY KEY,
  symbol VARCHAR(16), date DATE, score INTEGER,
  price_anomaly NUMERIC, money_flow NUMERIC,
  sentiment NUMERIC, event NUMERIC, rank INTEGER
);

CREATE TABLE news_item (
  id BIGSERIAL PRIMARY KEY,
  url VARCHAR(512) UNIQUE,
  title VARCHAR(256), content TEXT, ts TIMESTAMP,
  sentiment NUMERIC, related_symbols VARCHAR(16)[]
);
```

## 5. Elasticsearch（新闻搜索）

- 索引按月滚动：`news-yyyy-MM`
- 中文分词用 IK Analyzer
- 字段：title, content, ts, related_symbols[], source
- 支持按关键词搜历史新闻、按股票搜相关新闻

## 6. MinIO / S3（冷数据）

- 路径：`raw/{source}/{yyyy}/{mm}/{dd}/{hh}.jsonl`
- 原始报文完整保留，供算法重放和回溯
- 生命周期：90 天后转归档存储降本

## 7. 数据生命周期

| 数据 | 热（Redis） | 温（DB） | 冷（归档） |
|---|---|---|---|
| tick | 实时榜 | TDengine 7 天 | 不归档 |
| 分钟线 | - | TDengine 1 年 | S3 永久 |
| 新闻 | 最新 100 条 | ES 90 天 | S3 永久 |
| 热点分 | ZSet Top 500 | PG 永久 | - |
