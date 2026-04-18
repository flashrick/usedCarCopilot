# 当前项目学习指南

这份文档的目的，是帮助你从零开始理解这个项目目前已经有哪些文件、用了哪些技术、每个技术解决什么问题，以及接下来应该怎么学习。它不是产品介绍，而是一份项目学习地图。

项目当前状态：已经有产品文档、种子数据、数据校验脚本、FastAPI 后端、PostgreSQL + pgvector 数据库、SQLAlchemy ORM 数据访问层，以及一个初版检索接口。前端和真正的 embedding / LLM 生成还没有开始。

## 1. 项目一句话理解

这个项目是一个 AI 二手车决策助手。

用户输入类似：

```text
我想买一辆 15000 纽币以内、省油、适合通勤的 Honda 或 Toyota。
```

系统应该做的事情不是随便聊天，而是：

1. 理解用户的预算、品牌、车型、用途等需求。
2. 从二手车 listing 数据里筛选候选车辆。
3. 从车型知识库里找出相关风险、维修成本、口碑和购买建议。
4. 组合 listing 和知识证据，给出推荐、风险提示和引用来源。
5. 用 eval cases 检查检索和回答质量。

目前项目已经完成了第 1 个基础版本：可以把 seed data 导入 PostgreSQL，并通过 API 根据结构化条件检索 listing 和车型知识。

## 2. 当前目录结构

下面是当前项目最重要的目录。

```text
usedCarCopilot/
├── README.md
├── AGENTS.md
├── PLANS.md
├── docker-compose.yml
├── .env.example
├── documents/
├── data/
│   ├── raw/
│   ├── seed/
│   └── processed/
├── scripts/
├── apps/
│   ├── api/
│   └── web/
├── packages/
│   ├── prompts/
│   ├── retrieval/
│   └── evaluation/
└── learning/
```

### 根目录

`README.md`

这是 GitHub 首页会看到的项目说明。它解释项目目标、MVP 范围、计划技术栈、当前状态和后端快速启动方式。

`AGENTS.md`

这是给 Codex / agent 使用的本地工作规则。它记录了项目边界、当前状态、不要随便改哪些文件、Git 操作注意事项等。

`PLANS.md`

这是长期执行计划。它记录已经完成什么、下一步做什么、当前阻塞点和决策。

`docker-compose.yml`

用于启动本地 PostgreSQL + pgvector 数据库。这个项目目前依赖 Docker Compose 来启动数据库。

`.env.example`

环境变量模板。当前最重要的是数据库连接字符串：

```text
DATABASE_URL=postgresql+psycopg://used_car:used_car@127.0.0.1:5432/used_car_copilot
```

### `documents/`

这是项目早期产品和技术规划文档所在位置。

重要文件：

- `documents/product-brief.md`：产品目标。
- `documents/mvp-spec.md`：MVP 具体功能。
- `documents/technical-architecture.md`：技术架构。
- `documents/data-and-evaluation-plan.md`：数据和评估计划。
- `documents/delivery-roadmap.md`：开发路线。
- `documents/README.md`：最早的原始项目说明。
- `documents/used-car-rag-build-guide.md`：原始 RAG 构建指南。
- `documents/linkedin-hr-pack.md`：作品集 / 求职包装材料。

学习时应该先看这些文档，理解“为什么要做这个项目”。

### `data/`

这是数据目录。

`data/raw/`

原始数据。比如从 Turners 等二手车网站收集下来的原始 listing。

`data/seed/`

目前后端真正使用的种子数据。

重要文件：

- `data/seed/listings.jsonl`：车辆 listing 数据。
- `data/seed/knowledge_sources.jsonl`：车型知识、维修风险、购买建议等文本知识。
- `data/seed/eval_cases.json`：用于评估检索质量的测试问题。

`data/processed/`

未来用于放处理后的数据，目前还不是主要工作区。

### `scripts/`

这是根目录脚本。

`scripts/prepare_seed_data.py`

把原始 listing 数据处理成 seed data 格式。

`scripts/validate_seed_data.py`

检查 seed data 是否格式正确、字段是否完整、车型覆盖是否合理。

学习这个项目时，这个脚本很重要。它告诉你系统期待什么样的数据。

### `apps/api/`

这是当前最核心的实现部分：Python FastAPI 后端。

