# Discrete Atom Network (DAN) Architecture & Specification

## 1. 核心理念 (Core Philosophy)

Nakari 的记忆不仅仅是存储，而是**认知**的基础。为了实现这一点，我们采用 **"Strong Nodes, Weak Edges" (强节点，弱边)** 的去中心化架构。

### 1.1 强节点 (Strong Nodes)
原子 (Atom) 是信息的绝对载体。所有的语义、情感、时间和元数据都封装在原子内部。
*   **Strong Content**: 每一个原子都必须包含具有独立语义的 `content`。
*   **Flexible Extensions**: 几乎所有非搜索关键的属性（如置信度、来源、上下文标记、情感极性）都存放在 `extensions` 字段中。这允许我们在不修改数据库结构的情况下，随意扩展原子的能力。

### 1.2 弱边 (Weak Edges)
连接仅仅代表“关联”。
*   边没有方向、没有类型（Label）、没有权重。
*   **语义涌现 (Emergence)**: 原子 A 和 原子 B 为什么连接？这种关系不在边上定义，而是在读取时，由 LLM 根据 A 和 B 的内容**现场推断**出来的。这避免了传统知识图普中刚性 Schema (如 `IS_A`, `KNOWS`) 导致的表达受限。

---

## 2. 数据结构 (Data Structures)

我们借鉴海马体（情景记忆）与皮层（语义记忆）的交互机制，采用双层架构。

### 2.1 两种类型的原子 (Atom Types)

虽然技术上它们都是 Node，但在逻辑上分为两类：

#### A. 概念原子 (Concept Atom) - "语义锚点"
代表抽象的实体、地点或概念。类似于大脑皮层中的概念神经元。
*   **Role**: 索引锚点，用于归纳和跨事件检索。
*   **Content**: 只有名词或短语。e.g., "Apple", "Home", "Work".
*   **Extensions**: `{ type: "concept" }`

#### B. 事实原子 (Fact Atom) - "具体情景"
代表一个具体的事件或陈述。类似于海马体中的情景印迹。解决了“绑定问题”——将多个概念在特定时间空间下绑定在一起。
*   **Role**: 信息的实际载体，包含完整语义。
*   **Content**: 完整陈述句。e.g., "There is a red apple on the kitchen table."
*   **Extensions**: `{ type: "fact", timestamp: "...", ... }`

### 2.2 连接策略 (Linking Strategy)

连接不再是随意的，而是遵循 **"参与 (Participation)"** 逻辑：

*   **Fact <-> Concept**: 表示该概念参与了这个事实。
    *   `Fact("Apple is on table")` --- link ---> `Concept("Apple")`
    *   `Fact("Apple is on table")` --- link ---> `Concept("Table")`
    *   **解决歧义**: 我们不使用 `(Apple)-[on]->(Table)` 这种容易产生歧义的三元组。关系逻辑封装在 Fact 的自然语言 Content 中，连接仅用于通过 Concept 检索到 Fact。

*   **Fact <-> Fact**: 表示时间或逻辑上的紧密关联（因果、连续发生）。

---

## 3. 转译层 (Translation Layer)

转译层是 "自然语言" 和 "离散原子" 之间的双向编译器。它包含两个核心管道。

### 3.1 写入管道 (Atomizer)
负责将用户的自然语言“粉碎”成原子并存入网络。

**流程**:
1.  **Input**: 原始用户 Input (e.g., "I went to the gym yesterday").
2.  **Context Grounding (指代与时间消解)**: 
    *   LLM 将 "I" 替换为 "User"， "yesterday" 替换为 "2023-10-01"。
    *   Result: "User went to the gym on 2023-10-01".
3.  **Atom Extraction (原子提取)**:
    *   LLM 将复合句拆解为原子单位。
    *   *Decision*: 是创建一个新 Atom，还是更新旧 Atom？
    *   Result: `Atom(content="User went to gym", extensions={time: "...", tags: ["activity"]})`
4.  **Vectorization**: 对 content 进行 Embedding。
5.  **Linking (关联建立)**:
    *   搜索图谱中相关的现有 Atom (如 "Gym", "Health", "User Habits").
    *   建立新 Atom 与这些旧 Atom 的弱连接。
