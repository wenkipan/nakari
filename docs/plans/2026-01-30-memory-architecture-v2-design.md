# 离散原子网络 (DAN) 架构设计 v2

## 概述

本文档记录了 Nakari 记忆系统的重新设计，核心目标是：
- 简化 Schema，减少冗余字段
- 统一更新规则，用一套机制处理所有场景
- 分离「当前状态」与「长期人格」
- 支持人格的长期演化

---

## 1. 数据结构 (Schema)

### 1.1 节点 (Atom)

```python
class Atom:
    content: str                                    # 核心内容（唯一标识）
    embedding: List[float]                          # 向量表示
    type: Literal["fact", "concept", "emotion"]     # 原子类型
    strength: float                                 # 0.0 ~ 1.0，当前强度
    timestamp: datetime                             # 上次激活时间
    extensions: Dict[str, Any]                      # 可选扩展字段
```

### 1.2 边 (Link)

```python
class Link:
    weight: float       # 0.0 ~ 1.0，连接强度
    timestamp: datetime # 上次激活时间
```

### 1.3 三种原子类型

| 类型 | 角色 | Content 示例 | 说明 |
|------|------|-------------|------|
| **Fact** | 具体情景 | "Wenki在熬夜" | 事件/陈述，包含完整语义 |
| **Concept** | 语义锚点 | "Wenki", "熬夜" | 抽象实体/概念，用于索引 |
| **Emotion** | 情绪节点 | "happy", "sad" | 情绪标签，strength 表示当前激活程度 |

### 1.4 边的连接类型

| 连接 | 语义 |
|------|------|
| Fact ↔ Concept | 概念参与了该事实 |
| Fact ↔ Fact | 时间/逻辑关联（因果、连续发生） |
| Emotion ↔ Fact | 对该事实的情绪 |
| Emotion ↔ Concept | 对该概念的情绪倾向 |

---

## 2. 核心规则：激活增强 + 时间衰减

所有更新场景统一为一套规则：

```python
def on_access(obj, decay_rate: float, boost: float):
    """
    节点或边被访问时的统一处理
    
    Args:
        obj: Atom 或 Link 对象
        decay_rate: 衰减速率（不同类型不同）
        boost: 激活增益
    """
    hours = (now() - obj.timestamp).total_seconds() / 3600
    
    # 1. 计算衰减后的真实值
    current_value = obj.strength if isinstance(obj, Atom) else obj.weight
    decayed = current_value * exp(-decay_rate * hours)
    
    # 2. 加上激活增益
    new_value = min(1.0, decayed + boost)
    
    # 3. 写回
    if isinstance(obj, Atom):
        obj.strength = new_value
    else:
        obj.weight = new_value
    obj.timestamp = now()
```

### 2.1 衰减速率参考值

| 对象 | decay_rate | 说明 |
|------|-----------|------|
| Fact.strength | 0.01 | 记忆会淡忘 |
| Concept.strength | 0.005 | 概念相对稳定 |
| Emotion.strength | 0.05 | 情绪波动快（当前状态） |
| 普通边.weight | 0.005 | 关联关系稳定 |
| 情绪边.weight | 0.001 | 人格演化缓慢 |

> 注：具体数值需要通过实验调优

---

## 3. 检索流程

### 3.1 并行检索

同时执行多路检索：

| 检索路径 | 方法 | 目标 |
|---------|------|------|
| 语义检索 | Query embedding → 向量相似度 | 找语义相关的 Fact/Concept |
| 情绪检索 | Query 情绪分析 → 匹配 Emotion 原子 | 找相关情绪 |
| 关键词检索 | 提取实体 → 精确匹配 Concept | 找明确提及的概念 |

### 3.2 边扩散

从 Phase 1 命中的原子出发，沿边扩散 1-2 跳，收集关联原子

### 3.3 统一排序

```python
def score(atom, query_embedding, weights, current_time):
    """
    计算候选原子的最终得分
    
    weights: {
        w1: 语义相似度权重,
        w2: 节点强度权重,
        w3: 边权重权重,
        w4: 情绪关联权重,
        w5: 时间因子权重,
        decay_rate: 时间衰减速率
    }
    """
    # 各因素计算
    semantic_sim = cosine_similarity(query_embedding, atom.embedding)
    
    # 节点强度（懒惰计算衰减）
    hours = (current_time - atom.timestamp).total_seconds() / 3600
    node_strength = atom.strength * exp(-get_decay_rate(atom.type) * hours)
    
    # 边权重（如果通过边扩散到达）
    edge_weight = get_edge_weight(atom) or 1.0
    
    # 情绪关联强度 = 连接的情绪原子 strength × 边 weight 的最大值
    emotion_boost = get_emotion_boost(atom)
    
    # 时间因子
    time_factor = exp(-weights.decay_rate * hours)
    
    # 加权求和
    final_score = (
        weights.w1 * semantic_sim +
        weights.w2 * node_strength +
        weights.w3 * edge_weight +
        weights.w4 * emotion_boost +
        weights.w5 * time_factor
    )
    
    return final_score
```

