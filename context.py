from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from config import llm

COMPACT_THRESHOLD = 20
KEEP_RECENT = 6


def compact_messages(messages: list) -> list:
    if len(messages) <= COMPACT_THRESHOLD:
        return messages

    system_msg = messages[0]
    start = max(1, len(messages) - KEEP_RECENT)
    while start > 1 and isinstance(messages[start], ToolMessage):
        start -= 1
    recent_messages = messages[start:]
    old_messages = messages[1:start]
    old_text = "\n".join(
        [f"{m.type}: {m.content}" for m in old_messages if m.content]
    )

    try:
        summary_resp = llm.invoke(
            [
                HumanMessage(
                    content=(
                        "请总结以下对话历史的关键信息、做出的决定和进展，去除冗余细节:\n\n"
                        f"{old_text}\n\n总结:"
                    )
                )
            ]
        )
        summary = summary_resp.content
        return [
            system_msg,
            HumanMessage(content=f"[历史对话摘要]\n{summary}"),
            AIMessage(content="[已理解历史，继续当前任务]"),
        ] + recent_messages
    except Exception:
        return [system_msg] + messages[-(KEEP_RECENT + 2):]
