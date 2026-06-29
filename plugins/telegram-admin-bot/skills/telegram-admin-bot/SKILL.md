---
name: telegram-admin-bot
description: >
  Wire up a Telegram bot for SaaS admin: daily reports, interactive webhook menu,
  new-user notifications, broadcast messages. Covers webhook security (secret token + allowlist),
  HTML parse_mode (never MarkdownV2), html.escape() for dynamic values, inline keyboard menus
  with editMessageText, and the common breakage points.
  Use when adding Telegram integration to any SaaS or backend project.
---

# Telegram Admin Bot

Two modes: **output-only** (sendMessage from backend) and **interactive** (webhook receives user commands). Most SaaS needs both.

---

## Architecture

```
Output-only:
  Backend event ──► sendMessage/sendPhoto ──► Telegram API ──► Admin chat

Interactive:
  Admin sends command ──► Telegram ──► POST /api/telegram/webhook ──► handler ──► editMessageText/sendMessage
```

Output-only is simpler — no webhook needed. Add interactive when you want the admin to query data from Telegram without opening the dashboard.

---

## Setup

### 1. Create bot

1. Message `@BotFather` → `/newbot`
2. Save `token` (format: `1234567890:AAAA...`)
3. Get your chat_id: message `@userinfobot` or check `getUpdates` after sending a message to the bot

### 2. Register webhook (interactive mode)

```python
import httpx

async def setup_webhook(bot_token: str, webhook_url: str, secret: str):
    r = await httpx.AsyncClient().post(
        f"https://api.telegram.org/bot{bot_token}/setWebhook",
        json={
            "url": webhook_url,                   # e.g. https://yourapp.com/api/telegram/webhook
            "secret_token": secret,               # random string, store in site_config
            "allowed_updates": ["message", "callback_query"],
        }
    )
    return r.json()

async def get_webhook_info(bot_token: str):
    r = await httpx.AsyncClient().get(
        f"https://api.telegram.org/bot{bot_token}/getWebhookInfo"
    )
    return r.json()
```

### 3. Nginx — allow webhook POST

```nginx
location /api/telegram/webhook {
    proxy_pass http://127.0.0.1:8130;
    proxy_set_header X-Real-IP $remote_addr;
    # No rate limit override needed — Telegram sends max ~30 req/s
}
```

---

## Security

```python
from fastapi import Header, HTTPException, Request

ALLOWED_CHATS_KEY = "telegram_allowed_chats"  # comma-separated IDs in site_config

async def verify_telegram(
    request: Request,
    x_telegram_bot_api_secret_token: str = Header(None),
    db=Depends(get_db),
):
    # 1. Verify secret token
    expected = get_config(db, "telegram_webhook_secret")
    if not expected or x_telegram_bot_api_secret_token != expected:
        raise HTTPException(403, "Forbidden")

    # 2. Allowlist check
    body = await request.json()
    chat_id = str(
        body.get("message", {}).get("chat", {}).get("id")
        or body.get("callback_query", {}).get("message", {}).get("chat", {}).get("id")
    )
    primary = get_config(db, "telegram_chat_id")
    extra = get_config(db, ALLOWED_CHATS_KEY) or ""
    allowed = {primary} | set(filter(None, extra.split(",")))
    if chat_id not in allowed:
        raise HTTPException(403, "Chat not allowed")
```

---

## Parse Mode — CRITICAL

**Always `parse_mode=HTML`. Never `MarkdownV2`.**

MarkdownV2 requires escaping `(`, `)`, `.`, `-`, `_`, `*`, `[`, `]`, `~`, `>`, `#`, `+`, `=`, `|`, `{`, `}` — any unescaped char silently drops the message. User names, emails, any dynamic value will break it.

```python
import html

def send_message(bot_token: str, chat_id: str, text: str, **kwargs):
    httpx.post(
        f"https://api.telegram.org/bot{bot_token}/sendMessage",
        json={"chat_id": chat_id, "text": text, "parse_mode": "HTML", **kwargs},
    )

# ALWAYS escape dynamic values:
name = html.escape(user.name)        # "O'Brien & Co." → "O&#x27;Brien &amp; Co."
email = html.escape(user.email)
text = f"<b>Novo usuário:</b> {name} — <code>{email}</code>"
```

