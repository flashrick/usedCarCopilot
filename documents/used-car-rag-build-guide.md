# AI Used Car Decision Copilot Build Guide

## 1. 项目定位

### 用户

- 第一次买车的人
- 预算有限、怕踩坑的人
- 想快速比较多辆车的人

### 核心问题

二手车平台里信息很多，但决策很难。用户通常不知道：

- 哪辆车更适合自己的场景
- 哪些 listing 有潜在风险
- 哪个价格更合理
- 哪些卖点只是营销词，哪些是真有价值

### 核心输出

系统不只回答问题，而是输出：

- 推荐车型或 listing 排名
- 推荐理由
- 风险提示
- 引用证据
- 对比报告
- 下一步建议

## 2. 为什么这个项目能打动 AI Engineer 招聘方

这个项目可以完整覆盖招聘里常见的 AI Engineer 能力要求：

- 端到端 RAG pipeline
- 文档 ingestion 和 chunking
- embedding 与向量索引
- hybrid retrieval
- reranking
- grounded generation with citations
- evaluation 和质量指标
- API 服务与前端集成
- 监控、日志、成本意识

最近公开职位也反复强调这些点：端到端 RAG、vector database、hybrid search、evaluation、Python API、监控和生产可靠性。

## 3. 最推荐的技术栈

为了兼顾招聘市场认知度、实现速度和演示效果，我建议：

### 后端

- Python
- FastAPI
- Pydantic
- Uvicorn

### AI 层

- OpenAI 或 Anthropic API
- Embedding model
- Reranker 可先用简单相似度，后续再升级

### 检索与存储

- `pgvector + PostgreSQL` 作为首选
- 如果你想突出“向量数据库”标签，也可以在第二版切到 Pinecone
- Redis 可选，用于缓存

### 数据处理

- Pandas
- BeautifulSoup 或 Playwright 做抓取和清洗

### 前端

- Next.js
- TypeScript
- Tailwind CSS

### 部署

- Vercel 部署前端
- Render / Railway / Fly.io / Azure App Service 部署 API
- Supabase 托管 Postgres

## 4. 数据设计

项目必须同时有结构化和非结构化数据。

### 结构化数据

- listing id
- price
- year
- mileage
- transmission
- fuel type
- seller type
- location
- brand / model / trim

### 非结构化数据

- listing 描述
- 车主评论
- 车型口碑
- 常见故障说明
- 维修保养建议
- 购车指南

### 推荐数据来源

- 公开二手车 listings 样本
- 公开车型参数页面
- 汽车论坛或公开评论
- 维修保养文章
- 自己手工构造一批高质量 demo 数据

注意：

- 第一版不需要追求“大而全”
- 先做一个垂直范围
- 例如只做 `Toyota / Mazda / Honda` 三个品牌

## 5. 系统架构

### 主流程

1. 用户输入需求
2. 后端解析预算、品牌偏好、用途、里程偏好等结构化条件
3. 同时检索：
   - listings 表
   - 向量库中的评论和知识片段
4. 对结果做 merge 和 rerank
5. 交给 LLM 生成：
   - 推荐结论
   - 风险点
   - 价格是否合理
   - 证据引用
6. 前端展示卡片、评分、引用片段和对比表

### 建议模块

- `ingestion`
- `embedding`
- `retrieval`
- `ranking`
- `generation`
- `evaluation`
- `api`
- `ui`

## 6. MVP 范围

第一版只做 4 个页面或模块：

- 搜索页：输入需求
- 推荐页：返回 top 3 结果
- 详情页：每辆车的证据与风险
- 对比页：两辆车并排比较

### MVP 必须完成的能力

- 支持自然语言查询
- 支持预算、品牌、用途的解析
- 支持向量检索
- 支持引用来源
- 支持简单风险评分
- 支持日志记录

### MVP 不要一开始就做

- 多 agent
- 复杂工作流编排
- fine-tuning
- 实时流式抓取
- 多模态图像识别

## 7. 分阶段开发步骤

## Phase 1: 定义问题和数据范围

- 定义目标用户画像
- 选 1 个城市或 1 个平台做 demo 范围
- 选 3 个品牌做样本集
- 定义 5 个最重要的决策维度：
  - 价格
  - 里程
  - 可靠性
  - 维护成本
  - 场景适配度

交付物：

- `problem statement`
- `scope`
- `data schema`

## Phase 2: 搭建数据层

