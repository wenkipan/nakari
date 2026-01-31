# Discrete Atom Network (DAN) Architecture & Specification v2

## 1. 核心理念 (Core Philosophy)

**设计原则**：
- 简化 Schema，减少冗余字段
- 统一更新规则：所有场景用「激活增强 + 时间衰减」
- 分离「当前状态」与「长期人格」
- 人格通过边权重的缓慢演化体现

---

## 2. 数据结构 (Schema)

### 2.1 节点 (Atom)

```python
class Atom:
    content: str                                    # 核心内容
    embedding: List[float]                          # 向量表示
    type: Literal["fact", "concept", "emotion"]     # 原子类型
    strength: float                                 # 0.0 ~ 1.0
    timestamp: datetime                             # 上次激活时间
    extensions: Dict[str, Any]                      # 可选扩展
```

### 2.2 边 (Link)

```python
class Link:
    weight: float       # 0.0 ~ 1.0
    timestamp: datetime # 上次激活时间
```

### 2.3 三种原子类型

| 类型 | 角色 | Content 示例 | 说明 |
|------|------|-------------|------|
| **Fact** | 具体情景 | "Wenki在熬夜" | 事件/陈述，包含完整语义。类似海马体中的情景印迹 |
| **Concept** | 语义锚点 | "Wenki", "熬夜" | 抽象实体/概念，用于索引。类似大脑皮层的概念神经元 |
| **Emotion** | 情绪节点 | "happy", "sad" | 类似杏仁核，strength 表示当前激活程度 |

**示例**：

```
Fact: "Wenki在熬夜"
  ├── Concept: "Wenki"
  ├── Concept: "熬夜"
  └── Emotion: "关心"
```

### 2.4 边的连接类型

| 连接 | 语义 |
|------|------|
| Fact ↔ Concept | 概念参与了该事实 |
| Fact ↔ Fact | 时间/逻辑关联（因果、连续发生） |
| Emotion ↔ Fact | 对该事实的情绪（当前反应） |
| Emotion ↔ Concept | 对该概念的情绪倾向（长期人格） |

**设计要点**：不使用 `(Apple)-[on]->(Table)` 三元组，关系语义封装在 Fact 的 content 中，边仅表示关联。

---

## 3. 核心规则：激活增强 + 时间衰减

所有更新场景统一为一套规则：

```python
def on_access(obj, decay_rate: float, boost: float):
    """节点或边被访问时的统一处理"""
    hours = (now() - obj.timestamp).total_seconds() / 3600
    
    # 1. 计算衰减后的真实值
    current = obj.strength if isinstance(obj, Atom) else obj.weight
    decayed = current * exp(-decay_rate * hours)
    
    # 2. 加上激活增益
    new_value = min(1.0, decayed + boost)
    
    # 3. 写回
    if isinstance(obj, Atom):
        obj.strength = new_value
    else:
        obj.weight = new_value
    obj.timestamp = now()
```

### 衰减速率参考

| 对象 | decay_rate | 说明 |
|------|-----------|------|
| Fact.strength | 0.01 | 记忆会淡忘 |
| Concept.strength | 0.005 | 概念相对稳定 |
| Emotion.strength | 0.05 | 情绪波动快（当前状态） |
| 普通边.weight | 0.005 | 关联关系稳定 |
| 情绪边.weight | 0.001 | 人格演化缓慢 |

> 具体数值需要通过实验调优

---

## 4. 检索策略 (Retrieval Strategy)

### 4.1 并行检索

| 检索路径 | 方法 | 目标 |
|---------|------|------|
| 语义检索 | Query embedding → 向量相似度 | 找语义相关的 Fact/Concept |
| 情绪检索 | Query 情绪分析 → 匹配 Emotion | 找相关情绪 |
| 关键词检索 | 提取实体 → 精确匹配 Concept | 找明确提及的概念 |

### 4.2 边扩散

从命中的原子出发，沿边扩散 1-2 跳，收集关联原子

### 4.3 统一排序

```python
final_score = (
    w1 * semantic_similarity +    # 语义相似度
    w2 * node_strength +          # 节点强度（含衰减）
    w3 * edge_weight +            # 边权重
    w4 * emotion_boost +          # 情绪关联强度
    w5 * time_factor              # 时间因子
)
```

**权重由调用方传入**，不同场景可用不同策略。

### 4.4 更新流程

检索完成后，对 Top-K 原子：

1. **节点更新**：`on_access(atom, decay_rate, boost)`
2. **Hebbian 边增强**：Top-K 内两两之间的边 `on_access(link, ...)`
3. **时间戳更新**：所有被访问的节点和边

