---
name: security-hardening-loop
description: 'Loop autônomo de hardening de segurança: escaneia o projeto com a metodologia do security-review, prioriza achados por severidade e CORRIGE as vulnerabilidades uma a uma, verificando após cada correção que o sistema continua operacional (testes, health checks, serviços) — com rollback automático quando algo quebra. Estado retomável em disco, guardrails e paradas nomeadas. Use quando o usuário disser: "corrige as vulnerabilidades", "endurece a segurança do projeto", "hardening do projeto", "loop de segurança", "conserta as falhas de segurança sem derrubar o sistema", "busca e corrige fragilidades", "aplica os patches de segurança", "/security-hardening-loop", "security fix loop". Para APENAS relatório de vulnerabilidades sem correção, use security-review.'
---

# Security Hardening Loop

Encontra vulnerabilidades e as **corrige** — uma por vez, em ordem de severidade — mantendo o
sistema operacional o tempo inteiro. Cada correção só é aceita depois que um CHECK externo
confirma que nada quebrou; caso contrário, rollback automático e a fila segue.

**Regra de ouro** (herdada do sandeco-loop): a habilidade central não é a correção, é o
**CHECK que decide se a correção pode ficar**. Sem check verde, a correção não existe.

## Diferença para o security-review

| | security-review | security-hardening-loop |
|---|---|---|
| Escaneia | ✅ | ✅ (mesma metodologia) |
| Corrige | ❌ propõe patches | ✅ aplica, uma por iteração |
| Verifica operação | ❌ | ✅ baseline + check pós-fix |
| Rollback | — | ✅ automático via git |
| Estado retomável | — | ✅ `.security-loop/state.json` |

Se o plugin `security-review` estiver instalado, use as references dele
(`vuln-categories.md`, `secret-patterns.md`, `language-patterns.md`,
`vulnerable-packages.md`) na fase de scan. Se não estiver, execute o scan com o
protocolo compacto descrito em `references/loop-protocol.md`.

## Pré-requisitos (verificar ANTES de qualquer coisa)

1. **Git obrigatório**: o projeto precisa ser um repositório git com working tree limpa.
   - Sem git → ofereça `git init` + commit inicial. Sem isso, NÃO execute o loop (não há rollback seguro).
   - Working tree suja → peça para o usuário commitar ou guardar as mudanças antes.
2. **Nunca em produção direta**: se o diretório for produção servida ao vivo (ex.: `/var/www`
   ativo, container em execução com bind mount), avise e prefira trabalhar em cópia/branch,
   com deploy manual depois.
3. **Aprovação de escopo**: antes de iniciar, mostre o plano (o que será escaneado, quais
   severidades serão corrigidas) e confirme com o usuário. Padrão: corrige CRITICAL e HIGH;
   MEDIUM sob confirmação; LOW/INFO só relatório.

## Fase 0 — Baseline operacional

Antes de tocar em qualquer arquivo, estabeleça o que significa "sistema operacional":

1. Detecte a stack e escolha os checks em `references/verification-checks.md`
   (testes, health endpoint, status de serviço, smoke test, lint/build).
2. **Execute os checks AGORA** e grave o resultado como baseline em
   `.security-loop/state.json`.
3. Se um check já falha antes de qualquer correção, registre como `baseline_failing` —
   esse check não pode reprovar correções (não foi você que quebrou), mas também não
   pode piorar.

Regra: após cada correção, o resultado dos checks deve ser **≥ baseline**. Nunca pior.

## Fase 1 — Scan

Execute o scan completo na metodologia security-review:

1. Resolução de escopo (path informado ou projeto inteiro) e detecção de linguagem/framework.
2. Auditoria de dependências (CVEs conhecidos).
3. Varredura de secrets (chaves, senhas, tokens hardcoded, `.env` commitado).
4. Deep scan de vulnerabilidades: injection (SQLi, XSS, command), autenticação e
   access control (BOLA/IDOR, JWT fraco, CSRF), manuseio de dados (path traversal,
   SSRF, desserialização), criptografia fraca, lógica de negócio.
5. Análise de fluxo de dados entre arquivos (entrada do usuário → sink perigoso).
6. Passada de autoverificação: descarte falsos positivos ANTES de entrarem na fila.

Saída da fase: lista de achados com severidade (CRITICAL/HIGH/MEDIUM/LOW/INFO),
confiança (High/Medium/Low), arquivo:linha e categoria.

