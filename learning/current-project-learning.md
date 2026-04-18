# 当前项目学习指南

这份文档用于帮助你理解 `usedCarCopilot` 当前已经完成了什么、每个目录和技术点的作用、怎样在本地跑起来，以及下一步应该学什么。

它不是产品宣传文案，而是项目学习地图。读完后，你应该能回答三个问题：

1. 这个项目现在做到哪一步了。
2. 后端数据、数据库、embedding、检索 API 是怎么连起来的。
3. 下一步开发 eval runner 和 recommendation API 前，需要先补哪些知识。

## 0. 当前状态

项目当前处于早期后端实现阶段。

已经完成：

- 产品和技术规划文档。
- canonical seed data：listing、knowledge source、eval cases。
- seed data 校验脚本。
- FastAPI 后端骨架。
- PostgreSQL + pgvector 本地数据库。
- SQLAlchemy ORM 数据访问层。
- seed ingestion：把 `data/seed/` 导入数据库。
- document chunk 生成。
- 本地 deterministic embedding 生成。
- `chunk_embeddings` 向量存储。
- `/retrieve` 结构化 listing 检索。
- `/retrieve` pgvector semantic chunk 检索。
- 请求 debug metadata。

还没有完成：

- 外部 embedding provider，例如 OpenAI embeddings。
- LLM recommendation generation。
- citation-aware recommendation JSON。
- eval runner 和 eval report。
- Next.js 前端。
- 部署。

当前最重要的下一步：

1. 给 `/retrieve` 增加 eval runner。
2. 用 `data/seed/eval_cases.json` 检查候选车型和风险主题覆盖率。
3. 再做 `/recommend`，生成 citation-aware JSON。

## 1. 项目一句话理解

这个项目是一个 AI 二手车决策助手。

用户输入类似：

```text
I want a reliable Toyota hybrid for daily commuting under 16000. Should I consider Aqua or Prius?
```

系统最终应该做的事情不是泛泛聊天，而是：

1. 解析预算、品牌、车型、用途等需求。
2. 从 listing 数据中筛选候选车辆。
3. 从车型知识库中检索相关风险、维修建议和购买建议。
4. 把 listing facts 和 knowledge evidence 合并。
5. 输出推荐、风险提示、引用来源和 debug 信息。
6. 用 eval cases 检查检索和回答质量。

当前项目已经跑通了前半段：

```text
seed data -> PostgreSQL -> embeddings -> pgvector retrieval -> /retrieve response
```

还没有进入 LLM 生成阶段。

## 2. 当前核心目录

```text
usedCarCopilot/
├── README.md
├── AGENTS.md
├── PLANS.md
├── docker-compose.yml
├── documents/
├── data/
│   ├── raw/
│   └── seed/
├── scripts/
├── apps/
│   ├── api/
│   └── web/
├── packages/
└── learning/
```

### 根目录

`README.md`

面向 GitHub 读者的项目说明。当前已经写明后端可以做 seed ingestion、local chunk embedding、pgvector semantic retrieval。

`AGENTS.md`

给 Codex / agent 使用的项目规则。重点是编辑边界和技术约束。

关键规则：

- 不要随便改原始规划文档。
- canonical seed data 在 `data/seed/`。
- 数据库 schema 变更放在 `apps/api/migrations/`。
- 后端 ingestion 代码放在 `apps/api/app/ingestion/`。
- 运行时数据库访问必须用 SQLAlchemy ORM。

`PLANS.md`

长期执行计划。当前状态是：

```text
Stage: Hybrid retrieval backend scaffold verified.
```

它记录了当前已完成本地 embedding 和 pgvector semantic retrieval，下一步是 eval runner。

`docker-compose.yml`

启动本地 PostgreSQL + pgvector。

核心命令：

```bash
docker compose up -d postgres
```

### `documents/`

项目产品和技术规划。

建议阅读顺序：

1. `documents/product-brief.md`
2. `documents/mvp-spec.md`
3. `documents/technical-architecture.md`
4. `documents/data-and-evaluation-plan.md`
5. `documents/delivery-roadmap.md`

原始笔记包括：

- `documents/README.md`
- `documents/used-car-rag-build-guide.md`
- `documents/linkedin-hr-pack.md`

这些原始笔记不要随便重写。

### `data/`

数据目录。

`data/raw/`