### 3.4 返回 Top-K

按 final_score 降序排列，返回前 K 个原子

---

## 4. 更新流程

检索完成后，对最终返回的 Top-K 原子执行更新：

```python
def on_retrieval_complete(top_k_atoms: List[Atom]):
    """检索完成后的更新"""
    
    # 1. 更新被检索到的节点
    for atom in top_k_atoms:
        on_access(atom, 
                  decay_rate=get_decay_rate(atom.type),
                  boost=get_boost_rate(atom.type))
    
    # 2. Hebbian 学习：Top-K 内两两之间的边增强
    for atom_a, atom_b in combinations(top_k_atoms, 2):
        link = get_or_create_link(atom_a, atom_b)
        # 情绪边用更低的衰减率
        is_emotion_link = (atom_a.type == "emotion" or atom_b.type == "emotion")
        decay = EMOTION_LINK_DECAY if is_emotion_link else NORMAL_LINK_DECAY
        on_access(link, decay_rate=decay, boost=EDGE_BOOST)
```

---

## 5. 状态 vs 人格

### 5.1 分离设计

| 概念 | 存储位置 | 衰减速率 | 说明 |
|------|---------|---------|------|
| 当前情绪状态 | Emotion.strength | 高 | 快速波动，会平复 |
| 长期情绪倾向（人格） | 情绪边.weight | 很低 | 缓慢演化 |

### 5.2 示例

```
[happy].strength = 0.3  (当前：情绪平静)

[happy] --weight=0.8-- [和朋友聊天]  (人格：聊天让我开心)
[happy] --weight=0.6-- [写代码]      (人格：写代码也挺愉快)
[happy] --weight=0.2-- [加班]        (人格：加班不太开心)
```

### 5.3 人格演化

- 持续的美好经历 → happy 与正面 Fact 的边权重逐渐增强
- 边权重衰减很慢 → 人格改变是渐进的
- 这自然实现了「积极经历塑造乐观人格」

---

## 6. 人格初始化 (Personality Initialization)

### 6.1 情绪原子

预设 12 种基础情绪原子：

```
happy, sad, anger, fear, surprise, disgust,
love, trust, anticipation, curiosity, calm, anxiety
```

**初始 strength**：在 `[0.3, 0.7]` 范围内均匀随机分布，体现个体差异。

### 6.2 偏好注入

通过 YAML 配置文件 (`memory/persona.yaml`) 注入初始人格：

```yaml
emotions:
  init_range: [0.3, 0.7]
  types: [happy, sad, anger, ...]

preferences:
  # 概念偏好
  concepts:
    - content: "cyberpunk"
      emotions:
        love: 0.8
        curiosity: 0.6
  
  # 人设陈述
  facts:
    - content: "I enjoy deep conversations"
      emotions:
        happy: 0.8
        curiosity: 0.7
```

### 6.3 初始化流程

```python
def init_personality(config_path: str):
    config = load_yaml(config_path)
    
    # 1. 创建情绪原子（随机 strength）
    for emotion_type in config["emotions"]["types"]:
        init_strength = random.uniform(*config["emotions"]["init_range"])
        create_atom(content=emotion_type, type="emotion", strength=init_strength)
    
    # 2. 创建偏好概念 + 情绪边
    for concept in config.get("preferences", {}).get("concepts", []):
        atom = create_atom(content=concept["content"], type="concept")
        for emotion, weight in concept["emotions"].items():
            create_link(atom, get_emotion(emotion), weight=weight)
    
    # 3. 创建人设陈述 + 情绪边
    for fact in config.get("preferences", {}).get("facts", []):
        atom = create_atom(content=fact["content"], type="fact")
        for emotion, weight in fact["emotions"].items():
            create_link(atom, get_emotion(emotion), weight=weight)
```

---

## 7. 待设计

以下部分尚未详细讨论：

- [ ] **反思机制 (Memory Consolidation)**：如何创建新原子、发现模式
- [ ] **具体参数调优**：各类 decay_rate 和 boost 的最佳值

---

## 7. 与旧设计的对比

| 方面 | v1 (SPEC.md) | v2 (本设计) |
|------|-------------|------------|
| 边的信息 | 无信息（纯连接） | 有 weight + timestamp |
| 节点属性 | extensions 包含大量字段 | 精简，核心字段提到顶层 |
| 情绪处理 | 存在节点 extensions 中 | 独立的 Emotion 原子类型 |
| 遗忘机制 | 复杂的多阶段衰减 | 统一的「激活+衰减」公式 |
| 人格演化 | 通过巩固管道 | 通过情绪边的缓慢权重变化 |
| 更新时机 | 检索 + 反思 | 检索时实时更新（写回） |
