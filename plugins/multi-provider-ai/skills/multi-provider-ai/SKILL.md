---
name: multi-provider-ai
description: >
  Route AI requests across OpenRouter and Google Gemini with automatic fallback.
  Config stored in DB (no redeploy on key change), per-provider model selection,
  structured JSON output with repair, token budget per provider.
  Use when building AI features that need reliability across providers, or when the user
  invokes /multi-provider-ai.
---

# Multi-Provider AI

One interface, multiple LLM backends. First provider succeeds → return. All fail → raise.

Primary use case: cost/reliability tradeoff. Run cheap/free models first; fall back to paid when they fail or return garbage.

---

## Architecture

```
_call_ai(prompt, system, db)
  │
  ├── _get_provider_chain(db) → ["openrouter", "gemini"]  (ordered by config)
  │
  ├── try openrouter → success → return
  ├── try gemini     → success → return
  └── all failed     → raise RuntimeError("All AI providers failed")
```

For critical flows (oracle, time-sensitive decisions), hardcode the order regardless of config — don't let a DB misconfiguration change provider priority.

---

## Config via DB

Store all keys and model choices in a `site_config` key-value table. Changes take effect immediately — no redeploy.

| Key | Example value |
|-----|---------------|
| `analysis_provider` | `openrouter` or `gemini` or `auto` |
| `openrouter_api_key` | `sk-or-v1-...` |
| `openrouter_model` | `anthropic/claude-sonnet-4-5` |
| `gemini_api_key` | `AIzaSy...` |
| `gemini_model` | `gemini-2.5-flash` |

```python
def get_config(db, key: str, default=None) -> str | None:
    row = db.query(SiteConfig).filter_by(key=key).first()
    return row.value if row else default

def _get_provider_chain(db) -> list[str]:
    provider = get_config(db, "analysis_provider", "auto")
    if provider == "openrouter":
        return ["openrouter"]
    if provider == "gemini":
        return ["gemini"]
    # auto: use whichever has a key configured
    chain = []
    if get_config(db, "openrouter_api_key"):
        chain.append("openrouter")
    if get_config(db, "gemini_api_key"):
        chain.append("gemini")
    return chain
```

---

## OpenRouter

```python
import httpx

async def _call_openrouter(prompt: str, system: str, db) -> str:
    key = get_config(db, "openrouter_api_key")
    model = get_config(db, "openrouter_model", "meta-llama/llama-3.3-70b-instruct:free")
    if not key:
        raise ValueError("OpenRouter key not configured")

    r = await httpx.AsyncClient(timeout=60).post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {key}",
            "HTTP-Referer": "https://yourapp.com",
            "X-Title": "YourApp",
        },
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user",   "content": prompt},
            ],
            "max_tokens": 8000,
            "response_format": {"type": "json_object"},  # structured output (most models support)
        },
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]
```

---

## Gemini (direct REST)

```python
async def _call_gemini(prompt: str, system: str, db) -> str:
    key = get_config(db, "gemini_api_key")
    model = get_config(db, "gemini_model", "gemini-2.5-flash")
    if not key:
        raise ValueError("Gemini key not configured")

    r = await httpx.AsyncClient(timeout=60).post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}",
        json={
            "system_instruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {            # ← must be inside generationConfig, not root
                "maxOutputTokens": 8192,
                "temperature": 0.3,
            },
        },
    )
    r.raise_for_status()
    return r.json()["candidates"][0]["content"]["parts"][0]["text"]
```

---

## Provider loop with fallback

```python
import logging

log = logging.getLogger(__name__)

async def _call_ai(prompt: str, system: str, db) -> str:
    chain = _get_provider_chain(db)
    if not chain:
        raise RuntimeError("No AI provider configured")

    for provider in chain:
        try:
            if provider == "openrouter":
                return await _call_openrouter(prompt, system, db)
            if provider == "gemini":
                return await _call_gemini(prompt, system, db)
        except Exception as e:
            log.warning("AI provider %s failed: %s", provider, e)
            continue

    raise RuntimeError("All AI providers failed")
```

---

## Force specific order (oracle pattern)

When a flow is time-sensitive or cost-sensitive, ignore the DB chain and hardcode:

```python
async def _oracle_decide(prompt: str, system: str, db) -> str:
    # Always try OpenRouter (Claude) first, Gemini as fallback
    # regardless of what site_config says
    for fn in [_call_openrouter, _call_gemini]:
        try:
            return await fn(prompt, system, db)
        except Exception as e:
            log.warning("Oracle provider failed: %s", e)
    raise RuntimeError("Oracle: all providers failed")
```

---

## JSON output

OpenRouter supports `response_format: {type: "json_object"}` for most models. Gemini does not — extract JSON from text:

```python
import json, re

def _extract_json(text: str) -> dict:
    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Extract JSON block from markdown or prose
    m = re.search(r'\{.*\}', text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass
    raise ValueError(f"No valid JSON in response: {text[:200]}")

async def call_ai_json(prompt: str, system: str, db) -> dict:
    text = await _call_ai(prompt, system, db)
    return _extract_json(text)
```

Always request JSON explicitly in the prompt:

```python
system = """
You are an analyst. Respond ONLY with valid JSON matching this schema:
{"overview": "string", "prediction": "string", "confidence": 0.0-1.0}
No markdown, no explanation — raw JSON only.
"""
```

---

## Background task safety

When calling AI from a background task (FastAPI `BackgroundTasks` or `asyncio` loop), always rollback on error to avoid cascade `InFailedSqlTransaction`:

```python
async def generate_analysis_bg(match_id: int, db_url: str):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        result = await call_ai_json(prompt, system, db)
        # save result
        db.commit()
    except Exception as e:
        db.rollback()   # ← CRITICAL: without this, subsequent queries fail with InFailedSqlTransaction
        log.error("Analysis bg failed: %s", e)
    finally:
        db.close()
```

---

## Model reference (2026-06)

### OpenRouter free models (verified working)
| Model | Context | Notes |
|-------|---------|-------|
| `nvidia/llama-3.1-nemotron-ultra-253b-v1:free` | 128k | High quality |
| `nousresearch/hermes-3-405b-instruct:free` | 8k | Good for structured JSON |
| `meta-llama/llama-3.3-70b-instruct:free` | 128k | Fast |

### OpenRouter paid
| Model | Notes |
|-------|-------|
| `anthropic/claude-sonnet-4-5` | Best quality |
| `google/gemini-2.5-flash` | Fast, cheap |
| `openai/gpt-4o` | Reliable JSON |

### Gemini direct
| Model | Notes |
|-------|-------|
| `gemini-2.5-flash` | Fast, cheap, good for JSON |
| `gemini-2.5-pro` | Highest quality |
| `gemini-2.0-flash` | Ultra-fast |

---

## Gotchas

### 1. Free models disappear without notice

OpenRouter `:free` models get removed or rate-limited without warning. Keep a fallback non-free model or check against `https://openrouter.ai/api/v1/models` before launch.

### 2. Gemini `maxOutputTokens` must be inside `generationConfig`

```python
# WRONG
json={"maxOutputTokens": 8192, "contents": [...]}

# RIGHT
json={"contents": [...], "generationConfig": {"maxOutputTokens": 8192}}
```

### 3. OpenRouter 429 ≠ quota exhausted

OpenRouter returns 429 for rate limit AND for quota issues. Check `r.json()["error"]["message"]` to distinguish. Don't assume 429 = temporary.

### 4. JSON truncated with low token budget

4096 tokens minimum for complex structured output. With 1024 tokens, JSON gets cut mid-string → `json.loads` fails. Set `max_tokens: 8000` / `maxOutputTokens: 8192`.

### 5. `response_format` not universally supported

Some OpenRouter models ignore `response_format: {type: "json_object"}`. Use `_extract_json()` regex fallback regardless of provider — assume text, extract JSON, don't trust format enforcement.

### 6. OpenRouter requires `HTTP-Referer`

Without `HTTP-Referer` header, some models reject the request or return lower quality. Include it even if your app is a backend service.

---

## Checklist

- [ ] Keys stored in DB/env, never hardcoded
- [ ] `_get_provider_chain()` reads from DB (no redeploy on key change)
- [ ] `generationConfig` wraps Gemini params (not root-level)
- [ ] `max_tokens` ≥ 4096 (8000+ preferred for JSON output)
- [ ] `_extract_json()` used regardless of `response_format` support
- [ ] JSON format requested explicitly in system prompt
- [ ] Background tasks call `db.rollback()` on exception
- [ ] Free models have paid fallback for production
- [ ] Try/except per provider, not global (allows partial fallback)