原始导出数据，可以重新生成或重新规范化。

`data/seed/`

当前后端真正使用的 canonical seed data。

重要文件：

- `data/seed/listings.jsonl`
- `data/seed/knowledge_sources.jsonl`
- `data/seed/eval_cases.json`

`listings.jsonl`

车辆 listing。包含价格、里程、车型、地点、车身类型、燃料类型、seller description 等。

`knowledge_sources.jsonl`

车型知识。包含 maintenance notes、owner experience、buying guide、risk themes 等。

`eval_cases.json`

后续 eval runner 要用的测试问题。每条 case 包含：

- 用户 query。
- expected filters。
- expected candidate models。
- expected risk themes。

### `scripts/`

根目录数据脚本。

`scripts/prepare_seed_data.py`

把 raw listing 数据规范化成 seed listing。

`scripts/validate_seed_data.py`

校验 seed data。

常用命令：

```bash
python3 scripts/validate_seed_data.py
```

当前验证结果应该包含这些模型：

```text
Honda Civic, Honda Fit, Honda HR-V,
Mazda CX-5, Mazda Mazda2, Mazda Mazda3,
Toyota Aqua, Toyota Prius, Toyota RAV4
```

### `apps/api/`

当前最核心的实现目录。

```text
apps/api/
├── README.md
├── pyproject.toml
├── migrations/
│   ├── 001_init.sql
│   └── 002_chunk_embedding_content_hash.sql
├── scripts/
│   ├── migrate.py
│   ├── ingest_seed.py
│   └── build_embeddings.py
└── app/
    ├── main.py
    ├── api/
    ├── core/
    ├── db/
    ├── embedding/
    ├── ingestion/
    ├── models/
    └── retrieval/
```

`apps/api/pyproject.toml`

定义后端 Python 包和依赖。

主要依赖：

- `fastapi`
- `uvicorn`
- `pydantic`
- `sqlalchemy`
- `psycopg[binary]`

`apps/api/migrations/001_init.sql`

创建基础 schema。

核心表：

- `ingestion_runs`
- `listings`
- `knowledge_sources`
- `document_chunks`
- `chunk_embeddings`
- `eval_cases`
- `request_logs`

`apps/api/migrations/002_chunk_embedding_content_hash.sql`

给 `chunk_embeddings` 增加 `content_hash`。

作用：如果 chunk 文本没有变化，重复运行 embedding 脚本时可以跳过，不重复写入。

`apps/api/scripts/migrate.py`

现在会按文件名顺序执行 `apps/api/migrations/*.sql`，不再只执行一个 migration。

`apps/api/scripts/ingest_seed.py`

把 seed data 导入 PostgreSQL。

它会导入：

- listings
- knowledge sources
- document chunks
- eval cases

`apps/api/scripts/build_embeddings.py`

为 `document_chunks` 生成本地 embedding，并写入 `chunk_embeddings`。

当前使用的 embedding model 名称：

```text
local-hash-embedding-v1
```

注意：这是开发阶段的 deterministic local embedding provider。它不等于生产级 embedding，也不等于 OpenAI embedding。它的作用是让 pgvector pipeline 在没有外部 API key 的情况下先跑通。

### `apps/api/app/main.py`

FastAPI 应用入口。

### `apps/api/app/api/routes.py`

HTTP 路由定义。

当前 endpoints：

- `GET /health`
- `GET /listings`
- `GET /knowledge`
- `POST /retrieve`

### `apps/api/app/core/config.py`

读取配置。

当前最重要的是：

```text
DATABASE_URL
SEED_DATA_DIR
API_HOST
API_PORT
```

默认数据库连接：

```text
postgresql+psycopg://used_car:used_car@127.0.0.1:5432/used_car_copilot
```

### `apps/api/app/db/connection.py`

创建 SQLAlchemy engine 和 session。

你需要理解：

- `create_engine(...)`
- `sessionmaker(...)`
- `get_session()`
- commit / rollback / close

### `apps/api/app/db/orm.py`

SQLAlchemy ORM model。

可以理解为：Python class 对应数据库 table。

主要 class：

- `ListingRecord`
- `KnowledgeSourceRecord`
- `DocumentChunkRecord`
- `ChunkEmbeddingRecord`
- `EvalCaseRecord`
- `RequestLogRecord`
- `IngestionRunRecord`

这里还有一个自定义类型：

