# 使用官方 Python 3.12 基础镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 1. 安装必要的系统依赖 (编译密码学库和网络搜索所需)
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 2. 安装 uv (既然你本地在用，容器里也用它，速度极快)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 3. 复制依赖描述文件
COPY pyproject.toml uv.lock ./

# 4. 安装依赖 (使用 uv 同步，不创建虚拟环境直接装在系统目录，适合容器)
RUN uv pip install --system --no-cache -r pyproject.toml

# 5. 复制所有源代码到容器
COPY . .

# 6. 暴露 FastAPI 的默认端口
EXPOSE 8000

# 7. 启动命令 (确保 host 为 0.0.0.0 以便外部访问)
CMD ["python", "main.py"]