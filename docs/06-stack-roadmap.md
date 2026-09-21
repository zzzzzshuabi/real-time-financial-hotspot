# 06 · 技术栈与路线图

## 1. 推荐技术栈

### MVP 阶段（2~4 周可跑通）

| 层 | 选型 | 理由 |
|---|---|---|
| 语言 | Python 3.11+ | 金融数据生态最全，开发快 |
| 采集 | aiohttp + websockets | 异步高并发 |
| 消息队列 | Redis Stream | 零部署，单进程搞定 |
| 时序存储 | SQLite / DuckDB | 本地文件级，MVP 够用 |
| 缓存 | Redis | 榜单、去重 |
| NLP | jieba + SnowNLP / FinBERT-Chinese | 情感分析 |
| 前端 | Streamlit / Gradio | 几行代码出榜单页 |
| 推送 | 企业微信机器人 Webhook | 零成本 |

### 生产阶段（2~3 月）

| 层 | 选型 | 理由 |
|---|---|---|
| 语言 | Python + Go（网关层） | Go 扛高并发 |
| 消息队列 | Kafka | 持久化、重放、多消费组 |
| 流计算 | Flink / Kafka Streams | 窗口计算、Exactly-Once |
| 时序库 | TDengine | A 股 tick 写入性价比高 |
| 关系库 | PostgreSQL | 元数据 |
| 搜索 | Elasticsearch | 新闻全文检索 |
| 对象存储 | MinIO / S3 | 原始报文归档 |
| 监控 | Prometheus + Grafana | 采集源健康度 |
| 部署 | Docker Compose → K8s | 先单机后集群 |
| 前端 | React + ECharts | 实时热力图、榜单 |

## 2. 分阶段路线图

### Phase 1：MVP（第 1~2 周）
- [ ] 接腾讯财经 WS，跑通 A 股实时行情
- [ ] 接财联社 RSS，快讯入 Redis
- [ ] 实现最简单的热度分：涨跌幅 + 量比 + 快讯计数
- [ ] Streamlit 页面展示 Top 20 热度榜
- [ ] 企微机器人推送 >80 分的股票

### Phase 2：信号增强（第 3~4 周）
- [ ] 接入东财资金流数据
- [ ] 接入雪球/股吧讨论量
- [ ] 中文情感分析（FinBERT）
- [ ] 板块级热度聚合
- [ ] 去重、断点续传、自动重连

### Phase 3：生产化（第 2~3 月）
- [ ] Kafka + Flink 替换 Redis Stream
- [ ] TDengine 替换 SQLite
- [ ] Elasticsearch 新闻搜索
- [ ] Grafana 监控面板
- [ ] 多通道推送（企微/钉钉/TG）
- [ ] 话题聚类（BERTopic）

### Phase 4：回测与优化（持续）
- [ ] 离线回测：Top 热点 T+1/T+5 涨跌幅
- [ ] 权重自动调参
- [ ] 误报率分析，调阈值
- [ ] 扩展到港股/美股/加密货币

## 3. 最小可行目录结构

```
real-time-financial-hotspot/
├── collectors/          # 采集器
│   ├── tick_qq.py       # 腾讯行情
│   ├── news_cls.py      # 财联社
│   ├── announcement.py  # 巨潮公告
│   └── social_xueqiu.py # 雪球
├── engines/            # 计算引擎
│   ├── price_anomaly.py
│   ├── money_flow.py
│   ├── sentiment.py
│   └── hotspot_fusion.py
├── storage/             # 存储
│   ├── redis_client.py
│   ├── timeseries.py
│   └── archive.py
├── notifier/            # 推送
│   ├── wecom_bot.py
│   └── dingtalk_bot.py
├── web/                 # 前端
│   └── app.py           # Streamlit
├── config/
│   └── settings.yaml
└── README.md
```

## 4. 合规与风控

- **数据合规**：只爬公开数据，遵守 robots.txt；商用数据走官方 API
- **版权**：新闻只存标题+摘要+链接，不全文转载
- **个人信息**：不爬取、不存储任何个人身份信息
- **礼貌使用**：QPS 限速，不对目标站造成压力
- **免责**：所有推送和页面标注"非投资建议，仅供参考"
- **数据安全**：API key 不硬编码，走环境变量 / 密钥管理
- **灾备**：原始报文多副本，关键配置版本化

## 5. 下一步建议

1. 先按 Phase 1 跑通最小闭环，别一上来就堆技术栈
2. 热度分权重先用经验值，上线后用真实数据回测调
3. 优先保证数据完整性，再谈算法精度
4. 每个采集源都要监控，挂了能告警
