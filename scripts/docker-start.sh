#!/bin/bash
# Nakari Docker 启动脚本 (Linux/Mac)
# Usage: ./scripts/docker-start.sh [command]
# Commands:
#   start    - 启动所有服务 (默认)
#   stop     - 停止所有服务
#   restart  - 重启所有服务
#   logs     - 查看日志
#   shell    - 进入应用容器
#   demo     - 运行演示脚本
#   test     - 运行测试
#   clean    - 清理所有容器和数据

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# 打印带颜色的消息
info() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 检查 Docker 是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    if ! docker info &> /dev/null; then
        error "Docker 服务未运行，请启动 Docker"
        exit 1
    fi
    success "Docker 已就绪"
}

# 检查 .env 文件
check_env() {
    if [ ! -f ".env" ]; then
        warn ".env 文件不存在，从 .env.example 复制..."
        if [ -f ".env.example" ]; then
            cp .env.example .env
            warn "请编辑 .env 文件配置你的 API 密钥"
            warn "至少需要配置: EMBEDDING_API_KEY, LLM_API_KEY"
        else
            error ".env.example 文件不存在"
            exit 1
        fi
    fi
    success ".env 文件已就绪"
}

# 等待服务健康
wait_for_services() {
    info "等待服务启动..."
    
    # 等待 Neo4j
    local max_attempts=30
    local attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if docker compose exec -T neo4j wget --no-verbose --tries=1 --spider http://localhost:7474 2>/dev/null; then
            success "Neo4j 已就绪"
            break
        fi
        attempt=$((attempt + 1))
        echo -n "."
        sleep 2
    done
    
    if [ $attempt -eq $max_attempts ]; then
        error "Neo4j 启动超时"
        exit 1
    fi
    
    # 等待 Redis
    attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if docker compose exec -T redis redis-cli ping 2>/dev/null | grep -q PONG; then
            success "Redis 已就绪"
            break
        fi
        attempt=$((attempt + 1))
        echo -n "."
        sleep 1
    done
    
    if [ $attempt -eq $max_attempts ]; then
        error "Redis 启动超时"
        exit 1
    fi
}

# 初始化 Neo4j 向量索引
init_neo4j() {
    info "初始化 Neo4j 向量索引..."
    if [ -f "scripts/init-neo4j.cypher" ]; then
        docker compose exec -T neo4j cypher-shell -u neo4j -p password123 < scripts/init-neo4j.cypher 2>/dev/null || true
        success "向量索引初始化完成"
    else
        warn "init-neo4j.cypher 不存在，跳过索引初始化"
    fi
}

# 启动服务
cmd_start() {
    check_docker
    check_env
    
    info "启动 Nakari 服务..."
    docker compose up -d
    
    wait_for_services
    init_neo4j
    
    echo ""
    success "=== Nakari 服务已启动 ==="
    echo ""
    info "Neo4j Browser: http://localhost:7474"
    info "  用户名: neo4j"
    info "  密码: password123"
    echo ""
    info "应用容器: docker compose exec app bash"
    info "运行演示: ./scripts/docker-start.sh demo"
    info "运行测试: ./scripts/docker-start.sh test"
    echo ""
}

# 停止服务
cmd_stop() {
    info "停止 Nakari 服务..."
    docker compose down
    success "服务已停止"
}

# 重启服务
cmd_restart() {
    cmd_stop
    cmd_start
}

# 查看日志
cmd_logs() {
    docker compose logs -f "${2:-}"
}

# 进入容器 shell
cmd_shell() {
    info "进入应用容器..."
    docker compose exec app bash
}

# 运行演示
cmd_demo() {
    info "运行 Memory 演示..."
    docker compose exec app python scripts/demo_memory.py
}

# 运行测试
cmd_test() {
    info "运行测试..."
    docker compose exec app pytest tests/ -v
}

# 清理
cmd_clean() {
    warn "这将删除所有容器、镜像和数据卷！"
    read -p "确定要继续吗？(y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        info "清理 Docker 资源..."
        docker compose down -v --rmi local
        success "清理完成"
    else
        info "已取消"
    fi
}

# 显示帮助
cmd_help() {
    echo "Nakari Docker 管理脚本"
    echo ""
    echo "用法: ./scripts/docker-start.sh [命令]"
    echo ""
    echo "命令:"
    echo "  start    启动所有服务 (默认)"
    echo "  stop     停止所有服务"
    echo "  restart  重启所有服务"
    echo "  logs     查看日志 (可选: logs neo4j)"
    echo "  shell    进入应用容器"
    echo "  demo     运行演示脚本"
    echo "  test     运行测试"
    echo "  clean    清理所有容器和数据"
    echo "  help     显示此帮助"
}

# 主入口
case "${1:-start}" in
    start)   cmd_start ;;
    stop)    cmd_stop ;;
    restart) cmd_restart ;;
    logs)    cmd_logs "$@" ;;
    shell)   cmd_shell ;;
    demo)    cmd_demo ;;
    test)    cmd_test ;;
    clean)   cmd_clean ;;
    help|-h|--help) cmd_help ;;
    *)
        error "未知命令: $1"
        cmd_help
        exit 1
        ;;
esac
