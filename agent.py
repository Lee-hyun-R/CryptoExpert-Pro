import os
import sqlite3
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain.tools import tool
from langchain_tavily import TavilyResearch
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain.agents import create_agent
from langchain.messages import HumanMessage

load_dotenv()


#导入工具
from Tools.randomness_tools import randomness_tools
from Tools.Sbox_tools_1 import Sbox_tools_1
from Tools.Sbox_tools_2 import Sbox_tools_2

# 封装成初始化函数，方便 main.py 调用
def init_crypto_agent():
    model = init_chat_model(
        # model="qwen3.6-max-preview",
        # model_provider="openai",
        # base_url=os.getenv("DASHSCOPE_BASE_URL"),
        # api_key=os.getenv("DASHSCOPE_API_KEY"),
        model="deepseek-chat",
        temperature = 0.5,
    )

    tavily = TavilyResearch(
        max_results=5,
        topic="general",
    )

    # 搜索Tool
    @tool
    def web_search(query: str):
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

    # 确保数据库路径存在
    os.makedirs("resources", exist_ok=True)
    connection = sqlite3.connect("resources/test.db", check_same_thread=False)
    checkpointer = SqliteSaver(connection)
    checkpointer.setup()

    # 此处省略你原本的 system_promot (保持不变即可)
    system_prompt = """
你是一个专注于密码算法分析的专业智能体，基于LangChain框架实现，核心职责是对各类密码相关的问题进行全面、深入的拆解与分析，为用户提供精准、专业的技术分析报告。
你的分析需兼顾专业性、逻辑性和实用性，严格遵循密码学领域的标准术语和分析规范，确保输出内容严谨、可落地。
# 你主要完成以下工作：

## 1. 计算S盒的性能指标
    当用户要求计算某S盒的安全指标时，若用户已提供该S盒，调用与计算S盒性能指标相关的Tools进行计算分析；但如果只是简单的说，例如“请帮我分析AES-128算法的S盒”，先利用搜索工具得到目标S盒再进行计算分析。
    如果用户指明了计算某个指标，计算该指标后进行分析；没有指明的话，先告诉用户，我目前能计算哪些指标，等待用户指出计算什么指标后再调用Tools进行计算分析。

## 2. 对比特序列进行随机性检测
    当用户要求对某比特序列进行随机性检测时，利用与随机性检测相关的Tools，根据计算结果进行分析。
    如果用户指明了使用某方法进行检测，如果有对应的Tools，就用对应的Tools进行计算；而如果没有相关的Tools，可以利用搜索工具进行搜索后得出结果，但是需要说明该结果不是计算得来的，并表明出处。

请积极调用各种Tools，尤其是当用户说想要检测某些指标时，先看一下有没有Tools是专门用于计算需求的指标的，如有对应的Tools务必调用，并结合计算结果进行分析，而如果没有对应的Tools，请上网查阅相关资源，结合搜索结果进行总结，可以适当自由发挥。

## 注意：如果调用了某些工具，需要向用户说一下此次分析调用了哪些Tools。
请始终以“专业、严谨、高效”为原则，完成密码算法的分析工作，确保输出内容符合用户需求，适配LangChain智能体的运行逻辑，助力用户快速掌握密码算法的核心特性与安全状况。
    """

    agent_tools = [] + randomness_tools + Sbox_tools_1 + Sbox_tools_2

    agent = create_agent(
        model=model,
        tools=agent_tools,
        system_prompt=system_prompt,
        checkpointer=checkpointer,
    )
    return agent