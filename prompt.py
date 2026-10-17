import glob as glob_module
import json
import os

RULES_DIR = ".agent/rules"
SKILLS_DIR = ".agent/skills"
MCP_CONFIG = ".agent/mcp.json"


def load_rules() -> str:
    rules = []
    if not os.path.exists(RULES_DIR):
        return ""
    for f in sorted(glob_module.glob(os.path.join(RULES_DIR, "*.md"))):
        stem = os.path.splitext(os.path.basename(f))[0]
        with open(f, "r", encoding="utf-8") as file:
            rules.append(f"# {stem}\n{file.read().strip()}")
    return "\n\n".join(rules)


def load_skills() -> str:
    skills = []
    if not os.path.exists(SKILLS_DIR):
        return ""
    for f in sorted(glob_module.glob(os.path.join(SKILLS_DIR, "*.json"))):
        with open(f, "r", encoding="utf-8") as file:
            data = json.load(file)
            skills.append(f"- {data.get('name', '')}: {data.get('description', '')}")
    return "\n".join(skills)


def load_mcp_tools(base_tools):
    if not os.path.exists(MCP_CONFIG):
        return base_tools
    try:
        with open(MCP_CONFIG, "r", encoding="utf-8") as f:
            config = json.load(f)
        mcp_tools = []
        for server_data in config.get("mcpServers", {}).values():
            if server_data.get("disabled", False):
                continue
            for tool in server_data.get("tools", []):
                mcp_tools.append({"type": "function", "function": tool})
        return base_tools + mcp_tools
    except Exception:
        return base_tools


def build_system_prompt(memory_text: str) -> str:
    rules = load_rules()
    skills = load_skills()
    prompt = """你是一个专业的编程助手。你可以使用工具来读取、编写、搜索文件和执行命令。
请严格按照要求完成任务。如果遇到错误，尝试分析原因并修复。"""
    if rules:
        prompt += f"\n\n## 规则 (必须严格遵守)\n{rules}"
    if skills:
        prompt += f"\n\n## 可用技能提示\n{skills}"
    if memory_text:
        prompt += f"\n\n## 历史记忆\n{memory_text}"
    return prompt
