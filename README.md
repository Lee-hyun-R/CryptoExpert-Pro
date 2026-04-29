# <img src="static/logo.ico" width="32"> CryptoExpert Pro

> **AI 驱动的密码算法分析助手**
> 
> 本项目是一款基于 LangChain 框架开发的智能分析工具，旨在结合大语言模型（LLM）的逻辑推理能力与专业的密码学检测Tools，为用户提供 S 盒性能评估、随机性检测及密码算法深度拆解等功能。

---

## 🌟 核心特性

- **S 盒安全性评估**：集成专业工具集，可自动计算差分均匀性、线性近似概率、雪崩效应等关键安全指标。
- **随机性检测系统**：基于 NIST SP800-22 标准，支持单比特检测、扑克检测、游程检测等多种随机性测试方案。
- **智能工具调用**：Agent 会根据用户指令自动判断是否需要进行网络搜索或调用本地计算工具。
- **对话持久化**：使用 SQLite 存储对话上下文，确保分析过程可追溯、可续接。

---

## 🛠️ 环境准备

### 1. 软件要求
- **Python**: 3.10 或更高版本

### 2. 克隆项目
```bash
git clone https://github.com/Lee-hyun-R/CryptoExpert-Pro.git
cd CryptoExpert-Pro
```

### 3. 安装好第三方库
所需要的库在**pyproject.toml**里有展示
```bash
fastapi
jinja2
langchain
langchain-deepseek
langchain-openai
langchain-tavily
langgraph
langgraph-checkpoint-sqlite
numpy
python-dotenv
scipy
scipy-stubs
uvicorn
```

### 4. 配置API_KEY
新建.env文件，参考编辑以下内容（注意不用加双引号）
```bash
DASHSCOPE_API_KEY=xxx
DASHSCOPE_BASE_URL=xxx
DEEPSEEK_API_KEY=xxx
TAVILY_API_KEY=xxx
```
### 5. 启动
新建一个resources文件夹（用于存放对话历史）
```bash
python main.py
访问http://127.0.0.1:8000 
```


