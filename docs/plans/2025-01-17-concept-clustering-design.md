# Concept 聚类设计

## 问题

当前架构中，Fact "苹果是红的" 会分别与 Concept "苹果" 和 Concept "红色" 建边，但苹果和红色之间没有直接关联。这导致：

- 检索"苹果"时，无法直接跳转到"红色"
- 必须经过 Fact 中转，效率低且语义间接
- 无法自然形成概念聚类（如红色物品的聚类）

## 解决方案

利用已有的检索更新流程，在 Top-K 原子中自动发现并建立 Concept 间的边。

### 1. 新增边类型

| 连接 | 语义 |
|------|------|
| **Concept ↔ Concept** | **概念间的语义关联/聚类（新增）** |
| Fact ↔ Concept | 概念参与了该事实 |
| Fact ↔ Fact | 时间/逻辑关联 |
| Emotion ↔ Fact | 对该事实的情绪反应 |
| Emotion ↔ Concept | 对该概念的情绪倾向 |

### 2. 检索时自动建边

```python
def update_after_retrieval(top_k_atoms, boost):
    # 1. 节点更新（不变）
    for atom in top_k_atoms:
        on_access(atom, decay_rate, boost)
    
    # 2. 边更新（增强 + 新建）
    for atom_a, atom_b in pairs(top_k_atoms):
        if not is_valid_link_type(atom_a.type, atom_b.type):
            continue  # 跳过不允许的类型对
        
        link = get_link(atom_a, atom_b)
        if link:
            # 已有边：增强
            on_access(link, decay_rate, boost)
        else:
            # 无边：新建
            create_link(atom_a, atom_b, weight=boost, timestamp=now())
```

**允许自动建边的类型**：
- Concept ↔ Concept ✓

### 3. 边权重初始化规则

```python
UNIFIED_BOOST = 0.05  # 统一激活增益

def create_link(atom_a, atom_b, weight=None, timestamp=None):
    """
    weight 来源优先级：
    1. 外部显式传入 → 使用外部值
    2. 未传入 → 使用 UNIFIED_BOOST
    """
    final_weight = weight if weight is not None else UNIFIED_BOOST
    return Link(weight=final_weight, timestamp=timestamp or now())
```

### 4. 衰减速率

| 边类型 | decay_rate | 说明 |
|--------|-----------|------|
| Concept ↔ Concept | 0.005 | 概念关联，稳定 |
| Fact ↔ Concept | 0.005 | 普通边，稳定 |
| Fact ↔ Fact | 0.005 | 普通边，稳定 |
| Emotion ↔ Fact | 0.005 | 普通边，稳定 |
| Emotion ↔ Concept | 0.001 | 人格边，非常稳定 |

## 效果

```
检索 "苹果是红的" → 苹果、红色同在 Top-K → 建边 苹果--红色
检索 "番茄是红的" → 番茄、红色同在 Top-K → 建边 番茄--红色
检索 "草莓是红的" → 草莓、红色同在 Top-K → 建边 草莓--红色

结果：以 "红色" 为中心的概念聚类自然涌现
      苹果 --0.05-- 红色 --0.05-- 番茄
                      |
                    草莓

多次共现后，边权重增强，聚类更紧密
```

## 设计优点

- **无需额外机制**：复用检索更新流程
- **规则统一**：统一 boost，差异靠 decay_rate
- **自然涌现**：聚类从共现中自然形成
- **噪声自清**：低权重边通过衰减消亡