HTML tags allowed: `<b>`, `<i>`, `<u>`, `<s>`, `<code>`, `<pre>`, `<a href="...">`.

---

## sendMessage / editMessageText

```python
async def tg(bot_token: str, method: str, **payload):
    async with httpx.AsyncClient() as c:
        r = await c.post(
            f"https://api.telegram.org/bot{bot_token}/{method}",
            json=payload,
        )
    return r.json()

# Send new message
await tg(token, "sendMessage",
    chat_id=chat_id,
    text="<b>Relatório</b>",
    parse_mode="HTML",
)

# Edit existing message (inline menu response)
await tg(token, "editMessageText",
    chat_id=chat_id,
    message_id=msg_id,       # from callback_query.message.message_id
    text=new_text,
    parse_mode="HTML",
    reply_markup={"inline_keyboard": [[{"text": "⬅️ Voltar", "callback_data": "menu"}]]},
)
```

---

## Interactive menu pattern

```python
MENU_KEYBOARD = {
    "inline_keyboard": [
        [{"text": "👥 Usuários", "callback_data": "q_users"},
         {"text": "📊 Acessos",  "callback_data": "q_views"}],
        [{"text": "🏅 Ranking",  "callback_data": "q_ranking"},
         {"text": "📋 Resumo",   "callback_data": "q_summary"}],
    ]
}

@router.post("/webhook")
async def webhook(request: Request, db=Depends(get_db), _=Depends(verify_telegram)):
    body = await request.json()

    # Text command (/start or /menu)
    if msg := body.get("message"):
        text = msg.get("text", "")
        chat_id = str(msg["chat"]["id"])
        if text.startswith("/start") or text.startswith("/menu"):
            await tg(token, "sendMessage",
                chat_id=chat_id,
                text="<b>Admin Panel</b>\nEscolha uma consulta:",
                parse_mode="HTML",
                reply_markup=MENU_KEYBOARD,
            )

    # Button press
    if cb := body.get("callback_query"):
        chat_id = str(cb["message"]["chat"]["id"])
        msg_id = cb["message"]["message_id"]
        data = cb.get("data", "")

        result_text = await _handle_query(data, db)

        try:
            await tg(token, "editMessageText",
                chat_id=chat_id,
                message_id=msg_id,
                text=result_text,
                parse_mode="HTML",
                reply_markup={"inline_keyboard": [[{"text": "⬅️ Menu", "callback_data": "menu"}]]},
            )
        except Exception:
            pass  # message may have been deleted

        # Acknowledge callback (required — removes loading spinner)
        await tg(token, "answerCallbackQuery", callback_query_id=cb["id"])

    return {"ok": True}
```

---

## New-user notification

```python
# report.py
async def notify_new_user_telegram(name: str, email: str, username: str, db):
    token = get_config(db, "telegram_bot_token")
    chat_id = get_config(db, "telegram_chat_id")
    if not token or not chat_id:
        return
    name_e = html.escape(name or "")
    email_e = html.escape(email or "")
    user_e = html.escape(username or "—")
    await tg(token, "sendMessage",
        chat_id=chat_id,
        text=f"🎉 <b>Novo usuário</b>\n{name_e} ({user_e})\n<code>{email_e}</code>",
        parse_mode="HTML",
    )

# auth.py (register endpoint)
background_tasks.add_task(notify_new_user_telegram, user.name, user.email, user.username, db)
```

Always use `BackgroundTasks` — never `await` inline in the endpoint. Telegram latency (~200ms) adds to request time.

---

## Daily report loop

