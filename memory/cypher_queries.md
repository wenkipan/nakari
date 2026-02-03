# DAN Memory - Neo4j Browser 查询脚本

在 Neo4j Browser (`http://localhost:7474`) 中运行以下查询。

---

## 1. 查看所有数据

### 1.1 查看所有节点和边（完整图）
```cypher
MATCH (n)
OPTIONAL MATCH (n)-[r]-(m)
RETURN n, r, m
```

### 1.2 仅查看所有节点
```cypher
MATCH (n)
RETURN n
```

### 1.3 仅查看所有边
```cypher
MATCH ()-[r:CONNECTED]-()
RETURN r
```

---

## 2. 按类型查看原子

### 2.1 所有 Emotion 节点
```cypher
MATCH (n:Emotion)
RETURN n
ORDER BY n.weight DESC
```

### 2.2 所有 Concept 节点
```cypher
MATCH (n:Concept)
RETURN n
ORDER BY n.weight DESC
```

### 2.3 所有 Fact 节点
```cypher
MATCH (n:Fact)
RETURN n
ORDER BY n.timestamp DESC
```

---

## 3. 统计信息

### 3.1 各类型节点数量
```cypher
MATCH (n)
RETURN labels(n)[0] AS type, COUNT(n) AS count
ORDER BY count DESC
```

### 3.2 边的数量
```cypher
MATCH ()-[r:CONNECTED]-()
RETURN COUNT(r) / 2 AS edge_count
```

### 3.3 完整统计摘要
```cypher
MATCH (n)
WITH labels(n)[0] AS type, COUNT(n) AS node_count
WITH COLLECT({type: type, count: node_count}) AS nodes, SUM(node_count) AS total_nodes
MATCH ()-[r:CONNECTED]-()
WITH nodes, total_nodes, COUNT(r) / 2 AS edge_count
RETURN nodes, total_nodes, edge_count
```

---

## 4. 探索特定节点

### 4.1 查看某个节点及其所有连接
```cypher
// 替换 'happy' 为你要查找的内容
MATCH (n {content: 'happy'})
OPTIONAL MATCH (n)-[r:CONNECTED]-(m)
RETURN n, r, m
```

### 4.2 查看节点的 N 跳邻居
```cypher
// 查看 2 跳内的所有节点
MATCH path = (n {content: 'happy'})-[*1..2]-(m)
RETURN path
```

### 4.3 查找高权重节点
```cypher
MATCH (n)
WHERE n.weight > 0.5
RETURN n.content AS content, labels(n)[0] AS type, n.weight AS weight
ORDER BY n.weight DESC
LIMIT 20
```

---

## 5. 边的分析

### 5.1 查看高权重边
```cypher
MATCH (a)-[r:CONNECTED]-(b)
WHERE r.weight > 0.5
RETURN a.content AS from, b.content AS to, r.weight AS weight
ORDER BY r.weight DESC
```

### 5.2 查看 Emotion 相关的所有边
```cypher
MATCH (e:Emotion)-[r:CONNECTED]-(n)
RETURN e.content AS emotion, n.content AS connected_to, labels(n)[0] AS type, r.weight AS weight
ORDER BY e.content, r.weight DESC
```

---

## 6. 表格视图（详细数据）

### 6.1 所有节点详细信息
```cypher
MATCH (n)
RETURN 
    elementId(n) AS id,
    labels(n)[0] AS type,
    n.content AS content,
    n.weight AS weight,
    n.timestamp AS timestamp
ORDER BY labels(n)[0], n.weight DESC
```

### 6.2 所有边详细信息
```cypher
MATCH (a)-[r:CONNECTED]-(b)
WHERE elementId(a) < elementId(b)  // 避免重复
RETURN 
    a.content AS source,
    b.content AS target,
    r.weight AS weight,
    r.timestamp AS timestamp
ORDER BY r.weight DESC
```

---

## 7. 调试查询

### 7.1 检查向量索引状态
```cypher
SHOW INDEXES
```

### 7.2 查看数据库 schema
```cypher
CALL db.schema.visualization()
```

### 7.3 删除所有数据（危险！仅用于测试）
```cypher
// 先删除所有边
MATCH ()-[r]-() DELETE r;

// 再删除所有节点
MATCH (n) DELETE n;
```

---

## 使用技巧

1. **图视图 vs 表格视图**：在结果区域顶部切换 Graph/Table/Text 视图
2. **展开节点**：双击节点可展开其关系
3. **样式设置**：点击节点类型可自定义颜色和大小
4. **导出**：右上角可导出为 PNG、SVG 或 JSON
5. **收藏查询**：点击星标可保存常用查询

---

## 可视化设置建议

在 Neo4j Browser 中，点击左侧的样式面板设置：

| 节点类型 | 建议颜色 | Caption |
|----------|----------|---------|
| Emotion | 红色 #E74C3C | content |
| Concept | 蓝色 #3498DB | content |
| Fact | 绿色 #2ECC71 | content |

节点大小可以根据 `weight` 属性动态调整。
