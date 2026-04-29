import math
from langchain.tools import tool

# ====================== S盒结构检测工具合集1 开始 ======================

@tool
def calculate_op(S_box: list[int | str], length: int = 16):
    """
    S-box Permutation Order (OP) Calculation.
    S盒置换阶(OP)计算，评估S盒置换代数结构特性。

    Args:
        S_box: 待检测S盒列表，支持十六进制0x格式/十进制整数
        length: S盒长度，4比特S盒默认16

    Returns:
        int: S盒置换阶数值
    """
    S_box = [int(x) for x in S_box]

    def gcd(a, b):
        while b != 0:
            a, b = b, a % b
        return a

    def lcm(a, b):
        return a * b // gcd(a, b)

    cycle_lengths = []
    for i in range(length):
        temp = 1
        t = i
        while S_box[t] != i:
            temp += 1
            t = S_box[t]
        cycle_lengths.append(temp)

    result = cycle_lengths[0]
    for cl in cycle_lengths[1:]:
        result = lcm(result, cl)
    return result


@tool
def calculate_fp(s_box: list[int | str], length: int = 16):
    """
    S-box Fixed Point (FP) Calculation.
    S盒不动点(FP)计算，统计满足 s_box[i] = i 的节点数量。

    Args:
        s_box: 待检测S盒列表，支持十六进制0x格式/十进制整数
        length: S盒长度，4比特S盒默认16

    Returns:
        int: S盒不动点数量
    """
    s_box = [int(x) for x in s_box]
    count = 0
    for i in range(length):
        if s_box[i] == i:
            count += 1
    return count


@tool
def calculate_ofp(s_box: list[int | str], length: int = 16):
    """
    S-box Opposite Fixed Point (OFP) Calculation.
    S盒反不动点(OFP)计算，统计按位取反相等的节点数量。

    Args:
        s_box: 待检测S盒列表，支持十六进制0x格式/十进制整数
        length: S盒长度，4比特S盒默认16

    Returns:
        int: S盒反不动点数量
    """
    s_box = [int(x) for x in s_box]
    count = 0
    mask = length - 1
    for i in range(length):
        if s_box[i] == (~i & mask):
            count += 1
    return count


@tool
def ifSAC(S: list[int | str], inputlen: int = 4, outputlen: int = 4):
    """
    S-box Strict Avalanche Criterion (SAC) Test.
    S盒严格雪崩准则(SAC)检测，输入单比特翻转时输出比特变化概率趋近0.5。

    Args:
        S: 待检测S盒列表，支持十六进制0x格式/十进制整数
        inputlen: S盒输入比特长度，默认4
        outputlen: S盒输出比特长度，默认4

    Returns:
        dict: 包含是否通过、检测说明、异常概率
    """
    S = [int(x) for x in S]
    n = 2 ** inputlen
    initial = 2 ** (inputlen - 1)

    for u in range(inputlen):
        diff = initial >> u
        count = [0] * outputlen
        for input_val in range(n):
            result = S[input_val] ^ S[input_val ^ diff]
            temp = 1
            for i in range(outputlen - 1, -1, -1):
                if temp & result:
                    count[i] += 1
                temp <<= 1
        for i in range(outputlen):
            probability = count[i] / n
            if abs(probability - 0.5) > 1e-6:
                return {
                    "pass_sac": False,
                    "message": "该S盒不满足严格雪崩准则(SAC)",
                    "bit_info": f"输入第{u+1}位变化，输出第{i+1}位翻转概率异常",
                    "probability": round(probability, 4)
                }
    return {
        "pass_sac": True,
        "message": "该S盒满足严格雪崩准则(SAC)",
        "bit_info": "全部输出比特符合SAC要求",
        "probability": 0.5
    }


