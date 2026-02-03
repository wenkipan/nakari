# Nakari - DAN Memory System
# Python 3.11 for better async performance

FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 安装开发依赖
RUN pip install --no-cache-dir \
    black \
    flake8 \
    mypy \
    isort \
    pyyaml

# 复制项目代码
COPY . .

# 设置 Python 路径
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 默认命令 - 保持容器运行
CMD ["tail", "-f", "/dev/null"]