6.  **Persistence**: 写入 Neo4j。

### 3.2 读取管道 (Synthesizer)
负责从图谱中提取信息，并“涌现”出自然语言回答。

**流程**:
1.  **Retrieve**: 执行检索策略 (见 Section 4)，获得一个 Subgraph (子图)。
2.  **Serialize**: 将原子和连接序列化为 LLM 可读的文本格式 (JSON 或 描述性列表)。
3.  **Inference (推理)**:
    *   System Prompt: "Based on these memory fragments and their connections..."
    *   LLM 观察连接的原子，推断它们之间的逻辑关系。
4.  **Output**: 生成最终回答。

---

## 4. 检索策略 (Retrieval Strategy)

我们不使用单一的搜索，而是使用 **混合检索 (Hybrid Search)**，结合双层架构实现类似人脑的联想回忆。

### 4.1 核心算法: 激活扩散 (Activation Spreading)

1.  **Dual Entry (双路入口)**:
    *   **Concept Entry**: 搜索 Query 如果包含明确实体 (e.g. "Apple"), 会命中 `Concept Atom`。
    *   **Fact Entry**: 搜索 Query 如果是具体描述 (e.g. "eating apple"), 会直接命中语义相似的 `Fact Atom`。
2.  **Spreading (扩散)**:
    *   从命中的 Concept 出发，扩散到所有连接的 Fact (上下文召回)。
    *   从命中的 Fact 出发，扩散到它涉及的其他 Concept，再由这些 Concept 发现相关的新 Fact (联想)。
    *   *Intersection (交集)*: 如果 Query 同时激活了 Concept A 和 Concept B，那么同时连接 A 和 B 的 Fact 将获得极高的相关性权重。

### 4.2 场景示例

#### 场景 A: 信息查询 ("我记得家里有些吃的东西？")
1.  **Query**: "food at home".
2.  **Vector Search**: 
    *   锚点 1: 命中 `Concept(Food)` (由词义相似性)。
    *   锚点 2: 命中 `Concept(Home)`。
3.  **Traversal**: 
    *   发现 `Fact("Red apple on the table at home")` 同时连接了 Home 相关的 Concept 和 Food 相关的 Concept (如 Apple)。
4.  **Result**: "我记得桌上有红苹果。"

#### 场景 B: 观点咨询 ("你觉得这件事怎么样?")
1.  **Query**: "Opinion on Event X".
2.  **Vector Search**: 命中 `Concept(Event X)`.
3.  **Traversal**: 
    *   检索连接到该 Concept 的所有 `Fact Atoms`.
    *   **关键**: 发现其中包含 **Subjective Fact (主观事实)** (e.g., Content="I felt sad when Event X happened", type="fact", tag="internal_thought").
4.  **Synthesis**: LLM 看到这些主观事实，生成："这件事让我感到很难过..."

---

## 5. 人格与自我 (Personality & Self-Model)

如何让 Nakari 拥有独立人格？答案不在代码里，而在 **记忆的数据分布** 里。

### 5.1 主观原子 (Subjective Atoms)
不仅记录“发生了什么”，还要记录“Nakari 对此的感受”。
*   **Fact Atom**: "User lost his job."
*   **Subjective Atom**: "I feel worried about User's future." (Linked to Fact Atom).
    *   `extensions.type`: "internal_thought"
    *   `extensions.emotion`: "worry"

### 5.2 偏好注入 (System Initial Memories)
在系统初始化时，预先写入一部分代表 Nakari 人设的 Atom。
*   Atom: "I love cyberpunk aesthetics."
*   Atom: "Logic is important but empathy matters more."
*   **效果**: 当讨论相关话题时，这些原子会被检索出来，从而引导 LLM 的回答风格。

### 5.3 反思 (Reflection)
通过后台任务，定期将碎片化的 Fact 转化为 High-Level 的 Insight。
*   Raw: "User sighed" + "User slept late" + "User worked OT".
*   Insight: "User is burnt out." (这是一个新的 Atom，连接到上述三个 Fact).
*   **人格体现**: 这个 Insight 包含了 Nakari 的关怀视角，当用户下次说 "Did you notice?" 时，Nakari 能调取这个 Insight 并回答 "Yes, I think you are burnt out."
