---
name: forge-agent-loop
description: Projeta, documenta e instala loops de agentes verificáveis e retomáveis, com estado em disco, critérios externos de parada e adaptadores para Codex, Claude Code e OpenCode. Use quando o usuário pedir para criar, forjar, especificar, endurecer, portar ou automatizar um workflow iterativo; criar um loop autônomo; transformar uma tarefa repetitiva em loop; ou adaptar um loop existente entre harnesses. Não usar para tarefas agendadas cujo resultado não altera a próxima ação, nem executar um loop sem pedido explícito.
---

# Forge Agent Loop

Criar a especificação e, quando solicitado, os adaptadores de execução de um loop. Separar sempre:

- **núcleo portátil:** objetivo, evidência, estado e parada;
- **adaptador:** modo de invocar o mesmo núcleo em Codex, Claude Code ou OpenCode;
- **execução:** só iniciar quando o usuário pedir explicitamente para rodar.

## Fluxo

### 1. Triar

Perguntar internamente: **a evidência de uma volta muda a próxima ação?**

- Se não, explicar que é uma tarefa recorrente, não um loop adaptativo, e entregar um prompt ou agendamento simples.
- Se sim, continuar.

Não confundir “rodar três vezes” com loop. Deve existir feedback que selecione a ação seguinte.

### 2. Descobrir o contexto

Inspecionar antes de entrevistar:

- raiz do repositório e instruções `AGENTS.md`/`CLAUDE.md`;
- scripts de teste, lint, build e métricas já existentes;
- skills que o loop pode compor;
- permissões, ambiente e operações de risco.

Perguntar apenas o que não puder ser inferido com segurança. Cobrir, uma pergunta por vez quando necessário:

1. estado final observável;
2. check externo que prova avanço e sucesso;
3. gatilho e cadência;
4. limites de voltas, tempo e custo;
5. ações que exigem aprovação;
6. local do estado e escopo projeto/global;
7. harnesses desejados;
8. se deve apenas especificar, instalar adaptadores ou também executar.

### 3. Classificar o loop

Escolher um modo:

- **sessão única:** cabe no contexto e termina em poucas voltas;
- **retomável:** pode atravessar sessões; registrar tudo em disco;
- **orquestrado externamente:** requer processo externo para iniciar sessões frescas. Não inventar daemon, cron ou `while true`; entregar somente se o usuário autorizar a automação externa.

### 4. Criar o esqueleto

Ler [references/spec.md](references/spec.md) antes de escrever a especificação.

Executar:

```bash
python3 <diretório-da-skill>/scripts/forge_loop.py init \
  --name <nome> \
  --scope project \
  --max-iterations <N>
```

Descobrir `<diretório-da-skill>` pelo caminho real desta skill. Em Claude, `${CLAUDE_SKILL_DIR}` também pode ser usado. Para escopo global, usar `--scope global`. Não sobrescrever artefatos sem `--force` e confirmação adequada.

O comando cria:

- `loops/<nome>/<nome>-loop.md` no projeto, ou `~/.agent-loops/<nome>/<nome>-loop.md` no escopo global;
- `state.json`, a memória mínima e legível por máquina.

Preencher a especificação com evidência concreta do projeto. Trocar `status: draft` por `status: ready` somente quando nenhum marcador pendente permanecer.
Atualizar também o `status` de `state.json` para `ready`; documento e estado não podem divergir.

### 5. Endurecer

Aplicar todas as regras:

- Usar check externo; nunca parar por autoavaliação vaga.
- Registrar comando, código de saída e resumo da evidência em cada volta.
- Definir `sucesso`, `sem-progresso`, `bloqueado` e `esgotado` como estados distintos.
- Tratar erro, timeout e teto atingido como não-sucesso.
- Fotografar a linha de base antes da primeira mudança.
- Fazer uma unidade reversível de mudança por volta.
- Manter mudança apenas se o check principal passar e os guardrails não regredirem.
- Impedir ciclos entre sub-loops e contabilizar o teto multiplicativo.
- Exigir aprovação antes de produção, publicação, mensagens externas, gastos, exclusões e outras ações irreversíveis.
- Nunca incluir segredos, tokens ou dados sensíveis no estado.
- Preservar alterações pré-existentes do usuário.

Quando o sucesso depender de julgamento, congelar uma rubrica antes da primeira volta, separar geração e avaliação quando possível e registrar a justificativa do juiz junto com a decisão.

### 6. Instalar adaptadores opcionais

Ler [references/harnesses.md](references/harnesses.md) antes de instalar adaptadores.

Só instalar quando o usuário pedir. Usar o subcomando dedicado; ele não reescreve a especificação nem o estado:

```bash
python3 <diretório-da-skill>/scripts/forge_loop.py install-adapters \
  --spec <caminho>/<nome>-loop.md \
  --harness codex --harness claude --harness opencode
```

No escopo de projeto, gerar:

- `.agents/skills/loop-<nome>/SKILL.md` para Codex e OpenCode;
- `.claude/skills/loop-<nome>/SKILL.md` para Claude Code.

Omitir `--harness` instala os três. Informar uma ou mais opções para customizar a instalação. Usar `--force` somente para substituir adaptadores existentes, nunca como atalho para recriar o loop.

Os adaptadores devem apontar para uma única especificação; não duplicar a lógica do loop.

### 7. Validar

Executar a validação estrita:

```bash
python3 <diretório-da-skill>/scripts/forge_loop.py validate \
  --spec <caminho>/<nome>-loop.md
```

Corrigir todos os erros. `--allow-draft` serve somente durante autoria e nunca para a entrega final.

Antes de entregar, confirmar:

- o check pode realmente ser executado no ambiente;
- a condição `Pronto =` é decidível pela saída registrada;
- o teto é finito;
- o estado permite retomada sem depender do histórico da conversa;
- cada adaptador usa a sintaxe do harness correto;
- o Git mostra apenas mudanças esperadas.

### 8. Executar somente sob pedido explícito

Ao executar um loop instalado:

1. ler a especificação e validar;
2. carregar `state.json` e reconciliar com o repositório atual;
3. rodar a linha de base se ainda não existir;
4. executar uma volta de cada vez;
5. persistir estado atomicamente depois do check;
6. continuar até um estado terminal ou até uma aprovação humana ser necessária;
7. relatar o estado terminal com a evidência final.

Não declarar sucesso com base em texto produzido pelo próprio agente.

## Entrega

Informar:

- caminho da especificação e do estado;
- adaptadores criados, se houver;
- check principal e condição de sucesso;
- limites e aprovações;
- resultado da validação;
- como invocar no(s) harness(es) selecionado(s).

Se houver execução, informar também voltas consumidas, mudanças aceitas, evidência final e motivo terminal.
