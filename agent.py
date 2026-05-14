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
    if base_url:
        model_kwargs["base_url"] = base_url
    model_kwargs["api_key"] = api_key

    if model_name.startswith("mimo"):
        model_kwargs["extra_body"] = {"enable_thinking": False}
    elif model_name.startswith("kimi"):
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

## 可用工具
- web_search: 网络搜索，用于获取加密算法资料、S盒数据等
- execute_python: 执行Python代码工具，用于运行用户的加密算法代码生成密文，然后对输出进行随机性检测
- S盒性能指标计算工具（集合1）: calculate_op（置换阶）, calculate_fp（不动点）, calculate_ofp（反不动点）, ifSAC（严格雪崩准则）, ifBIC（比特独立准则）, calculate_ai（代数免疫性）, calculate_ssi（平方和指标）, calcu_lat（线性近似表）, calculate_lap（线性逼近概率）, calculate_nl（非线性度）, calculate_lbn（线性分支数）
- S盒性能指标计算工具（集合2）: check_linear_structure（线性结构检测）, analyze_sbox_ci（相关免疫性）, calculate_du（差分均匀性）, calculate_dbn（差分分支数）, analyze_sbox_pc（传播特性）, calculate_ubd（无扰动比特密度）, calculate_bu（回旋均匀性）, calculate_dlu（差分-线性均匀性）, calculate_algebraic_degree（代数次数）, calculate_dpa_snr（DPA-SNR）, calculate_transparency_order（透明阶）
- 比特序列随机性检测工具: monobit_freq_test, runs_dist_test, runs_test, poker_test, overlap_test

注意：S盒值可以是十进制整数或十六进制字符串（如0xC），工具内部已做兼容处理，直接传入即可。

## 工作流程（必须严格按顺序执行）
1. 若用户提供了具体的S盒或比特序列，直接调用对应工具计算
2. 若用户提供了加密算法代码（如AES、DES等），使用execute_python执行代码获取密文输出
3. **【关键】获得密文输出后，必须依次调用以下随机性检测工具进行分析：**
   - monobit_freq_test（单比特频数检测）
   - runs_test（游程总数检测）
   - poker_test（扑克检测）
   - overlap_test（重叠子序列检测）
   - runs_dist_test（游程分布检测）
4. 若用户只说了算法名称（如"AES-128"）但没有提供代码：
   - 编写一个生成AES密文的Python代码
   - 使用execute_python执行代码生成密文
   - **必须调用随机性检测工具进行分析**
5. 若没有对应的工具可用，直接使用web_search搜索并标注信息来源

## 回复要求（按以下顺序输出）
1. **先展示各类加密时使用的参数（如果存在的话，例如工作模式、IV、明文、密钥等）、密文/序列**
2. **展示工具计算结果**：展示每个随机性检测的详细结果（包含原始数值）
3. **用通俗语言解释结果含义**
4. **明确标注使用了哪些工具**
5. **给出最终结论**
6. 询问用户是否需要改变传入的各种参数，然后再对其进行加密模拟，对新得到的密文进行随机性检测
7. 若工具调用失败，说明原因并尝试搜索替代

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
    model_name = os.getenv("MODEL_NAME", "deepseek-chat")
    model_provider = os.getenv("MODEL_PROVIDER", "deepseek")
    return create_crypto_agent(model_name, model_provider)