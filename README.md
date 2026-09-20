# Charaka IP

Minimal LangChain + FastAPI backend: one agent, one tool. It answers questions
about **IP law** (patents, trademarks, GI, copyright) and **Ayurveda/AYUSH
regulatory topics** by running a live Tavily web search, then citing every
factual claim inline with a "Sources" list of real URLs. No vector DB, no
knowledge graph, no multi-agent orchestration.

## How citations work

The system prompt requires the model to number search results as they come in
and cite them inline (`[1]`, `[2]`, ...). The **Sources section is not trusted
from the model** — `agent.py` rebuilds it in code from the actual Tavily JSON
results attached to the conversation, keeping only the numbers the model
actually cited. This makes fabricated URLs structurally impossible: a citation
can only point at a source that was really returned by the search tool.

If the search returns nothing usable, the system prompt requires the model to
say so plainly instead of answering from its own knowledge.

## Setup

```bash
uv sync
```

Edit `.env` with real keys:

```
OPENAI_API_KEY=...
TAVILY_API_KEY=...
COHERE_API_KEY=...
LLM_PROVIDER=cohere   # or "openai" once a real OpenAI key is in place
```

`LLM_PROVIDER` picks the chat model (`agent.py:_build_model`). Everything else
(the tool, the citation logic, the prompt) is provider-agnostic.

## Run

API server:

```bash
uv run uvicorn main:app --reload
```

```bash
curl -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Section 3(p) of the Indian Patents Act?"}'
```

Demo script (runs the three required test questions and prints full output):

```bash
uv run python run_demo.py
```

## Files

- `agent.py` — agent construction, system prompt, citation/source extraction
- `main.py` — FastAPI app (`POST /ask`, `GET /health`)
- `schemas.py` — request/response models
- `run_demo.py` — prints full answers + sources for the three test questions
