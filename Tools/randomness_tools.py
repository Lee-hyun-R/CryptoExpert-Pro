# 随机性检测工具集合

from scipy.special import gammaincc
import math
from langchain.tools import tool


# 1.单比特频数检测
@tool
def monobit_freq_test(seq: str | list, alpha: float = 0.01):
    """
    Monobit Frequency Test (NIST SP800-22), used to evaluate the uniformity of 0s and 1s distribution in binary sequences.
    单比特频数检测（NIST标准），判断二进制序列0和1分布是否均匀。

    Args:
        seq: Binary sequence under test (string of 0/1 or list of 0/1 integers)
             待检测的二进制序列（0/1组成的字符串 或 0/1整数列表）
        alpha: Significance level, default 0.01
               显著性水平，默认0.01（P值 >= alpha 则通过检测）

    Returns:
        tuple: (is_random: bool, P_value: float, Q_value: float)
            - is_random: Whether the sequence passes the randomness test
                         序列是否通过随机性检测（True=均匀随机）
            - P_value: Probability value for hypothesis test
                       假设检验P值（越大越均匀）
            - Q_value: Complementary probability value
                       互补概率值
    """
    # 统一转换为整数列表
    if isinstance(seq, str):
        seq = [int(bit) for bit in seq.strip()]

    n = len(seq)
    # 短序列不具备检测意义
    if n < 10:
        return False, 0.0, 0.0

    # 核心检测计算
    X = [2 * b - 1 for b in seq]
    S_n = sum(X)
    V = S_n / math.sqrt(n)
    P_value = math.erfc(abs(V) / math.sqrt(2))
    Q_value = 0.5 * math.erfc(V / math.sqrt(2))

    # 返回结果
    return P_value >= alpha, round(P_value, 4), round(Q_value, 4)

