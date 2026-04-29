import math
from langchain.tools import tool
import numpy as np

# ====================== S盒结构检测工具合集2 开始 ======================

@tool
def check_linear_structure(sbox: list[int | str], n: int = 4, m: int = 4):
    """
    S-box Linear Structure Detection.
    S盒线性结构检测，判断S盒是否存在线性结构。

    Args:
        sbox: S盒列表（支持十六进制/十进制）
        n: 输入比特数，默认4
        m: 输出比特数，默认4

    Returns:
        int: 1=存在线性结构，0=不存在
    """
    sbox = [int(x) for x in sbox]

    # 内部点积函数
    def dot_product(a, b, bits):
        result = 0
        for i in range(bits):
            if ((a >> i) & 1) and ((b >> i) & 1):
                result ^= 1
        return result

    # 内部计算LAT
    def compute_lat(sbox, n, m):
        input_size = 1 << n
        output_size = 1 << m
        lat = [[0] * output_size for _ in range(input_size)]
        for alpha in range(input_size):
            for beta in range(output_size):
                count = 0
                for x in range(input_size):
                    left = dot_product(alpha, x, n)
                    right = dot_product(beta, sbox[x], m)
                    if left == right:
                        count += 1
                lat[alpha][beta] = count - (input_size // 2)
        return lat

    # 内部判断线性结构
    def haveLS(lat, n, m):
        input_size = 1 << n
        output_size = 1 << m
        max_bias = input_size // 2
        for alpha in range(1, input_size):
            for beta in range(1, output_size):
                if abs(lat[alpha][beta]) == max_bias:
                    return 1
        return 0

    lat = compute_lat(sbox, n, m)
    return haveLS(lat, n, m)


@tool
def analyze_sbox_ci(sbox: list[int | str], n: int = 4, m: int = 4):
    """
    S-box Correlation Immunity Analysis.
    S盒相关免疫性分析，计算S盒的最小相关免疫阶数。

    Args:
        sbox: S盒列表（支持十六进制/十进制整数）
        n: 输入比特长度，默认4
        m: 输出比特长度，默认4

    Returns:
        int: S盒最小相关免疫阶数
    """
    # 转换为十进制
    sbox = [int(x) for x in sbox]

    # 汉明重量
    def hamming_weight(x, n_bits):
        weight = 0
        for i in range(n_bits):
            weight += (x >> i) & 1
        return weight

    # 点积
    def dot_product(a, b, bits):
        res = 0
        for i in range(bits):
            if ((a >> i) & 1) and ((b >> i) & 1):
                res ^= 1
        return res

    # Walsh 变换
    def walsh_transform(f, n_w):
        size = 1 << n_w
        walsh = [0.0] * size
        for omega in range(size):
            total = 0.0
            for x in range(size):
                exp = f[x] ^ dot_product(omega, x, n_w)
                total += 1.0 if exp == 0 else -1.0
            walsh[omega] = total
        return walsh

    # 计算相关免疫阶数
    def have_ci(walsh, n_c):
        max_imm = 0
        size = 1 << n_c
        for order in range(1, n_c + 1):
            immune = True
            for omega in range(1, size):
                hw = hamming_weight(omega, n_c)
                if 1 <= hw <= order and abs(walsh[omega]) > 1e-10:
                    immune = False
                    break
            if immune:
                max_imm = order
            else:
                break
        return max_imm

    # S盒转布尔函数
    def sbox_to_booleans(sb, n_s, m_s):
        funcs = []
        for i in range(m_s):
            f = []
            for x in sb:
                f.append((x >> i) & 1)
            funcs.append(f)
        return funcs

    # 主逻辑
    bool_funcs = sbox_to_booleans(sbox, n, m)
    ci_list = []
    for f in bool_funcs:
        w = walsh_transform(f, n)
        ci = have_ci(w, n)
        ci_list.append(ci)

    return min(ci_list)

@tool
def calculate_du(sbox: list[int | str], n: int = 4, m: int = 4):
    """
    S-box Differential Uniformity (DU) Calculation.
    S盒差分均匀性(DU)计算，用于评估S盒抵抗差分攻击的能力。

    Args:
        sbox: S盒列表（支持十六进制/十进制整数）
        n: 输入比特长度，默认4
        m: 输出比特长度，默认4

    Returns:
        int: 差分均匀性 DU 值
    """
    # 转换为十进制
    sbox = [int(x) for x in sbox]

    # 内部：计算差分分布表 DDT
    def haveddt(sbox, n, m):
        input_size = 1 << n
        output_size = 1 << m
        ddt = [[0] * output_size for _ in range(input_size)]
        for a in range(1, input_size):
            for x in range(input_size):
                x2 = x ^ a
                y1 = sbox[x]
                y2 = sbox[x2]
                b = y1 ^ y2
                ddt[a][b] += 1
        return ddt

    # 内部：计算差分均匀性 DU
    def havedu(ddt, n, m):
        input_size = 1 << n
        output_size = 1 << m
        max_du = 0
        for a in range(1, input_size):
            for b in range(output_size):
                if ddt[a][b] > max_du:
                    max_du = ddt[a][b]
        return max_du

    ddt = haveddt(sbox, n, m)
    du = havedu(ddt, n, m)
    return du

@tool
def calculate_dbn(sbox: list[int | str], n: int = 4, m: int = 4):
    """
    S-box Differential Branch Number (DBN) Calculation.
    S盒差分分支数(DBN)计算，用于评估S盒的差分扩散能力与安全性。

    Args:
        sbox: S盒列表（支持十六进制/十进制整数）
        n: 输入比特长度，默认4
        m: 输出比特长度，默认4

    Returns:
        int: S盒差分分支数 DBN 值
    """
    # 统一转换为十进制整数
    sbox = [int(x) for x in sbox]

    # 内部函数：计算汉明重量
    def hamming_weight(x, n_bits):
        weight = 0
        for i in range(n_bits):
            weight += (x >> i) & 1
        return weight

    input_size = 1 << n
    min_branch_number = float('inf')

    # 遍历所有非零输入差分
    for a in range(1, input_size):
        hw_input = hamming_weight(a, n)
        min_hw_output = float('inf')

        for x in range(input_size):
            x2 = x ^ a
            output_diff = sbox[x] ^ sbox[x2]
            hw_output = hamming_weight(output_diff, m)

            if hw_output < min_hw_output:
                min_hw_output = hw_output

        branch_number = hw_input + min_hw_output
        if branch_number < min_branch_number:
            min_branch_number = branch_number

    return min_branch_number

@tool
def analyze_sbox_pc(sbox: list[int | str], n: int = 4, m: int = 4):
    """
    S-box Propagation Characteristics (PC) Analysis.
    S盒传播特性(PC)分析，计算S盒最小传播特性阶数。

    Args:
        sbox: S盒列表（支持十六进制/十进制整数）
        n: 输入比特长度，默认4
        m: 输出比特长度，默认4

    Returns:
        int: S盒最小传播特性阶数
    """
    sbox = [int(x) for x in sbox]

    def hamming_weight(x: int) -> int:
        weight = 0
        while x:
            weight += x & 1
            x >>= 1
        return weight

    def autocorrelation(n: int, f: list[int], a: int) -> int:
        N = 1 << n
        sum_val = 0
        for x in range(N):
            x_xor_a = x ^ a
            fx = f[x]
            f_xor = f[x_xor_a]
            value = -1 if (fx ^ f_xor) else 1
            sum_val += value
        return sum_val

    def checkpc(n: int, f: list[int], k: int) -> bool:
        N = 1 << n
        for a in range(1, N):
            hw = hamming_weight(a)
            if hw <= k:
                r = autocorrelation(n, f, a)
                if r != 0:
                    return False
        return True

    def maxpc(n: int, f: list[int]) -> int:
        max_k = 0
        for k in range(1, n + 1):
            if checkpc(n, f, k):
                max_k = k
            else:
                break
        return max_k

    def sbox_to_boolean_functions(sbox, n, m):
        functions = []
        for i in range(m):
            f = []
            for x in sbox:
                f.append((x >> i) & 1)
            functions.append(f)
        return functions

    boolean_functions = sbox_to_boolean_functions(sbox, n, m)
    pc_values = []
    for f in boolean_functions:
        max_pc = maxpc(n, f)
        pc_values.append(max_pc)

    min_pc = min(pc_values)
    return min_pc

@tool
def calculate_ubd(sbox: list[int | str], n: int = 4, m: int = 4):
    """
    S-box Undisturbed Bit Density (UBD) Calculation.
    S盒无扰动比特密度(UBD)计算，用于评估S盒差分扰动特性与安全性。

    Args:
        sbox: S盒列表（支持十六进制/十进制整数）
        n: 输入比特长度，默认4
        m: 输出比特长度，默认4

    Returns:
        float: S盒无扰动比特密度 UBD 值
    """
    sbox = [int(x) for x in sbox]

    def hamming_weight(x, n_bits):
        weight = 0
        for i in range(n_bits):
            weight += (x >> i) & 1
        return weight

    def compute_ddt(sbox, n, m):
        input_size = 1 << n
        output_size = 1 << m
        ddt = [[0] * output_size for _ in range(input_size)]
        for a in range(1, input_size):
            for x in range(input_size):
                x2 = x ^ a
                y1 = sbox[x]
                y2 = sbox[x2]
                b = y1 ^ y2
                ddt[a][b] += 1
        return ddt

    def find_candidate_pairs(ddt, n, m):
        input_size = 1 << n
        output_size = 1 << m
        candidate_pairs = []
        for a in range(1, input_size):
            for b in range(output_size):
                if ddt[a][b] > 0:
                    candidate_pairs.append((a, b))
        return candidate_pairs

    def find_undisturbed_bits(sbox, n, m, a, b):
        input_size = 1 << n
        disturbed_bits = []
        undisturbed_bits = []
        x_list = []
        for x in range(input_size):
            x2 = x ^ a
            y1 = sbox[x]
            y2 = sbox[x2]
            if (y1 ^ y2) == b:
                x_list.append(x)
        if len(x_list) < 2:
            for i in range(m):
                undisturbed_bits.append(i)
            return disturbed_bits, undisturbed_bits
        for i in range(m):
            bits = []
            for x in x_list:
                y = sbox[x]
                bit = (y >> i) & 1
                bits.append(bit)
            if all(bit == bits[0] for bit in bits):
                undisturbed_bits.append(i)
            else:
                disturbed_bits.append(i)
        return disturbed_bits, undisturbed_bits

    ddt = compute_ddt(sbox, n, m)
    candidate_pairs = find_candidate_pairs(ddt, n, m)
    total_pairs = len(candidate_pairs)
    if total_pairs == 0:
        return 0.0
    total_undisturbed = 0
    for (a, b) in candidate_pairs:
        disturbed, undisturbed = find_undisturbed_bits(sbox, n, m, a, b)
        total_undisturbed += len(undisturbed)
    ubd = total_undisturbed / (total_pairs * m)
    return ubd

@tool
def calculate_bu(sbox: list[int | str], n: int = 4, m: int = 4):
    """
    S-box Boomerang Uniformity (BU) Calculation.
    S盒回旋均匀性(BU)计算，用于评估S盒抵抗回旋攻击的能力。

    Args:
        sbox: S盒列表（支持十六进制/十进制整数）
        n: 输入比特长度，默认4
        m: 输出比特长度，默认4

    Returns:
        int: S盒回旋均匀性 BU 值
    """
    sbox = [int(x) for x in sbox]

    def compute_bct(sbox, n, m):
        input_size = 1 << n
        output_size = 1 << m
        sbox_inv = [0] * input_size
        for i in range(input_size):
            sbox_inv[sbox[i]] = i

        bct = [[0] * output_size for _ in range(input_size)]
        for alpha in range(1, input_size):
            for beta in range(1, output_size):
                count = 0
                for x in range(input_size):
                    y = sbox[x]
                    x_prime = x ^ alpha
                    y_prime = sbox[x_prime]
                    y_double_prime = y ^ beta
                    x_double_prime = sbox_inv[y_double_prime]
                    x_triple_prime = x_double_prime ^ alpha
                    y_triple_prime = sbox[x_triple_prime]
                    if y_triple_prime == (y_prime ^ beta):
                        count += 1
                bct[alpha][beta] = count
        return bct

    bct = compute_bct(sbox, n, m)
    max_count = 0
    for row in bct:
        for count in row:
            if count > max_count:
                max_count = count
    return max_count

@tool
def calculate_dlu(sbox: list[int | str]) -> int:
    """
    S-box Differential-Linear Uniformity (DLU) Calculation.
    S盒差分-线性均匀性(DLU)计算，用于评估S盒抵抗差分-线性攻击的能力。

    Args:
        sbox: S盒列表（支持十六进制/十进制整数）

    Returns:
        int: S盒差分-线性均匀性 DLU 值
    """
    sbox = [int(x) for x in sbox]

    def dot_product(a, b):
        return bin(a & b).count('1') % 2

    n = len(sbox).bit_length() - 1
    size = 1 << n
    max_dlct = 0

    for delta in range(1, size):
        for lam in range(1, size):
            count = 0
            for x in range(size):
                s_x = sbox[x]
                s_xd = sbox[x ^ delta]
                if dot_product(s_x, lam) == dot_product(s_xd, lam):
                    count += 1
            dlct = count - (1 << (n - 1))
            abs_dlct = abs(dlct)
            if abs_dlct > max_dlct:
                max_dlct = abs_dlct

    return max_dlct


@tool
def calculate_algebraic_degree(sbox: list[int | str]) -> int:
    """
    S-box Algebraic Degree Calculation.
    S盒代数次数计算，用于评估S盒抵抗代数攻击的能力。

    Args:
        sbox: S盒列表（支持十六进制/十进制整数）

    Returns:
        int: S盒代数次数
    """
    sbox = [int(x) for x in sbox]

    def _compute_boolean_degree(f, n):
        mobius = [0] * (1 << n)
        for x in range(1 << n):
            mobius[x] = f(x)
            y = x
            while y > 0:
                y = (y - 1) & x
                mobius[x] ^= mobius[y]

        max_degree = 0
        for x in range(1 << n):
            if mobius[x] == 1:
                weight = bin(x).count('1')
                if weight > max_degree:
                    max_degree = weight
        return max_degree

    n = len(sbox).bit_length() - 1
    m = max(sbox).bit_length()
    max_degree = 0

    for bit in range(m):
        def boolean_function(x):
            return (sbox[x] >> bit) & 1

        degree = _compute_boolean_degree(boolean_function, n)
        if degree > max_degree:
            max_degree = degree

    return max_degree

@tool
def calculate_dpa_snr(sbox: list[int | str], key: int, num_traces: int = 1000, noise_std: float = 0.5) -> float:
    """
    S-box DPA Signal-to-Noise Ratio (SNR) Calculation.
    S盒差分功耗分析信噪比(DPA-SNR)计算，评估侧信道攻击抗性。

    Args:
        sbox: S盒列表（支持十六进制/十进制整数）
        key: 模拟密钥整数值
        num_traces: 模拟功耗轨迹数量，默认1000
        noise_std: 高斯噪声标准差，默认0.5

    Returns:
        float: DPA-SNR 值
    """
    # 统一转换为十进制
    sbox = [int(x) for x in sbox]

    # 内部：汉明重量
    def hamming_weight(x):
        return bin(x).count('1')

    n = len(sbox).bit_length() - 1
    inputs = np.random.randint(0, 1 << n, num_traces)
    hamming_weights = []

    for d in inputs:
        v = sbox[d ^ key]
        hw = hamming_weight(v)
        hamming_weights.append(hw)

    # 模拟功耗轨迹
    power_traces = np.array(hamming_weights) + np.random.normal(0, noise_std, num_traces)

    # 计算方差
    total_variance = np.var(power_traces)
    signal_variance = np.var(hamming_weights)
    noise_variance = total_variance - signal_variance

    if noise_variance <= 0:
        noise_variance = 1e-10

    snr = signal_variance / noise_variance
    return snr


@tool
def calculate_transparency_order(sbox: list[int | str]) -> float:
    """
    S-box Transparency Order Calculation.
    S盒透明阶计算，用于评估S盒抵抗侧信道攻击的能力。

    Args:
        sbox: S盒列表（支持十六进制/十进制整数）

    Returns:
        float: S盒透明阶值
    """
    sbox = [int(x) for x in sbox]

    def hamming_weight(x):
        return bin(x).count('1')

    def compute_walsh_for_bit(sbox, bit, n):
        walsh = [0] * (1 << n)
        for a in range(1 << n):
            s = 0
            for x in range(1 << n):
                s_x_bit = (sbox[x] >> bit) & 1
                dot = bin(a & x).count('1') % 2
                s += (-1) ** (s_x_bit ^ dot)
            walsh[a] = s
        return walsh

    n = len(sbox).bit_length() - 1
    m = max(sbox).bit_length()
    walsh_spectra = []

    for bit in range(m):
        walsh = compute_walsh_for_bit(sbox, bit, n)
        walsh_spectra.append(walsh)

    max_to = 0.0
    for beta in range(1 << m):
        hw_beta = hamming_weight(beta)
        term1 = abs(m - 2 * hw_beta)
        sum_a = 0

        for a in range(1 << n):
            sum_j = 0
            for j in range(m):
                sign = -1 if ((beta >> j) & 1) else 1
                sum_j += sign * walsh_spectra[j][a]
            sum_a += abs(sum_j)

        denominator = (1 << (2 * n)) - (1 << n)
        term2 = sum_a / denominator if denominator != 0 else 0.0
        to_value = term1 - term2

        if to_value > max_to:
            max_to = to_value

    return max_to

# ====================== S盒结构检测工具合集2 结束 ======================

Sbox_tools_2 = [
    check_linear_structure,
    analyze_sbox_ci,
    calculate_du,
    calculate_dbn,
    analyze_sbox_pc,
    calculate_ubd,
    calculate_bu,
    calculate_dlu,
    calculate_algebraic_degree,
    calculate_dpa_snr,
    calculate_transparency_order,
]