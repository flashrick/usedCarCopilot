# AI Engineer Portfolio Plan

## 目标

你的目标不是做一个“看起来像 AI”的 demo，而是做一个能让 HR 和技术面试官一眼看出你具备下面能力的项目：

- 真实的 RAG 设计与落地
- 向量数据库与混合检索
- 结构化数据和非结构化数据结合
- LLM 评估、监控、成本和可靠性意识
- 面向业务场景的产品思维

基于 `IT` list 里的项目点子，我建议你优先做这个：

## 最优项目

**AI Used Car Decision Copilot**

中文可以叫：**AI 二手车决策助手**

一句话介绍：

> 一个面向真实购车场景的 AI 决策系统，整合二手车 listings、车辆参数、用户偏好、车型口碑和养护知识，通过 RAG、向量检索和结构化规则，给出带引用依据的购车建议、风险提示和对比报告。

## 为什么它最适合你

这个项目来自你 `IT` list 里的 `AI 搜二手车`，但我建议把它升级成“决策助手”，而不是简单搜索工具。

它比其他点子更强，原因有这几个：

- 它天然适合 `RAG + vector DB + hybrid search`。你可以同时处理车型说明、用户评论、维修建议、市场价格趋势、卖家描述。
- 它有明确业务价值。HR 一看就能理解用户是谁、痛点是什么、为什么值得做。
- 它比纯聊天机器人更像 AI Engineer 项目。因为它需要数据 ingestion、embedding、检索、rerank、structured filtering、evaluation、API、前端展示。
- 它容易做出“可展示”的结果。你可以展示搜索结果、引用片段、风险评分、价格对比、推荐理由。
- 它容易写成 LinkedIn 项目故事。可以强调“帮助用户降低买到高风险二手车的概率”，比“做了个 AI 工具”更有吸引力。

## 不作为主项目的点子

以下点子可以做第二项目，但不建议先做：

- `搜集需求的agent`
  原因：更偏 agent workflow，RAG 和向量数据库不是核心卖点。
- `演讲稿软件，跟随语音标记`
  原因：更像语音产品或前端交互项目，不够突出 AI retrieval 能力。
- `小说生成工具`
  原因：太像普通生成类 demo，难体现 grounding、评估、生产化思维。
- `取名网`
  原因：有趣但业务复杂度和技术深度不够，难打动 AI Engineer 招聘方。

## 你要向 HR 展示的能力

项目做完后，你的对外叙事应该围绕这几个关键词：

- `Python`
- `FastAPI`
- `RAG`
- `Vector Database`
- `Hybrid Search`
- `Embeddings`
- `LLM Evaluation`
- `Citation / Grounded Answers`
- `Prompt Engineering`
- `Observability`
- `Production-minded AI systems`

## 最小成品标准

如果你想把它放到 LinkedIn 和 GitHub，至少要做到：

- 用户能输入购车需求
- 系统能检索 listings + 车型知识 + 评论片段
- 系统能输出推荐结果，不是只返回聊天文字
- 每条结论都带证据引用
- 有风险提示，如高里程、事故风险、维护成本偏高
- 有可解释的评分维度
- 有 README、架构图、短 demo 视频

## 交付文件

- [used-car-rag-build-guide.md](/home/rick/workspace/my-learning-life/AI%20Engineer/used-car-rag-build-guide.md)
- [linkedin-hr-pack.md](/home/rick/workspace/my-learning-life/AI%20Engineer/linkedin-hr-pack.md)
