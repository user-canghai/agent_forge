import re
import sys
from typing import Optional, Tuple

import config

MAX_OUTPUT_LENGTH = 5000

DANGEROUS_PATTERNS = [
    r"\brm\s+-rf\s+/(\s|;|&|\||$)",
    r"\brm\s+-rf\s+/\*",
    r"\brm\s+-rf\s+\*",
    r"\bmkfs\b",
    r"\bdd\s+.*of=/dev/",
    r"\bchmod\s+-R\s+777\s+/",
    r"\bcurl\s+[^|]*\|\s*(ba)?sh\b",
    r"\bwget\s+[^|]*\|\s*(ba)?sh\b",
]


def is_dangerous(command: str) -> Tuple[bool, Optional[str]]:
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, pattern
    return False, None


def ask_user_confirmation(tool_name: str, args: dict) -> bool:
    if config.AUTO_APPROVE:
        return True
    print(f"\n即将执行工具: {tool_name}")
    args_str = str(args)
    if len(args_str) > 200:
        args_str = args_str[:200] + "..."
    print(f"参数: {args_str}")
    while True:
        try:
            choice = input("是否允许执行？[Y/N/Q]: ").strip().lower()
        except EOFError:
            return False
        if choice == "y":
            return True
        if choice == "n":
            return False
        if choice == "q":
            print("用户主动终止程序。")
            sys.exit(0)
        print("请输入 Y、N 或 Q。")


def truncate_output(text: str) -> str:
    if len(text) <= MAX_OUTPUT_LENGTH:
        return text
    keep_len = MAX_OUTPUT_LENGTH // 2
    return (
        text[:keep_len]
        + f"\n\n[... 输出已截断，总长度 {len(text)} ...]\n\n"
        + text[-keep_len:]
    )


def execute_tool_with_hooks(tool_instance, tool_args: dict) -> str:
    tool_name = tool_instance.name

    if tool_name == "bash":
        cmd = tool_args.get("command", "")
        dangerous, pattern = is_dangerous(cmd)
        if dangerous:
            return f"安全拦截：命令匹配到危险模式 '{pattern}'，执行已中止。"

    if tool_name in ["bash", "edit"]:
        if not ask_user_confirmation(tool_name, tool_args):
            return f"用户拒绝执行工具 {tool_name}。"

    try:
        result = tool_instance.invoke(tool_args)
    except Exception as e:
        return f"工具执行出错: {type(e).__name__} - {str(e)}"

    return truncate_output(str(result))