## Fase 2 — Fila de correção

1. Grave todos os achados em `.security-loop/state.json` (schema em
   `references/loop-protocol.md`), ordenados por severidade e depois por confiança.
2. Entram na fila de correção: CRITICAL e HIGH (e MEDIUM se o usuário aprovou).
   LOW/INFO ficam só no relatório.
3. Achados com confiança Low NÃO são corrigidos automaticamente — viram item de
   relatório com patch proposto para revisão humana.
4. Crie o branch de trabalho: `security-hardening/AAAA-MM-DD`.

## Fase 3 — Loop de correção

Para CADA achado da fila, nesta ordem exata:

```
1. PICK    — próximo achado pending de maior severidade
2. FIX     — aplique a correção mínima (playbook em references/fix-playbooks.md)
             • um achado por iteração; nunca refatore além do necessário
             • preserve estilo, nomes e estrutura do código original
3. CHECK   — rode TODOS os checks do baseline
             • todos ≥ baseline → continua
             • qualquer um pior que baseline → passo 5
4. COMMIT  — git commit isolado: "security: corrige <categoria> em <arquivo>"
             marque o achado como fixed no state.json → volta ao passo 1
5. ROLLBACK — git checkout/restore para desfazer SÓ esta correção
             marque como blocked com o motivo (qual check falhou, output)
             → volta ao passo 1 com o PRÓXIMO achado (nunca re-tenta cego)
```

Atualize `state.json` a cada transição — o loop precisa ser retomável se a sessão cair.
Na retomada, leia o state, confira `git log` do branch e continue do primeiro `pending`.

## Paradas nomeadas (encerre o loop declarando qual ocorreu)

- **SUCESSO** — fila vazia: todos os achados fixed, blocked ou deliberadamente skipped.
- **SEM-PROGRESSO** — 2 rollbacks consecutivos no mesmo achado ou 3 iterações sem
  nenhum fixed novo.
- **CHECK-QUEBRADO** — os checks falham mesmo após rollback (ambiente degradou por
  causa externa). Pare imediatamente, não corrija mais nada, reporte.
- **ESGOTAMENTO** — atingiu o teto de iterações (padrão: 20; configurável).
- **BLOQUEIO** — correção exige decisão que só o usuário pode tomar (ex.: trocar
  secret em produção, migração de schema). Liste as pendências e pare.

## Guardrails

- NUNCA aplique correção sem baseline estabelecido.
- NUNCA edite mais de um achado por iteração; nunca "aproveite para melhorar" código são.
- NUNCA rode em working tree suja nem fora de branch dedicado.
- NUNCA faça push, deploy ou restart de serviço de produção sem pedido explícito.
- NUNCA delete dados, tabelas ou arquivos de config — correção de secret exposto =
  mover para variável de ambiente + invalidar/rotacionar a chave COM o usuário.
- Rotação de secrets: o loop remove o secret do código, mas a revogação da chave velha
  é sempre tarefa humana listada no relatório final.
- Correções de dependência (bump de versão) exigem que o lockfile seja regenerado e os
  checks passem; major version bump vai para BLOQUEIO, não para fix automático.

## Fase 4 — Re-scan e relatório final

1. Re-execute o scan (fase 1) no escopo corrigido: confirme que cada achado fixed
   não aparece mais.
2. Gere o relatório final:
   - Tabela-resumo: achados por severidade × status (fixed/blocked/skipped/reported).
   - Por correção: arquivo, categoria, commit hash, check que validou.
   - Por bloqueio: motivo, output do check, patch proposto para revisão humana.
   - Pendências humanas: secrets a rotacionar, bumps major, decisões adiadas.
3. Deixe o branch pronto para revisão. Merge é decisão do usuário — sugira
   `git diff main...security-hardening/<data>` para revisar tudo de uma vez.

## Arquivos de referência

- `references/loop-protocol.md` — schema do state.json, máquina de estados, retomada,
  scan compacto para quando o security-review não está instalado.
- `references/verification-checks.md` — checks de operação por stack (PHP, Node,
  Python, Docker, systemd, nginx) e como montar o baseline.
- `references/fix-playbooks.md` — correção segura por categoria de vulnerabilidade:
  o fix mínimo que fecha a falha sem mudar comportamento legítimo.
