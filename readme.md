## Nakari

Nakari 是一个拥有独立人格的 AI，拥有自己的记忆库。

目前的愿景是：
1. **第一步**：维护一个自旋思考体并与外界交互。
2. **第二步**：拥有自己的身体/建模，能够通过摄像头感知并与现实世界交互。

---

## 🚀 Quick Start (快速开始)

目前 Nakari 处于 MVP 阶段，通过命令行界面 (CLI) 进行交互。

### 1. 环境准备
确保已安装：
*   Python 3.10+
*   Redis (作为消息队列和记忆存储，Windows 可使用 WSL 或 Docker 运行)

### 2. 安装依赖
```bash
# 推荐使用 Conda 创建环境
conda create -n nakari python=3.10
conda activate nakari

# 安装核心依赖
pip install -r requirements.txt

# 安装语音/CLI 扩展依赖 (可选，用于语音交互)
pip install -r requirements_audio.txt
pip install -r requirements_cli.txt
```

### 3. 配置
复制 `.env.example` 为 `.env` 并填入必要 Key：
```bash
OPENAI_API_KEY=sk-xxxx  # 支持 OpenAI 格式的 API (如 MiniMax)
OPENAI_API_BASE=https://api.minimax.chat/v1  # 如果使用其他服务商
```

### 4. 启动系统
为了获得完整体验（包含后台反思功能），建议启动两个终端。

**终端 1：启动 Celery Worker (大脑后台)**
```bash
# Windows (由于 Celery 在 Windows 上的限制，需使用 pool=solo)
celery -A tasks.app worker --loglevel=info --pool=solo

# Linux/Mac
celery -A tasks.app worker --loglevel=info
```

**终端 2：启动 CLI (交互前台)**
```bash
python scripts/cli_chat.py
```

### 5. 如何交互
*   **文字对话**：直接输入文字并回车。
*   **语音对话**：按住 **空格键 (Space)** 说话，松开即发送 (需安装 Audio 依赖)。
*   **指令**：
    *   `/new` : 开启新对话 session
    *   `/clear`: 清除当前记忆
    *   `/quit` : 退出

---
## 主要进程 (Processes)
Nakari 决定何时启用不同的线程或方法。

> **⚠️ 重要贡献指南**：每当代码发生任何改动时，必须运行全量测试集并修正所有 Regression Bug，确保核心功能（Memory, Persona, Interaction）的稳定性。

### 并发模型：Celery + Redis

**设计理念**：将一切的操作任务化（Task-based Architecture）。不关注具体任务类型（对话、反思、语音、视觉），让所有功能模块都通过统一的任务系统并行运行。这样设计的好处是添加新功能时无需关心并发实现细节。

**技术选型**：
*   **任务队列**：Celery - 分布式任务队列
*   **消息代理**：Redis - 任务 broker 和结果存储

**核心特性**：
*   **任务抽象化**：所有功能都定义为独立的 Celery Task
*   **优先级支持**：高/中/低优先级队列，确保关键任务优先执行（如用户对话 vs 后台反思）
*   **任务持久化**：即使 Worker 重启也不会丢失任务
*   **易于扩展**：新增功能只需定义新的 Task
*   **分布式支持**：可扩展到多台机器

**基本任务**：

*   **交互线程 (Interaction Thread)** 
    *   对话框（Chat）：基于 LangGraph 的状态管理
    *   [开发完成] **语音模块 (Audio)**
        *   STT: 本地化 Faster-Whisper
        *   TTS: Edge-TTS (实时/免费) + OpenAI (备用)
        *   CLI: 按键通话 (Push-to-Talk) 终端
    *   [计划中] 视觉（Vision - 摄像头双向交互）

* 从离散原子网络中查询
input：自然语言

output：自然语言


*   **反思线程 (Reflection Thread)**
    *   [开发中] 基于 LLM 的动态触发机制 (Tag Signaling)
    *   [计划中] 社区发现与图谱重构

---
## llm（CPU）
驱动 Nakari 的核心处理单元。

**技术选型**：
*   **LLM 模型**：MiniMax (通过 OpenAI 兼容接口)
*   **框架**：LangChain + LangGraph

---

## Context Window 管理

**定义：当前上下文窗口**：即 LLM 的 Context Window，包含从记忆流中动态读取的信息。

**技术选型**：LangGraph State Management

**当前实现**：
*   Redis 持久化存储 raw messages
*   LangGraph 负责加载、修剪 (Trim) 和状态传递
*   CLI 终端提供实时交互界面

