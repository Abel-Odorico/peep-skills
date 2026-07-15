# Checks de operação por stack — o que significa "sistema continua no ar"

O baseline é a combinação de 2 a 5 checks abaixo, escolhidos pela stack detectada.
Ordem de preferência: **teste automatizado > health endpoint > smoke test > status de
serviço > build/lint**. Sempre inclua pelo menos um check que exercite o runtime de
verdade — build passar não prova que a aplicação responde.

Cada check precisa ser: executável por comando único, determinístico, e com critério de
pass/fail objetivo (exit code ou output comparável). Grave comando + resultado no state.json.

## Detecção da stack

| Arquivo presente | Stack provável |
|---|---|
| `composer.json` / `*.php` | PHP (Laravel se `artisan`) |
| `package.json` | Node (Next se `next.config.*`, Express etc.) |
| `requirements.txt` / `pyproject.toml` | Python (FastAPI/Django/Flask) |
| `docker-compose.yml` / `Dockerfile` | serviços containerizados |
| `go.mod`, `Cargo.toml`, `Gemfile` | Go, Rust, Ruby |

## Checks por tipo

### Testes automatizados (melhor sinal, use se existir)
```bash
# Node                         # PHP                          # Python
npm test --silent              ./vendor/bin/phpunit           pytest -q
# Laravel                      # Go                           # Rust
php artisan test               go test ./...                  cargo test -q
```
Pass = exit 0. Se a suíte demora >5 min, use o subconjunto de smoke/integration.

### Health endpoint (aplicações web)
```bash
curl -sf -m 10 http://localhost:<porta>/health          # ou /api/health, /status
curl -sf -m 10 -o /dev/null -w '%{http_code}' http://localhost:<porta>/   # espera 200/302
```
Descubra a porta em config/nginx/docker-compose. Sem endpoint de health, use a raiz.

### Smoke test funcional (quando não há suíte)
Um fluxo real mínimo, ex.:
```bash
# login retorna token
curl -sf -m 10 -X POST localhost:8000/api/login -d '{"user":"smoke","pass":"..."}' \
  -H 'Content-Type: application/json' | grep -q token
# página renderiza conteúdo esperado
curl -sf localhost:8080/ | grep -qi '<title>'
```
Use credencial de teste/admin já existente — NUNCA crie usuário novo em base real.

### Status de serviço
```bash
systemctl is-active <servico>                    # espera "active"
docker compose ps --format '{{.Name}} {{.State}}' | grep -cv running   # espera 0
docker inspect -f '{{.State.Health.Status}}' <container>              # espera "healthy"
```

### Sintaxe / build (barato, roda primeiro para falhar rápido)
```bash
php -l <arquivo_editado>                # PHP: lint só dos arquivos tocados
node --check <arquivo_editado>          # Node sem bundler
npm run build                           # quando o projeto tem build
python -m py_compile <arquivo_editado>  # Python
nginx -t                                # se tocou config nginx (NUNCA reload automático)
```

## Montagem do baseline (fase 0)

1. Detecte a stack e selecione checks: sintaxe (dos arquivos que serão tocados) +
   1 check de runtime (health/smoke) + testes se existirem + serviço se aplicável.
2. Rode todos, salve output bruto em `.security-loop/baseline.log`.
3. Check que já falha → entra em `failing_at_baseline`: não reprova fixes, mas se um
   fix o fizer falhar DIFERENTE (novo erro), trate como regressão.

## Execução pós-fix (passo CHECK do loop)

- Rode na ordem: sintaxe → build → testes → health/smoke → serviço. Pare no primeiro fail.
- Timeout por check: 10 min. Timeout = fail.
- Fail → capture o output no finding (`blocked_reason`) antes do rollback.
- Aplicações que precisam de restart para carregar código (PHP-FPM opcache, serviços
  systemd, containers): em DEV, reinicie e re-teste. Em máquina com produção junto,
  NÃO reinicie serviço compartilhado — valide por teste/lint e marque restart como
  tarefa humana no relatório.

## Anti-autoengano

- NUNCA afrouxe um check para o fix passar (pular teste, aumentar timeout, trocar
  `-sf` por `-s`). Check é contrato: se está errado, corrija o check ANTES do loop
  e re-estabeleça o baseline.
- NUNCA marque `fixed` com check "quase passando" ou "falha não relacionada" — falha
  não relacionada ou é `failing_at_baseline` ou é regressão sua.
- Desconfie de pass instantâneo: teste que passa em 0.1s provavelmente não rodou nada.