```text
apps/api/
├── README.md
├── pyproject.toml
├── migrations/
│   └── 001_init.sql
├── scripts/
│   ├── migrate.py
│   └── ingest_seed.py
└── app/
    ├── main.py
    ├── core/
    ├── db/
    ├── models/
    ├── ingestion/
    ├── retrieval/
    └── api/
```

`apps/api/pyproject.toml`

定义后端 Python 包和依赖。

当前主要依赖：

- `fastapi`
- `uvicorn`
- `pydantic`
- `sqlalchemy`
- `psycopg[binary]`

`apps/api/migrations/001_init.sql`

数据库建表 SQL。虽然运行时已经改成 ORM，但建表仍然用 migration SQL 文件。

当前表包括：

- `ingestion_runs`
- `listings`
- `knowledge_sources`
- `document_chunks`
- `chunk_embeddings`
- `eval_cases`
- `request_logs`

`apps/api/scripts/migrate.py`

读取 migration SQL，并把表创建到 PostgreSQL。

`apps/api/scripts/ingest_seed.py`

把 `data/seed/` 里的 JSONL / JSON 数据导入数据库。

`apps/api/app/main.py`

FastAPI 应用入口。

`apps/api/app/api/routes.py`

定义 HTTP API 路由。

当前 endpoint：

- `GET /health`
- `GET /listings`
- `GET /knowledge`
- `POST /retrieve`

`apps/api/app/core/config.py`

读取配置，例如 `DATABASE_URL`。

`apps/api/app/db/connection.py`

创建 SQLAlchemy engine 和 session。

这是后端连接数据库的入口。

`apps/api/app/db/orm.py`

定义 SQLAlchemy ORM model。

简单理解：这里的 Python class 对应数据库里的 table。

例如：

- `ListingRecord` 对应 `listings` 表。
- `KnowledgeSourceRecord` 对应 `knowledge_sources` 表。
- `DocumentChunkRecord` 对应 `document_chunks` 表。
- `ChunkEmbeddingRecord` 对应 `chunk_embeddings` 表。
- `EvalCaseRecord` 对应 `eval_cases` 表。
- `RequestLogRecord` 对应 `request_logs` 表。

`apps/api/app/models/schemas.py`

定义 Pydantic schema。

简单理解：Pydantic schema 用来描述 API 的输入输出格式。

`apps/api/app/ingestion/seed_loader.py`

导入 seed data 的核心逻辑。

它会：

1. 读取 `listings.jsonl`。
2. 读取 `knowledge_sources.jsonl`。
3. 读取 `eval_cases.json`。
4. 写入 PostgreSQL。
5. 记录一次 `ingestion_runs`。

`apps/api/app/retrieval/service.py`

当前检索逻辑。

它会：

1. 从用户 query 里推断一些 filter，例如车型、预算、body type。
2. 查询 `listings` 表找到候选车辆。
3. 根据候选车辆的 brand / model 查询 `knowledge_sources`。
4. 把请求记录到 `request_logs`。
5. 返回 listing、knowledge 和 debug 信息。

注意：当前检索还没有使用 embedding，也没有调用 LLM。它是一个先验证数据库和 API contract 的基础版本。

### `apps/web/`

未来的前端目录。

目前只有 README，还没有 Next.js 实现。

### `packages/`

未来共享包目录。

计划用途：

- `packages/prompts/`：prompt 模板。
- `packages/retrieval/`：可复用检索逻辑。
- `packages/evaluation/`：评估逻辑。

目前这些目录还没有真实代码。

### `learning/`

学习文档目录。

你现在正在看的这份文档就在这里。

## 3. 当前系统如何工作

可以把当前后端理解成下面这条链路：

```text
data/seed/*.jsonl / *.json
        |
        v
apps/api/scripts/ingest_seed.py
        |
        v
SQLAlchemy ORM
        |
        v
PostgreSQL + pgvector
        |
        v
FastAPI endpoints
        |
        v
GET /listings, GET /knowledge, POST /retrieve
```

如果用户调用 `POST /retrieve`，当前流程是：

```text
用户 query
   |
   v
RetrieveRequest
   |
   v
infer_filters()
   |
   v
查询 listings
   |
   v
根据候选 listing 的 brand/model 查询 knowledge_sources
   |
   v
写入 request_logs
   |
   v
RetrieveResponse
```

这个版本的意义是先让数据、数据库、API、schema 和检索返回格式跑通。之后再加入 embedding、向量检索、reranking 和 LLM 生成。

## 4. 当前用了哪些技术

### Python

