# Docker Setup Guide

This guide explains how to run the Nakari DAN Memory System using Docker.

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows/Mac) or Docker Engine (Linux)
- At least 4GB of available RAM
- API keys for embedding and LLM services (e.g., Zhipu, OpenAI)

## Quick Start

### Windows (PowerShell)

```powershell
# First time setup
cp .env.example .env
# Edit .env with your API keys

# Start all services
.\scripts\docker-start.ps1 start

# Run the demo
.\scripts\docker-start.ps1 demo
```

### Linux/Mac (Bash)

```bash
# First time setup
cp .env.example .env
# Edit .env with your API keys

# Make script executable
chmod +x scripts/docker-start.sh

# Start all services
./scripts/docker-start.sh start

# Run the demo
./scripts/docker-start.sh demo
```

## Services

The Docker setup includes the following services:

| Service | Port | Description |
|---------|------|-------------|
| Neo4j | 7474 (HTTP), 7687 (Bolt) | Graph database with vector search |
| Redis | 6379 | Celery message broker & cache |
| App | 8000 | Nakari application container |
| Celery Worker | - | Async task worker |

## Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```env
# Required: Embedding API (OpenAI-compatible)
EMBEDDING_API_BASE=https://open.bigmodel.cn/api/paas/v4
EMBEDDING_API_KEY=your_key_here
EMBEDDING_MODEL=embedding-3

# Required: LLM API (OpenAI-compatible)
LLM_API_BASE=https://open.bigmodel.cn/api/paas/v4
LLM_API_KEY=your_key_here
LLM_MODEL=glm-4

# Auto-configured by Docker (no changes needed)
NEO4J_URI=bolt://neo4j:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password123
```

### Supported Providers

The system supports any OpenAI-compatible API:

| Provider | API Base URL | Embedding Models |
|----------|-------------|------------------|
| Zhipu | `https://open.bigmodel.cn/api/paas/v4` | `embedding-3`, `embedding-3-pro` |
| OpenAI | `https://api.openai.com/v1` | `text-embedding-3-small`, `text-embedding-3-large` |
| Moonshot | `https://api.moonshot.cn/v1` | `moonshot-v1-8k` |

## Commands Reference

### Windows (PowerShell)

```powershell
.\scripts\docker-start.ps1 start    # Start all services
.\scripts\docker-start.ps1 stop     # Stop all services
.\scripts\docker-start.ps1 restart  # Restart all services
.\scripts\docker-start.ps1 logs     # View all logs
.\scripts\docker-start.ps1 logs neo4j  # View Neo4j logs
.\scripts\docker-start.ps1 shell    # Enter app container
.\scripts\docker-start.ps1 demo     # Run memory demo
.\scripts\docker-start.ps1 test     # Run tests
.\scripts\docker-start.ps1 clean    # Remove all data
.\scripts\docker-start.ps1 help     # Show help
```

### Linux/Mac (Bash)

```bash
./scripts/docker-start.sh start    # Start all services
./scripts/docker-start.sh stop     # Stop all services
./scripts/docker-start.sh restart  # Restart all services
./scripts/docker-start.sh logs     # View all logs
./scripts/docker-start.sh logs neo4j  # View Neo4j logs
./scripts/docker-start.sh shell    # Enter app container
./scripts/docker-start.sh demo     # Run memory demo
./scripts/docker-start.sh test     # Run tests
./scripts/docker-start.sh clean    # Remove all data
./scripts/docker-start.sh help     # Show help
```

## Accessing Services

### Neo4j Browser

1. Open http://localhost:7474
2. Connect with:
   - URI: `bolt://localhost:7687`
   - Username: `neo4j`
   - Password: `password123`

### Application Container

```bash
# Enter the container
docker compose exec app bash

# Run Python scripts
docker compose exec app python scripts/demo_memory.py

# Run tests
docker compose exec app pytest tests/ -v

# Interactive Python
docker compose exec app python
```

## Vector Index Configuration

The setup uses Neo4j 5.23.0 which supports up to 4096-dimensional vectors. The initialization script (`scripts/init-neo4j.cypher`) creates:

- Vector indexes for Atom embeddings (4096 dimensions, cosine similarity)
- Fulltext index for content search
- Standard indexes for type, timestamp, and weight fields

### Changing Vector Dimensions

If you're using a model with different embedding dimensions (e.g., `embedding-3` = 2048 dimensions), you need to:

1. Edit `scripts/init-neo4j.cypher`
2. Change `vector.dimensions` from `4096` to your model's dimension
3. Restart with clean data: `.\scripts\docker-start.ps1 clean && .\scripts\docker-start.ps1 start`

## Troubleshooting

### Docker not running

```
[ERROR] Docker 未安装或未运行
```

Solution: Start Docker Desktop or Docker Engine.

### Neo4j startup timeout

```
[ERROR] Neo4j 启动超时
```

Solutions:
- Increase available RAM (Neo4j needs at least 512MB heap)
- Check Docker resource limits in Docker Desktop settings
- View logs: `docker compose logs neo4j`

### Port conflicts

```
Error: bind: address already in use
```

Solutions:
- Stop conflicting services: `netstat -tulpn | grep 7474`
- Or change ports in `docker-compose.yml`

### Permission denied (Linux/Mac)

```
bash: ./scripts/docker-start.sh: Permission denied
```

Solution: `chmod +x scripts/docker-start.sh`

### Vector dimension mismatch

```
Cannot create vector with X dimensions when index requires Y dimensions
```

Solution: 
1. Clean existing data: `.\scripts\docker-start.ps1 clean`
2. Edit `scripts/init-neo4j.cypher` to match your model's dimensions
3. Restart: `.\scripts\docker-start.ps1 start`

## Data Persistence

Docker volumes are used for data persistence:

| Volume | Purpose |
|--------|---------|
| `nakari_neo4j_data` | Neo4j database files |
| `nakari_neo4j_logs` | Neo4j log files |
| `nakari_redis_data` | Redis persistence |
| `nakari_pip_cache` | Python package cache |

To backup Neo4j data:
```bash
docker compose exec neo4j neo4j-admin database dump --to-path=/logs neo4j
docker cp nakari-neo4j:/logs/neo4j.dump ./backup/
```

To restore:
```bash
docker cp ./backup/neo4j.dump nakari-neo4j:/logs/
docker compose exec neo4j neo4j-admin database load --from-path=/logs neo4j
```

## Development Workflow

1. **Start services**: `.\scripts\docker-start.ps1 start`
2. **Make code changes**: Edit files in your local editor
3. **Changes auto-sync**: The `/app` volume mounts your local directory
4. **Run tests**: `.\scripts\docker-start.ps1 test`
5. **View logs**: `.\scripts\docker-start.ps1 logs app`

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Docker Network                     │
│  (nakari_network)                                   │
│                                                      │
│  ┌──────────┐   ┌──────────┐   ┌────────────────┐  │
│  │  Neo4j   │   │  Redis   │   │ Celery Worker  │  │
│  │  :7687   │   │  :6379   │   │                │  │
│  └────▲─────┘   └────▲─────┘   └───────▲────────┘  │
│       │              │                  │           │
│       └──────────────┼──────────────────┘           │
│                      │                              │
│              ┌───────┴───────┐                      │
│              │   App (API)   │                      │
│              │    :8000      │                      │
│              └───────────────┘                      │
│                                                      │
└─────────────────────────────────────────────────────┘
                        │
                        ▼
              ┌─────────────────┐
              │  Local Volume   │
              │  (./:/app)      │
              └─────────────────┘
```
