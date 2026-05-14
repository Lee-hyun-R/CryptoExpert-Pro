# AGENTS.md

## Project

CryptoExpert Pro — AI-driven cryptography analysis assistant. LangChain + LangGraph ReAct agent with S-box security evaluation, NIST SP800-22 randomness testing, and tool-calling LLMs.

## Commands

```bash
uv sync                 # Install deps (uses Tsinghua PyPI mirror by default)
python main.py          # Start dev server on 127.0.0.1:8001
python clear_db.py      # Wipe all SQLite checkpoint data
docker-compose up -d    # Build and run (broken — see Gotchas)
```

No test suite, linter, or type checker is configured.

## Architecture

- `main.py` — FastAPI entry point. Lazy-creates agents per model in a `agents` dict cache.
- `agent.py` — `create_crypto_agent()` builds a LangGraph ReAct agent per model. System prompt is in Chinese. Provider routing: `"deepseek"` → DeepSeek API; `"openai"` / `"qwen"` → DashScope; `"kimi"` / `"mimo"` → rewritten to `provider="openai"` with custom `base_url`.
- `Tools/` — 27 LangChain `@tool` functions exported as 3 lists: `randomness_tools` (5), `Sbox_tools_1` (11), `Sbox_tools_2` (11). Plus `execute_python` (subprocess code runner). `structural_tools.py` is empty.
- `static/index.html` — Single-page frontend.
- `clear_db.py` — Deletes all rows from SQLite checkpoint tables.

## Environment

`.env` required (gitignored, no `.env.example` exists). Keys:

```
DEEPSEEK_API_KEY=...
DASHSCOPE_API_KEY=...
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
KIMI_API_KEY=...
KIMI_BASE_URL=https://api.moonshot.cn/v1
MIMO_API_KEY=...
MIMO_BASE_URL=https://api.xiaomimimo.com/v1
TAVILY_API_KEY=...
DB_PATH=resources/test.db
```

DB directory auto-created if missing. SQLite checkpointer uses `check_same_thread=False`.

## Gotchas

- **Port mismatch**: `main.py:189` binds to **8001**. README, `docker-compose.yml`, and `test_main.http` all reference 8000. Docker maps `8000:8000` but container listens on 8001 — deploy is broken without fixing one side.
- **Provider quirks**: Kimi K2.6 forces `temperature=0.6` and disables thinking via `extra_body={"thinking": {"type": "disabled"}}` (its default is thinking ON). Mimo disables thinking via `extra_body={"enable_thinking": False}`. Both are needed because LangChain doesn't handle `reasoning_content` in multi-turn calls.
- **Recursion limit**: Agent invoke uses `recursion_limit=100` (`main.py:96`).
- **uv index**: Default PyPI source is Tsinghua mirror (`https://pypi.tuna.tsinghua.edu.cn/simple`) — may be slow outside China.
- **Message cleanup**: Both `/api/chat/` and `/api/history/{thread_id}` truncate dangling tool-call messages before returning.
- **Code execution**: `execute_python` runs user code via `subprocess` with a 30s timeout in a temp file.
- **Hex string handling**: LLMs format S-box values differently — Kimi passes `"0xC"` (string), Mimo passes `12` (int). The `_to_int()` helper in both Sbox tool files handles this. If adding new S-box tools, use `_to_int(x)` instead of `int(x)`.