- 建立 listings 表
- 建立 documents 表
- 建立 embeddings pipeline
- 把评论、车型知识、维护建议切 chunk
- 写入 pgvector

交付物：

- 可重复运行的 ingestion 脚本
- 数据字典
- 初始向量索引

## Phase 3: 做检索

- 做结构化过滤
- 做 semantic retrieval
- 做 hybrid retrieval
- 做 top-k 返回
- 做 chunk 去重

建议先用简单策略：

- structured filter 先过滤价格、品牌、年份
- 向量检索召回评论和知识
- 再按规则重排

交付物：

- `/search`
- `/retrieve`
- retrieval debug 输出

## Phase 4: 做答案生成

- 设计统一 prompt
- 输出 JSON 格式结果
- 结论必须绑定引用
- 生成风险标签和建议动作

推荐输出结构：

- `recommended_cars`
- `why_it_matches`
- `risk_flags`
- `price_commentary`
- `evidence`
- `next_steps`

交付物：

- `/recommend`
- citation-aware response

## Phase 5: 做评估

这是最能体现你不是“只会调用 API”的环节。

至少做 3 类评估：

- Retrieval:
  - top-k 命中是否合理
  - evidence 是否相关
- Generation:
  - 有没有胡编
  - 结论和引用是否一致
- Product:
  - 推荐结果是否可解释
  - 用户是否能据此做决定

建议做一份小型 eval 数据集：

- 20 个用户问题
- 每个问题手工写期望结果
- 记录命中率、引用质量、回答稳定性

交付物：

- `eval_cases.json`
- `eval_report.md`

## Phase 6: 做前端展示

前端不要做成普通聊天框，要更像一个决策工作台。

页面上至少展示：

- 用户需求摘要
- top 3 推荐
- 每辆车的适配评分
- 风险标签
- 引用片段
- 价格评论
- 对比表格

## Phase 7: 做工程化包装

- Dockerfile
- `.env.example`
- clear README
- 架构图
- demo 视频
- 错误日志
- 请求日志
- 成本记录

## 8. 你应该重点展示的技术亮点

如果你想让 HR 主动来找你，你要在项目里突出这些亮点：

### 亮点 1

不是普通 chatbot，而是 **decision support system**

### 亮点 2

同时结合：

- structured filtering
- vector retrieval
- grounded generation

### 亮点 3

有 **evaluation pipeline**

### 亮点 4

有 **citations、risk scoring、explainability**

### 亮点 5

有 **deployment、logs、observability**

## 9. GitHub 仓库结构建议

```text
used-car-ai-copilot/
  apps/
    web/
    api/
  packages/
    prompts/
    retrieval/
    evaluation/
  data/
    raw/
    processed/
  scripts/
    ingest_listings.py
    build_embeddings.py
    run_eval.py
  docs/
    architecture.md
    demo-script.md
    eval-report.md
  README.md
```

## 10. 8 周执行计划

### Week 1

- 定义问题
- 选数据范围
- 定 schema

### Week 2

- 收集和清洗 demo 数据
- 建库和 ingestion

### Week 3

- 做 embeddings 和向量检索

### Week 4

- 做 hybrid retrieval 和 rerank

### Week 5

- 做 recommendation API
- 做 citation 输出

### Week 6

- 做前端结果页和对比页

### Week 7

- 做 evaluation、日志、监控

### Week 8

- 写 README
- 录 demo
- 发布 LinkedIn

## 11. 完成后必须有的公开材料

- 一张架构图
- 一个 2 到 3 分钟 demo 视频
- GitHub README
- 3 到 5 张产品截图
- 一段 LinkedIn 项目介绍
- 一份 resume bullet

## 12. 面试时要怎么讲

你的讲法不要是：

> 我做了一个 AI 搜车工具。

你要讲成：

> 我设计并实现了一个面向真实购车场景的 AI decision support system。它把结构化 listing 数据和非结构化评论、维护知识结合起来，通过 hybrid retrieval、vector search 和 citation-based generation 输出可解释的推荐和风险提示。我还做了评估、日志和部署，目标是让系统不仅能回答问题，还能支持真实决策。

## 13. 第二项目建议

当这个项目做完后，第二个项目推荐做你 `IT` list 里的：

**搜集需求的 agent**

这样你的作品集会形成组合：

- 项目 1：RAG + vector DB + eval
- 项目 2：agent workflow + tool calling + orchestration

这个组合比两个纯 RAG 项目更强。