```python
class Vector(UserDefinedType):
```

它把 Python 的 `list[float]` 转成 pgvector 可以接收的字符串格式：

```text
[0.1,0.2,0.3]
```

也支持从数据库返回值转回 Python list。

### `apps/api/app/models/schemas.py`

Pydantic schema。

当前重要 schema：

- `Listing`
- `KnowledgeSource`
- `RetrievedChunk`
- `RetrieveRequest`
- `RetrieveResponse`

`RetrieveResponse` 当前包含：

```text
query
applied_filters
listings
knowledge
chunks
debug
```

其中 `chunks` 是 semantic retrieval 返回的证据片段。

### `apps/api/app/ingestion/seed_loader.py`

seed ingestion 核心逻辑。

流程：

```text
read listings.jsonl
read knowledge_sources.jsonl
read eval_cases.json
write listings
write knowledge_sources
split knowledge text into document_chunks
write eval_cases
write ingestion_runs
```

当前 chunk 逻辑比较简单：按 word count 切分，每 chunk 默认最多 180 words。

### `apps/api/app/embedding/service.py`

本地 embedding provider。

核心 class：

```python
class LocalHashEmbeddingProvider:
```

它做的事情：

1. 把文本切成 token。
2. 加入一些汽车领域词扩展，例如 `commute -> fuel/economy/urban`。
3. 用 hash 把 token 映射到 1536 维向量桶。
4. 做 L2 normalization。

优点：

- 不需要网络。
- 不需要 API key。
- 每次结果稳定。
- 可以让 pgvector retrieval pipeline 先跑通。

缺点：

- 不是语义模型。
- 召回质量有限。
- 之后应该替换或抽象成真正 embedding provider。

### `apps/api/app/embedding/builder.py`

embedding 构建逻辑。

核心函数：

```python
build_chunk_embeddings(limit: int | None = None)
```

它会：

1. 查询所有 `document_chunks`。
2. 计算每个 chunk 的 `content_hash`。
3. 如果已有 embedding 且 model/hash 都没变，就跳过。
4. 否则生成 embedding 并写入 `chunk_embeddings`。

### `apps/api/app/retrieval/service.py`

当前 retrieval 核心逻辑。

它包含两部分：

1. 结构化 listing 检索。
2. pgvector semantic chunk 检索。

整体流程：

```text
RetrieveRequest
   |
   v
infer_filters()
   |
   v
query listings with structured filters
   |
   v
collect candidate brand/model pairs
   |
   v
query model-linked knowledge_sources
   |
   v
embed query with LocalHashEmbeddingProvider
   |
   v
pgvector cosine distance search over chunk_embeddings
   |
   v
write request_logs
   |
   v
RetrieveResponse
```

当前 debug 信息示例：

```json
{
  "candidate_models": ["Toyota Aqua", "Toyota Prius"],
  "retrieval_mode": "structured_filters_plus_semantic_chunks",
  "embedding_search_enabled": true,
  "embedding_model": "local-hash-embedding-v1",
  "semantic_chunk_count": 6
}
```

## 3. 本地运行顺序

从 repo root 执行。

### 1. 启动 PostgreSQL + pgvector

```bash
docker compose up -d postgres
```

### 2. 安装依赖

如果 `.venv` 已存在，先激活：

```bash
source .venv/bin/activate
```

如果还没安装 API 包：

```bash
pip install -e apps/api
```

### 3. 跑 migration

```bash
python3 apps/api/scripts/migrate.py
```

如果你使用 `.venv` 的解释器：

```bash
.venv/bin/python apps/api/scripts/migrate.py
```

### 4. 导入 seed data

```bash
python3 apps/api/scripts/ingest_seed.py
```

预期输出：

```text
Seed ingestion completed
- listings: 63
- knowledge_sources: 27
- eval_cases: 20
```

### 5. 生成 embeddings

```bash
python3 apps/api/scripts/build_embeddings.py
```

第一次预期类似：

```text
Chunk embedding generation completed
- embedding_model: local-hash-embedding-v1
- scanned_chunks: 27
- embedded_chunks: 27
- skipped_chunks: 0
```

第二次预期类似：

```text
Chunk embedding generation completed
- embedding_model: local-hash-embedding-v1
- scanned_chunks: 27
- embedded_chunks: 0
- skipped_chunks: 27
```

### 6. 启动 API

