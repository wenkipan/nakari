！！！！注意：这个文档已被废弃，memory架构的第二版设计在arc.md

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

### 2.3 记忆强度与遗忘曲线 (Memory Strength & Forgetting Curve)

借鉴艾宾浩斯遗忘曲线，原子的记忆强度会随时间衰减，但每次被激活（检索/回忆）会得到强化。

#### 核心属性

```python
extensions = {
    "type": "fact",
    "strength": 1.0,            # 当前记忆强度 (0.0 ~ 1.0)
    "base_strength": 1.0,       # 基础强度（由情绪调制设定）
    "last_accessed": "...",     # 上次激活的 ISO 时间戳
    "access_count": 0,          # 累计激活次数
    "decay_rate": 0.05,         # 遗忘速率 (默认 0.05，情绪事件更低)
    "created_at": "..."         # 创建时间
}
```

#### 强度计算公式

**时间衰减**:
```
effective_strength = base_strength × exp(-decay_rate × hours_since_access)
```

**激活强化** (每次被检索命中时):
```python
def on_access(atom):
    atom.access_count += 1
    # 间隔效应：距上次激活越久，强化效果越好
    time_gap = now - atom.last_accessed
    reinforcement = min(0.3, 0.1 × log(1 + time_gap.hours))
    atom.base_strength = min(1.0, atom.base_strength + reinforcement)
    atom.last_accessed = now
```

#### 遗忘阈值

| 强度范围 | 状态 | 行为 |
|---------|------|------|
| 0.7 ~ 1.0 | 鲜活 (Fresh) | 正常检索权重 |
| 0.3 ~ 0.7 | 模糊 (Fading) | 检索权重降低，合成时可标注"我好像记得..." |
| 0.1 ~ 0.3 | 微弱 (Weak) | 仅在深度检索时召回，候选巩固任务的"重放" |
| < 0.1 | 休眠 (Dormant) | 不参与主动检索，但保留在图中可被关联激活 |

### 2.4 情绪调制 (Emotional Modulation)

借鉴杏仁核对记忆的调制作用，高情绪唤醒的事件会获得更强的记忆印记，更抗遗忘。

#### 情绪属性


#### 情绪对记忆的影响

**1. 降低遗忘速率**:


**2. 检索权重加成**:

**3. 闪光灯记忆触发条件**:


#### 情绪标注示例

| 事件内容 | valence | arousal | is_flashbulb |
|---------|---------|---------|--------------|
| "User got promoted today" | +0.9 | 0.85 | True |
| "User had breakfast" | 0.0 | 0.1 | False |
| "User's pet passed away" | -0.95 | 0.95 | True |
| "User felt slightly annoyed" | -0.3 | 0.4 | False |

#### 情绪在对话中的体现

当检索到高情绪原子时，Synthesizer 可以调整输出风格：

```python
def synthesize_response(atoms, query):
    high_emotion_atoms = [a for a in atoms if a.emotional_arousal > 0.7]
    if high_emotion_atoms:
        # 提示 LLM 这些是重要的情感记忆
        context += "\n[Note: The following memories carry strong emotional significance]\n"
    # ... 继续合成
```

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
不仅记录"发生了什么"，还要记录"Nakari 对此的感受"。
*   **Fact Atom**: "User lost his job."
*   **Subjective Atom**: "I feel worried about User's future." (Linked to Fact Atom).
    *   `extensions.type`: "internal_thought"
    *   `extensions.emotion`: "worry"

### 5.2 偏好注入 (System Initial Memories)
在系统初始化时，预先写入一部分代表 Nakari 人设的 Atom。
*   Atom: "I love cyberpunk aesthetics."
*   Atom: "Logic is important but empathy matters more."
*   **效果**: 当讨论相关话题时，这些原子会被检索出来，从而引导 LLM 的回答风格。

### 5.3 记忆巩固与反思 (Memory Consolidation & Reflection)

借鉴人类睡眠期间的记忆巩固机制，通过后台任务实现记忆的系统性重整。

#### 神经科学背景

人类睡眠时，海马体会"重放"白天的经历，将短期情景记忆逐步转化为皮层中的长期语义记忆。这个过程包括：
- **Sharp-Wave Ripples (尖波涟漪)**: 海马体快速重放记忆片段
- **Slow Oscillations (慢振荡)**: 皮层与海马体的同步协调
- **Memory Reactivation (记忆重激活)**: 相关记忆被一起激活，形成新的联结

