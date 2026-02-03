// Nakari Neo4j 初始化脚本
// 用于创建向量索引和约束
// 使用: docker compose exec neo4j cypher-shell -u neo4j -p password123 < scripts/init-neo4j.cypher

// ============================================
// 唯一性约束
// ============================================

// Atom ID 唯一约束
CREATE CONSTRAINT atom_id_unique IF NOT EXISTS
FOR (a:Atom) REQUIRE a.id IS UNIQUE;

// ============================================
// 向量索引 (Neo4j 5.23+)
// ============================================
// 支持 4096 维向量 (embedding-3-pro)
// 如果使用 embedding-3 (2048 维), 请修改 dimensions 参数

// Atom 向量索引 - 用于 FACT 类型
CREATE VECTOR INDEX atom_embedding_fact IF NOT EXISTS
FOR (a:Atom)
ON a.embedding
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 4096,
    `vector.similarity_function`: 'cosine'
  }
};

// Atom 向量索引 - 用于 CONCEPT 类型
CREATE VECTOR INDEX atom_embedding_concept IF NOT EXISTS
FOR (a:Atom)
ON a.embedding
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 4096,
    `vector.similarity_function`: 'cosine'
  }
};

// Atom 向量索引 - 用于 EMOTION 类型
CREATE VECTOR INDEX atom_embedding_emotion IF NOT EXISTS
FOR (a:Atom)
ON a.embedding
OPTIONS {
  indexConfig: {
    `vector.dimensions`: 4096,
    `vector.similarity_function`: 'cosine'
  }
};

// ============================================
// 全文搜索索引
// ============================================

// Atom 内容全文搜索
CREATE FULLTEXT INDEX atom_content_fulltext IF NOT EXISTS
FOR (a:Atom)
ON EACH [a.content];

// ============================================
// 普通索引 (加速查询)
// ============================================

// Atom 类型索引
CREATE INDEX atom_type_index IF NOT EXISTS
FOR (a:Atom)
ON (a.atom_type);

// Atom 时间戳索引
CREATE INDEX atom_created_at_index IF NOT EXISTS
FOR (a:Atom)
ON (a.created_at);

// Atom 权重索引 (用于衰减排序)
CREATE INDEX atom_weight_index IF NOT EXISTS
FOR (a:Atom)
ON (a.weight);

// Edge 类型索引
CREATE INDEX edge_type_index IF NOT EXISTS
FOR ()-[e:RELATES_TO]-()
ON (e.edge_type);

// ============================================
// 显示已创建的索引
// ============================================

SHOW INDEXES;
