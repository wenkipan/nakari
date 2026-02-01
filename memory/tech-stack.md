# DAN Memory 技术选型

## 运行形态

| 项目 | 选择 | 说明 |
|------|------|------|
| 形态 | Python 库 | 可扩展为独立服务 |
| Python | >=3.10 | 平衡新特性与兼容性 |

## 存储

| 项目 | 选择 | 说明 |
|------|------|------|
| 数据库 | Neo4j | 图为核心数据模型 |
| 向量索引 | Neo4j 内置 | 5.11+ 原生支持 |

**选择理由**：
- 原生支持边遍历，无需多次 JOIN
- 支持 PageRank、社区发现等图算法（反思模块扩展）
- 单一数据库，架构简单
- 避免后续架构迁移

## Embedding

| 项目 | 选择 |
|------|------|
| 策略 | 可配置，支持多种提供者 |
| 提供者 | openai / sentence-transformers / custom |

## 依赖

```
# Core
neo4j           # Neo4j Python 驱动
pydantic        # 数据验证

# Embedding (可选)
openai                   # OpenAI API
sentence-transformers    # 本地模型

# Dev
pytest
mypy
```

## 架构图

```
┌─────────────────────────────────────────┐
│              DAN Memory                 │
├─────────────────────────────────────────┤
│  Interfaces (create_atom, retrieve...)  │
├─────────────────────────────────────────┤
│  Core Logic (on_access, scoring...)     │
├──────────────────┬──────────────────────┤
│  Embedding       │  Storage             │
│  (pluggable)     │  (Neo4j)             │
│  - OpenAI        │  - Atoms as Nodes    │
│  - Local         │  - Links as Edges    │
│  - Custom        │  - Vector Index      │
└──────────────────┴──────────────────────┘
```