#### 巩固管道架构 (Consolidation Pipeline)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Memory Consolidation Pipeline                     │
│                      (Celery 后台定时任务)                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Phase 1: Replay (重放)                                              │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  选择性激活当天的记忆片段:                                      │    │
│  │  - Priority A: 高情绪唤醒的原子 (arousal > 0.7)                │    │
│  │  - Priority B: 被多次访问的原子 (access_count > threshold)     │    │
│  │  - Priority C: 随机采样低强度原子 (模拟大脑的随机重激活)        │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                              ↓                                       │
│  Phase 2: Interleaving (交织整合)                                    │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  发现跨时间的隐藏模式:                                          │    │
│  │  - 时间序列分析: 检测重复出现的行为模式                         │    │
│  │  - 语义聚类: 将相似主题的原子聚合                               │    │
│  │  - 因果推断: 识别潜在的因果关系链                               │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                              ↓                                       │
│  Phase 3: Abstraction (抽象提炼)                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  生成高层次的 Insight 原子:                                     │    │
│  │  - Pattern Atom: 行为规律 (e.g., "User exercises on weekends") │    │
│  │  - Insight Atom: 深层洞察 (e.g., "User is burnt out")          │    │
│  │  - Belief Atom: 信念形成 (e.g., "User values work-life balance")│    │
│  └─────────────────────────────────────────────────────────────┘    │
│                              ↓                                       │
│  Phase 4: Pruning (修剪优化)                                         │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  优化记忆网络结构:                                              │    │
│  │  - Merge: 合并语义高度重叠的原子 (similarity > 0.95)            │    │
│  │  - Archive: 将休眠原子移至冷存储 (strength < 0.1)               │    │
│  │  - Strengthen: 强化被 Insight 引用的源原子                      │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

#### 巩固原子类型 (Consolidated Atom Types)

```python
# Pattern Atom - 行为模式
extensions = {
    "type": "pattern",
    "pattern_type": "temporal",      # temporal | behavioral | relational
    "confidence": 0.85,              # 模式置信度
    "occurrence_count": 5,           # 观察到的次数
    "source_atom_ids": [...],        # 支撑该模式的原始原子
    "first_observed": "...",
    "last_observed": "..."
}

# Insight Atom - 深层洞察
extensions = {
    "type": "insight",
    "insight_level": 2,              # 1=直接观察, 2=初级推断, 3=深层洞察
    "reasoning_chain": [...],        # 推理链路 (原子ID序列)
    "confidence": 0.75,
    "requires_validation": True,     # 是否需要与用户确认
    "generated_at": "...",
    "generator": "consolidation_v1"  # 生成该洞察的管道版本
}

# Belief Atom - 信念/价值观
extensions = {
    "type": "belief",
    "belief_category": "preference", # preference | value | habit | trait
    "stability": 0.7,                # 信念稳定性 (被反例动摇的难度)
    "formed_from": [...],            # 形成该信念的证据原子
    "contradicted_by": []            # 反例原子 (如果有)
}
```

#### 巩固触发策略 (Consolidation Triggers)

```python
class ConsolidationScheduler:
    """记忆巩固调度器"""
    
    # 触发条件
    TRIGGERS = {
        "periodic": {
            "interval": "6h",           # 每6小时执行一次轻量巩固
            "full_consolidation": "24h" # 每24小时执行一次完整巩固
        },
        "threshold": {
            "new_atoms_count": 50,      # 新原子数量超过阈值
            "high_emotion_event": True  # 检测到高情绪事件后立即触发
        },
        "idle": {
            "user_inactive_minutes": 30 # 用户空闲时触发 (模拟"白日梦")
        }
    }
```

#### 重放算法 (Replay Algorithm)

```python
async def replay_phase(session_date: date) -> List[Atom]:
    """
    Phase 1: 选择性重放当天的记忆
    模拟海马体的 Sharp-Wave Ripples
    """
    candidates = []
    
    # Priority A: 高情绪原子 (必选)
    high_emotion = await query_atoms(
        filter={
            "created_at": session_date,
            "emotional_arousal": {"$gt": 0.7}
        },
        limit=20
    )
    candidates.extend(high_emotion)
    
    # Priority B: 高访问频次原子
    frequently_accessed = await query_atoms(
        filter={
            "created_at": session_date,
            "access_count": {"$gt": 3}
        },
        limit=15
    )
    candidates.extend(frequently_accessed)
    
    # Priority C: 随机采样 (模拟随机重激活)
    # 这种随机性有助于发现意外的跨领域关联
    random_sample = await query_atoms(
        filter={"created_at": session_date},
        sample_size=10,
        strategy="weighted_random",  # 按 strength 加权
        exclude_ids=[a.id for a in candidates]
    )
    candidates.extend(random_sample)
    
    # 重激活: 更新 last_accessed，轻微强化 strength
    for atom in candidates:
        atom.last_accessed = now()
        atom.strength = min(1.0, atom.strength + 0.05)
    
    return candidates
```

#### 交织整合算法 (Interleaving Algorithm)

