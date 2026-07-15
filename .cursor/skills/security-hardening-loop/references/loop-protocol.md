# Protocolo do loop — estado, máquina de estados e retomada

## Layout em disco

```
<projeto>/
  .security-loop/
    state.json      # única fonte de verdade do loop
    baseline.log    # output bruto dos checks na fase 0
    findings/       # um .md por achado com detalhe e patch (para auditoria)
```

Adicione `.security-loop/` ao `.gitignore` do projeto (estado é local, não vai para o repo).

## Schema do state.json

```json
{
  "version": 1,
  "started_at": "2026-07-15T14:00:00-03:00",
  "scope": ".",
  "branch": "security-hardening/2026-07-15",
  "iteration": 4,
  "max_iterations": 20,
  "baseline": {
    "checks": [
      { "id": "tests", "cmd": "npm test", "status": "pass" },
      { "id": "health", "cmd": "curl -sf localhost:8130/health", "status": "pass" },
      { "id": "service", "cmd": "docker compose ps --status running -q | wc -l", "status": "pass", "expect": "3" }
    ],
    "failing_at_baseline": []
  },
  "findings": [
    {
      "id": "F001",
      "severity": "CRITICAL",
      "confidence": "High",
      "category": "sql-injection",
      "file": "api/users.php",
      "line": 42,
      "summary": "Interpolação direta de $_GET[id] em query",
      "status": "fixed",
      "commit": "abc1234",
      "attempts": 1
    },
    {
      "id": "F002",
      "severity": "HIGH",
      "confidence": "High",
      "category": "hardcoded-secret",
      "file": "config.php",
      "line": 7,
      "summary": "API key da Stripe hardcoded",
      "status": "blocked",
      "blocked_reason": "check 'tests' falhou pós-fix: fixture usa a key literal",
      "attempts": 2
    }
  ],
  "human_tasks": [
    "Rotacionar a API key da Stripe exposta em config.php (removida do código, chave velha ainda válida)"
  ],
  "stop": null
}
```

## Estados de um achado

```
pending ──fix ok──▶ fixed
   │
   ├──check falha, rollback, re-tenta 1x──▶ pending (attempts+1)
   │        └──falha de novo──▶ blocked
   ├──confiança Low ou decisão humana──▶ reported (patch proposto, sem aplicar)
   └──usuário mandou pular──▶ skipped
```

Regras:
- `attempts` máximo por achado: 2. Segunda falha → `blocked`, nunca terceira tentativa.
- A re-tentativa (attempts=2) só é válida com abordagem DIFERENTE da primeira — se não
  existe abordagem alternativa, vá direto para `blocked`.
- `blocked` e `reported` sempre carregam o patch proposto em `findings/<id>.md`.

## Transições do loop (campo `stop`)

| Valor | Quando |
|---|---|
| `null` | loop em andamento |
| `"sucesso"` | nenhum finding `pending` |
| `"sem-progresso"` | 3 iterações seguidas sem novo `fixed` |
| `"check-quebrado"` | checks falham APÓS rollback confirmado limpo (`git status` limpo, ainda falha) |
| `"esgotamento"` | `iteration >= max_iterations` |
| `"bloqueio"` | só restam findings que exigem decisão humana |

## Retomada de sessão

1. Leia `.security-loop/state.json`. Se não existe → não há loop; comece da fase 0.
2. Confira coerência: branch atual == `state.branch`? `git log --oneline` contém os
   commits dos findings `fixed`? Divergência → pare e reporte, não "conserte" o estado.
3. Re-rode os checks do baseline (o ambiente pode ter mudado desde a última sessão).
   - Checks piores que o baseline gravado → trate como `check-quebrado` até o usuário resolver.
4. Continue do primeiro finding `pending` na ordem de severidade.

## Scan compacto (fallback sem o plugin security-review)

Quando as references do security-review não estão disponíveis, escaneie nesta ordem:

1. **Dependências**: lockfiles (`package-lock.json`, `composer.lock`, `requirements.txt`,
   `go.sum`, `Cargo.lock`, `Gemfile.lock`) — versões antigas pinadas, libs de crypto
   depreciadas, pacotes com CVE conhecido do seu conhecimento.
2. **Secrets**: grep por padrões de alta precisão —
   `(api[_-]?key|secret|password|passwd|token)\s*[:=]\s*['"][^'"]{8,}`,
   prefixos conhecidos (`sk_live_`, `AKIA`, `ghp_`, `xox[bp]-`, `AIza`), blocos
   `-----BEGIN .* PRIVATE KEY-----`, strings de conexão com credencial embutida.
   Cheque também `.env` versionado, Dockerfiles, CI/CD e dumps de log.
3. **Injection**: concatenação/interpolação de entrada do usuário em SQL, `exec`/`system`/
   `spawn`/`shell_exec`, `innerHTML`/`dangerouslySetInnerHTML`/`echo` sem escape,
   `include`/`require` com input, header injection.
4. **Auth/acesso**: endpoints sensíveis sem checagem de auth, IDs previsíveis sem
   verificação de dono (IDOR), JWT sem validação de expiração/alg, ausência de CSRF
   em mutações, mass assignment.
5. **Dados/crypto**: MD5/SHA1 para senha, `Math.random()`/`rand()` para token,
   TLS verify desligado, path traversal (`../` em caminhos vindos do usuário), SSRF
   (URL do usuário em fetch server-side), desserialização de input.
6. **Fluxo entre arquivos**: para cada entrada HTTP, siga o dado até o sink. Vulnerabilidade
   só é real se o caminho entrada→sink não tem sanitização — verifique antes de reportar.

Cada achado: severidade, confiança, arquivo:linha, trecho exato, o que um atacante consegue fazer.
