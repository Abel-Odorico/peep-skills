---
name: web-push
description: >
  Implement Web Push notifications (VAPID) in any PWA — backend subscription storage,
  per-notification-type URL/tag routing, service worker push handler, tag deduplication,
  and common gotchas (tag collision, iOS limitations, renotify).
  Use when adding push notifications to web apps, fixing push not showing, or improving push UX.
---

# Web Push — VAPID Implementation Pattern

Full implementation of Web Push from backend to service worker, including the non-obvious parts that tutorials skip.

---

## Architecture overview

```
Browser                         Backend
  │                               │
  ├─ subscribe()                  │
  │   └─ PushSubscription ──────► POST /push/subscribe (save to DB)
  │                               │
  │                    trigger ──►├─ send_push_to_users(user_ids, ...)
  │                               │   └─ pywebpush/web-push → FCM/APNS
  │◄─ push event ─────────────────┘
  │   └─ sw.js showNotification()
  │       └─ notificationclick → navigate to url
```

---

## Backend

### 1. VAPID key generation (one-time)

```bash
# Python
pip install py-vapid
vapid --gen

# Node
npm i -g web-push
web-push generate-vapid-keys
```

Store in `.env`:
```
VAPID_PRIVATE_KEY=...
VAPID_PUBLIC_KEY=...
VAPID_CLAIMS_EMAIL=mailto:you@example.com
```

### 2. Subscription model

```python
class PushSubscription(Base):
    __tablename__ = "push_subscriptions"
    id         = Column(Integer, primary_key=True)
    user_id    = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    endpoint   = Column(Text, unique=True, nullable=False)
    p256dh     = Column(Text, nullable=False)
    auth       = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utcnow)
```

### 3. Send helper (FastAPI + pywebpush)

```python
import json
from pywebpush import webpush, WebPushException

def send_push_to_users(
    db, user_ids: list[int], title: str, body: str,
    url: str = "/", tag: str = "app-push"
) -> int:
    subs = db.query(PushSubscription).filter(
        PushSubscription.user_id.in_(user_ids)
    ).all()
    ok = 0
    for sub in subs:
        try:
            webpush(
                subscription_info={
                    "endpoint": sub.endpoint,
                    "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
                },
                data=json.dumps({
                    "title": title, "body": body,
                    "url": url, "tag": tag       # ← tag MUST be in payload
                }),
                vapid_private_key=settings.vapid_private_key,
                vapid_claims={"sub": settings.vapid_claims_email},
            )
            ok += 1
        except WebPushException as e:
            if e.response and e.response.status_code == 410:
                db.delete(sub)  # subscription expired, clean up
            log.warning("push failed: %s", e)
    db.commit()
    return ok
```

### 4. Per-type routing — the key pattern

Instead of hardcoding URL or tag, use a config dict:

```python
_PUSH_CONFIG: dict[str, tuple[bool, str, str]] = {
    # type              push?   url              tag (unique per logical group)
    "order_placed":    (True,  "/orders",        "app-order"),
    "order_shipped":   (True,  "/orders",        "app-order"),
    "message":         (True,  "/messages",      "app-message"),
    "promo":           (True,  "/promos",        "app-promo"),
    "weekly_summary":  (True,  "/dashboard",     "app-weekly"),
}
_PUSH_DEFAULT = (True, "/", "app-push")

def notify(db, user_id, type_, title, body):
    push_enabled, url, tag = _PUSH_CONFIG.get(type_, _PUSH_DEFAULT)
    if push_enabled:
        send_push_to_users(db, [user_id], title, body, url=url, tag=tag)
```

---

## Service Worker

### Push handler

```js
self.addEventListener('push', e => {
  const data = e.data?.json() || {}
  e.waitUntil(
    self.registration.showNotification(data.title || 'App', {
      body:    data.body || '',
      icon:    '/icon-192.png',
      badge:   '/badge-72.png',
      tag:     data.tag || 'app-push',   // ← read from payload, NOT hardcoded
      renotify: true,                     // show even if same tag exists
      data:    { url: data.url || '/' },
      vibrate: [200, 100, 200],
    })
  )
})

self.addEventListener('notificationclick', e => {
  e.notification.close()
  const url = e.notification.data?.url || '/'
  e.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then(list => {
      const existing = list.find(c => c.focus)
      if (existing) return existing.navigate(url).then(c => c.focus())
      return clients.openWindow(url)
    })
  )
})
```