```bash
uvicorn app.main:app --app-dir apps/api --reload
```

### 7. 调用 `/retrieve`

示例 request：

```json
{
  "query": "I want a reliable Toyota hybrid for daily commuting under 16000. Should I consider Aqua or Prius?",
  "limit": 3
}
```

预期结果：

- `applied_filters.max_price = 16000`
- `applied_filters.models` 包含 `Aqua` 和 `Prius`
- `listings` 返回候选车辆
- `chunks` 返回 semantic evidence chunks
- `debug.embedding_search_enabled = true`

## 4. 当前系统如何工作

### 数据导入链路

```text
data/seed/listings.jsonl
data/seed/knowledge_sources.jsonl
data/seed/eval_cases.json
        |
        v
apps/api/scripts/ingest_seed.py
        |
        v
apps/api/app/ingestion/seed_loader.py
        |
        v
SQLAlchemy ORM
        |
        v
PostgreSQL tables
```

### embedding 链路

```text
document_chunks
        |
        v
apps/api/scripts/build_embeddings.py
        |
        v
LocalHashEmbeddingProvider
        |
        v
chunk_embeddings.embedding vector(1536)
```

### retrieval 链路

```text
POST /retrieve
        |
        v
RetrieveRequest
        |
        v
infer_filters()
        |
        v
structured listings query
        |
        v
model-linked knowledge query
        |
        v
query embedding
        |
        v
pgvector semantic chunk query
        |
        v
RetrieveResponse
```

## 5. 当前用了哪些技术

### Python

后端主要语言。

你需要掌握：

- 函数。
- 类型标注。
- `dict` / `list`。
- `Path`。
- JSON / JSONL。
- package import。
- 虚拟环境。

重点文件：

- `scripts/validate_seed_data.py`
- `apps/api/app/ingestion/seed_loader.py`
- `apps/api/app/embedding/service.py`
- `apps/api/app/retrieval/service.py`

### FastAPI

Web API 框架。

它负责：

- 定义 endpoint。
- 接收 request。
- 返回 response。
- 用 Pydantic 做输入输出校验。

重点文件：

- `apps/api/app/main.py`
- `apps/api/app/api/routes.py`

重点概念：

- `APIRouter`
- `@router.get`
- `@router.post`
- `response_model`
- request body
- query parameter

### Pydantic

定义 API 输入输出结构。

重点文件：

```text
apps/api/app/models/schemas.py
```

重点概念：

- `BaseModel`
- `Field`
- `ConfigDict(from_attributes=True)`
- `str | None`
- `list[...]`
- response validation

### PostgreSQL

关系型数据库。

本项目用它存：

- listing。
- knowledge source。
- document chunk。
- embedding vector。
- eval case。
- request log。

### pgvector

PostgreSQL 向量扩展。

本项目使用：

```sql
embedding vector(1536)
```

semantic retrieval 使用 cosine distance operator：

```sql
<=>
```

在 SQLAlchemy 中通过：

```python
ChunkEmbeddingRecord.embedding.op("<=>")(...)
```

### SQLAlchemy ORM

数据库访问层。

本项目运行时数据库访问必须用 ORM，不要直接在业务代码里写 raw SQL。

重点概念：

- `DeclarativeBase`
- `Mapped`
- `mapped_column`
- `relationship`
- `select`
- `join`
- `outerjoin`
- `session.execute`
- `session.scalars`
- `session.merge`
- `session.add`

### psycopg

PostgreSQL driver。

数据库 URL：

```text
postgresql+psycopg://used_car:used_car@127.0.0.1:5432/used_car_copilot
```

SQLAlchemy 负责 ORM 抽象，psycopg 负责底层连接。

### Docker Compose

用于启动本地数据库。

命令：

```bash
docker compose up -d postgres
docker compose ps
docker compose logs --tail 80 postgres
```

### JSON / JSONL

`JSON`：一个完整 JSON 文档。

`JSONL`：每一行是一个 JSON object。

本项目用 JSONL 存 listing 和 knowledge source，因为它适合一条记录一行，方便导入和校验。

### RAG

RAG 是 Retrieval-Augmented Generation。

完整流程：

```text
user query
   |
   v
retrieve evidence
   |
   v
build prompt with evidence
   |
   v
LLM generation
   |
   v
answer with citations
```

当前项目已经完成 retrieval 的基础部分，但还没有做 LLM generation。