@tool
def ifBIC(S: list[int | str], inputlen: int = 4, outputlen: int = 4):
    """
    S-box Bit Independence Criterion (BIC) Test.
    S盒比特独立准则(BIC)检测，检验输出比特之间的相互独立性。

    Args:
        S: 待检测S盒列表，支持十六进制0x格式/十进制整数
        inputlen: S盒输入比特长度，默认4
        outputlen: S盒输出比特长度，默认4

    Returns:
        dict: 包含是否通过、相关系数、异常说明
    """
    S = [int(x) for x in S]
    inputsum = 2 ** inputlen
    initial = 2 ** (inputlen - 1)

    for u in range(inputlen):
        diff = initial >> u
        difference = [0] * inputsum
        for input_val in range(inputsum):
            difference[input_val] = S[input_val] ^ S[input_val ^ diff]
        for i in range(outputlen):
            temp1 = 1 << i
            for j in range(i + 1, outputlen):
                temp2 = 1 << j
                counti = countj = countij = 0
                for z in range(inputsum):
                    if difference[z] & temp1:
                        counti += 1
                    if difference[z] & temp2:
                        countj += 1
                    if (difference[z] & temp1) and (difference[z] & temp2):
                        countij += 1
                Ei = counti / inputsum
                Ej = countj / inputsum
                Eij = countij / inputsum
                cov = Eij - (Ei * Ej)
                if abs(cov) < 1e-5:
                    continue
                Di = math.sqrt(Ei * (1.0 - Ei)) if Ei * (1 - Ei) > 0 else 0.0
                Dj = math.sqrt(Ej * (1.0 - Ej)) if Ej * (1 - Ej) > 0 else 0.0
                if Di < 1e-8 or Dj < 1e-8:
                    continue
                p = cov / (Di * Dj)
                if not (abs(p) < 1e-5):
                    return {
                        "pass_bic": False,
                        "message": "该S盒不满足比特独立准则(BIC)",
                        "correlation": round(p, 6)
                    }
    return {
        "pass_bic": True,
        "message": "该S盒满足比特独立准则(BIC)",
        "correlation": 0.0
    }


@tool
def calculate_ai(S: list[int | str], inputlen: int = 4, outputlen: int = 4):
    """
    S-box Algebraic Immunity (AI) Calculation.
    S盒代数免疫性(AI)计算，评估抵抗代数攻击的能力。

    Args:
        S: 待检测S盒列表，支持十六进制0x格式/十进制整数
        inputlen: S盒输入比特长度，默认4
        outputlen: S盒输出比特长度，默认4

    Returns:
        int: 代数免疫性最大绝对值和指标
    """
    S = [int(x) for x in S]
    inputsum = 2 ** inputlen
    outputsum = 2 ** outputlen
    aimax = 0

    for r in range(inputsum):
        for p in range(outputsum):
            sum_val = 0
            for input_val in range(inputsum):
                result = S[input_val] ^ S[input_val ^ r]
                temp = p & result
                index = 0
                mask = 1 << (outputlen - 1)
                while mask > 0:
                    if mask & temp:
                        index ^= 1
                    mask >>= 1
                sum_val += 1 if index else -1
            abs_sum = abs(sum_val)
            if abs_sum > aimax:
                aimax = abs_sum
    return aimax


@tool
def calculate_ssi(S: list[int | str], inputlen: int = 4, outputlen: int = 4):
    """
    S-box Sum of Squares Indicator (SSI) Calculation.
    S盒平方和指标(SSI)计算，反映差分均匀性与密码扩散性能。

    Args:
        S: 待检测S盒列表，支持十六进制0x格式/十进制整数
        inputlen: S盒输入比特长度，默认4
        outputlen: S盒输出比特长度，默认4

    Returns:
        int: 平方和指标SSI数值
    """
    S = [int(x) for x in S]
    inputsum = 2 ** inputlen
    outputsum = 2 ** outputlen
    aimax = 0

    for r in range(inputsum):
        for p in range(outputsum):
            sum_val = 0
            for input_val in range(inputsum):
                result = S[input_val] ^ S[input_val ^ r]
                temp = p & result
                index = 0
                mask = 1 << (outputlen - 1)
                while mask > 0:
                    if mask & temp:
                        index ^= 1
                    mask >>= 1
                sum_val += 1 if index else -1
            aimax += sum_val * sum_val
    return aimax