---

## 5. 人格与自我 (Personality & Self-Model)

### 5.1 状态 vs 人格分离

| 概念 | 存储位置 | 衰减速率 | 说明 |
|------|---------|---------|------|
| 当前情绪状态 | Emotion.strength | 高 | 快速波动，会平复 |
| 长期情绪倾向 | 情绪边.weight | 很低 | 人格，缓慢演化 |

**示例**：

```
[happy].strength = 0.3  (当前：情绪平静)

[happy] --weight=0.8-- [和朋友聊天]  (人格：聊天让我开心)
[happy] --weight=0.2-- [加班]        (人格：加班不太开心)
```

### 5.2 人格演化

- 持续美好经历 → happy 与正面 Fact 的边权重增强 → 人格变乐观
- 边权重衰减很慢 → 人格改变是渐进的
- 无需固定 baseline，人格自然从经历中涌现

### 5.3 人格初始化

人格通过 YAML 配置文件初始化，支持两部分：

1. **情绪原子**：12 种基础情绪，strength 在 [0.3, 0.7] 均匀随机初始化
2. **偏好注入**（可选）：预设的概念/事实原子及其与情绪的边权重

#### 情绪原子列表

```
happy, sad, anger, fear, surprise, disgust,
love, trust, anticipation, curiosity, calm, anxiety
```

#### 配置文件格式 (persona.yaml)

```yaml
# Nakari 人格配置文件

# 情绪原子初始化
emotions:
  init_range: [0.3, 0.7]  # strength 随机范围
  types:
    - happy
    - sad
    - anger
    - fear
    - surprise
    - disgust
    - love
    - trust
    - anticipation
    - curiosity
    - calm
    - anxiety

# 偏好注入（可选）
preferences:
  # 概念偏好：概念 -> 情绪 -> 边权重
  concepts:
    - content: "cyberpunk"
      emotions:
        love: 0.8
        curiosity: 0.6
    
    - content: "empathy"
      emotions:
        love: 0.9
        trust: 0.7

  # 人设陈述（Fact 原子）
  facts:
    - content: "Logic is important but empathy matters more"
      emotions:
        love: 0.7
        calm: 0.5
    
    - content: "I enjoy deep conversations"
      emotions:
        happy: 0.8
        curiosity: 0.7
```

#### 初始化流程

```python
def init_personality(config_path: str):
    config = load_yaml(config_path)
    
    # 1. 创建情绪原子
    for emotion_type in config["emotions"]["types"]:
        init_strength = random.uniform(*config["emotions"]["init_range"])
        create_atom(
            content=emotion_type,
            type="emotion",
            strength=init_strength,
            timestamp=now()
        )
    
    # 2. 创建偏好概念和边
    for concept in config.get("preferences", {}).get("concepts", []):
        atom = create_atom(content=concept["content"], type="concept", ...)
        for emotion, weight in concept["emotions"].items():
            create_link(atom, get_emotion(emotion), weight=weight)
    
    # 3. 创建人设陈述和边
    for fact in config.get("preferences", {}).get("facts", []):
        atom = create_atom(content=fact["content"], type="fact", ...)
        for emotion, weight in fact["emotions"].items():
            create_link(atom, get_emotion(emotion), weight=weight)
```

---

## 6. 记忆巩固与反思 (Memory Consolidation & Reflection)

> 待设计

可能的方向：
- 发现模式，创建新的 Fact 原子（如 "User 最近经常熬夜"）
- 将模式 Fact 与相关原子建立连接
- 反思时也触发 `on_access`，遵循统一规则

---

## 7. 设计决策记录

| 问题 | 决策 | 理由 |
|------|------|------|
| 是否保留 id | 否 | 用 content hash 或数据库自动管理 |
| timestamp 语义 | 上次激活时间 | 用于计算衰减，检索时更新 |
| 边是否有信息 | 有 weight + timestamp | 支持 Hebbian 学习和人格演化 |
| type 是否显式保留 | 是 | 便于查询过滤和差异化处理 |
| 懒惰计算后是否写回 | 是 | 保持 strength 反映真实状态 |
| 情绪如何演化 | 通过边权重 | 分离状态（节点）和人格（边） |
| 情绪原子列表 | 12 种 | happy, sad, anger, fear, surprise, disgust, love, trust, anticipation, curiosity, calm, anxiety |
| 情绪初始 strength | [0.3, 0.7] 随机 | 体现个体差异 |
| 偏好注入 | 可配置 (YAML) | 用户可选择是否加载预设人格 |
