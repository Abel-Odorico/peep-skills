# Adaptadores por harness

## Índice

1. Regra comum
2. Codex
3. Claude Code
4. OpenCode
5. Escopo global
6. Limites de portabilidade

## 1. Regra comum

Usar o mesmo documento `loops/<nome>/<nome>-loop.md`. O adaptador apenas:

1. exige invocação explícita;
2. localiza e valida a especificação;
3. lê e atualiza `state.json`;
4. executa até um estado terminal ou aprovação necessária.

Nunca copiar critérios de aceite para o adaptador. Isso criaria duas fontes de verdade.

## 2. Codex

- Skill de projeto: `.agents/skills/loop-<nome>/SKILL.md`.
- Invocação explícita: mencionar `$loop-<nome>` no pedido.
- Preservar `AGENTS.md`, sandbox e aprovações do ambiente.
- Não assumir que `/goal` existe. Um objetivo persistente é capacidade do produto, não parte do contrato portátil.

## 3. Claude Code

- Skill de projeto: `.claude/skills/loop-<nome>/SKILL.md`.
- Invocação: `/loop-<nome>`; em plugin, o nome pode ser namespaced.
- Usar `disable-model-invocation: true` em loops executáveis para impedir disparo automático.
- Não depender de `.claude/commands/`; skills são o formato preferido e suportam arquivos auxiliares.

## 4. OpenCode

- OpenCode descobre `.agents/skills/<nome>/SKILL.md`; reutilizar o adaptador do Codex.
- Invocar pedindo explicitamente `Use a skill loop-<nome>` quando a interface não oferecer menção direta.
- Confirmar que a permissão `skill` não está `deny` em `opencode.json`.
- Não assumir `/loop` nativo nem semântica de sessão persistente.

## 5. Escopo global

- Especificação: `~/.agent-loops/<nome>/<nome>-loop.md`.
- Codex: `~/.agents/skills/loop-<nome>/SKILL.md`.
- Claude Code: `~/.claude/skills/loop-<nome>/SKILL.md`.
- OpenCode: pode reutilizar `~/.agents/skills` ou usar `~/.config/opencode/skills`.

Criar adaptadores globais somente com autorização, pois afetam todos os projetos do usuário.

## 6. Limites de portabilidade

- Sintaxe de invocação, permissões, sandbox, retomada e subagentes variam.
- O loop nunca amplia permissões do harness.
- Ações externas continuam sujeitas às aprovações do ambiente.
- Automação entre sessões exige um orquestrador externo autorizado; a skill não promete execução em background por si só.