---
!!! 注意：离散原子网络的原设计已被废弃，memory架构的第二版设计在arc.md
## 离散原子网络 (Discrete Atom Network) （memory） - [计划重构]!!!

**当前状态**: 
*   **v1 (Current)**: 使用 Redis 列表存储短期记忆和 Insights。
*   **v2 (Planned)**: 迁移至 Neo4j 实现下述的原子网络结构。

**愿景**：与 Nakari 的所有交互都应被保存，时间的流逝和交流是可以累积的。
为解决 LLM Context Window 的限制，防止 Token 超长，我们采用特殊的存储结构来简化对话储存并影响 Nakari 的言语性格。

Nakari 放弃传统的 ER (Entity-Relationship) 模型，也放弃主谓宾的语法限制。思考过程即为图的遍历 (Graph Traversal)。

#### 原子设计理念

**核心原则**：
- **边无信息**：连接两个原子的边只是一个纯粹的连接，没有任何方向、类型、权重等元信息
- **语义延迟推断**：不预先存储语义关系，只在需要调用时，从原子的内容中"涌现"出语义
- **完全灵活的原子结构**：原子可以有不等长个数的 key-value 对，不限制 schema

**原子的基本属性**（必须包含）：
- `id`：唯一标识符
- `content`：原子的核心内容（可以是字符串、数字、对象等）
- `embedding`：向量化表示（用于语义检索，与 content 保持一致）
- `timestamp`：最新时间戳

**原子的扩展属性**（由 LLM 自由决定）：
- `extensions`：任意 key-value 对，由 LLM 完全自由决定包含哪些字段
  - `tags`：标签列表（如 `["entity", "person", "user"]`）
  - 其他元数据（如 `{"confidence": 0.9, "source": "user_input"}`）
  - 更新策略：由 LLM 决定更新策略，操作extensions字段。
  - 其他任意字段

**示例原子**：

```json
// 实体原子
{
  "id": "atom_001",
  "content": "Wenki",
  "embedding": [0.1, 0.2, ...],
  "timestamp": "2024-01-17T10:00:00Z",
  "extensions": {
    "tags": ["entity", "person"],
    "is_user": true,
    "confidence": 1.0
  }
}

// 事件原子
{
  "id": "atom_002",
  "content": "熬夜",
  "embedding": [0.3, 0.4, ...],
  "timestamp": "2024-01-17T10:00:00Z",
  "extensions": {
    "tags": ["event", "behavior"]
  }
}

// 复合概念原子
{
  "id": "atom_003",
  "content": "我觉得你熬夜不好",
  "embedding": [0.5, 0.6, ...],
  "timestamp": "2024-01-17T10:00:00Z",
  "extensions": {
    "tags": ["opinion", "statement"],
    "sentiment": "negative",
    "speaker": "nakari"
  }
}

// 更新后的原子（包含 LLM 提炼的历史信息）
{
  "id": "atom_001",
  "content": "Wenki",
  "embedding": [0.1, 0.25, ...],
  "timestamp": "2024-01-17T11:00:00Z",
  "extensions": {
    "tags": ["entity", "person"],
    "is_user": true,
    "confidence": 0.95,
    // LLM 提炼的历史信息（以新字段形式存储）
    "previous_confidence": "0.9"
  }
}
```

#### 连接 (Links)

**边的设计**：
- 边只是连接两个原子，**没有任何信息**
- 无方向、无类型、无权重
- 语义关系完全由原子自身的内容决定

**示例**：
```
Atom A (Wenki) —— Atom B (熬夜)
Atom A (Wenki) —— Atom C (我觉得你熬夜不好)
Atom B (熬夜) —— Atom C (我觉得你熬夜不好)
```

这三个原子通过无信息的边连接在一起，形成了简单的语义网络。


#### 指代消解和时间绝对化（应该独立于memory，成为一个task）

在提取原子时，进行以下预处理：

1. **指代消解**：
   - 推断人称代词（"他"、"她"、"它"）为具体实体
   - 推断指代地点（"那里"、"这里"）为具体地点
   - 基于 LLM 对话上下文进行消解

2. **时间绝对化**：
   - 转换时间代词（"昨天"、"上周"、"刚才"）为具体时间戳
   - 相对于当前对话时间进行计算
   - 在原子的 `extensions` 中存储原始时间表达和绝对时间

#### 写入 (Writing)