后端主要语言。

你需要掌握：

- 函数、类型标注、dict/list。
- 文件读取。
- JSON / JSONL 处理。
- 虚拟环境 `.venv`。
- Python package 结构。

在本项目出现的位置：

- `scripts/`
- `apps/api/app/`
- `apps/api/scripts/`

### FastAPI

FastAPI 是 Python Web API 框架。

它负责：

- 定义 HTTP endpoint。
- 接收 request。
- 返回 response。
- 根据 Pydantic schema 做输入输出校验。

在本项目出现的位置：

- `apps/api/app/main.py`
- `apps/api/app/api/routes.py`

你要重点理解：

- `APIRouter`
- `@router.get(...)`
- `@router.post(...)`
- `response_model`
- request body 和 query parameter 的区别。

### Uvicorn

Uvicorn 是运行 FastAPI 的 ASGI server。

简单理解：FastAPI 是应用代码，Uvicorn 是把这个应用跑起来的服务器。

运行命令：

```bash
uvicorn app.main:app --app-dir apps/api --reload
```

### Pydantic

Pydantic 用来定义数据结构和校验数据。

在本项目中，Pydantic schema 用来定义：

- API 请求体。
- API 返回体。
- listing / knowledge 的字段结构。

出现位置：

```text
apps/api/app/models/schemas.py
```

你要理解：

- `BaseModel`
- 字段类型，例如 `str | None`
- 默认值
- `ConfigDict(from_attributes=True)`

`from_attributes=True` 的作用是让 Pydantic 可以直接从 SQLAlchemy ORM object 转成 API response。

### PostgreSQL

PostgreSQL 是关系型数据库。

这个项目用它存：

- 车辆 listing。
- 车型知识。
- 文档 chunk。
- 未来的 embedding 向量。
- eval cases。
- request logs。

出现位置：

- `docker-compose.yml`
- `apps/api/migrations/001_init.sql`
- `apps/api/app/db/`

### pgvector

pgvector 是 PostgreSQL 的向量扩展。

未来它用于存储 embedding，并支持向量相似度搜索。

当前 schema 已经有：

```sql
embedding vector(1536)
```

但目前还没有真正生成 embedding，也没有真正做向量搜索。

你现在只需要理解：

- embedding 是一组数字。
- 相似文本的 embedding 在向量空间里距离更近。
- pgvector 让 PostgreSQL 可以存这些向量并做相似度搜索。

### SQLAlchemy ORM

SQLAlchemy 是 Python 里常用的数据库工具。

ORM 的意思是 Object Relational Mapping。

简单理解：

数据库表：

```text
listings
```

Python class：

```python
class ListingRecord(Base):
    __tablename__ = "listings"
```

数据库中的一行：

```text
listing_id = "seed-civic-001"
brand = "Honda"
model = "Civic"
```

Python object：

```python
ListingRecord(
    listing_id="seed-civic-001",
    brand="Honda",
    model="Civic",
)
```

在本项目出现的位置：

- `apps/api/app/db/connection.py`
- `apps/api/app/db/orm.py`
- `apps/api/app/ingestion/seed_loader.py`
- `apps/api/app/retrieval/service.py`
- `apps/api/app/api/routes.py`

你要理解：

- `engine`
- `Session`
- `select()`
- `session.scalars(...)`
- `session.merge(...)`
- `session.add(...)`
- `relationship`
- `mapped_column`
- `Mapped[...]`

### psycopg

psycopg 是 Python 连接 PostgreSQL 的 driver。

SQLAlchemy 负责 ORM，psycopg 负责底层实际连接数据库。

当前数据库 URL 是：

```text
postgresql+psycopg://...
```

这表示 SQLAlchemy 使用 psycopg driver 连接 PostgreSQL。

### Docker Compose

Docker Compose 用来启动本地数据库。

当前项目没有要求你手动安装 PostgreSQL。你只需要用：

```bash
docker compose up -d postgres
```

它会根据 `docker-compose.yml` 启动一个带 pgvector 的 PostgreSQL container。

### JSON 和 JSONL

`JSON` 是常见数据格式。

例如：

```json
{
  "brand": "Honda",
  "model": "Civic"
}
```

`JSONL` 是每一行都是一个 JSON object 的格式。

例如：

```jsonl
{"brand":"Honda","model":"Civic"}
{"brand":"Toyota","model":"Prius"}
```

