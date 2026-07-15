---
name: sandeco-loop
description: >
  Entrevista, especifica, endurece e instala loops de agente com checks externos,
  estado retomável em disco, guardrails reais, estados de parada nomeados e
  adaptadores automáticos para Codex, Claude Code e OpenCode. A habilidade central
  não é o prompt do loop, é o CHECK que decide se o trabalho terminou — e a
  evidência que separa sucesso real de autoengano.
  Detecta automaticamente quando uma tarefa do usuário é candidata a loop e sugere
  a especificação antes mesmo de ser chamada.
  Use SEMPRE que o usuário disser: "/sandeco-loop", "forja um loop",
  "especifica um loop", "cria um loop autônomo", "endurece esse loop",
  "quero automatizar essa tarefa iterativa", "loop que roda sozinho até",
  "loop de cobertura/testes/refatoração", "transforma isso num loop",
  "instala adaptadores para esse loop".
  Também use QUANDO DETECTAR o padrão: o usuário descreve uma tarefa repetitiva
  com verificação (ex: "preciso rodar os testes até passar", "tem que revisar
  todos os arquivos até ficar bom", "quero que execute isso N vezes melhorando
  a cada vez"). Nesse caso, sugira proativamente.
  NÃO use para tarefas agendadas cujo resultado não altera a próxima ação, nem
  para gerar slides Mira, nem para executar o loop sem pedido explícito.
---

# Sandeco Loop — Forja de Loops Verificáveis

Forjar a especificação completa de um loop e, quando solicitado, instalar os
adaptadores de execução para Codex, Claude Code e/ou OpenCode.

Separe sempre três planos:
1. **Núcleo portátil** — objetivo, check, evidência, estado e parada
2. **Adaptador** — invocação no harness específico (aponta para o mesmo núcleo)
3. **Execução** — só roda quando o usuário pedir explicitamente

---

## Fluxo

### Fase 0 — Triagem (antes de qualquer pergunta)

Pergunte a si mesmo: **"O resultado de cada volta muda a próxima ação?"**

- **Não**: avise que não é loop. Entregue um prompt agendado simples (tarefa + cadência) e encerre.
- **Sim**: prossiga para a entrevista.

Critérios que NÃO são loop: rodar 3 vezes o mesmo comando, gerar N variações independentes, executar em horário fixo sem feedback entre execuções.

### Fase 1 — Descoberta de contexto (antes de perguntar)

Inspecione o ambiente antes de entrevistar:
- Raiz do Git, `AGENTS.md`, `CLAUDE.md`, `opencode.json`
- Scripts de teste, lint, build, deploy já existentes
- Skills instaladas que o loop pode compor
- Permissões do ambiente (bash, escrita, rede)

Pergunte APENAS o que não puder inferir.

### Fase 2 — Entrevista (uma pergunta por vez)

1. **Meta** — estado final concreto e observável. O quê, não como.
2. **Entradas (opcional)** — o loop precisa perguntar algo ao usuário no início? Se for autônomo, não.
3. **Verificável?** — é número/teste/comando ou depende de juízo?
4. **Check** — qual comando/aferição prova que a volta avançou? SEMPRE externo.
5. **Gatilho** — manual, agendado (cron), ou por evento (PR, push)?
6. **Estados de parada** — sucesso, sem-progresso, bloqueado, esgotado.
7. **Skills chamadas** — quais skills o loop compõe?
8. **Memória** — onde vive o estado entre voltas?
9. **Guardrails** — teto de voltas/custo, ações que exigem aprovação humana.

### Fase 3 — Endurecimento (checklist teórico)

Cada regra existe por uma razão comprovada (ver referências teóricas):

- **Check externo**: nunca parar por "ficou bom". A parada vem de comando que roda fora do agente.
- **Evidência na conversa**: o avaliador só lê o transcript. O loop precisa RODAR o check e JOGAR a saída na conversa. A condição de parada é escrita sobre essa saída.
- **Juiz LLM**: se inevitável, rubrica congelada, separar gerador de avaliador, quebrar simetria de contexto (não compartilhar histórico de quem fez com quem julga).
- **Estados nomeados**: sucesso, sem-progresso (2 voltas sem ganho), bloqueado, esgotado. Erro NUNCA é sucesso.
- **Uma mudança por volta**: fotografe o "antes", mude uma coisa, verifique.
- **Skills nomeadas**: loop sem skills reusáveis é `while true` em volta de um estranho.
- **Sub-loops**: aninham com teto multiplicativo (P × F). Ciclos proibidos.
- **Memória em disco**: sobrevive entre voltas e permite contexto fresco.
- **Métrica de saúde**: custo por mudança aceita = tokens / mudanças que passaram no check.

### Fase 4 — Escolha o acionamento

- **Curto/médio (cabe no contexto)**: `/goal` que referencia o loop.
- **Longo (estoura contexto)**: esqueleto Ralph — laço shell que relê o documento + estado a cada volta.

### Fase 5 — Onde salvar

Pergunte (uma de cada vez):
1. **Local** (`./loops/<nome>/`) ou **global** (`~/.agent-loops/<nome>/`)?
2. **Quer comandos `/loop-<nome>`** nos harnesses?Instala adaptadores em `.agents/skills/`, `.claude/skills/`.

### Fase 6 — Escreva o documento

Use o gabarito em [references/spec.md](references/spec.md) para gerar `<nome>-loop.md`.
Crie também `state.json` ao lado.

### Fase 7 — Instale adaptadores (se solicitado)

Use [references/harnesses.md](references/harnesses.md) como guia.
Crie SKILL.md de adaptador em cada pasta de harness.
O adaptador NUNCA duplica a lógica do loop — só invoca a especificação.

### Fase 8 — Valide antes de entregar

```bash
python3 <skill-dir>/scripts/forge_loop.py validate --spec <caminho>/<nome>-loop.md
```

Corrija todos os erros. Verifique:
- O check roda no ambiente atual?
- `Pronto =` é decidível pela saída registrada?
- O teto é finito?
- O estado permite retomada sem o histórico da conversa?
- Cada adaptador usa a sintaxe correta do harness?

### Fase 9 — Auto-sugestão (gatilho proativo)

Detecte padrões na fala do usuário que indicam loop. Categorize por contexto:

**Padrões universais:**
> "rodar até passar", "melhorar até ficar bom", "revisar todos os arquivos",
> "executar N vezes", "até atingir X%", "validar cada um", "iterativamente",
> "fazer em todos", "um por um", "passar em cada", "até funcionar",
> "enquanto não passar", "tentar de novo", "refinar até"

**Padrões específicos do ecossistema Peep:**
| Projeto | Padrão detectável | Sugestão |
|---------|------------------|----------|
| Mira | "criar animação que melhora a cada iteração" | Loop de coreografia D3 |
| Gestor Peep | "testar todos os webhooks" | Loop de cobertura de testes |
| predicts | "validar todos os palpites da rodada" | Loop de validação em lote |
| Evo Manager | "verificar todas as instâncias" | Loop de healthcheck |
| Fin Dashboard | "atualizar todos os indicadores" | Loop de ETL |
| PeepNews | "revisar artigos pendentes" | Loop de revisão editorial |

**Trigger automático no opencode:** se o pedido do usuário contiver palavras-chave
(`iterar`, `cada`, `todos`, `até`, `enquanto`, `N vezes`, `repetir`, `loop`) E
mencionar verificação (`testar`, `validar`, `passar`, `verificar`), sugira
proativamente antes de executar qualquer ação.

**Resposta padrão:**
> "Isso se encaixa no padrão de loop do Sandeco — tarefa iterativa com verificação.
> Quer que eu forje uma especificação completa com check externo, estado retomável
> e adaptadores para Codex, Claude Code e OpenCode?"

NÃO sugira se: é tarefa única descartável, é agendamento fixo sem feedback,
já existe skill específica que cobre o caso, ou o usuário pediu execução direta.

---

## Entrega

Informe sempre:
- Caminho da especificação (`<nome>-loop.md`) e do estado (`state.json`)
- Adaptadores criados (se houver), com caminhos
- Check principal e condição de `Pronto =`
- Teto de voltas e ações protegidas
- Resultado da validação
- Métrica de saúde esperada
- Como invocar em cada harness instalado

---

---

## Quickstart — loops prontos para cenários comuns

Use estes templates quando o usuário não quiser passar pela entrevista completa.
Ajuste o nome e o contexto, e o loop sai em segundos.

### Loop de cobertura de testes
```yaml
name: cobertura-<modulo>
check: npm test -- --coverage
pronto: saída 0 + 100% no módulo alvo
passos: fotografe cobertura → ataque arquivo mais descoberto → 1 teste → prove vermelho/verde → rode suíte → aceite se nada regrediu
parada: 100% | 2 sem-progresso | 30 turnos
```

### Loop de revisão de PRs
```yaml
name: revisao-<repo>
check: gh pr view <n> --json reviewDecision | jq .reviewDecision
pronto: APPROVED em todos os PRs abertos
passos: liste PRs abertos sem approval → revise 1 PR → aprove ou solicite mudanças → marque como revisado
parada: todos aprovados | 2 sem-progresso | bloqueado se conflito
```

### Loop de healthcheck multi-serviço
```yaml
name: healthcheck-<projeto>
check: curl -s -o /dev/null -w '%{http_code}' <url>
pronto: todos os endpoints retornam 200
passos: liste endpoints → teste 1 → registre status → se falhou, tente reiniciar → notifique se persistir
parada: todos OK | 3 sem-progresso | bloqueado se 2+ críticos offline
```

### Loop de ETL incremental
```yaml
name: etl-<origem>
check: diff <(wc -l destino) <(wc -l destino.anterior)
pronto: diff > 0 sem erros
passos: conecte origem → extraia lote → transforme → carregue → compare linhas → registre timestamp
parada: sem dados novos | 2 sem-progresso | bloqueado se schema mudou
```

---

## Referências teóricas

- **2305.19118** — Self-Refine: iterative refinement with external feedback
- **2502.19559** — Constitutional AI, separation of generator and evaluator
- **Sandeco Loop original** — github.com/sandeco/prompts (loop specification pattern)
- **Forge Agent Loop** — peep-skills/plugins/forge-agent-loop (implementação irmã)
