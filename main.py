import json
import sys

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

import config
from config import llm, team_llm
from graph import build_graph
from logger import save_trace_to_md
from memory import load_memory, save_memory
from prompt import build_system_prompt


def stream_graph(graph, inputs):
    last_len = len(inputs.get("messages", []))
    final_messages = inputs["messages"]

    for event in graph.stream(inputs, stream_mode="values"):
        current_msgs = event.get("messages", [])
        final_messages = current_msgs
        if len(current_msgs) > last_len:
            new_msg = current_msgs[-1]
            last_len = len(current_msgs)
            if isinstance(new_msg, AIMessage):
                if new_msg.content:
                    print(f"\n[Agent 思考]:\n{new_msg.content}")
                if hasattr(new_msg, "tool_calls") and new_msg.tool_calls:
                    for tc in new_msg.tool_calls:
                        print(f"\n[Agent 决定调用工具]: {tc['name']}")
                        print(f"   参数: {tc['args']}")
            elif isinstance(new_msg, ToolMessage):
                content = str(new_msg.content)
                display_content = content[:300] + (
                    "..." if len(content) > 300 else ""
                )
                print(f"\n[工具执行结果]:\n{display_content}")
    return final_messages


class Agent:
    def __init__(self, name, role, max_iters=30):
        self.name = name
        self.role = role
        self.inbox = []
        self.graph = build_graph(team_llm, max_loops=max_iters)

    def receive(self, sender, message):
        self.inbox.append(f"[来自 {sender}]: {message}")

    def chat(self, task):
        messages = [SystemMessage(content=self.role)]
        if self.inbox:
            messages.append(
                HumanMessage(content="请先阅读以下消息：\n" + "\n".join(self.inbox))
            )
            self.inbox = []
        messages.append(HumanMessage(content=task))
        inputs = {"messages": messages}
        final_messages = stream_graph(self.graph, inputs)
        return str(final_messages[-1].content), final_messages


class Team:
    def __init__(self):
        self.agents = {}

    def hire(self, name, role):
        self.agents[name] = Agent(name, role)

    def broadcast(self, from_name, message):
        for name, agent in self.agents.items():
            if name != from_name:
                agent.receive(from_name, message)


def _extract_json(text):
    if not isinstance(text, str):
        text = str(text)
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("未找到 JSON 对象")
    return json.loads(text[start : end + 1])


def _load_team_plan(content):
    plan = _extract_json(content)
    team_config = plan.get("team")
    if not isinstance(team_config, list) or not team_config:
        raise ValueError("团队配置为空")
    normalized = []
    for member in team_config:
        name = str(member.get("name", "")).strip()
        role = str(member.get("role", "")).strip()
        task = str(member.get("task", "")).strip()
        if not name or not role or not task:
            raise ValueError("团队成员配置不完整")
        normalized.append({"name": name, "role": role, "task": task})
    return normalized


def run_single(task):
    memory = load_memory()
    system_prompt = build_system_prompt(memory)
    graph = build_graph(llm, max_loops=10)
    init_msgs = [SystemMessage(content=system_prompt), HumanMessage(content=task)]

    print("\n开始执行单 Agent 任务...\n" + "=" * 40)
    messages = stream_graph(graph, {"messages": init_msgs})
    final_answer = str(messages[-1].content)
    print("\n" + "=" * 40 + "\n任务完成:\n" + final_answer + "\n" + "=" * 40)

    save_trace_to_md(task, messages)
    save_memory(task, final_answer)


def run_team_mode(task):
    pm_resp = llm.invoke(
        [
            SystemMessage(
                content=(
                    "你是一个项目经理。将任务拆解为 JSON 团队格式。返回纯 JSON: "
                    '{"team": [{"name":"...","role":"...","task":"..."}]}。'
                    "最后一个必须是审查者。"
                )
            ),
            HumanMessage(content=task),
        ]
    )

    try:
        team_config = _load_team_plan(pm_resp.content)
    except Exception:
        print("PM 规划失败，退化为单 Agent 模式")
        return run_single(task)

    print(f"\n团队组建完成，共 {len(team_config)} 名成员：")
    for m in team_config:
        print(f"  - {m['name']} ({m['role']})")

    team = Team()
    for m in team_config:
        team.hire(m["name"], m["role"])

    summaries = {}
    all_traces = []

    for m in team_config:
        name = m["name"]
        print("\n" + "=" * 40 + f"\n [{name}] 正在执行任务: {m['task'][:50]}...")
        res, trace = team.agents[name].chat(m["task"])
        summaries[name] = res
        all_traces.extend(trace)
        team.broadcast(name, f"我已经完成了我的任务。工作摘要: {res[:500]}")

    reviewer = team_config[-1]
    print("\n" + "=" * 40 + f"\n [{reviewer['name']}] 正在进行最终审查...")
    final_task = (
        f"以下是团队工作摘要:\n"
        f"{json.dumps(summaries, ensure_ascii=False, indent=2)}\n\n"
        "请进行最终审查和整合输出。"
    )
    final_result, final_trace = team.agents[reviewer["name"]].chat(final_task)
    all_traces.extend(final_trace)

    print("\n" + "=" * 40 + "\n最终结果:\n" + final_result + "\n" + "=" * 40)
    save_trace_to_md(task, all_traces)
    save_memory(task, final_result)


def main():
    auto = "--auto" in sys.argv
    team_mode = "--team" in sys.argv
    task_args = [arg for arg in sys.argv[1:] if not arg.startswith("--")]

    if auto:
        config.AUTO_APPROVE = True

    if not task_args:
        print("用法: python main.py [--auto] [--team] <任务描述>")
        return 1

    task = " ".join(task_args)
    if team_mode:
        run_team_mode(task)
    else:
        run_single(task)
    return 0


if __name__ == "__main__":
    sys.exit(main())