本项目用 JSONL 存 listing 和 knowledge source，是因为这种格式适合一行一条记录，方便追加、检查和导入。

### RAG

RAG 是 Retrieval-Augmented Generation。

中文可以理解为：先检索资料，再让大模型基于资料回答。

完整 RAG 流程通常是：

```text
用户问题
   |
   v
检索相关资料
   |
   v
把资料放进 prompt
   |
   v
LLM 生成答案
   |
   v
附上引用和证据
```

当前项目已经开始做 retrieval 的基础，但还没有做 LLM generation。

### Hybrid Retrieval

Hybrid retrieval 是混合检索。

未来这个项目计划结合：

- 结构化过滤：价格、年份、品牌、里程、地点、body type。
- 关键词搜索：文本里直接匹配词。
- 向量搜索：embedding semantic search。

当前已经有结构化过滤和车型知识关联，还没有关键词全文检索和向量检索。

### Evaluation

Evaluation 是评估。

这个项目不是只做一个能跑的 demo，而是要证明结果质量。

当前 eval data 在：

```text
data/seed/eval_cases.json
```

未来可以检查：

- 检索结果是否包含正确车型。
- 风险主题是否覆盖。
- citation 是否支持生成内容。
- 推荐是否稳定。

## 5. 数据库表怎么理解

### `listings`

车辆 listing。

核心字段：

- `listing_id`
- `title`
- `brand`
- `model`
- `year`
- `price`
- `mileage`
- `location`
- `body_type`
- `description`
- `raw_payload`

学习重点：这是系统推荐车辆的候选池。

### `knowledge_sources`

车型知识来源。

例如：

- 某车型常见问题。
- 维修风险。
- 购买建议。
- 油耗和使用场景。

核心字段：

- `source_id`
- `source_type`
- `source_channel`
- `title`
- `brand`
- `model`
- `tags`
- `summary`
- `text`
- `evidence_level`

学习重点：这是 RAG 里的知识库原文来源。

### `document_chunks`

知识来源切分后的文本块。

RAG 系统通常不会把一整篇长文直接塞给模型，而是先切成 chunk。

当前 chunk 是 ingestion 时从 `knowledge_sources.text` 切出来的。

学习重点：chunk 是未来 embedding 和向量检索的基本单位。

### `chunk_embeddings`

未来存 embedding。

当前表已经建好，但还没有数据。

核心字段：

- `chunk_id`
- `embedding_model`
- `embedding vector(1536)`

学习重点：这是 pgvector 将来真正发挥作用的地方。

### `eval_cases`

评估用例。

每条 eval case 通常包括：

- 用户 query。
- 期望 filters。
- 期望候选车型。
- 期望风险主题。

学习重点：这是让项目从“能跑”变成“可验证”的关键。

### `request_logs`

请求日志。

每次调用 `/retrieve` 会记录：

- endpoint
- query
- filters
- listing_count
- knowledge_count
- latency_ms
- error

学习重点：这是 observability 的起点。以后调试检索质量会很依赖日志。

### `ingestion_runs`

导入记录。

每次 seed data ingestion 都会记录：

- 开始时间。
- 完成时间。
- 状态。
- 导入了多少 listings / knowledge / eval cases。
- 错误信息。

学习重点：数据导入不能只看“脚本有没有报错”，还应该有可追踪的运行记录。

## 6. 目前可以运行的命令

先安装依赖：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e apps/api
```

校验 seed data：

```bash
python3 scripts/validate_seed_data.py
```

启动数据库：

```bash
docker compose up -d postgres
```

执行 migration：

```bash
python3 apps/api/scripts/migrate.py
```

导入 seed data：

```bash
python3 apps/api/scripts/ingest_seed.py
```

启动 API：

```bash
uvicorn app.main:app --app-dir apps/api --reload
```

测试 health：

```bash
curl http://127.0.0.1:8000/health
```

查看 listings：

```bash
curl "http://127.0.0.1:8000/listings?limit=2"
```

测试 retrieve：

```bash
curl -X POST http://127.0.0.1:8000/retrieve \
  -H "Content-Type: application/json" \
  -d '{"query":"I want a Honda Civic under $15000 for commuting","limit":3}'