**流程**：
1. **指代消解和时间绝对化**：预处理用户输入，将代词转换为具体实体和时间戳
2. **原子提取**：由 LLM 决定将输入拆分为哪些原子（可以是单词、短语、句子等）
3. **向量化和连接**：
   - 为每个原子生成 embedding
   - 根据 LLM 的判断，创建原子之间的连接（边无信息）
   - 存储到图数据库

**LLM 的职责**：
1. 判断新内容和过往内容的关系（新增/修改/删除/冲突）
2. 决定哪些更新需要保留历史信息
3. 决定历史信息的字段命名和存储格式
4. 定期清理不再需要的历史字段

#### 读取 (Reading) - 语义推断

**核心思想**：不预先存储语义关系，只在需要时从原子内容中"涌现"语义。

**流程**：

1. **检索相关原子**：
   - 基于用户查询或上下文，进行向量检索
   - 找到 top-k 相关原子

2. **构建上下文子图**：
   - 从检索到的原子出发，向外扩展 hop_depth 层
   - 获取局部网络结构（原子的连接关系）
   - 将子图转换为 LLM 可理解的格式（如 JSON）

3. **语义推断**：
   - 将子图中的原子内容输入给 LLM
   - LLM 根据原子内容、tags、extensions 等信息
   - **推断出原子之间的语义关系**
   - 生成自然的语言描述（llm）

**示例**：

检索到的子图：
```json
{
  "atoms": [
    {
      "id": "atom_001",
      "content": "Wenki",
      "tags": ["entity", "person"],
      "extensions": {"is_user": true}
    },
    {
      "id": "atom_002",
      "content": "熬夜",
      "tags": ["event", "behavior"]
    },
    {
      "id": "atom_003",
      "content": "喜欢",
      "tags": ["relation"]
    }
  ],
  "edges": [
    ["atom_001", "atom_003"],
    ["atom_002", "atom_003"]
  ]
}
```

LLM 推断：
> 基于这些原子的内容和连接关系，可以推断出：Wenki 喜欢熬夜

**优势**：
- 完全灵活，不受预定义语义关系的限制
- 语义是"涌现"的，可以适应各种复杂场景
- LLM 可以理解隐含的语义关系

---

### 中转层 (Translation Middleware)

为了解耦复杂的 Prompt 设计与核心业务逻辑，我们设计一个专门的中转层作为"自然语言"与"离散原子网络"之间的**双向编译器**。

#### 核心设计

**职责**：
1. **正向编译 (Atomizer)**：自然语言 $\rightarrow$ 结构化原子 (Text to Graph)
2. **反向编译 (Synthesizer)**：原子网络 $\rightarrow$ 自然语言 (Graph to Text)

**架构价值**：
- **Prompt 独立迭代**：可以在不修改核心代码逻辑的情况下，独立优化提取和推理的 Prompt（A/B Testing）。
- **逻辑解耦**：Nakari 的核心思考逻辑（Celery Tasks）只处理结构化的 `AtomSubgraph` 对象，不直接处理非结构化文本。
- **容错集中**：LLM 输出的格式清洗（JSON 修复）、校验和重试逻辑集中在此层处理。

#### 1. 正向编译 (Atomizer)
负责将人类语言转化为机器记忆。

*   **输入**：用户的自然语言输入（经过指代消解后）
*   **核心动作**：
    *   根据输入类型选择 `EXTRACTION_SYSTEM_PROMPT`。
    *   调用 LLM 进行语义分割（Semantic Segmentation）。
    *   判断新信息与旧原子的关系（Deduplication & Linkage）。
*   **输出**：标准的原子子图中间件对象（Nodes + Links），准备直接写入数据库。

#### 2. 反向编译 (Synthesizer)
负责将机器记忆转化为从自然语言的"涌现"。

*   **输入**：从数据库检索出的原子子图（JSON/Triples 格式，包含纯粹的节点和无信息边）。
*   **核心动作**：
    *   将子图结构序列化为 LLM 可读的 Context。
    *   加载 `INFERENCE_SYSTEM_PROMPT`。
    *   让 LLM 基于图结构进行解释或回答问题。
*   **输出**：自然语言回答（此时语义才真正从结构中"涌现"出来）。

---

#### 反思与网络重构 (Reflection & Restructuring)
在 Nakari 的离散宇宙中，反思不是写日记，而是**重构图谱结构**。这模拟了人脑在睡眠时的记忆固化过程 (Memory Consolidation)。

