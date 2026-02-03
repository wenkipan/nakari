# Discrete Atom Network (DAN) Architecture & Specification v3

DAN存储了长期记忆，并能在llm需要时给出记忆点，这些记忆点和记忆连边都有一个权重，权重随着时间下降，模拟艾宾浩斯遗忘曲线

## tech stack

图数据库Neo4j，

向量检索Embedding，提供抽象接口，当前先支持openai配置

## 1. 核心理念 (Core Philosophy)

Atom和Edge对应图的点和无向边

有三类Atom：
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

atom有属性如
```json
{
  "content":,    //内容
  "embedding":,  //向量embedding，用于语义查找
  "weight":,     //点的权重，0.0 ~ 1.0
  "timestamp":,  //最后访问时间
  "extensions":, //可选扩展
}
```
Edge有属性如：
```json
{
  "weight":,     //点的权重，0.0 ~ 1.0
  "timestamp":,  //最后访问时间
}
```
---
## 2.核心概念

### 懒惰计算策略 (Lazy Evaluation)

模拟艾宾浩斯遗忘曲线理论上需要实时更新数据库开销巨大，因此系统采用**懒惰计算**策略：

对访问到的Atom和Edge统一处理：
1. `weight = weight × exp(-decay_rate × hours)` 
2. `hours`为已经过去的时间（now - timestamp）
3. 更新timestamp

衰减速率参考：

| 对象 | decay_rate | 说明 |
|------|-----------|------|
| Fact.weight | 0.01 | 记忆会淡忘 |
| Concept.weight | 0.005 | 概念相对稳定 |
| Emotion.weight | 0.05 | 情绪波动快（当前状态） |
| 普通边.weight | 0.005 | 关联关系稳定 |
| 情绪边（任意一端节点为 Emotion 类型）.weight | 0.001 | 人格演化缓慢 |

### boost操作
为了模拟反复记忆对抗艾宾浩斯遗忘曲线，引入boost概念

输入：一组原子。

流程：
对于这组原子，进行`weight = weight + boost`
对于这组原子，枚举所有二元组：
1.若不存在连边，创建连边，设置`weight = boost`
2.对于已存在的边：`weight = weight + boost`

boost值参考

| 对象 | boost | 说明 |
|------|-----------|------|
| Fact | 0.1 | 记忆会淡忘 |
| Concept | 0.1 | 概念相对稳定 |
| Emotion | 0.1 | 情绪波动快（当前状态） |
| 普通边 | 0.1 | 关联关系稳定 |
| 情绪边（查询一端节点是否为 Emotion 类型）.weight | 0.1 | 人格演化缓慢 |

---

## 3. 检索

### 3.1 检索：

输入：                                                          
   一组检索词                   
   一组评分权重RetrievalWeights（可选，有默认值）    
   一组RetrievalConfig     # n_hops（可选，有默认值2）, top_k（可选，有默认值3）, decay_rate（可选，有默认值）    

流程：                                                          
1. 对每个 query 分别做 vector_search，收集种子原子        
2. 从种子出发扩展搜索n_hops跳可到达的所有原子
3. 合并多query的搜索集，计算经过懒惰计算策略后的weight
4. 用 RetrievalWeights 综合评分排序
5. 返回 Top-K 原子 

#### 排序说明：
RetrievalWeights：
```json
{
  "semantic_similarity": 1.0,    //query与content 相近度权重
  "Fact_weight":0.1,             //Atom为Fact label时的权重
  "Concept_weight":0.1,          //Atom为Fact label时的权重
  "Emotion_weight":0.2,          //Atom为Fact label时的权重
}
```
```
final_score = 
    RetrievalWeights.semantic_similarity * semantic_similarity +
    (is_Fact?RetrievalWeights.Fact_weight:0) * weight +
    (is_Concept?RetrievalWeights.Concept_weight:0) * weight +
    (is_Emotion?RetrievalWeights.Emotion_weight:0) * weight

```


#### 针对检索胜利的TOPK原子的更新（模拟对抗遗忘）
输入：TOPK的原子
对TOPK个原子以及TOPK的连边
1. 对weight执行懒惰计算
2. 做一次boost操作
3. 批量写回数据库
---

## 4.创建原子

输入：内容，类型，原子强度
在数据库中创建对应类型的原子

---

## 5. 创建/插入数据

向neo4j中写入数据有流程如下

输入：
  主原子：内容，原子类型，原子强度
  
  副原子1：内容，原子类型，与主原子的连接强度（对应`edge_weight`
  副原子2：内容，原子类型，与主原子的连接强度（对应`edge_weight`

```json
{
  "main": {"content": "Wenki在熬夜", "type": "fact","weight": 0.8},
  "related": [
    {"content": "Wenki", "type": "concept", "edge_weight": 0.8},
    {"content": "熬夜", "type": "concept", "edge_weight": 0.6}
  ]
}
```

执行：
对这组json内的原子，若原子不存在（content 精确匹配失败），创建原子
创建边，若边不存在
更新边和原子的权重


---
## 6 人格初始化

人格通过 YAML 配置文件初始化，支持两部分：

1. **情绪原子**：12 种基础情绪，strength 在 [0.3, 0.7] 均匀随机初始化
2. **偏好注入**（可选）：预设的概念/事实原子及其与情绪的边权重，通过`4. 插入数据`的方式插入DAN

#### 情绪原子列表

```
happy, sad, anger, fear, surprise, disgust,
love, trust, anticipation, curiosity, calm, anxiety
```

### 遗留问题

防止图无限增长机制（暂不考虑