---

## Frontend — subscribe/unsubscribe

```js
// usePushNotifications.js
const PUBLIC_KEY = await fetch('/api/push/vapid-key').then(r => r.json()).then(d => d.publicKey)

async function subscribe() {
  const reg = await navigator.serviceWorker.ready
  const sub = await reg.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: urlBase64ToUint8Array(PUBLIC_KEY),
  })
  const { endpoint, keys: { p256dh, auth } } = sub.toJSON()
  await fetch('/api/push/subscribe', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify({ endpoint, p256dh, auth }),
  })
}

// urlBase64ToUint8Array — required conversion for applicationServerKey
function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - base64String.length % 4) % 4)
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/')
  const raw = atob(base64)
  return new Uint8Array([...raw].map(c => c.charCodeAt(0)))
}
```

---

## Common gotchas

### 1. Tag collision (most common)

**Problem:** All notifications share the same tag → each new push replaces the previous one. User only ever sees the latest.

**Cause:** `tag` not included in JSON payload → SW uses fallback `'app-push'` for everything.

**Fix:** Include `tag` in the JSON payload sent by backend. SW reads `data.tag`, not a hardcoded string.

```python
# WRONG
data=json.dumps({"title": title, "body": body})
# RIGHT
data=json.dumps({"title": title, "body": body, "url": url, "tag": tag})
```

### 2. URL hardcoded to one page

**Problem:** Clicking any notification always opens the same page (e.g. `/home`).

**Fix:** Use `_PUSH_CONFIG` dict — each notification type has its own `url`.

### 3. Expired subscriptions accumulate

**Problem:** `pywebpush` throws 410 Gone for stale subscriptions, fills logs.

**Fix:** Catch 410 and delete the subscription from DB immediately:
```python
if e.response and e.response.status_code == 410:
    db.delete(sub)
```

### 4. iOS (Safari) limitations

- Push on iOS only works when the PWA is **installed to home screen** (Add to Home Screen)
- iOS doesn't support `actions` in notifications
- iOS doesn't support `badge` count from push (only in-app)
- No workaround — document this for users

### 5. `renotify: true` required for repeated same-tag

Without `renotify: true`, a second push with same `tag` replaces the first silently (no sound/vibration). With `renotify: true`, each push makes noise even if it replaces a previous one.

### 6. SW cache version bump

After changing `sw.js`, bump the cache version string to force SW update:
```js
const CACHE = 'app-v23'  // ← increment this
```
Without this, users get the old SW for days.

### 7. Background vs foreground

SW `push` event fires even when app is open. If you want to suppress system notifications when the app is visible:
```js
self.addEventListener('push', async e => {
  const clients = await self.clients.matchAll({ type: 'window' })
  const appFocused = clients.some(c => c.focused)
  if (appFocused) return  // skip system notification, app handles it
  // ... showNotification
})
```

---

## Node.js equivalent

```bash
npm i web-push
```

```js
const webpush = require('web-push')
webpush.setVapidDetails(
  'mailto:you@example.com',
  process.env.VAPID_PUBLIC_KEY,
  process.env.VAPID_PRIVATE_KEY
)

await webpush.sendNotification(
  { endpoint, keys: { p256dh, auth } },
  JSON.stringify({ title, body, url, tag })
)
```

---

## Checklist

- [ ] VAPID keys in `.env`, never in code
- [ ] `tag` included in JSON payload (not just in SW fallback)
- [ ] Per-type routing: different notification types → different url + tag
- [ ] 410 responses clean up expired subscriptions from DB
- [ ] `renotify: true` in `showNotification()`
- [ ] SW cache version bumped after any SW change
- [ ] iOS limitation documented for users (needs home screen install)
- [ ] `urlBase64ToUint8Array()` used for applicationServerKey conversion