```

停止数据库：

```bash
docker compose down
```

## 7. 应该按什么顺序学习

### 第 1 阶段：先理解产品目标

阅读：

1. `README.md`
2. `documents/product-brief.md`
3. `documents/mvp-spec.md`
4. `documents/technical-architecture.md`

你要能回答：

- 这个项目为什么不是普通 chatbot？
- 用户输入什么？
- 系统应该输出什么？
- 为什么需要 citation？
- 为什么需要 evaluation？

### 第 2 阶段：理解数据

阅读：

1. `data/README.md`
2. `data/seed/listings.jsonl`
3. `data/seed/knowledge_sources.jsonl`
4. `data/seed/eval_cases.json`
5. `scripts/validate_seed_data.py`

你要能回答：

- listing 是什么？
- knowledge source 是什么？
- eval case 是什么？
- 为什么 listing 和 knowledge 要分开？
- JSON 和 JSONL 有什么区别？

练习：

1. 手动读 3 条 listing。
2. 找出它们的 brand、model、price、mileage。
3. 在 `knowledge_sources.jsonl` 里找同 brand/model 的知识。
4. 运行 `python3 scripts/validate_seed_data.py`。

### 第 3 阶段：理解数据库

阅读：

1. `docker-compose.yml`
2. `apps/api/migrations/001_init.sql`
3. `apps/api/app/db/orm.py`

你要能回答：

- 为什么要用 PostgreSQL？
- `listings` 表和 `knowledge_sources` 表分别存什么？
- `document_chunks` 为什么存在？
- `chunk_embeddings` 现在为什么是空的？
- SQL table 和 ORM class 怎么对应？

练习：

1. 找到 `ListingRecord`。
2. 对照 `CREATE TABLE listings`。
3. 看每个字段类型是怎么对应的。
4. 找到 `KnowledgeSourceRecord` 和 `knowledge_sources` 的对应关系。

### 第 4 阶段：理解 ORM

阅读：

1. `apps/api/app/db/connection.py`
2. `apps/api/app/db/orm.py`
3. `apps/api/app/ingestion/seed_loader.py`
4. `apps/api/app/retrieval/service.py`

你要能回答：

- `engine` 是什么？
- `session` 是什么？
- `session.merge()` 和 `session.add()` 大概有什么区别？
- `select(ListingRecord)` 是什么意思？
- 为什么运行时不直接到处写 SQL？

练习：

1. 在 `seed_loader.py` 里找到写入 listing 的代码。
2. 在 `retrieval/service.py` 里找到查询 listing 的代码。
3. 对照 ORM class 看查询字段。

### 第 5 阶段：理解 API

阅读：

1. `apps/api/app/main.py`
2. `apps/api/app/api/routes.py`
3. `apps/api/app/models/schemas.py`

你要能回答：

- `GET /health` 做什么？
- `GET /listings` 返回什么？
- `POST /retrieve` 的 request body 长什么样？
- `response_model` 有什么作用？
- Pydantic schema 和 ORM model 有什么区别？

练习：

1. 启动 API。
2. 用 curl 调 `/health`。
3. 用 curl 调 `/listings?limit=2`。
4. 用 curl 调 `/retrieve`。
5. 看返回 JSON 里有哪些字段。

### 第 6 阶段：理解 retrieval

阅读：

```text
apps/api/app/retrieval/service.py
```

你要能回答：

- `infer_filters()` 做什么？
- `MODEL_ALIASES` 做什么？
- 当前是如何从 query 中识别 Honda Civic 的？
- 当前排序为什么优先 price、mileage、year？
- 为什么返回里有 `debug`？
- 为什么 `embedding_search_enabled` 是 `False`？

练习：

1. 搜索 Civic。
2. 搜索 SUV。
3. 搜索 under $15000。
4. 改变 limit，看返回数量变化。
5. 观察 `applied_filters`。

### 第 7 阶段：再学 RAG、embedding、pgvector

这一阶段是下一步开发会用到的。

你要先理解：

- chunk 是什么。
- embedding 是什么。
- vector search 是什么。
- pgvector 的 `vector(1536)` 是什么。
- cosine similarity 是什么。
- citation 为什么要绑定到 source/chunk。

当前代码里可以先看：

- `document_chunks` 表。
- `chunk_embeddings` 表。
- `DocumentChunkRecord`。
- `ChunkEmbeddingRecord`。

但要记住：这些现在是为下一步准备的，不代表已经完成 semantic search。

## 8. 技术名词怎么查

查技术名词时，建议用这个顺序：

1. 先在项目里搜，看它在哪里出现。
2. 再查官方文档。
3. 再看中文解释。
4. 最后看博客或视频。

### 在项目里查

查某个词在哪些文件出现：

```bash
rg "SQLAlchemy"
```

查某个 class：

```bash
rg "ListingRecord"
```

查 endpoint：

```bash
rg "/retrieve"
```

查所有文件：

```bash
rg --files
```

查数据库表：

```bash
rg "CREATE TABLE"
```

### 去网上查

推荐搜索格式：

```text
FastAPI official docs APIRouter
SQLAlchemy 2.0 ORM select official docs
Pydantic v2 BaseModel official docs
PostgreSQL JSONB official docs
pgvector official docs
Docker Compose official docs
RAG retrieval augmented generation explanation
embedding vector search cosine similarity explanation
```

如果你想要中文解释，可以加：

```text
中文解释
```

例如：

```text
SQLAlchemy ORM 中文解释
pgvector 中文解释
RAG 中文解释
```

### 怎么判断资料是否靠谱

优先级：

1. 官方文档。
2. 项目源码。
3. 官方 GitHub README。
4. 高质量教程。
5. 随机博客。

如果官方文档和博客说法冲突，优先相信官方文档和项目源码。

## 9. 常见术语表

### API

Application Programming Interface。

在这个项目里，API 指后端暴露给前端或用户调用的 HTTP 接口，比如 `/retrieve`。

### Endpoint

一个具体的 API 地址。

例如：

```text
GET /listings
POST /retrieve
```

### Request

客户端发给服务端的数据。

例如用户调用 `/retrieve` 时发：

```json
{
  "query": "I want a Honda Civic under $15000",
  "limit": 3
}
```

### Response

服务端返回给客户端的数据。

例如返回 listings、knowledge 和 debug。

### Schema

数据结构定义。

这个项目里有两种 schema：

- 数据库 schema：`001_init.sql`。
- API schema：`schemas.py`。

### Migration

数据库结构变更脚本。

当前是：

```text
apps/api/migrations/001_init.sql
```

### ORM

Object Relational Mapping。

用 Python class 操作数据库表，而不是在业务代码里到处手写 SQL。

### Model

这个词容易混淆。

在这个项目中可能有三种意思：

1. 车辆 model：例如 Honda Civic。
2. ORM model：例如 `ListingRecord`。
3. AI model：例如未来的 embedding model 或 LLM。

看到 model 时，要根据上下文判断。

### Engine

SQLAlchemy 里的数据库连接入口。

当前在：

```text
apps/api/app/db/connection.py
```

### Session

SQLAlchemy 里的一次数据库操作上下文。

你可以理解为：用 session 查询、写入、提交或回滚数据库。

### Driver

Python 连接数据库的底层库。

当前 driver 是 psycopg。

### Seed Data

开发初期手动准备或半自动准备的小规模数据，用来让系统能跑起来。

当前在：

```text
data/seed/
```

### Ingestion

数据导入。

在这个项目里，ingestion 指把 `data/seed/` 的文件写入 PostgreSQL。

### Listing

一条二手车广告 / 车源。

包含价格、里程、年份、地点、描述等。

### Knowledge Source

一条车型知识来源。

比如某个车型的常见问题、维修风险、购买建议。

### Chunk

长文本切分后的小文本块。

RAG 系统一般按 chunk 检索，而不是直接检索整篇长文。

### Embedding

把文本转换成一组数字向量。

语义相近的文本，embedding 通常也更接近。

### Vector Search

向量搜索。

用 embedding 找语义相似内容。

### pgvector

PostgreSQL 的向量扩展，用来存 embedding 并做向量相似度搜索。

### RAG

Retrieval-Augmented Generation。

先检索资料，再让 LLM 基于资料生成答案。

### Citation

引用来源。

在这个项目里，citation 很重要，因为推荐和风险提示必须能回到 listing 或 knowledge source。

### Reranking

重新排序。

通常先粗略召回一批候选结果，再用更精细的模型或规则重新排序。

### Observability

可观测性。

简单说，就是系统出问题时，你能通过日志、指标、trace 知道发生了什么。

当前的 `request_logs` 是 observability 的早期基础。

### Smoke Test

冒烟测试。

不是完整测试，只是快速确认核心链路是否能跑。

例如：

- `/health` 返回 ok。
- `/listings` 有数据。
- `/retrieve` 能返回候选车辆。

## 10. 如何从文件找到概念

如果你看到一个技术名词，不知道它在项目哪里，按下面找。

### FastAPI

看：

```text
apps/api/app/main.py
apps/api/app/api/routes.py
```

搜索：

```bash
rg "FastAPI|APIRouter|router"
```

### Pydantic

看：

```text
apps/api/app/models/schemas.py
```

搜索：

```bash
rg "BaseModel|ConfigDict"
```

### SQLAlchemy ORM

看：

```text
apps/api/app/db/connection.py
apps/api/app/db/orm.py
apps/api/app/retrieval/service.py
apps/api/app/ingestion/seed_loader.py
```

搜索：

```bash
rg "select\\(|session\\.|mapped_column|Mapped"
```

### PostgreSQL schema

看：

```text
apps/api/migrations/001_init.sql
```

搜索：

```bash
rg "CREATE TABLE|CREATE INDEX"
```

### 数据导入

看：

```text
apps/api/scripts/ingest_seed.py
apps/api/app/ingestion/seed_loader.py
```

搜索：

```bash
rg "ingest|seed|merge"
```

### 检索逻辑

看：

```text
apps/api/app/retrieval/service.py
```

搜索：

```bash
rg "retrieve|infer_filters|MODEL_ALIASES"
```

### 数据校验

看：

```text
scripts/validate_seed_data.py
```

搜索：

```bash
rg "validate|expected|required"
```

## 11. 推荐动手练习

### 练习 1：读懂一条 listing

打开：

```text
data/seed/listings.jsonl
```

找一条 Honda Civic。

回答：

- 它的 `listing_id` 是什么？
- `price` 是多少？
- `mileage` 是多少？
- `body_type` 是什么？
- `source` 是什么？

### 练习 2：找到同车型知识

打开：

```text
data/seed/knowledge_sources.jsonl
```

找 Honda Civic 相关知识。

回答：

- 它的 `source_type` 是什么？
- 它有什么 `tags`？
- 它的 `summary` 讲了什么？
- 它和 listing 如何关联？

### 练习 3：运行校验

运行：

```bash
python3 scripts/validate_seed_data.py
```

回答：

- 它校验了哪些文件？
- 如果字段缺失，它会在哪里报错？

### 练习 4：理解 ORM class

打开：

```text
apps/api/app/db/orm.py
```

找到：

```python
class ListingRecord(Base):
```

对照：

```text
apps/api/migrations/001_init.sql
```

回答：

- `listing_id` 在 SQL 里是什么类型？
- `listing_id` 在 ORM 里是什么类型？
- `raw_payload` 为什么是 JSONB？

### 练习 5：调用 API

启动数据库和 API 后，调用：

```bash
curl -X POST http://127.0.0.1:8000/retrieve \
  -H "Content-Type: application/json" \
  -d '{"query":"I want a Honda Civic under $15000 for commuting","limit":3}'