```python
# main.py — in lifespan
import asyncio
from zoneinfo import ZoneInfo

_DAILY_REPORT_TIMES = [(7, 0), (14, 0)]  # BRT hours

async def _daily_report_loop():
    tz = ZoneInfo("America/Sao_Paulo")
    while True:
        now = datetime.now(tz)
        next_fires = []
        for h, m in _DAILY_REPORT_TIMES:
            t = now.replace(hour=h, minute=m, second=0, microsecond=0)
            if t <= now:
                t = t + timedelta(days=1)
            next_fires.append(t)
        next_fire = min(next_fires)
        await asyncio.sleep((next_fire - now).total_seconds())
        with SessionLocal() as db:
            await push_daily_report(db)

# report.py
async def push_daily_report(db):
    token = get_config(db, "telegram_bot_token")
    chat_id = get_config(db, "telegram_chat_id")
    if not token or not chat_id:
        return
    report = _build_report(db)
    text = _format_text(report)
    await tg(token, "sendMessage", chat_id=chat_id, text=text, parse_mode="HTML")
```

### Report format

```python
def _format_text(r: dict) -> str:
    sep = "─────────────────────"
    lines = [
        f"📊 <b>RELATÓRIO DIÁRIO</b>",
        sep,
        f"👥 <b>USUÁRIOS</b>",
        f"Total: <b>{r['users']['total']}</b>  |  Hoje: <b>{r['users']['today']}</b>",
        sep,
        f"🎯 <b>APOSTAS</b>",
        f"Total: <b>{r['bets']['total']}</b>  |  Hoje: <b>{r['bets']['today']}</b>",
        sep,
        f"🌐 <b>ACESSOS</b>  (últimas 24h)",
        f"Views: <b>{r['views']['last24h']}</b>  |  Únicos: <b>{r['views']['unique']}</b>",
    ]
    # Top 5 ranking
    if r.get("ranking"):
        lines += [sep, "🏅 <b>RANKING TOP 5</b>"]
        for i, u in enumerate(r["ranking"][:5], 1):
            name_e = html.escape(u["name"] or "")
            lines.append(f"{i}. {name_e} — <b>{u['points']} pts</b>")
    return "\n".join(lines)
```

---

## Gotchas

### 1. MarkdownV2 drops messages silently

If `parse_mode=MarkdownV2` and any char is unescaped → Telegram returns `{"ok": false, "error_code": 400, "description": "Bad Request: can't parse entities"}`. The message simply doesn't arrive. No exception raised if you ignore the response. Switch to HTML.

### 2. `html.escape()` on every dynamic value

Forgetting escape on a user-supplied value = potential HTML injection in Telegram. Won't cause XSS (Telegram strips scripts) but can break message formatting with `<` or `&` in names.

### 3. `inline_keyboard` must be list of lists

```python
# WRONG — flat list
{"inline_keyboard": [{"text": "A", "callback_data": "a"}]}

# RIGHT — list of rows, each row is a list of buttons
{"inline_keyboard": [[{"text": "A", "callback_data": "a"}, {"text": "B", "callback_data": "b"}]]}
```

### 4. `editMessageText` fails on deleted messages

Wrap in try/except. Telegram returns 400 "message to edit not found" if the user deleted the bot message. Don't crash the webhook handler.

### 5. Output-only bot still needs `/start` handler

A bot that only sends messages (no webhook) will show "can't start" if a user tries to message it. Either set a webhook with a minimal `/start` response or use BotFather's `/setdescription` to explain "Este bot só envia notificações."

### 6. `answerCallbackQuery` is required

After handling a `callback_query`, always call `answerCallbackQuery`. Without it, Telegram shows a loading spinner on the button for 10s before timing out. It just needs `callback_query_id` — text is optional.

---

## Checklist

- [ ] `parse_mode=HTML` everywhere, never MarkdownV2
- [ ] `html.escape()` on every dynamic value (name, email, username, any user content)
- [ ] Webhook secured with `secret_token` header check + chat allowlist
- [ ] `answerCallbackQuery` called after every callback_query
- [ ] `editMessageText` wrapped in try/except (deleted message)
- [ ] Notifications sent via `BackgroundTasks`, never awaited inline
- [ ] Daily report loop uses `zoneinfo` for BRT timezone (not UTC offset hardcoded)
- [ ] Bot token and chat_id stored in DB/site_config (not hardcoded)
- [ ] `/start` or `/menu` handler present even on output-only bots
