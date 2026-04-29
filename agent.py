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

def create_crypto_agent(model_name: str, model_provider: str = "deepseek") -> Any:
    base_url = None
    api_key = None

    if model_provider == "deepseek":
        api_key = os.getenv("DEEPSEEK_API_KEY")
    elif model_provider in ("openai", "qwen"):
        base_url = os.getenv("DASHSCOPE_BASE_URL")
        api_key = os.getenv("DASHSCOPE_API_KEY")

    if not api_key:
        raise ValueError(f"API key not found for provider: {model_provider}. Please check your .env file.")

    logger.info(f"Creating agent with model: {model_name}, provider: {model_provider}")

    model_kwargs = {"temperature": 0.5}
    if base_url:
        model_kwargs["base_url"] = base_url
    model_kwargs["api_key"] = api_key

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

    system_prompt = """
你是一个基于LangChain构建的专注于密码算法分析的专业智能体。

## 可用工具
- web_search: 网络搜索，用于获取加密算法资料、S盒数据等
- S盒性能指标计算工具: calculate_op, calculate_fp, calculate_dap, calculate_lap, calculate_sac, calculate_nonlinearity, calculate_resilience, calculate_bic, calculate_bic_sac, calculate_auto_correlation, calculate_maximum_dependence, calculate_maximum_diffusion
- 比特序列随机性检测工具: monobit_test, chi_square_test, runs_test, longest_run_test, serial_test, approximate_entropy_test, cumulative_sums_test, binary_derivative_test

## 工作流程
1. 若用户提供了具体的S盒或比特序列，直接调用对应工具计算
2. 若用户只说了算法名称（如"AES-128"），先用web_search获取相关参数，再进行计算
3. 若没有对应的工具可用，直接使用web_search搜索并标注信息来源

## 回复要求
1. 先展示工具计算结果（包含原始数值）
2. 用通俗语言解释结果含义
3. 明确标注使用了哪些工具，调用了哪些Tools
4. 如需进一步分析，主动询问用户
5. 若工具调用失败，说明原因并尝试搜索替代

## 注意
若用户未明确指定要计算哪个指标，先告知用户你能计算哪些指标，等待用户选择。
"""

    agent_tools: list[BaseTool] = [web_search] + randomness_tools + Sbox_tools_1 + Sbox_tools_2

    agent = create_react_agent(
        model=model,
        tools=agent_tools,
        prompt=system_prompt,
        checkpointer=checkpointer,
    )
    logger.info(f"Agent created successfully with model: {model_name}")
    return agent


def init_crypto_agent() -> Any:
    model_name = os.getenv("MODEL_NAME", "deepseek-chat")
    model_provider = os.getenv("MODEL_PROVIDER", "deepseek")
    return create_crypto_agent(model_name, model_provider)