### Hybrid Retrieval

Hybrid retrieval 是混合检索。

本项目当前已经有：

- 结构化过滤：location、max_price、brand、models、body_type。
- model-linked knowledge retrieval。
- pgvector semantic chunk retrieval。

未来可以继续加：

- full-text keyword search。
- reranking。
- listing + evidence scoring。

### Evaluation

Evaluation 是项目质量证明。

当前 eval data 在：

```text
data/seed/eval_cases.json
```

下一步 eval runner 应该检查：

- query 推断出的 filters 是否合理。
- listing candidate models 是否覆盖 expected models。
- semantic chunks 是否覆盖 expected risk themes。
- debug metadata 是否足够定位问题。

## 6. 当前 API 合约

### `GET /health`

检查数据库连接是否正常。

返回：

```json
{
  "status": "ok"
}
```

### `GET /listings`

返回 listing 列表。

参数：

```text
limit: int = 20
```

### `GET /knowledge`

返回 knowledge source 列表。

参数：

```text
limit: int = 20
```

### `POST /retrieve`

请求 schema：

```json
{
  "query": "string",
  "max_price": 16000,
  "brand": "Toyota",
  "models": ["Aqua", "Prius"],
  "body_type": "hatchback",
  "location": "Auckland",
  "limit": 5
}
```

所有字段不一定都要传。

当前 `infer_filters()` 会从 query 里保守推断：

- 车型，例如 Aqua、Prius、Civic。
- body type，例如 suv、hatchback、sedan。
- `under 16000` 形式的预算。

返回 schema：

```json
{
  "query": "...",
  "applied_filters": {},
  "listings": [],
  "knowledge": [],
  "chunks": [],
  "debug": {}
}
```

`chunks` 中每条记录包含：

```json
{
  "chunk_id": "...",
  "source_id": "...",
  "source_title": "...",
  "source_type": "maintenance",
  "brand": "Toyota",
  "model": "Aqua",
  "evidence_level": "medium",
  "text": "...",
  "similarity": 0.1234
}
```

## 7. 已验证过的命令

这些命令已经在当前项目状态下跑通过。

```bash
python3 scripts/validate_seed_data.py
```

```bash
.venv/bin/python -m compileall apps/api/app apps/api/scripts
```

```bash
docker compose up -d postgres
```

```bash
.venv/bin/python apps/api/scripts/migrate.py
```

```bash
.venv/bin/python apps/api/scripts/ingest_seed.py
```

```bash
.venv/bin/python apps/api/scripts/build_embeddings.py
```

服务层 retrieval smoke test 已验证：

- 可以解析 `under 16000`。
- 可以返回 Toyota Aqua / Prius listing。
- 可以返回 Aqua / Prius semantic chunks。
- `debug.embedding_search_enabled = true`。

注意：FastAPI `TestClient` 当前没有跑，因为环境里缺 `httpx`。这不是业务代码问题。如果要做正式 API test，可以把 `httpx` 加到 dev/test dependencies。

## 8. 建议学习顺序

### 第一阶段：理解数据

读：

1. `data/seed/listings.jsonl`
2. `data/seed/knowledge_sources.jsonl`
3. `data/seed/eval_cases.json`
4. `scripts/validate_seed_data.py`

目标：

- 知道 listing 有哪些字段。
- 知道 knowledge source 有哪些字段。
- 知道 eval case 希望检查什么。

### 第二阶段：理解数据库

读：

1. `apps/api/migrations/001_init.sql`
2. `apps/api/migrations/002_chunk_embedding_content_hash.sql`
3. `apps/api/app/db/orm.py`

目标：

- 知道每张表存什么。
- 知道 ORM class 如何对应 table。
- 知道 `chunk_embeddings` 如何存 vector。

### 第三阶段：理解 ingestion

读：

1. `apps/api/scripts/ingest_seed.py`
2. `apps/api/app/ingestion/seed_loader.py`

目标：

- 知道 seed data 如何写入数据库。
- 知道 knowledge source 如何变成 document chunks。
- 知道 ingestion run 如何记录。

### 第四阶段：理解 embedding

读：

1. `apps/api/scripts/build_embeddings.py`
2. `apps/api/app/embedding/service.py`
3. `apps/api/app/embedding/builder.py`

目标：

