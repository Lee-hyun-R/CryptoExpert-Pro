# <img src="static/logo.ico" width="32"> CryptoExpert Pro

> **AI 驱动的密码算法分析助手**
>
> 本项目是一款基于 LangChain + LangGraph 框架开发的智能分析工具，结合大语言模型（LLM）的逻辑推理能力与专业的密码学检测工具，为用户提供 S 盒性能评估、随机性检测及密码算法深度分析等功能。

---

## 核心特性

### S 盒安全性评估
集成专业工具集，可自动计算多种关键安全指标：

| 类别 | 指标 |
|------|------|
| **结构特性** | 置换阶(OP)、不动点(FP)、反不动点(OFP) |
| **扩散特性** | 差分均匀性(DU)、差分分支数(DBN)、线性分支数(LBN)、线性逼近概率(LAP)、非线性度(NL) |
| **密码准则** | 严格雪崩准则(SAC)、比特独立准则(BIC)、相关免疫性(CI)、传播特性(PC) |
| **代数攻击** | 代数免疫性(AI)、代数次数、透明阶(TO) |
| **侧信道攻击** | DPA-SNR、回旋均匀性(BU)、差分-线性均匀性(DLU)、无扰动比特密度(UBD) |
| **其他** | 线性结构检测、平方和指标(SSI)、线性近似表(LAT) |

### 随机性检测系统
基于 NIST SP800-22 及国标标准的随机性测试：

- 单比特频数检测 (Monobit Frequency Test)
- 游程总数检测 (Runs Test)
- 游程分布检测 (Runs Distribution Test)
- 扑克检测 (Poker Test)
- 重叠子序列检测 (Overlap Test)

### 智能对话系统
- 支持多模型切换（DeepSeek Chat / Qwen 3.6）
- 自动工具调用（网络搜索 + 本地计算工具）
- 对话持久化（SQLite 存储上下文）
- 流式响应 + Markdown 渲染

---

## 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                    前端 (HTML/CSS/JS)                   │
│  - 侧边栏会话管理  - 模型切换  - Markdown渲染            │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP/WebSocket
┌────────────────────▼────────────────────────────────────┐
│                 FastAPI Server (main.py)                │
│  - RESTful API  - 多模型路由  - 会话管理                │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│           LangGraph Agent (agent.py)                    │
│  - ReAct 推理  - 工具编排  - Checkpointer               │
└───────┬────────────────────┬─────────────────┬─────────┘
        │                    │                 │
   ┌────▼────┐        ┌─────▼─────┐    ┌──────▼──────┐
   │ Web     │        │  S盒      │    │ 随机性      │
   │ Search  │        │ Tools     │    │ Tools       │
   │ (Tavily)│        │ (22个)    │    │ (5个)       │
   └─────────┘        └───────────┘    └─────────────┘
```

---

## 环境配置

### 1. 环境要求
- **Python**: 3.12 或更高版本
- **依赖管理**: uv（项目已包含 pyproject.toml）

### 2. 克隆项目
```bash
git clone https://github.com/Lee-hyun-R/CryptoExpert-Pro.git
cd CryptoExpert-Pro
```

### 3. 配置环境变量
新建 `.env` 文件，参考以下内容：
```bash
# DeepSeek 配置
DEEPSEEK_API_KEY=your_deepseek_key
DEEPSEEK_BASE_URL=https://api.deepseek.com

# 通义千问配置
DASHSCOPE_API_KEY=your_qwen_key
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# 网络搜索配置
TAVILY_API_KEY=your_tavily_key

# 数据库路径（可选）
DB_PATH=resources/test.db
```

### 4. 安装依赖
```bash
# 使用 uv 安装
uv sync

# 或使用 pip
pip install -r pyproject.toml
```

### 5. 启动服务
```bash
# 创建数据目录
mkdir -p resources

# 启动服务
python main.py
# 访问 http://127.0.0.1:8000
```

### 6. Docker 部署
```bash
# 构建并运行
docker-compose up -d

# 停止服务
docker-compose down
```

---

## 项目结构

```
Agent_load/
├── main.py              # FastAPI 服务入口
├── agent.py             # LangGraph Agent 构建
├── clear_db.py          # 数据库清理工具
├── pyproject.toml       # 依赖配置
├── Dockerfile           # Docker 镜像配置
├── docker-compose.yml   # Docker Compose 配置
├── .env                 # 环境变量（需自行创建）
├── static/
│   └── index.html       # 前端页面
├── Tools/
│   ├── __init__.py
│   ├── randomness_tools.py    # 随机性检测工具 (5个)
│   ├── Sbox_tools_1.py        # S盒工具集1 (11个)
│   └── Sbox_tools_2.py        # S盒工具集2 (11个)
└── resources/
    └── test.db          # SQLite 数据库（自动创建）
```

---

## API 接口

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/` | 获取前端页面 |
| POST | `/api/chat/` | 发送聊天消息 |
| GET | `/api/history/{thread_id}` | 获取历史记录 |
| GET | `/api/models` | 获取可用模型列表 |
| DELETE | `/api/chat/{thread_id}` | 删除对话记录 |

---

## 使用示例

### S盒分析
用户可以发送 S 盒数据进行分析：
```
请分析这个S盒 [0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5, ...] 的安全性
```

### 随机性检测
发送二进制序列进行检测：
```
请检测这个序列 101100110101... 的随机性
```

---

## 依赖库

```
fastapi>=0.136.1
langchain>=1.2.15
langgraph>=1.1.9
langgraph-checkpoint-sqlite>=3.0.3
numpy>=2.4.4
scipy>=1.17.1
uvicorn>=0.46.0
python-dotenv>=1.2.2
```

---

