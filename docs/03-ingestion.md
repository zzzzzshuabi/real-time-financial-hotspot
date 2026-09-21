# 03 · 实时采集设计

## 1. 三种采集模式

| 模式 | 适用场景 | 延迟 | 实现要点 |
|---|---|---|---|
| WebSocket 直连 | 行情、实时推送 | <1s | 断线自动重连、指数补偿 |
| HTTP 轮询 | RSS、新闻列表 | 3~30s | ETag/Last-Modified 增量拉取 |
| 定时爬虫 | 龙虎榜、财务数据 | 日级 | 调度器 + 失败重试 |

## 2. 统一事件 Schema

所有源的数据接入后，统一成内部标准事件：

```json
{
  "event_id": "uuid",
    "source": "cls_telegraph",
      "event_type": "news | tick | announcement | social | flow",
        "ts_ms": 1726891234567,
          "symbol": "600519.SH",
            "title": "标题",
              "content": "正文摘要",
                "raw_url": "https://...",
                  "extra": {}
                  }
                  ```

                  ## 3. 去重策略

                  - **文本类（新闻/社媒）**：URL 规范化后 MD5 去重；正文用 SimHash 64 位指纹，海明距离 ≤3 视为重复
                  - **行情 tick**：(symbol, ts_ms, price) 三元组去重
                  - **公告**：按披露编号（如 `临2024-001`）去重
                  - **已处理指纹存 Redis**，TTL 24~72 小时

                  ## 4. 可靠性设计

                  - **进程级**：每个 collector 独立进程，systemd / supervisor 守护，崩溃自动重启
                  - **断点续传**：记录每个源最后成功处理的时间戳 / offset，重启后从断点继续
                  - **熔断机制**：某源连续失败 N 次自动暂停，5 分钟后探测恢复
                  - **背压**：下游消费慢时，采集端限速，不把消息队列撑爆
                  - **原始报文归档**：全部落 MinIO，算法升级后可离线重放

                  ## 5. 消息队列设计

                  ### MVP：Redis Stream
                  - 简单，一个实例就够
                  - 消费者组（Consumer Group）支持多消费
                  - 缺点：扩容不如 Kafka

                  ### 生产：Kafka
                  - Topic 按事件类型分：`tick.*` / `news.raw` / `social.raw`
                  - 保留 7 天，供重放
                  - 3 副本，跨可用区

                  ## 6. 限流与反爬

                  - 每个外部源独立限速器（令牌桶）
                  - 请求间隔随机抖动，模拟真人
                  - User-Agent 池轮换
                  - 遇到 403/429 指数退避
                  - 不碰需要登录/付费墙的内容