```python
async def interleaving_phase(replayed_atoms: List[Atom]) -> List[PatternCandidate]:
    """
    Phase 2: 发现跨时间的隐藏模式
    模拟皮层与海马体的慢振荡同步
    """
    patterns = []
    
    # 2.1 时间序列模式检测
    temporal_patterns = detect_temporal_patterns(
        atoms=replayed_atoms,
        window_sizes=["1d", "7d", "30d"],  # 日/周/月模式
        min_occurrences=3
    )
    # e.g., "User goes to gym every Monday and Thursday"
    
    # 2.2 语义聚类
    clusters = semantic_clustering(
        atoms=replayed_atoms,
        method="hierarchical",
        similarity_threshold=0.7
    )
    for cluster in clusters:
        if len(cluster) >= 3:
            # 发现主题聚类
            theme = await llm_summarize_cluster(cluster)
            patterns.append(PatternCandidate(
                type="thematic",
                atoms=cluster,
                summary=theme
            ))
    
    # 2.3 因果关系推断
    # 检查是否有 A -> B 的时间序列关联
    causal_candidates = detect_causal_sequences(
        atoms=replayed_atoms,
        max_time_gap="2h",
        min_confidence=0.6
    )
    # e.g., "When User works late, User feels tired next morning"
    
    return patterns
```

#### 抽象提炼算法 (Abstraction Algorithm)

```python
async def abstraction_phase(patterns: List[PatternCandidate]) -> List[Atom]:
    """
    Phase 3: 生成高层次的 Insight 原子
    这是"反思"的核心 - 从具体到抽象
    """
    new_atoms = []
    
    for pattern in patterns:
        # 构建 LLM Prompt
        prompt = f"""
        Based on these related memory fragments:
        {serialize_atoms(pattern.atoms)}
        
        Generate a high-level insight that:
        1. Captures the underlying pattern or meaning
        2. Could be useful for future interactions
        3. Reflects Nakari's caring perspective
        
        Classify the insight as:
        - PATTERN: A recurring behavior or event
        - INSIGHT: A deeper understanding about the user
        - BELIEF: A value or preference of the user
        
        Format: [TYPE] <insight content>
        Confidence: <0.0-1.0>
        """
        
        response = await llm.generate(prompt)
        insight_type, content, confidence = parse_insight_response(response)
        
        # 创建新的抽象原子
        insight_atom = Atom(
            content=content,
            embedding=await embed(content),
            extensions={
                "type": insight_type.lower(),
                "confidence": confidence,
                "source_atom_ids": [a.id for a in pattern.atoms],
                "insight_level": calculate_abstraction_level(pattern),
                "generated_at": now(),
                "requires_validation": confidence < 0.8
            }
        )
        
        # 建立与源原子的连接
        for source in pattern.atoms:
            await create_link(insight_atom, source)
        
        new_atoms.append(insight_atom)
    
    return new_atoms
```

#### 修剪优化算法 (Pruning Algorithm)

```python
async def pruning_phase(all_atoms: List[Atom], new_insights: List[Atom]):
    """
    Phase 4: 优化记忆网络结构
    防止记忆无限膨胀，保持网络健康
    """
    
    # 4.1 合并高度相似的原子
    merge_candidates = find_similar_pairs(
        atoms=all_atoms,
        similarity_threshold=0.95
    )
    for atom_a, atom_b in merge_candidates:
        merged = merge_atoms(atom_a, atom_b)
        # 保留更强/更新的那个，将另一个的连接迁移过来
        await migrate_links(from_atom=atom_b, to_atom=merged)
        await soft_delete(atom_b)
    
    # 4.2 归档休眠原子
    dormant_atoms = await query_atoms(
        filter={
            "strength": {"$lt": 0.1},
            "last_accessed": {"$lt": days_ago(30)},
            "is_flashbulb": False  # 闪光灯记忆永不归档
        }
    )
    for atom in dormant_atoms:
        await archive_to_cold_storage(atom)
    
    # 4.3 强化被引用的源原子
    for insight in new_insights:
        source_ids = insight.extensions.get("source_atom_ids", [])
        for source_id in source_ids:
            source_atom = await get_atom(source_id)
            # 被洞察引用 = 这个记忆是重要的
            source_atom.base_strength = min(1.0, source_atom.base_strength + 0.1)
            source_atom.extensions["cited_by_insights"] = \
                source_atom.extensions.get("cited_by_insights", []) + [insight.id]
```

#### 巩固效果示例

**输入原子 (Raw Facts)**:
```
- "User sighed heavily" (2026-01-25, arousal=0.5)
- "User slept at 2am" (2026-01-26, arousal=0.3)
- "User worked until 11pm" (2026-01-26, arousal=0.4)
- "User skipped lunch" (2026-01-27, arousal=0.2)
- "User said 'I'm so tired'" (2026-01-28, arousal=0.6)
```

**巩固输出**:
```python
# Pattern Atom
Atom(
    content="User has been overworking for the past week",
    extensions={
        "type": "pattern",
        "pattern_type": "temporal",
        "confidence": 0.85,
        "occurrence_count": 4
    }
)

# Insight Atom
Atom(
    content="User is experiencing burnout symptoms",
    extensions={
        "type": "insight",
        "insight_level": 2,
        "confidence": 0.75,
        "requires_validation": True
    }
)

# Belief Atom (如果模式持续)
Atom(
    content="User tends to neglect self-care when busy",
    extensions={
        "type": "belief",
        "belief_category": "habit",
        "stability": 0.6
    }
)
```