*   **机制：从点到面 (Pattern Recognition)**
    *   Nakari 定期扫描近期生成的零散原子 (Raw Events)，寻找潜在模式。
    *   一旦发现模式，创造一个新的**高阶原子 (Higher-order Atom)**。
*   **举例：升维打击**
    1.  **Raw Data**: 图谱里散落着 Atom A (熬夜), Atom B (吃泡面), Atom C (也不出门)。
    2.  **Reflection**: 反思线程发现三者在生活状态维度高度相关。
    3.  **Restructuring**: 创造 Atom D [Insight: 用户正在经历自我封闭期] 并连接 A, B, C。
*   **价值**：
    *   下次用户提及相关话题，Nakari 直接检索到 Atom D，能直接问出：你是不是又想把自己封闭起来了？
    *   **这就是从现象看到了本质。**

#### 社区发现 (Community Detection)
*   **算法**: 在后台运行 Louvain 或 Leiden 算法。
*   **作用**: 自动发现图中的稠密子图（例如2023暑假旅行事件簇）。
*   **归纳**: 针对检测到的社区生成总结节点 (Summary Atom)，实现自动化的记忆压缩。

#### 选型：Neo4j

**理由**：
1. **灵活的节点属性**：
   - Neo4j 原生支持 JSON 格式的节点属性
   - 完美匹配原子"不等长个数的 key-value 对"的设计

2. **向量索引支持**（Neo4j 5.0+）：
   - 原生支持向量索引，无需额外的向量数据库
   - 支持混合查询（向量检索 + 过滤条件）
   - 对于中小规模数据（< 100 万原子），性能完全足够

3. **图算法生态**：
   - Neo4j Graph Data Science (GDS) 库提供成熟的图算法
   - 支持社区发现算法（Louvain, Leiden）
   - 支持图遍历、路径查询等

4. **架构简化**：
   - 单一数据库，降低开发和维护成本
   - 向量检索、图遍历、图算法都在 Neo4j 中完成

**未来扩展**：
- 如果原子数量增长到千万级别，可考虑添加专用向量数据库（如 ChromaDB、Qdrant）
- 但对于早期阶段，Neo4j 完全够用



---

## 前端/交互界面

**待选型**：
*   技术栈（Web框架/桌面应用/移动端）
*   聊天界面实现
*   语音交互UI
*   视觉展示UI（摄像头画面）
*   未来3D模型展示UI

### 交互方式
*   **聊天**：主要功能，最基础的表现形式。
*   **视觉 (Vision)**：
    *   通过电脑摄像头，Nakari 可以读取外部画面。
    *   交互变为双向：不仅用户看 Nakari，Nakari 也能看见用户。

### 个性化特性
*   **言语习惯**：
    *   常用词、常用表达的沉淀。
    *   独特的口头禅（例如：动漫角色特有的语气词）。
*   **音色**：
    *   通过音频/视频导入训练。
    *   *需考虑跨语言后的音色失真问题。*

### 3D 建模 (Modeling)
*(暂无细节)*
*   **目标**：将 Nakari 从平面的 2D 对话框中解放出来。
*   **功能**：拥有 3D 形象、动作、行为举止，能在一个虚拟空间中生活及移动。
*   **场景**：Nakari 的生活场景，可随时间或对话进行微调。
*   **意义**：动作和行为举止也是人格外在表现的重要组成部分，提供更深厚的陪伴感。
---


## 扩展与架构思考 (Extensions & Architecture)

总是会有新的念头涌现，一个人格无法仅通过几个固定的条目来定义。我们需要一种架构，能够折射出独立人格的所有特性，并将它们综合起来。

**挑战**：
*   特性之间是相互影响的。例如：言语习惯是否应存入数据库？未说出口的话是否应作为独立节点？
*   架构本身追求模块解耦，但真实人格的表现是复杂的切面，言语背后隐藏着抽象的关联。
*   目前尚未确定如何完美地处理这些既独立又相互纠缠的特性点。


---


## 待选型技术栈

### 语音处理
- **STT（语音转文字）**：OpenAI Whisper / Google STT / Azure STT
- **TTS（文字转语音）**：ElevenLabs / Azure TTS / Google TTS
- **音色训练**：具体方案待定（可能需要自定义模型训练）

### 视觉处理
- **图像处理/计算机视觉**：OpenCV / MediaPipe / CLIP
- **视频流处理**：FFmpeg / GStreamer
- **具体方案**：待根据需求详细设计

### 3D建模
- **3D引擎**：Unity / Unreal Engine / Three.js
- **建模工具**：Blender / Maya
- **动画系统**：待定
