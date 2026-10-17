# AgentForge

基于 LangGraph 与 LangChain 实现的可扩展智能体实验平台，包含模型配置、长短期记忆、工具调用、临时子智能体、安全防护、提示词工程、上下文压缩、单 Agent 模式和多 Agent 团队模式。

## 项目结构

```text
agent-forge/
├── .agent/
│   ├── mcp.json
│   ├── rules/
│   │   └── project.md
│   └── skills/
│       └── file-analysis.json
├── traces/
│   └── .gitkeep
├── .env.example
├── .gitignore
├── README.md
├── config.py
├── context.py
├── graph.py
├── logger.py
├── main.py
├── memory.py
├── prompt.py
├── pyproject.toml
├── requirements.txt
├── security.py
├── tools.py
└── uv.lock
```

## 环境准备

建议使用 Python 3.11。

使用 pip：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

使用 uv（推荐）：

```bash
pip install uv
uv sync
cp .env.example .env
```

在 `.env` 中填写模型服务信息：

```dotenv
OPENAI_API_KEY=你的 API Key
OPENAI_BASE_URL=https://api.deepseek.com/v1
MODEL_NAME=deepseek-v4-pro
TEAM_MODEL_NAME=deepseek-flash
```

如需使用本地部署模型，填写 `LOCAL_BASE_URL` 和 `LOCAL_MODEL_NAME`，并将 `config.py` 中的 `llm`、`team_llm` 切换为 `llm_local`。

`.env` 已被 `.gitignore` 忽略，请勿将 API Key 提交到仓库。

## 运行

单 Agent 模式：

```bash
python main.py --auto "统计当前目录下有多少个 Python 文件，并把结果写入 count.txt"
```

团队模式：

```bash
python main.py --team "统计当前目录下有多少个 Python 文件，并把结果写入 count.txt"
```

交互确认模式：

```bash
python main.py "统计当前目录下有多少个 Python 文件，并把结果写入 count.txt"
```

使用 uv 时也可以用 `uv run main.py` 替代 `python main.py`。

`--auto` 会自动执行非高危工具操作。`bash` 和 `edit` 在未开启 `--auto` 时会请求用户确认，输入 `Y` 执行、`N` 跳过、`Q` 终止程序。

## 输出

- `agent_memory.md`：跨会话记忆文件，保存最近任务和结果摘要。
- `traces/<时间戳>_<任务名>.md`：完整执行轨迹，包含模型思考、工具调用和工具结果。

## 模块说明

| 文件 | 职责 |
| --- | --- |
| `config.py` | 本地与云端模型配置、安全开关 |
| `memory.py` | 记忆加载、截断与持久化 |
| `tools.py` | 文件读写、精确编辑、内容搜索、文件查找、Shell 执行、临时子智能体 |
| `security.py` | 高危命令黑名单、用户确认、输出截断与 Hook 管道 |
| `prompt.py` | Rules、Skills、MCP 配置加载与系统提示词拼接 |
| `context.py` | 基于模型总结的上下文压缩 |
| `graph.py` | LangGraph 状态、节点、条件边与图编译 |
| `logger.py` | Markdown 执行轨迹保存 |
| `main.py` | 流式输出、单 Agent、多 Agent 团队与命令行入口 |

## 安全机制

1. 高危命令黑名单拦截 `rm -rf /`、`mkfs`、`dd of=/dev/`、`chmod -R 777 /`、远程脚本管道执行等模式。
2. `bash` 与 `edit` 默认需要用户确认。
3. 工具输出超过 5000 字符时保留首尾各 2500 字符。