# 2.游程分布检测
@tool
def runs_dist_test(seq: str | list, alpha: float = 0.01):
    """
    Runs Distribution Test (NIST SP800-22), used to test whether the run-length distribution of binary sequence conforms to random characteristics.
    游程分布检测（NIST标准），检验二进制序列中游程长度分布是否符合随机特性。

    Args:
        seq: Binary sequence under test (string of 0/1 or list of 0/1 integers)
             待检测的二进制序列（0/1组成的字符串 或 0/1整数列表）
        alpha: Significance level, default 0.01
               显著性水平，默认0.01（P值 >= alpha 则通过检测）

    Returns:
        tuple: (is_random: bool, P_value: float, Q_value: float, k: int, total_runs: int,
                one_runs: list, zero_runs: list, exp_runs: list)
            - is_random: Whether the sequence passes the randomness test
                         序列是否通过随机性检测（True=符合随机游程分布）
            - P_value: Probability value for hypothesis test
                       假设检验P值（越大越符合随机分布）
            - Q_value: Complementary probability value
                       互补概率值
            - k: Maximum run length used in the test (e_i >= 5)
                 检测使用的最大游程长度（满足e_i >= 5）
            - total_runs: Total number of valid runs
                          有效游程总数
            - one_runs: Count of 1-runs for each length
                        各长度1游程的数量统计
            - zero_runs: Count of 0-runs for each length
                         各长度0游程的数量统计
            - exp_runs: Expected runs for each length
                        各长度的期望游程数
    """
    # 自动处理输入：如果是比特字符串，转成整数列表
    if isinstance(seq, str):
        seq = [int(bit) for bit in seq.strip()]

    n = len(seq)
    # 序列长度不足，无法检测
    if n < 2:
        print("序列长度不足，无法进行游程分布检测")
        return False, 0.0, 0.0, 0, 0, [], [], []

    # 第一步：计算 e_i 并确定 k
    # e_i = (n - i + 3) / 2^(i+2)，k 为满足 e_i >= 5 的最大正整数 i
    k = 0
    max_i = n  # i 不可能超过序列长度
    for i in range(1, max_i + 1):
        ei = (n - i + 3) / (2 ** (i + 2))
        if ei >= 5:
            k = i
        else:
            break  # 后面的 i 只会更小，无需继续
    # 无满足条件的k值，终止检测
    if k == 0:
        print("无满足 e_i >= 5 的 i，无法进行游程分布检测")
        return False, 0.0, 0.0, 0, 0, [], [], []

    # 第二步：遍历序列，统计所有游程（比特值 + 游程长度）
    runs = []
    cur_bit = seq[0]
    cur_len = 1
    for bit in seq[1:]:
        if bit == cur_bit:
            cur_len += 1
        else:
            runs.append((cur_bit, cur_len))
            cur_bit = bit
            cur_len = 1
    runs.append((cur_bit, cur_len))  # 加入最后一个游程

    # 第三步：统计1游程和0游程的长度分布
    # b_i: 长度为 i 的1游程数；g_i: 长度为 i 的0游程数（长度超过k的计入k）
    b = [0] * (k + 1)  # 索引从1到k
    g = [0] * (k + 1)
    for bit, length in runs:
        if length > k:
            length = k
        if bit == 1:
            b[length] += 1
        else:
            g[length] += 1

    # 第四步：计算总有效游程数
    T = sum(b[1:k + 1]) + sum(g[1:k + 1])
    if T == 0:
        print("无有效游程，无法进行游程分布检测")
        return False, 0.0, 0.0, k, T, b, g, []

    # 第五步：计算各长度游程的期望数量 e'_i
    e_prime = [0.0] * (k + 1)
    for i in range(1, k + 1):
        if i < k:
            e_prime[i] = T / (2 ** (i + 1))
        else:  # i == k，最长游程计算公式不同
            e_prime[i] = T / (2 ** i)

    # 第六步：计算卡方统计量 V
    V = 0.0
    for i in range(1, k + 1):
        ei = e_prime[i]
        if ei == 0:
            continue  # 避免除以0
        V += (b[i] - ei) ** 2 / ei
        V += (g[i] - ei) ** 2 / ei

    # 第七步：根据卡方分布计算P值（自由度 df = k-1）
    df = k - 1
    P_value = gammaincc(df, V / 2) if df > 0 else 1.0

    # 第八步：计算互补概率Q值
    Q_value = P_value

    # 返回最终检测结果
    return P_value >= alpha, round(P_value, 4), round(Q_value, 4), k, T, b, g, e_prime


# 3.游程总数检测
@tool
def runs_test(seq: str | list, alpha: float = 0.01):
    """
    Runs Test (NIST SP800-22), used to test whether the total number of runs in binary sequence conforms to random distribution characteristics.
    游程总数检测（NIST标准），检验二进制序列中游程总数是否符合随机分布特征。

    Args:
        seq: Binary sequence under test (string of 0/1 or list of 0/1 integers)
             待检测的二进制序列（0/1组成的字符串 或 0/1整数列表）
        alpha: Significance level, default 0.01
               显著性水平，默认0.01（P值 >= alpha 则通过检测）

    Returns:
        tuple: (is_random: bool, P_value: float, Q_value: float, total_runs: int, pi: float, V_stat: float)
            - is_random: Whether the sequence passes the randomness test
                         序列是否通过随机性检测（True=符合随机游程总数）
            - P_value: Probability value for hypothesis test
                       假设检验P值（越大越符合随机分布）
            - Q_value: Complementary probability value
                       互补概率值
            - total_runs: Observed total number of runs
                          观测到的游程总数
            - pi: Proportion of 1s in the sequence
                  序列中1的比例
            - V_stat: Normalized test statistic
                      归一化检验统计量
    """
    # 自动处理输入：如果是比特字符串，转成整数列表
    if isinstance(seq, str):
        seq = [int(bit) for bit in seq.strip()]

    n = len(seq)
    # 短序列不具备检测意义
    if n < 2:
        print("序列长度不足，无法进行游程总数检测")
        return False, 0.0, 0.0, 0, 0.0, 0.0

    # 第一步：计算观测游程总数 V_n(obs)
    # r(i) = 1 当 ε_i != ε_{i+1}，否则为0；V_n(obs) = Σr(i) + 1
    V_obs = 1
    for i in range(n - 1):
        if seq[i] != seq[i + 1]:
            V_obs += 1

    # 第二步：计算序列中1的比例 π
    pi = sum(seq) / n

    # 特殊情况：序列全0或全1，无随机性，直接不通过
    if pi == 0 or pi == 1:
        print("序列全为0或全为1，游程总数检测不通过")
        return False, 0.0, 0.0, V_obs, pi, 0.0

    # 第三步：计算归一化检验统计量 V
    numerator = V_obs - 2 * n * pi * (1 - pi)
    denominator = 2 * math.sqrt(n) * pi * (1 - pi)
    V = numerator / denominator

    # 第四步：计算P值（互补误差函数）
    P_value = math.erfc(abs(V) / math.sqrt(2))

    # 第五步：计算互补概率Q值
    Q_value = 0.5 * math.erfc(V / math.sqrt(2))

    # 返回最终检测结果
    return P_value >= alpha, round(P_value, 4), round(Q_value, 4), V_obs, round(pi, 4), round(V, 4)

