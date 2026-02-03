"""DAN Memory 端到端演示脚本.

演示完整的 Memory 工作流程：
1. 初始化人格（情感 + 偏好）
2. 存储记忆（事实、概念）
3. 查询检索
4. 查看 Neo4j 中的数据
"""

import asyncio
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# 设置 UTF-8 输出
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# 加载环境变量
load_dotenv()

from memory.config import EmbeddingConfig, Neo4jConfig
from memory.embedding import OpenAICompatibleEmbeddingProvider
from memory.store import Neo4jAtomStore
from memory.dan import DANMemory, InsertRequest, RelatedAtom
from memory.models import AtomType
from memory.personality import (
    PersonalityInitializer,
    PersonalityConfig,
    PreferenceItem,
)


async def print_separator(title: str):
    """打印分隔线."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


async def print_atom(atom, prefix: str = ""):
    """打印原子信息."""
    print(f"{prefix}[{atom.atom_type.value.upper()}] {atom.content}")
    print(f"{prefix}  ID: {atom.id[:20]}..." if atom.id else f"{prefix}  ID: None")
    print(f"{prefix}  Weight: {atom.weight:.4f}")
    print(f"{prefix}  Timestamp: {atom.timestamp}")


async def dump_all_data(store: Neo4jAtomStore):
    """导出 Neo4j 中的所有数据."""
    await print_separator("Neo4j 数据库内容")

    # 获取所有节点
    query_nodes = """
    MATCH (n)
    RETURN elementId(n) as id, labels(n) as labels, n.content as content, 
           n.weight as weight, n.timestamp as timestamp
    ORDER BY labels(n)[0], n.weight DESC
    """

    async with store._driver.session(database=store.database) as session:
        result = await session.run(query_nodes)
        nodes = []
        async for record in result:
            nodes.append(dict(record))

    print(f"总节点数: {len(nodes)}")
    print()

    # 按类型分组显示
    by_type = {}
    for node in nodes:
        label = node["labels"][0] if node["labels"] else "Unknown"
        if label not in by_type:
            by_type[label] = []
        by_type[label].append(node)

    for label, items in by_type.items():
        print(f"【{label}】({len(items)} 个)")
        for item in items[:10]:  # 最多显示 10 个
            print(f"  - {item['content'][:30]:<30} (weight: {item['weight']:.4f})")
        if len(items) > 10:
            print(f"  ... 还有 {len(items) - 10} 个")
        print()

    # 获取所有边
    query_edges = """
    MATCH (a)-[r:CONNECTED]-(b)
    WHERE elementId(a) < elementId(b)
    RETURN a.content as source, b.content as target, r.weight as weight
    ORDER BY r.weight DESC
    LIMIT 20
    """

    async with store._driver.session(database=store.database) as session:
        result = await session.run(query_edges)
        edges = []
        async for record in result:
            edges.append(dict(record))

    print(f"总边数: {len(edges)} (显示前 20 条)")
    print()
    for edge in edges:
        src = edge["source"][:15] if edge["source"] else "?"
        tgt = edge["target"][:15] if edge["target"] else "?"
        print(f"  {src:<15} <--({edge['weight']:.2f})--> {tgt:<15}")


async def main():
    """主函数."""
    print("\n" + "=" * 60)
    print("  DAN Memory 端到端演示")
    print("=" * 60)

    # 1. 初始化配置
    await print_separator("1. 初始化配置")

    embedding_config = EmbeddingConfig.from_env()
    neo4j_config = Neo4jConfig.from_env()

    print(f"Embedding API: {embedding_config.api_base}")
    print(f"Embedding Model: {embedding_config.model}")
    print(f"Neo4j URI: {neo4j_config.uri}")

    # 2. 创建组件
    await print_separator("2. 创建组件")

    embedding_provider = OpenAICompatibleEmbeddingProvider.from_config(embedding_config)
    print("✓ Embedding Provider 已创建")

    store = Neo4jAtomStore(
        uri=neo4j_config.uri,
        username=neo4j_config.username,
        password=neo4j_config.password,
        database=neo4j_config.database,
    )
    print("✓ Neo4j Store 已创建")

    dan = DANMemory(store=store, embedding_provider=embedding_provider)
    print("✓ DANMemory 已创建")

    # 3. 清空现有数据并创建索引
    await print_separator("3. 初始化数据库")

    vector_search_available = False

    async with store._driver.session(database=store.database) as session:
        # 检查 Neo4j 版本
        result = await session.run(
            "CALL dbms.components() YIELD versions RETURN versions[0] as version"
        )
        record = await result.single()
        neo4j_version = record["version"] if record else "unknown"
        print(f"Neo4j 版本: {neo4j_version}")

        # 清空数据
        await session.run("MATCH (n) DETACH DELETE n")
        print("✓ 已清空 Neo4j 数据库")

        # 删除旧索引
        for idx_name in ["atom_embeddings", "concept_embeddings", "emotion_embeddings"]:
            try:
                await session.run(f"DROP INDEX {idx_name} IF EXISTS")
            except Exception:
                pass
        print("✓ 已删除旧向量索引")

        # 创建向量索引 (4096 维度，适用于智谱 embedding-3-pro)
        # Neo4j 5.23+ 支持 4096 维度
        try:
            await session.run("""
                CREATE VECTOR INDEX atom_embeddings IF NOT EXISTS
                FOR (n:Fact) ON (n.embedding)
                OPTIONS {indexConfig: {
                    `vector.dimensions`: 4096,
                    `vector.similarity_function`: 'cosine'
                }}
            """)
            await session.run("""
                CREATE VECTOR INDEX concept_embeddings IF NOT EXISTS
                FOR (n:Concept) ON (n.embedding)
                OPTIONS {indexConfig: {
                    `vector.dimensions`: 4096,
                    `vector.similarity_function`: 'cosine'
                }}
            """)
            await session.run("""
                CREATE VECTOR INDEX emotion_embeddings IF NOT EXISTS
                FOR (n:Emotion) ON (n.embedding)
                OPTIONS {indexConfig: {
                    `vector.dimensions`: 4096,
                    `vector.similarity_function`: 'cosine'
                }}
            """)
            print("✓ 已创建向量索引 (4096 维)")
            vector_search_available = True
        except Exception as e:
            print(f"⚠ 创建向量索引失败: {e}")
            print("  提示: Neo4j 5.23+ 才支持 4096 维向量")
            print("  向量搜索将被跳过，但数据存储正常")
        except Exception as e:
            print(f"⚠ 创建向量索引失败: {e}")
            print("  请确保 Neo4j 版本 >= 5.11 或安装了向量索引插件")

    # 4. 初始化人格
    await print_separator("4. 初始化人格")

    personality_config = PersonalityConfig(
        preferences=[
            PreferenceItem(
                content="编程",
                atom_type="concept",
                emotion="curiosity",
                edge_weight=0.9,
            ),
            PreferenceItem(
                content="阅读",
                atom_type="concept",
                emotion="calm",
                edge_weight=0.8,
            ),
            PreferenceItem(
                content="音乐",
                atom_type="concept",
                emotion="happy",
                edge_weight=0.85,
            ),
        ]
    )

    initializer = PersonalityInitializer(dan=dan)
    emotion_atoms = await initializer.initialize_personality(personality_config)

    print(f"✓ 已创建 {len(emotion_atoms)} 个情感原子")
    print(f"✓ 已创建 {len(personality_config.preferences)} 个偏好")

    # 显示部分情感
    print("\n情感原子示例:")
    for name, atom in list(emotion_atoms.items())[:5]:
        print(f"  - {name}: weight={atom.weight:.4f}")

    # 5. 存储一些记忆
    await print_separator("5. 存储记忆")

    memories = [
        {
            "main": {"content": "今天学习了 Python 的异步编程", "type": AtomType.FACT},
            "related": [
                {"content": "编程", "type": AtomType.CONCEPT},
                {"content": "Python", "type": AtomType.CONCEPT},
            ],
        },
        {
            "main": {
                "content": "读完了《深度学习》这本书，收获很大",
                "type": AtomType.FACT,
            },
            "related": [
                {"content": "阅读", "type": AtomType.CONCEPT},
                {"content": "深度学习", "type": AtomType.CONCEPT},
            ],
        },
        {
            "main": {"content": "听了一首很好听的古典音乐", "type": AtomType.FACT},
            "related": [
                {"content": "音乐", "type": AtomType.CONCEPT},
                {"content": "古典音乐", "type": AtomType.CONCEPT},
            ],
        },
        {
            "main": {"content": "用 Neo4j 实现了图数据库存储", "type": AtomType.FACT},
            "related": [
                {"content": "编程", "type": AtomType.CONCEPT},
                {"content": "Neo4j", "type": AtomType.CONCEPT},
                {"content": "图数据库", "type": AtomType.CONCEPT},
            ],
        },
    ]

    for i, memory in enumerate(memories, 1):
        request = InsertRequest(
            main=RelatedAtom(
                content=memory["main"]["content"],
                atom_type=memory["main"]["type"],
            ),
            related=[
                RelatedAtom(
                    content=r["content"],
                    atom_type=r["type"],
                    edge_weight=0.7,
                )
                for r in memory["related"]
            ],
        )
        atom = await dan.insert_data(request)
        print(f"✓ 记忆 {i}: {memory['main']['content'][:30]}...")

    # 6. 查询检索
    await print_separator("6. 查询检索")

    if not vector_search_available:
        print("⚠ 向量搜索不可用 (需要 Neo4j 5.23+)")
        print("  升级 Neo4j 后，向量搜索将自动启用")
        print("\n  手动查询示例 (在 Neo4j Browser 中运行):")
        print("  MATCH (n) WHERE n.content CONTAINS '编程' RETURN n")
    else:
        queries = [
            ["编程", "Python"],
            ["阅读", "学习"],
            ["音乐"],
        ]

        for query in queries:
            print(f"\n查询: {query}")
            print("-" * 40)

            results = await dan.retrieve(query)

            if results:
                for i, atom in enumerate(results, 1):
                    print(f"  {i}. [{atom.atom_type.value}] {atom.content[:40]}")
                    print(f"     weight: {atom.weight:.4f}")
            else:
                print("  (无结果)")

    # 7. 导出所有数据
    await dump_all_data(store)

    # 8. 清理
    await print_separator("8. 清理资源")

    await embedding_provider.close()
    await store.close()
    print("✓ 已关闭所有连接")

    print("\n" + "=" * 60)
    print("  演示完成!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
