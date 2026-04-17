# LinkedIn And HR Pack

## 1. LinkedIn 项目标题

优先用这种风格，不要只写“AI 项目”：

- `Built an AI Used Car Decision Copilot with RAG, Vector Search, and Grounded Recommendations`
- `Designed a production-minded RAG system for used car decision support`
- `Built a citation-based AI recommendation system using FastAPI, pgvector, and LLMs`

## 2. LinkedIn 项目简介

你可以直接用这版英文：

> Built an AI decision support system for used car buyers that combines structured vehicle listings with unstructured reviews, maintenance knowledge, and buying guides. The system uses embeddings, vector search, hybrid retrieval, and citation-based generation to recommend vehicles, explain trade-offs, and highlight risk factors. I also added evaluation workflows, logging, and deployment to make it closer to a production-ready AI engineering project rather than a simple chatbot demo.

## 3. Resume Bullet

可以直接放简历：

- Built an AI decision support application for used car selection using Python, FastAPI, pgvector, and LLM APIs; implemented document ingestion, embeddings, hybrid retrieval, citation-grounded recommendations, and evaluation workflows for answer quality and retrieval relevance.

- Designed a RAG pipeline combining structured listing filters and unstructured knowledge retrieval to generate explainable recommendations, risk flags, and comparison reports for end users.

## 4. GitHub README 必须写清楚的内容

- Problem
- Why this matters
- System architecture
- Data pipeline
- Retrieval strategy
- Evaluation approach
- Screenshots
- Demo video
- Tech stack
- Limitations
- Future improvements

## 5. Demo 视频脚本

2 到 3 分钟就够。

### 第一段

介绍问题：

> Buying a used car is a high-risk decision because listings are incomplete, reviews are scattered, and buyers often lack the technical knowledge to compare options confidently.

### 第二段

介绍方案：

> I built an AI decision copilot that combines structured listing data with review snippets, maintenance knowledge, and buying guides through a RAG pipeline.

### 第三段

展示页面：

- 输入需求
- 返回推荐
- 展示引用
- 展示风险标签
- 展示对比页

### 第四段

强调工程能力：

> Beyond generation, I focused on retrieval quality, explainability, evaluation, and deployment, because those are the parts that make an AI system usable in real scenarios.

## 6. HR 最容易被吸引的关键词

你在 LinkedIn、README、简历里可以反复出现这些词，但要和真实实现对应：

- `RAG`
- `Vector Database`
- `pgvector`
- `Embeddings`
- `Hybrid Retrieval`
- `FastAPI`
- `Evaluation`
- `Grounded Answers`
- `Citations`
- `Decision Support`
- `Production-ready`
- `Observability`

## 7. 不要这样包装

不要写：

- `Built a chatbot`
- `Built an AI app`
- `Used OpenAI API to answer questions`
- `Created a car recommendation project`

这些说法太弱，不能体现你的 AI engineering 深度。

## 8. 更强的包装方式

你要强调：

- 你处理了真实数据问题
- 你设计了 retrieval 流程
- 你做了 grounded generation
- 你做了 evaluation
- 你考虑了 latency、cost、logs、deployment

## 9. 发布 LinkedIn 时的正文模板

```text
I recently built an AI decision support project for used car buyers.

Instead of building a generic chatbot, I wanted to work on an AI system that solves a real decision-making problem. The project combines structured car listing data with unstructured reviews, maintenance knowledge, and buying guides.

Tech stack:
- Python + FastAPI
- pgvector / vector search
- LLM APIs
- Hybrid retrieval
- Citation-based generation
- Evaluation workflow

The system can recommend vehicles, explain trade-offs, surface risk flags, and show evidence behind each recommendation.

This project helped me practice what I believe matters most in AI engineering: retrieval quality, grounding, evaluation, and production-minded system design.

If you're working on AI products involving RAG, retrieval systems, or LLM applications, I’d be happy to connect.
```

## 10. 项目完成标准

在你发 LinkedIn 之前，至少确认下面都齐了：

- GitHub 仓库公开可见
- README 完整
- 有架构图
- 有 demo 视频
- 有部署链接
- 有 3 张以上截图
- 有 evaluation 说明
- 有 limitations 和 next steps
