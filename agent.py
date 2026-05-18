import logging
import os
from typing import Any

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.tools import BaseTool
from langchain_tavily import TavilyResearch
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.prebuilt import create_react_agent


load_dotenv()

logger = logging.getLogger(__name__)
from langchain.tools import tool
from Tools.randomness_tools import randomness_tools
from Tools.Sbox_tools_1 import Sbox_tools_1
from Tools.Sbox_tools_2 import Sbox_tools_2
from Tools.code_executor import execute_python


def create_crypto_agent(model_name: str, model_provider: str = "deepseek") -> Any:
    base_url = None
    api_key = None

    if model_provider == "deepseek":
        api_key = os.getenv("DEEPSEEK_API_KEY")
    elif model_provider in ("openai", "qwen"):
        base_url = os.getenv("DASHSCOPE_BASE_URL")
        api_key = os.getenv("DASHSCOPE_API_KEY")
    elif model_provider in ("kimi", "mimo"):
        model_provider = "openai"
        if model_name.startswith("kimi"):
            base_url = os.getenv("KIMI_BASE_URL", "https://api.moonshot.cn/v1")
            api_key = os.getenv("KIMI_API_KEY")
        elif model_name.startswith("mimo"):
            base_url = os.getenv("MIMO_BASE_URL", "https://api.xiaomimimo.com/v1")
            api_key = os.getenv("MIMO_API_KEY")

    if not api_key:
        raise ValueError(f"API key not found for provider: {model_provider}. Please check your .env file.")

    logger.info(f"Creating agent with model: {model_name}, provider: {model_provider}")

    temperature = 0.6 if model_name.startswith("kimi") else 0.5
    model_kwargs = {"temperature": temperature}
    if base_url and model_provider != "deepseek":
        model_kwargs["base_url"] = base_url
    model_kwargs["api_key"] = api_key

    if model_name.startswith("mimo"):
        model_kwargs["extra_body"] = {"enable_thinking": False}
    elif model_name.startswith("kimi"):
        model_kwargs["extra_body"] = {"thinking": {"type": "disabled"}}
    elif model_name.startswith("deepseek"):
        model_kwargs["extra_body"] = {"thinking": {"type": "disabled"}}

    model = init_chat_model(
        model=model_name,
        model_provider=model_provider,
        **model_kwargs
    )

    tavily = TavilyResearch(max_results=5, topic="general")

    @tool
    def web_search(query: str) -> str:
        """
        Web Search Tool, used to search online for relevant information.
        网络搜索工具，用于从网络搜索获取相关资料与参考信息。

        Args:
            query: Search keyword/query content
                   搜索关键词/查询内容
        Returns:
            Search result content
            搜索结果内容
        """
        return tavily.invoke(query)

    db_path = os.getenv("DB_PATH", "resources/test.db")
    db_dir = os.path.dirname(db_path) or "resources"
    os.makedirs(db_dir, exist_ok=True)

    import sqlite3
    conn = sqlite3.connect(db_path, check_same_thread=False)
    checkpointer = SqliteSaver(conn)

    system_prompt = """你是一个基于LangChain构建的专注于密码算法分析的专业智能体。

## 你的核心性格
你是一个**保守型助手**。你不会在用户需求不明确时直接执行分析，而是会主动询问细节，确保完全理解用户的需求后再行动。你的目标是通过与用户的对话，逐步了解用户的真实需求。

## 可用工具
- web_search: 网络搜索，用于获取加密算法资料、S盒数据等
- execute_python: 执行Python代码工具，用于运行用户的加密算法代码生成密文，然后对输出进行随机性检测
- S盒性能指标计算工具（集合1）: calculate_op（置换阶）, calculate_fp（不动点）, calculate_ofp（反不动点）, ifSAC（严格雪崩准则）, ifBIC（比特独立准则）, calculate_ai（代数免疫性）, calculate_ssi（平方和指标）, calcu_lat（线性近似表）, calculate_lap（线性逼近概率）, calculate_nl（非线性度）, calculate_lbn（线性分支数）
- S盒性能指标计算工具（集合2）: check_linear_structure（线性结构检测）, analyze_sbox_ci（相关免疫性）, calculate_du（差分均匀性）, calculate_dbn（差分分支数）, analyze_sbox_pc（传播特性）, calculate_ubd（无扰动比特密度）, calculate_bu（回旋均匀性）, calculate_dlu（差分-线性均匀性）, calculate_algebraic_degree（代数次数）, calculate_dpa_snr（DPA-SNR）, calculate_transparency_order（透明阶）
- 比特序列随机性检测工具: monobit_freq_test, runs_dist_test, runs_test, poker_test, overlap_test

注意：S盒值可以是十进制整数或十六进制字符串（如0xC），工具内部已做兼容处理，直接传入即可。

## 交互原则（必须严格遵守）

### 第一步：理解需求
当用户提出一个模糊的请求时（如"帮我分析AES"、"检测一下这个算法"等），你**必须**先询问细节，而不是直接执行。你需要了解：

1. **分析目标**：用户想要分析什么？是S盒安全性、随机性、还是其他？
2. **数据来源**：用户是否有自己的数据（S盒、密钥、明文等），还是需要你来生成？
3. **参数偏好**：工作模式、密钥长度、IV等参数是否有特定要求？
4. **分析范围**：用户想要全面分析还是只关注某些特定指标？

### 第二步：确认方案
在收集到足够信息后，向用户确认你的理解，例如：
"好的，我理解你想要...，我会使用...方式，你确认这样可以吗？"

### 第三步：执行分析
只有在用户确认后，才开始调用工具执行分析。

### 第四步：结果解读
分析完成后，用通俗易懂的语言解释结果含义，并询问用户是否需要进一步分析。

## 询问示例

当用户说"帮我分析AES"时，你应该回复类似：
"好的，我可以帮你分析AES算法。为了给你最合适的分析，我需要了解几个细节：

1. **分析类型**：你想要分析AES的S盒安全性，还是想要对AES加密后的密文进行随机性检测？
2. **数据来源**：
   - 如果是S盒分析：你有自己定义的S盒，还是使用AES标准S盒？
   - 如果是随机性检测：你有现成的密文数据，还是需要我生成？如果需要生成，明文和密钥是自动生成还是你来提供？
3. **参数设置**：
   - AES密钥长度：128位、192位还是256位？
   - 工作模式：ECB、CBC、CTR等？
   - 如果需要IV，是自动生成还是你来提供？
4. **分析范围**：想要全面分析还是只关注某些特定指标？

请告诉我你的需求，我会根据你的回答制定合适的分析方案。"

## 回复风格
- 使用中文回复
- 语气友好、专业
- 不要一次问太多问题，可以分批次询问
- 如果用户已经提供了部分信息，只需要询问缺失的部分
- 当用户明确表示"直接分析"、"你来决定"等，可以使用默认参数，但需要告知用户你将使用什么参数
"""

    agent_tools: list[BaseTool] = [web_search, execute_python] + randomness_tools + Sbox_tools_1 + Sbox_tools_2

    agent = create_react_agent(
        model=model,
        tools=agent_tools,
        prompt=system_prompt,
        checkpointer=checkpointer,
        debug=False,
    )
    logger.info(f"Agent created successfully with model: {model_name}")
    return agent


def init_crypto_agent() -> Any:
    model_name = os.getenv("MODEL_NAME", "deepseek-v4-flash")
    model_provider = os.getenv("MODEL_PROVIDER", "deepseek")
    return create_crypto_agent(model_name, model_provider)