```

回答：

- `applied_filters` 里识别出了什么？
- 返回了几个 listings？
- 返回了哪些 knowledge？
- `debug.retrieval_mode` 是什么？

### 练习 6：做一个小改动

尝试在 `data/seed/listings.jsonl` 里加一条新 listing。

然后运行：

```bash
python3 scripts/validate_seed_data.py
python3 apps/api/scripts/ingest_seed.py
```

再调用 `/listings` 或 `/retrieve` 看它是否出现。

注意：真实开发时，改数据前应该先看当前格式，不要随便改字段名。

## 12. 当前还没有完成什么

这些是接下来会继续学习和实现的内容。

### 还没有真正的 semantic search

虽然数据库有 `chunk_embeddings` 表，也启用了 pgvector，但当前还没有：

- 调 embedding API。
- 写入 embedding。
- 按向量相似度搜索。

### 还没有 LLM 生成答案

当前 `/retrieve` 只返回候选 listing 和 knowledge。

还没有：

- prompt 模板。
- LLM 调用。
- final recommendation 生成。
- citation-grounded answer。

### 还没有前端

`apps/web/` 还没有 Next.js 应用。

### 还没有完整自动化测试

当前有数据校验和手动 smoke test，但还没有正式 pytest 测试套件。

### 还没有部署

当前是本地开发状态。

未来可能部署：

- frontend 到 Vercel。
- API 到 Render / Railway / Fly.io / Azure App Service。
- Postgres 到 Supabase 或其他托管数据库。

## 13. 你现在最应该掌握的最小知识集

如果你想尽快掌握当前项目，不需要一开始就把所有技术学很深。先掌握下面这些。

### 必须马上懂

- JSON / JSONL。
- Python 基础。
- FastAPI endpoint。
- Pydantic schema。
- PostgreSQL table。
- SQLAlchemy ORM class。
- seed data ingestion。
- `/retrieve` 当前检索流程。

### 可以稍后深入

- pgvector index。
- embedding 模型。
- reranking。
- LLM prompt engineering。
- evaluation metrics。
- frontend UI。
- deployment。

### 当前最重要的代码阅读顺序

建议按这个顺序读：

1. `README.md`
2. `data/README.md`
3. `data/seed/listings.jsonl`
4. `data/seed/knowledge_sources.jsonl`
5. `scripts/validate_seed_data.py`
6. `apps/api/migrations/001_init.sql`
7. `apps/api/app/db/orm.py`
8. `apps/api/app/db/connection.py`
9. `apps/api/app/ingestion/seed_loader.py`
10. `apps/api/app/models/schemas.py`
11. `apps/api/app/api/routes.py`
12. `apps/api/app/retrieval/service.py`

读完之后，你应该能说清楚：

- 数据从哪里来。
- 数据怎么进数据库。
- API 怎么查数据库。
- `/retrieve` 怎么返回候选结果。
- 下一步为什么要加 embedding 和 LLM。

## 14. 一张当前项目概念图

```text
              documents/
                  |
                  v
            产品目标和技术计划

