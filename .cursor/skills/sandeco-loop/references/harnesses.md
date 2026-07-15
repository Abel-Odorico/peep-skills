# Adaptadores por harness — Sandeco Loop

## Índice

1. Regra comum
2. Codex
3. Claude Code
4. OpenCode
5. Escopo global vs projeto
6. Limites de portabilidade

---

## 1. Regra comum

Um único documento `<nome>-loop.md` como fonte da verdade.
O adaptador de cada harness apenas:
1. Exige invocação explícita (nunca executa automático)
2. Localiza e valida a especificação
3. Lê e atualiza `state.json`
4. Executa até estado terminal ou aprovação humana

Nunca duplicar critérios de aceite no adaptador — isso cria duas fontes de verdade.

---

## 2. Codex

- **Skill de projeto:** `.agents/skills/loop-<nome>/SKILL.md`
- **Invocação:** mencionar `$loop-<nome>` no pedido
- Preservar `AGENTS.md`, sandbox e aprovações do ambiente
- Não assumir `/goal` — objetivo persistente é capacidade do produto, não contrato portátil
- **Adaptador global:** `~/.agents/skills/loop-<nome>/SKILL.md`

---

## 3. Claude Code

- **Skill de projeto:** `.claude/skills/loop-<nome>/SKILL.md`
- **Invocação:** `/loop-<nome>` (plugin pode adicionar namespace)
- Usar `disable-model-invocation: true` para impedir disparo automático
- **Adaptador global:** `~/.claude/skills/loop-<nome>/SKILL.md`
- **Plugin:** também pode ser instalado via `claude plugin install`

---

## 4. OpenCode

- **Skill de projeto:** `.agents/skills/loop-<nome>/SKILL.md` (reusa Codex)
- **Invocação:** pedir explicitamente "Use a skill loop-<nome>"
- **Descoberta:** opencode lê de `.agents/skills/<nome>/SKILL.md`
- **Config:** verificar `opencode.json` — skill não pode estar em `deny`
- **Não assumir:** `/loop` nativo nem sessão persistente
- **Adaptador global:** `~/.agents/skills/loop-<nome>/SKILL.md`

---

## 5. Escopo global vs projeto

| Item | Projeto | Global |
|------|---------|--------|
| Especificação | `./loops/<nome>/` | `~/.agent-loops/<nome>/` |
| Codex | `.agents/skills/loop-<nome>/` | `~/.agents/skills/loop-<nome>/` |
| Claude | `.claude/skills/loop-<nome>/` | `~/.claude/skills/loop-<nome>/` |
| OpenCode | `.agents/skills/loop-<nome>/` | `~/.agents/skills/loop-<nome>/` |

Criar adaptadores globais só com autorização — afeta todos os projetos.

---

## 6. Limites de portabilidade

- Sintaxe de invocação, permissões, sandbox e subagentes variam entre harnesses
- O loop nunca amplia permissões do harness
- Ações externas continuam sujeitas às aprovações do ambiente
- Automação entre sessões exige orquestrador externo autorizado (a skill não promete background)
- OpenCode não tem `/goal` nativo — usar skill explícita sempre