# 4.扑克检测
@tool
def poker_test(seq: str | list, m: int = 4, alpha: float = 0.01):
    """
    Poker Test (NIST SP800-22), used to test whether the count of m-bit non-overlapping subsequence types is close to the expected random distribution.
    扑克检测（NIST标准），检测二进制序列中等长非重叠子序列的类型数量是否接近随机分布的期望。

    Args:
        seq: Binary sequence under test (string of 0/1 or list of 0/1 integers)
             待检测的二进制序列（0/1组成的字符串 或 0/1整数列表）
        m: Length of each m-bit subsequence (block size), default 4
           子序列分组长度（块大小），默认4
        alpha: Significance level, default 0.01
               显著性水平，默认0.01（P值 >= alpha 则通过检测）

    Returns:
        tuple: (is_random: bool, P_value: float, Q_value: float, V_stat: float, freq_dict: dict)
            - is_random: Whether the sequence passes the randomness test
                         序列是否通过随机性检测（True=符合随机分布）
            - P_value: Probability value for hypothesis test
                       假设检验P值（越大越均匀随机）
            - Q_value: Complementary probability value
                       互补概率值
            - V_stat: Poker test statistic (chi-square value)
                      扑克检测统计量（卡方值）
            - freq_dict: Frequency count of each m-bit subsequence pattern
                         各m比特子序列模式的频数统计字典
    """
    # 自动处理输入：如果是比特字符串，转成整数列表
    if isinstance(seq, str):
        seq = [int(bit) for bit in seq.strip()]

    n = len(seq)
    # 划分非重叠m比特子序列，N为有效子序列个数（向下取整，舍弃末尾不足m的比特）
    N = n // m
    # 子序列数量不足，不具备检测意义
    if N < 2:
        print("子序列数量N不足2，无法进行扑克检测")
        return False, 0.0, 0.0, 0.0, {}

    # 统计每个m-bit模式出现的频数 n_i
    cnt = {}
    for i in range(N):
        # 取出第i个长度为m的非重叠子序列
        subseq = seq[i * m: (i + 1) * m]
        # 将子序列转换为元组作为哈希键
        key = tuple(subseq)
        cnt[key] = cnt.get(key, 0) + 1

    # 计算卡方统计量 V = (2^m / N) * Σ(n_i^2) - N
    sum_n2 = sum(v ** 2 for v in cnt.values())
    V = ((2 ** m) / N) * sum_n2 - N

    # 计算P值：使用正则化上不完全伽马函数（对应NIST公式）
    k = (2 ** m - 1) / 2
    x = V / 2
    P_value = gammaincc(k, x)

    # 计算互补概率Q值
    Q_value = P_value

    # 返回最终检测结果（保留4位小数）
    return P_value >= alpha, round(P_value, 4), round(Q_value, 4), round(V, 4), cnt