data/raw/  --->  scripts/prepare_seed_data.py
                  |
                  v
              data/seed/
                  |
                  v
        scripts/validate_seed_data.py
                  |
                  v
        apps/api/scripts/ingest_seed.py
                  |
                  v
          SQLAlchemy ORM models
                  |
                  v
        PostgreSQL + pgvector database
                  |
                  v
             FastAPI endpoints
                  |
                  v
      /health  /listings  /knowledge  /retrieve
                  |
                  v
       retrieval/service.py 当前检索逻辑
```

## 15. 学习时不要混淆的几组概念

### ORM model 和 Pydantic schema

ORM model：

- 面向数据库。
- 对应 table。
- 例子：`ListingRecord`。

Pydantic schema：

- 面向 API 输入输出。
- 对应 request / response。
- 例子：`Listing`、`RetrieveRequest`、`RetrieveResponse`。

### Migration 和 ORM

Migration：

- 创建或修改数据库结构。
- 当前是 SQL 文件。

ORM：

- 运行时读写数据库。
- 当前是 Python class。

### Listing 和 Knowledge

Listing：

- 具体某一辆车。
- 有价格、年份、里程。

Knowledge：

- 关于某车型或购买风险的知识。
- 用于解释为什么推荐或提醒风险。

### Retrieval 和 Generation

Retrieval：

- 找资料。
- 当前已经有基础版本。

Generation：

- 用 LLM 组织最终回答。
- 当前还没有实现。

### pgvector 已配置 和 semantic search 已完成

pgvector 已配置：

- 数据库支持向量字段。
- schema 有 `chunk_embeddings`。

semantic search 已完成：

- 需要真的生成 embedding。
- 需要写入 embedding。
- 需要查询向量相似度。

当前项目只完成了前者，还没有完成后者。

## 16. 接下来学习和开发的合理方向

建议下一步按这个顺序推进：

1. 给当前 API 加 pytest 测试。
2. 给 retrieval 写评估脚本，读取 `eval_cases.json`。
3. 生成 knowledge chunk embeddings。
4. 把 `/retrieve` 从结构化过滤升级为 hybrid retrieval。
5. 加 LLM 生成推荐答案。
6. 加 citation 检查。
7. 再开始前端。

为什么先做测试和评估？

因为这个项目的重点是 portfolio-grade AI engineering。它不只是做一个页面，而是要展示：

- 数据质量。
- 检索质量。
- 可解释推荐。
- 引用证据。
- 评估和观测。
- 可部署 API/UI。

## 17. 每次学习一个新技术时的提问模板

当你遇到一个新词，比如 SQLAlchemy、pgvector、Pydantic，可以按这个模板问自己：

1. 它解决什么问题？
2. 如果没有它，项目会怎么做？
3. 它在本项目哪个文件出现？
4. 它的输入是什么？
5. 它的输出是什么？
6. 它和上下游文件怎么连接？
7. 当前项目只是配置了它，还是已经真正使用了它？

用这个模板，你会更容易判断一个技术在项目里的真实作用，而不是只背定义。

