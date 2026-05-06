import subprocess
import tempfile
import os
from langchain.tools import tool


@tool
def execute_python(code: str, timeout: int = 30) -> str:
    """
    Execute Python code and return the output result.
    执行Python代码并返回输出结果。

    This tool is used to run user's encryption algorithm code to generate ciphertext,
    then perform randomness detection on the output.
    该工具用于运行用户的加密算法代码生成密文，然后对输出进行随机性检测。

    Args:
        code: Python code to execute
              需要执行的Python代码
        timeout: Maximum execution time in seconds, default 30
                 最大执行时间（秒），默认30

    Returns:
        str: Execution output including stdout, stderr, and execution status
             执行输出，包括 stdout、stderr 和执行状态
    """
    output_parts = []

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        f.write(code)
        temp_file = f.name

    try:
        result = subprocess.run(
            ['python', temp_file],
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding='utf-8'
        )

        output_parts.append("=== STDOUT ===")
        output_parts.append(result.stdout if result.stdout else "(empty)")

        if result.stderr:
            output_parts.append("\n=== STDERR ===")
            output_parts.append(result.stderr)

        output_parts.append(f"\n=== EXIT CODE ===")
        output_parts.append(str(result.returncode))

        return "\n".join(output_parts)

    except subprocess.TimeoutExpired:
        return f"Execution timeout: code exceeded {timeout} seconds"
    except FileNotFoundError:
        return "Error: Python interpreter not found. Please ensure Python is installed and in PATH."
    except Exception as e:
        return f"Execution error: {str(e)}"
    finally:
        if os.path.exists(temp_file):
            try:
                os.unlink(temp_file)
            except Exception:
                pass