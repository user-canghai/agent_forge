from typing import Annotated, Literal, TypedDict

from langchain_core.messages import AIMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

from context import compact_messages
from security import execute_tool_with_hooks
from tools import ALL_TOOLS


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


def agent_node(state: AgentState, llm_instance):
    messages = compact_messages(state["messages"])
    llm_with_tools = llm_instance.bind_tools(ALL_TOOLS)
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


def tool_node(state: AgentState):
    last_message = state["messages"][-1]
    tool_messages = []
    for tc in last_message.tool_calls:
        tool_inst = next((t for t in ALL_TOOLS if t.name == tc["name"]), None)
        if tool_inst:
            result = execute_tool_with_hooks(tool_inst, tc["args"])
        else:
            result = f"Error: 找不到工具 {tc['name']}"
        tool_messages.append(
            {"role": "tool", "content": str(result), "tool_call_id": tc["id"]}
        )
    return {"messages": tool_messages}


def build_graph(llm_instance, max_loops: int):
    def _agent_node(state: AgentState):
        return agent_node(state, llm_instance)

    def _should_continue(state: AgentState) -> Literal["tools", "__end__"]:
        last_message = state["messages"][-1]
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            ai_msgs_count = sum(
                1 for m in state["messages"] if isinstance(m, AIMessage)
            )
            if ai_msgs_count >= max_loops:
                return "__end__"
            return "tools"
        return "__end__"

    workflow = StateGraph(AgentState)
    workflow.add_node("agent", _agent_node)
    workflow.add_node("tools", tool_node)
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges(
        "agent", _should_continue, {"tools": "tools", "__end__": END}
    )
    workflow.add_edge("tools", "agent")
    return workflow.compile()
