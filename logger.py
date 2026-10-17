import os
from datetime import datetime

TRACE_DIR = "traces"


def save_trace_to_md(task: str, messages: list) -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_task = "".join(
        [c for c in task if c.isalnum() or c in (" ", "-", "_")]
    ).rstrip()
    safe_task = safe_task.replace(" ", "_")[:50] if safe_task else "task"
    filename = os.path.join(TRACE_DIR, f"{timestamp}_{safe_task}.md")
    os.makedirs(TRACE_DIR, exist_ok=True)

    with open(filename, "w", encoding="utf-8") as f:
        f.write("# 任务执行轨迹\n\n")
        f.write(f"**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**任务**: {task}\n\n---\n\n")
        for msg in messages:
            role = getattr(msg, "type", "unknown").upper()
            content = getattr(msg, "content", "")
            f.write(f"## [{role}]\n\n")
            if content:
                f.write(f"```\n{content}\n```\n\n")
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                f.write("**Tool Calls:**\n")
                for tc in msg.tool_calls:
                    f.write(
                        f"- 调用工具: `{tc.get('name', '')}`\n"
                        f"  参数: `{tc.get('args', {})}`\n"
                    )
                f.write("\n")

    print(f"完整运行轨迹已保存至: {filename}")
    return filename
