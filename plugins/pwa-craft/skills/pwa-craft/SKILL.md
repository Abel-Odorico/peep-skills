---
name: pwa-craft
description: >
  Ship a production PWA: service worker with cache versioning, network-first API + cache-first assets,
  offline fallback page, iOS safe-area support, install prompt (beforeinstallprompt + iOS detection),
  and the gotchas that break PWAs silently.
  Use when adding PWA support to any web app, fixing SW update issues, or implementing install prompts.
---

# PWA Craft

A PWA is three things: HTTPS + manifest + service worker. Getting them right means: instant load, offline fallback, installable on Android/iOS, and updates that don't strand users on old code.

---

## Architecture

```
main.jsx (SW registration — global, not in App.jsx)
  └── sw.js
       ├── install  → pre-cache shell (icons, manifest, offline.html)
       ├── activate → delete old caches + clients.claim()
       ├── fetch    → cache-first /assets/* | network-first /api/* | offline fallback nav
       └── push     → showNotification (see web-push skill)

useInstallPrompt.js
  ├── Android/Desktop: capture beforeinstallprompt, expose install()
  └── iOS: detect via userAgent + !navigator.standalone → isIOS flag
```

Register SW in `main.jsx`, not `App.jsx`. App.jsx may not mount if auth redirects early — SW registration would never happen, breaking background push.

---

## Service Worker — `sw.js`

```js
const CACHE = 'app-v22'  // ← bump on every sw.js change

const SHELL = [
  '/',
  '/index.html',
  '/offline.html',
  '/manifest.json',
  '/icon-192.png',
  '/icon-512.png',
]

// Install: pre-cache shell
self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(SHELL))
  )
  self.skipWaiting()
})

// Activate: purge old caches, claim clients
self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
    // ⚠️ DO NOT call clients.matchAll().then(wins => wins.forEach(w => w.navigate(w.url)))
    // That forces reload of all tabs on SW activation — causes unexpected navigation mid-interaction
  )
})

// Fetch: routing strategies
self.addEventListener('fetch', e => {
  const { request } = e
  const url = new URL(request.url)

  // 1. Cache-first: Vite assets (content-hashed, immutable)
  if (url.pathname.startsWith('/assets/')) {
    e.respondWith(
      caches.match(request).then(cached => cached || fetch(request).then(res => {
        const clone = res.clone()
        caches.open(CACHE).then(c => c.put(request, clone))
        return res
      }))
    )
    return
  }

  // 2. Network-first: API calls
  if (url.pathname.startsWith('/api/')) {
    e.respondWith(
      fetch(request).catch(() => new Response('{"error":"offline"}', {
        headers: { 'Content-Type': 'application/json' }
      }))
    )
    return
  }

  // 3. Network-first with offline fallback: navigation (SPA)
  if (request.mode === 'navigate') {
    e.respondWith(
      fetch(request).catch(() => caches.match('/offline.html'))
    )
    return
  }

  // 4. Default: network, no caching
  e.respondWith(fetch(request))
})
```

---

## SW Registration — `main.jsx`

```jsx
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js')
      .then(reg => console.log('SW registered', reg.scope))
      .catch(err => console.warn('SW registration failed', err))
  })
}
```

Register on `window load`, not DOMContentLoaded — avoid contending with critical resources.

---

## manifest.json

```json
{
  "name": "App Name",
  "short_name": "App",
  "description": "App description",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#0d1b2a",
  "theme_color": "#0f7a78",
  "icons": [
    { "src": "/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any maskable" },
    { "src": "/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable" }
  ],
  "screenshots": [
    { "src": "/screenshot-mobile.png", "sizes": "390x844", "type": "image/png", "form_factor": "narrow" },
    { "src": "/screenshot-desktop.png", "sizes": "1280x720", "type": "image/png", "form_factor": "wide" }
  ]
}
```

`screenshots` unlocks the richer install prompt on Android Chrome (shows preview before install).

---

## Install Prompt Hook — `useInstallPrompt.js`