# 5.重叠子序列检测
@tool
def overlap_test(seq: str | list, m: int = 2, alpha: float = 0.01):
    """
    Overlapping Subsequences Test (National Standard), used to test the distribution randomness of m-bit overlapping patterns in binary sequences.
    重叠子序列检测（国标标准），用于检测二进制序列中指定长度的重叠模板分布是否符合随机特性。

    Args:
        seq: Binary sequence under test (string of 0/1 or list of 0/1 integers)
             待检测的二进制序列（0/1组成的字符串 或 0/1整数列表）
        m: Length of overlapping template (block size), default 3
           重叠模板长度（块大小），默认3
        alpha: Significance level, default 0.01
               显著性水平，默认0.01（P值 >= alpha 则通过检测）

    Returns:
        tuple: (is_random: bool, P1_value: float, P2_value: float, Q1_value: float, Q2_value: float)
            - is_random: Whether the sequence passes the randomness test
                         序列是否通过随机性检测（需同时满足P1、P2 ≥ alpha）
            - P1_value: P-value for first-order difference test
                        一阶差分检验P值
            - P2_value: P-value for second-order difference test
                        二阶差分检验P值
            - Q1_value: Complementary probability for first-order difference
                        一阶差分互补概率值
            - Q2_value: Complementary probability for second-order difference
                        二阶差分互补概率值
    """
    # 自动处理输入：如果是比特字符串，转成整数列表
    if isinstance(seq, str):
        seq = [int(bit) for bit in seq.strip()]

    n = len(seq)
    # 序列长度小于模板长度，无法检测
    if n < m:
        print("序列长度不足，无法进行重叠子序列检测")
        return False, 0.0, 0.0, 0.0, 0.0

    # 第一步：构造循环扩展序列（解决末尾重叠边界问题）
    seq_ext = seq + seq[:m - 1]

    # 第二步：统计指定长度的所有重叠模式出现频数
    def count_pat(L):
        count = {}
        for i in range(n):
            pat = tuple(seq_ext[i:i + L])
            count[pat] = count.get(pat, 0) + 1
        return count

    # 分别统计 m、m-1、m-2 长度的重叠模式频数
    v_m = count_pat(m)
    v_m1 = count_pat(m - 1)
    v_m2 = count_pat(m - 2) if m >= 2 else {}

    # 第三步：计算卡方统计量 Ψ²
    def psi(cnt, L):
        s = sum(v * v for v in cnt.values())
        return ((2 ** L) / n) * s - n

    # 计算各长度对应的卡方值
    psi_m = psi(v_m, m)
    psi_m1 = psi(v_m1, m - 1)
    psi_m2 = psi(v_m2, m - 2) if m >= 2 else 0

    # 第四步：计算一阶、二阶差分（国标检测核心公式）
    grad1 = psi_m - psi_m1  # 一阶差分 ∇Ψ²
    grad2 = (psi_m - 2 * psi_m1 + psi_m2)  # 二阶差分 ∇²Ψ²

    # 第五步：计算对应自由度的P值（不完全伽马函数）
    df1 = 2 ** (m - 2)
    df2 = 2 ** (m - 3)
    P1 = gammaincc(df1, grad1 / 2)
    P2 = gammaincc(df2, grad2 / 2)

    # 互补概率值Q = P值
    Q1, Q2 = P1, P2
    # 需同时通过两个检验才算通过
    pass_test = (P1 >= alpha) and (P2 >= alpha)

    # 返回最终结果（保留4位小数，与其他检测函数格式统一）
    return pass_test, round(P1, 4), round(P2, 4), round(Q1, 4), round(Q2, 4)


randomness_tools = [
    monobit_freq_test,
    runs_dist_test,
    runs_test,
    poker_test,
    overlap_test
]