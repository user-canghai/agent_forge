import os
from datetime import datetime

MEMORY_FILE = "agent_memory.md"


def load_memory() -> str:
    if not os.path.exists(MEMORY_FILE):
        return ""
    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
    if len(lines) > 50:
        lines = lines[-50:]
        hint = "[... 历史记忆已被截断 ...]\n"
        return hint + "".join(lines)
    return "".join(lines)


def save_memory(task: str, result: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    short_result = result[:500] + ("..." if len(result) > 500 else "")
    content = f"\n---\n**时间**: {timestamp}\n**任务**: {task}\n**结果**: {short_result}\n"
    with open(MEMORY_FILE, "a", encoding="utf-8") as f:
        f.write(content)