```js
import { useState, useEffect } from 'react'

export function useInstallPrompt() {
  const [prompt, setPrompt] = useState(null)
  const [isInstalled, setIsInstalled] = useState(false)
  const [isIOS, setIsIOS] = useState(false)

  useEffect(() => {
    // iOS detection: PWA not installable via JS, show manual instructions
    const ios = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.navigator.standalone
    setIsIOS(ios)

    // Already installed (standalone mode)
    if (window.matchMedia('(display-mode: standalone)').matches) {
      setIsInstalled(true)
    }

    const handler = e => {
      e.preventDefault()   // prevent browser's default mini-infobar
      setPrompt(e)         // save for later
    }
    window.addEventListener('beforeinstallprompt', handler)
    window.addEventListener('appinstalled', () => setIsInstalled(true))
    return () => window.removeEventListener('beforeinstallprompt', handler)
  }, [])

  const install = async () => {
    if (!prompt) return
    prompt.prompt()
    const { outcome } = await prompt.userChoice
    if (outcome === 'accepted') setIsInstalled(true)
    setPrompt(null)
  }

  return {
    isInstallable: !!prompt,  // Android/Desktop: show install button
    isIOS,                    // iOS: show "Share → Add to Home Screen" instructions
    isInstalled,
    install,
  }
}
```

### Usage

```jsx
const { isInstallable, isIOS, isInstalled, install } = useInstallPrompt()

if (!isInstalled) {
  if (isInstallable) return <button onClick={install}>📲 Instalar App</button>
  if (isIOS) return <p>Toque em Compartilhar → "Adicionar à Tela Inicial"</p>
}
```

---

## iOS Safe Area

Without these, content hides under iPhone notch/home indicator:

```html
<!-- index.html -->
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
```

```css
/* Without viewport-fit=cover, env() returns 0 in Safari */
.mobile-dock {
  height: calc(var(--mobile-nav) + env(safe-area-inset-bottom));
  padding-bottom: env(safe-area-inset-bottom);
}

.mobile-drawer {
  bottom: calc(var(--mobile-nav) + env(safe-area-inset-bottom));
}

.page-content {
  padding-bottom: calc(var(--mobile-nav) + env(safe-area-inset-bottom) + 1rem);
}
```

---

## offline.html

Minimal page served when navigation fails offline:

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Sem conexão</title>
  <style>
    body { font-family: system-ui; display: flex; align-items: center; justify-content: center;
           min-height: 100vh; margin: 0; background: #0d1b2a; color: #e2e8f0; text-align: center; }
  </style>
</head>
<body>
  <div>
    <h1>📡 Sem conexão</h1>
    <p>Verifique sua internet e tente novamente.</p>
    <button onclick="location.reload()">Tentar novamente</button>
  </div>
</body>
</html>
```

Pre-cache this in SHELL — it must be available when fetch fails.

---

## Gotchas

### 1. SW doesn't update without cache version bump

Users keep the old SW until `CACHE` string changes AND they close all tabs. Bump `app-v22` → `app-v23` on every `sw.js` change, or users run old code for days.

### 2. `skipWaiting` + `navigate(w.url)` = reload loop

`skipWaiting()` in `install` + `w.navigate(w.url)` in `activate` forces every open tab to reload when the new SW activates. This happens mid-interaction. Use only `clients.claim()` — no navigate.

### 3. `beforeinstallprompt` never fires on iOS

iOS doesn't support the install prompt API. Detecting iOS and showing manual instructions ("Compartilhar → Adicionar à Tela Inicial") is the only option. `isInstallable` will always be false on iOS.

### 4. iOS push requires home screen install

Web Push on iOS only works when the app is installed (launched from home screen in standalone mode). Users on mobile Safari in browser mode won't receive push. Document this, don't try to workaround it.

### 5. HTTPS required (except localhost)

SW won't register on HTTP. Use localhost for dev, HTTPS everywhere else. nginx: redirect all HTTP → HTTPS.

### 6. `Cache-Control: no-store` on API responses prevents accidental caching

If your backend returns API responses with `Cache-Control: no-store`, the browser-level cache (not SW cache) won't store them. This is usually correct — don't fight it in the SW fetch handler.

### 7. Vite assets are content-hashed — safe to cache forever

`/assets/index-abc123.js` — the hash changes on rebuild. Cache-first is safe. Never cache `/` or `/index.html` forever — they're not hashed.

---

## Checklist

- [ ] `viewport-fit=cover` in `<meta name="viewport">` (iOS safe area)
- [ ] SW registered in `main.jsx` (not `App.jsx`)
- [ ] `CACHE` version string bumped on every sw.js change
- [ ] `activate` uses only `clients.claim()` — no `w.navigate()`
- [ ] `offline.html` in SHELL pre-cache list
- [ ] `manifest.json` has 192 + 512 icons with `purpose: "any maskable"`
- [ ] `beforeinstallprompt` captured and saved (not called immediately)
- [ ] iOS detected separately (`/iPad|iPhone|iPod/` + `!standalone`)
- [ ] Safe area CSS uses `env(safe-area-inset-bottom)` on dock/drawer
- [ ] HTTPS configured (SW won't register on HTTP)
