import glob as glob_module
import os
import subprocess

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool

from security import execute_tool_with_hooks, truncate_output


@tool
def read(path: str, offset: int = None, limit: int = None) -> str:
    """读取文件内容。可以指定起始行(offset)和读取行数。返回带行号的文本。"""
    if not os.path.exists(path):
        return f"Error: 文件 {path} 不存在"
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        start = offset if offset is not None else 0
        end = (start + limit) if limit is not None else len(lines)
        lines = lines[start:end]
        return "\n".join(
            [f"{i + start + 1:4d} {line.rstrip()}" for i, line in enumerate(lines)]
        )
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def write(path: str, content: str) -> str:
    """将内容写入文件。如果文件不存在或父目录不存在，会自动创建。"""
    try:
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"成功写入 {len(content)} 个字符到 {path}"
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def edit(path: str, old_string: str, new_string: str) -> str:
    """精确替换文件中的一段文本。要求 old_string 在文件中必须唯一存在。"""
    if not os.path.exists(path):
        return f"Error: 文件 {path} 不存在"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    count = content.count(old_string)
    if count == 0:
        return "Error: 未找到匹配的文本"
    if count > 1:
        return f"Error: 找到 {count} 处匹配，请提供更具体的 old_string 以确保唯一性"
    new_content = content.replace(old_string, new_string, 1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)
    return "文件修改成功"


@tool
def grep(pattern: str, path: str = ".") -> str:
    """在指定目录下递归搜索包含特定正则模式的文本内容。"""
    try:
        result = subprocess.run(
            ["grep", "-rn", pattern, path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = result.stdout
        if not output:
            return "No matches found"
        return output
    except subprocess.TimeoutExpired:
        return "Error: grep 执行超时 (30秒)"
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def glob(pattern: str) -> str:
    """使用 glob 模式查找文件路径（如 **/*.py），按修改时间倒序返回。"""
    matches = glob_module.glob(pattern, recursive=True)
    if not matches:
        return "No files found"
    matches.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    return "\n".join(matches)


@tool
def bash(command: str) -> str:
    """在终端中执行 Bash 命令，超时时间 30 秒。谨慎使用危险命令。"""
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=30
        )
        output = result.stdout + result.stderr
        if not output and result.returncode == 0:
            return "命令执行成功，无输出"
        return truncate_output(output)
    except subprocess.TimeoutExpired:
        return "Error: 命令执行超时 (30秒)"
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def subagent(role: str, task: str) -> str:
    """启动一个一次性的子智能体来完成特定子任务。"""
    from config import llm

    sub_tools = [read, write, edit, grep, glob, bash]
    sub_llm = llm.bind_tools(sub_tools)
    sub_messages = [SystemMessage(content=role), HumanMessage(content=task)]

    for _ in range(10):
        resp = sub_llm.invoke(sub_messages)
        if not resp.tool_calls:
            return str(resp.content)
        sub_messages.append(resp)
        for tc in resp.tool_calls:
            tool_instance = next(
                (t for t in sub_tools if t.name == tc["name"]), None
            )
            if not tool_instance:
                result = f"Error: 子智能体找不到工具 {tc['name']}"
            else:
                result = execute_tool_with_hooks(tool_instance, tc["args"])
            sub_messages.append(
                ToolMessage(content=str(result), tool_call_id=tc["id"])
            )
    return "SubAgent: 达到最大迭代次数 (10次) 仍未结束"


ALL_TOOLS = [read, write, edit, grep, glob, bash, subagent]