@tool
def calcu_lat(s_box: list[int | str], input_len: int = 4, output_len: int = 4):
    """
    S-box Linear Approximation Table (LAT) Calculation.
    S盒线性近似表(LAT)计算，用于分析S盒线性密码特性。

    Args:
        s_box: 待检测S盒列表，支持十六进制0x格式/十进制整数
        input_len: 输入比特长度，默认4
        output_len: 输出比特长度，默认4

    Returns:
        list[list[int]]: 线性近似表二维数组
    """
    s_box = [int(x) for x in s_box]

    def inner(a, b, length):
        result = a & b
        sum_val = 0
        temp = 1 << (length - 1)
        while temp > 0:
            if temp & result:
                sum_val ^= 1
            temp >>= 1
        return sum_val

    input_sum = 1 << input_len
    output_sum = 1 << output_len
    lat = [[0] * output_sum for _ in range(input_sum)]
    for p in range(input_sum):
        for f in range(output_sum):
            count = 0
            for i in range(input_sum):
                if inner(p, i, input_len) == inner(f, s_box[i], output_len):
                    count += 1
            lat[p][f] = count - (input_sum // 2)
    return lat


@tool
def calculate_lap(s_box: list[int | str], input_len: int = 4, output_len: int = 4):
    """
    S-box Linear Approximation Probability (LAP) Calculation.
    S盒线性逼近概率(LAP)计算，衡量线性攻击抵抗能力。

    Args:
        s_box: 待检测S盒列表，支持十六进制0x格式/十进制整数
        input_len: 输入比特长度，默认4
        output_len: 输出比特长度，默认4

    Returns:
        float: 最大线性逼近概率
    """
    s_box = [int(x) for x in s_box]

    def inner(a, b, length):
        result = a & b
        sum_val = 0
        temp = 1 << (length - 1)
        while temp > 0:
            if temp & result:
                sum_val ^= 1
            temp >>= 1
        return sum_val

    input_sum = 2 ** input_len
    output_sum = 2 ** output_len
    max_val = 0
    for p in range(1, input_sum):
        for f in range(output_sum):
            count = 0
            for i in range(input_sum):
                if inner(p, i, input_len) == inner(f, s_box[i], output_len):
                    count += 1
            if count > max_val:
                max_val = count
    lap = abs(max_val / input_sum)
    return lap


@tool
def calculate_nl(s_box: list[int | str], input_len: int = 4, output_len: int = 4):
    """
    S-box Nonlinearity (NL) Calculation.
    S盒非线性度(NL)计算，核心安全指标，抵御线性攻击。

    Args:
        s_box: 待检测S盒列表，支持十六进制0x格式/十进制整数
        input_len: 输入比特长度，默认4
        output_len: 输出比特长度，默认4

    Returns:
        int: S盒非线性度数值
    """
    s_box = [int(x) for x in s_box]

    def inner(a, b, length):
        result = a & b
        sum_val = 0
        temp = 1 << (length - 1)
        while temp > 0:
            if temp & result:
                sum_val ^= 1
            temp >>= 1
        return sum_val

    input_sum = 1 << input_len
    output_sum = 1 << output_len
    max_val = 0
    for p in range(1, input_sum):
        for r in range(output_sum):
            nl = 0
            for i in range(input_sum):
                if not (inner(p, i, input_len) ^ inner(r, s_box[i], output_len)):
                    nl += 1
                else:
                    nl -= 1
            if nl > max_val:
                max_val = nl
    result = (1 << (input_len - 1)) - 0.5 * abs(max_val)
    return int(result)


@tool
def calculate_lbn(s_box: list[int | str], input_length: int = 4, output_length: int = 4):
    """
    S-box Linear Branch Number (LBN) Calculation.
    S盒线性分支数(LBN)计算，表征密码扩散与混淆能力。

    Args:
        s_box: 待检测S盒列表，支持十六进制0x格式/十进制整数
        input_length: 输入比特长度，默认4
        output_length: 输出比特长度，默认4

    Returns:
        int: S盒线性分支数
    """
    s_box = [int(x) for x in s_box]

    def calculate_weight(goal, length):
        temp = 2 ** (length - 1)
        res = 0
        while temp > 0:
            if temp & goal:
                res += 1
            temp >>= 1
        return res

    input_sum = 2 ** input_length
    lbn = 128
    for i in range(1, input_sum):
        w_i = calculate_weight(i, input_length)
        w_s = calculate_weight(s_box[i], output_length)
        lbn = min(lbn, w_i + w_s)
    return lbn

# ====================== S盒结构检测工具合集1 结束 ======================

Sbox_tools_1 = [
    calculate_op,
    calculate_fp,
    calculate_ofp,
    ifSAC,
    ifBIC,
    calculate_ai,
    calculate_ssi,
    calcu_lat,
    calculate_lap,
    calculate_nl,
    calculate_lbn
]