- 知道本地 embedding provider 只是开发 scaffold。
- 知道 content hash skip 是怎么工作的。
- 知道未来替换 OpenAI embeddings 时应该替换哪一层。

### 第五阶段：理解 retrieval

读：

1. `apps/api/app/models/schemas.py`
2. `apps/api/app/retrieval/service.py`
3. `apps/api/app/api/routes.py`

目标：

- 知道 request schema。
- 知道 filters 如何推断。
- 知道 listing query 如何构造。
- 知道 semantic chunk query 如何构造。
- 知道 response 里每个字段给谁用。

### 第六阶段：做 eval runner

下一步最适合做这个。

建议新增：

```text
apps/api/app/evaluation/
apps/api/scripts/run_retrieval_eval.py
```

eval runner 第一版不需要复杂。

它可以：

1. 读取数据库里的 `eval_cases`。
2. 对每条 case 调用 `retrieve(...)`。
3. 检查 candidate models 覆盖率。
4. 检查 chunks 文本是否包含 expected risk themes 的关键词。
5. 输出 pass/fail summary。

第一版目标不是完美评估，而是建立回归测试入口。

## 9. 当前技术债和注意点

### local hash embedding 不是最终方案

`local-hash-embedding-v1` 是为了让 pgvector pipeline 先跑通。

不能把它当成真正语义 embedding。

后续应该做 provider abstraction，例如：

```text
EmbeddingProvider
├── LocalHashEmbeddingProvider
└── OpenAIEmbeddingProvider
```

### query parser 很保守

当前 `infer_filters()` 只能处理少量情况。

例如：

- `under 16000`
- 车型别名
- `suv` / `hatchback` / `sedan`

后续可以改进，但不要太早做复杂 NLP。先让 eval runner 暴露真实缺口。

### `/retrieve` 不是最终推荐 API

`/retrieve` 只返回候选 listing 和 evidence。

未来 `/recommend` 才应该负责：

- ranking。
- risk scoring。
- LLM generation。
- citations。
- stable JSON output。

### request logs 还很基础

当前 `request_logs` 记录：

- endpoint
- query
- filters
- listing_count
- knowledge_count

后续可以增加：

- retrieved chunk ids。
- latency by stage。
- model name。
- token usage。
- error details。

## 10. 你现在应该能解释的内容

如果你要把这个项目讲给面试官，当前可以这样说：

```text
I am building a used-car decision support system rather than a generic chatbot.
The current backend uses FastAPI, PostgreSQL, SQLAlchemy, and pgvector.
Seed listings and model knowledge are normalized into canonical JSONL files,
loaded into Postgres, chunked, embedded with a deterministic local embedding
provider, and retrieved through a hybrid `/retrieve` endpoint.

The current retrieval combines structured filters such as budget, location,
body type, and model with semantic chunk retrieval over pgvector. The local
embedding provider is a development scaffold so the vector pipeline can be
tested without external API keys. The next step is a retrieval eval runner
using fixed eval cases before adding citation-grounded recommendation
generation.
```

中文版本：

```text
这个项目不是普通聊天机器人，而是一个二手车决策支持系统。
当前后端使用 FastAPI、PostgreSQL、SQLAlchemy 和 pgvector。
项目把 listing 和车型知识整理成 seed data，导入数据库后生成 document chunks，
再用本地 deterministic embedding 写入 pgvector。`/retrieve` 接口现在同时支持
结构化筛选和 semantic chunk retrieval。

当前 embedding provider 只是开发阶段 scaffold，用来在没有外部 API key 的情况下
跑通向量检索链路。下一步会用 eval cases 做 retrieval eval runner，然后再实现
带 citation 的 recommendation JSON。
```

## 11. 下一步任务建议

优先级从高到低：

1. 新增 retrieval eval runner。
2. 把 eval summary 输出到 markdown 或 JSON。
3. 给 `/retrieve` 增加更明确的 retrieved chunk ids debug。
4. 设计 `/recommend` response schema。
5. 实现 deterministic recommendation baseline，不先接 LLM。
6. 再抽象外部 embedding / LLM provider。
7. 最后开始前端 decision workbench。

当前最推荐下一步：

```text
Build a small retrieval eval runner before adding LLM generation.
```

原因很直接：如果 retrieval 质量没有固定评估，后面 LLM 生成出来的推荐会很难判断是检索问题、prompt 问题，还是模型问题。
