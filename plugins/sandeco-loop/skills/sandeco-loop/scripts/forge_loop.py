#!/usr/bin/env python3
"""Scaffold, valida e instala adaptadores de loops Sandeco.

Comandos:
  init              — cria especificação + state.json + adaptadores opcionais
  validate          — valida especificação e estado contra o contrato
  install-adapters  — instala adaptadores sem alterar especificação

Uso:
  python3 forge_loop.py init --name meu-loop [--scope project|global] [opções]
  python3 forge_loop.py validate --spec loops/meu-loop/meu-loop-loop.md
  python3 forge_loop.py install-adapters --spec <caminho> [--harness codex]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path


REQUIRED_HEADINGS = (
    "Descrição", "Use quando", "Entradas", "Meta",
    "Verificação", "Passos da volta", "Estados de parada",
    "Guardrails", "Memória", "Sub-loops", "Como acionar",
    "Métrica de saúde",
)
TERMINAL_STATES = ("sucesso", "sem-progresso", "bloqueado", "esgotado")
PENDING_MARKERS = ("[PREENCHER]", "[TODO]", "<preencher>")

# Quickstart templates: nome -> (check, pronto, parada, descrição)
QUICKSTART_TEMPLATES = {
    "cobertura": {
        "desc": "Loop de cobertura de testes",
        "check": "npm test -- --coverage",
        "pronto": "saída 0 + 100% no módulo alvo",
        "parada": "100% | 2 sem-progresso | 30 turnos",
    },
    "revisao": {
        "desc": "Loop de revisão de PRs",
        "check": "gh pr view <n> --json reviewDecision | jq .reviewDecision",
        "pronto": "APPROVED em todos os PRs abertos",
        "parada": "todos aprovados | 2 sem-progresso | bloqueado se conflito",
    },
    "healthcheck": {
        "desc": "Loop de healthcheck multi-serviço",
        "check": "curl -s -o /dev/null -w '%{http_code}' <url>",
        "pronto": "todos os endpoints retornam 200",
        "parada": "todos OK | 3 sem-progresso | bloqueado se 2+ críticos offline",
    },
    "etl": {
        "desc": "Loop de ETL incremental",
        "check": "diff <(wc -l destino) <(wc -l destino.anterior)",
        "pronto": "diff > 0 sem erros",
        "parada": "sem dados novos | 2 sem-progresso | bloqueado se schema mudou",
    },
}


def slugify(value: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    if not s or len(s) > 48:
        raise ValueError("slug deve ter 1-48 caracteres")
    return s


def git_root(cwd: Path) -> Path:
    r = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=cwd,
                       capture_output=True, text=True, check=False)
    return Path(r.stdout.strip()) if r.returncode == 0 else cwd.resolve()


def write_atomically(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(f".tmp.{os.urandom(4).hex()}")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def check_existing(paths: list[Path], force: bool) -> None:
    existing = [p for p in paths if p.exists()]
    if existing and not force:
        raise FileExistsError(
            "Já existem:\n" + "\n".join(f"  - {p}" for p in existing) +
            "\nUse --force para substituir."
        )


def spec_template(name: str, scope: str, max_iter: int) -> str:
    return f"""---
name: {name}
schema-version: 1
scope: {scope}
status: draft
owner: human
base-teorica: 2305.19118, 2502.19559
---

# Loop {name}

## Descrição
[PREENCHER] O que melhora a cada volta, em até duas frases.

## Use quando
[PREENCHER] Situação concreta. Não usar quando: [PREENCHER].

## Entradas
[PREENCHER] ou "Não se aplica".

## Meta
[PREENCHER] Estado final concreto. Verificável? sim/não.

## Verificação
- Check primário: `[PREENCHER]`
- Evidência registrada: código de saída + resumo em state.json.
- Pronto = [PREENCHER predicado exato].
- Regressão: `[PREENCHER]`
- Falha/timeout: registrar; nunca tratar como sucesso.

## Passos da volta
1. Reconciliar state.json com o repositório.
2. Medir linha de base.
3. Escolher o maior gargalo.
4. Aplicar UMA mudança reversível.
5. Rodar check + regressão.
6. Aceitar/reverter.
7. Persistir.
8. Avaliar parada.

## Estados de parada
- sucesso: [PREENCHER]
- sem-progresso: 2 voltas sem ganho
- bloqueado: [PREENCHER]
- esgotado: {max_iter} voltas

## Guardrails
- Teto: {max_iter} voltas.
- Aprovação antes de: produção, exclusão, gasto.

## Memória / estado
state.json ao lado.

## Sub-loops (opcional)
[PREENCHER] ou "Não se aplica".

## Como acionar
/goal Use o loop {name}. Até <condição>. Pare se <bloqueio> ou após {max_iter} turnos.

## Métrica de saúde
tokens / mudanças aceitas.
"""


def state_template(name: str, max_iter: int) -> str:
    return json.dumps({
        "schema_version": 1,
        "loop": name,
        "status": "draft",
        "iteration": 0,
        "max_iterations": max_iter,
        "baseline": None,
        "last_check": None,
        "accepted_changes": [],
        "attempts": [],
        "terminal_reason": None,
    }, ensure_ascii=False, indent=2) + "\n"


def adapter_skill(name: str, spec_rel: str, harness: str) -> str:
    disable = "disable-model-invocation: true\n" if harness == "claude" else ""
    return f"""---
{disable}description: Executa, só sob pedido explícito, o loop {name} em {spec_rel}; valida, retoma state.json, para por sucesso/sem-progresso/bloqueio/esgotamento.
---

# Loop {name}

1. Localizar e ler `{spec_rel}` na raiz do Git.
2. Validar a especificação.
3. Carregar `state.json` ao lado, reconciliar com repositório.
4. Executar uma volta por vez, persistindo evidência após cada check.
5. Parar apenas em estado terminal ou quando aprovação humana for necessária.
6. Nunca ampliar permissões, tratar erro como sucesso, ou alterar código fora do escopo.
7. Relatar: estado terminal, evidência final, voltas consumidas, mudanças aceitas.
"""


def parse_frontmatter(text: str) -> dict:
    m = re.match(r"\A---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not m:
        return {}
    data = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            data[k.strip()] = v.strip()
    return data


def validate(path: Path, allow_draft: bool = False) -> list[str]:
    errs = []
    if not path.is_file():
        return [f"Arquivo não encontrado: {path}"]

    text = path.read_text("utf-8")
    fm = parse_frontmatter(text)
    for k in ("name", "schema-version", "scope", "status", "owner"):
        if not fm.get(k):
            errs.append(f"frontmatter sem `{k}`")

    name = fm.get("name", "")
    if name and slugify(name) != name:
        errs.append("name deve estar em kebab-case")
    if fm.get("schema-version") != "1":
        errs.append("schema-version deve ser 1")
    if fm.get("scope") not in ("project", "global"):
        errs.append("scope deve ser project ou global")
    status = fm.get("status", "")
    if status not in ("draft", "ready", "running", "retired"):
        errs.append(f"status inválido: {status}")
    if not allow_draft and status != "ready":
        errs.append("entrega final exige status: ready")

    for h in REQUIRED_HEADINGS:
        if f"## {h}" not in text:
            errs.append(f"Seção ausente: {h}")

    lower = text.lower()
    for s in TERMINAL_STATES:
        if s not in lower:
            errs.append(f"Estado terminal ausente: {s}")
    for p in ("check primário:", "evidência registrada:", "pronto ="):
        if p not in lower:
            errs.append(f"Verificação sem `{p}`")

    if not allow_draft:
        for m in PENDING_MARKERS:
            if m.lower() in lower:
                errs.append(f"Marcador pendente: {m}")

    state_p = path.with_name("state.json")
    if not state_p.is_file():
        errs.append(f"state.json ausente: {state_p}")
    else:
        try:
            st = json.loads(state_p.read_text("utf-8"))
            if st.get("loop") != name:
                errs.append("state.json.loop != spec.name")
            sts = st.get("status")
            ok_states = ("draft", "ready", "running", "success",
                         "no-progress", "blocked", "exhausted")
            if sts not in ok_states:
                errs.append(f"state.json.status inválido: {sts}")
            if not allow_draft and sts == "draft":
                errs.append("entrega final exige state.json status ready+")
            if not isinstance(st.get("max_iterations"), int) or st.get("max_iterations", 0) < 1:
                errs.append("state.json.max_iterations inválido")
        except (json.JSONDecodeError, OSError) as e:
            errs.append(f"state.json inválido: {e}")
    return errs


def cmd_init(args: argparse.Namespace) -> int:
    name = slugify(args.name)
    if args.max_iterations < 1:
        raise ValueError("max-iterations precisa ser positivo")

    if args.scope == "project":
        root = Path(args.root).resolve() if args.root else git_root(Path.cwd())
        loop_dir = root / "loops" / name
        spec_rel = f"loops/{name}/{name}-loop.md"
    else:
        root = (Path(args.root).expanduser().resolve()
                if args.root else Path.home() / ".agent-loops")
        loop_dir = root / name
        spec_rel = str(loop_dir / f"{name}-loop.md")

    spec = loop_dir / f"{name}-loop.md"
    state = loop_dir / "state.json"
    outputs = [(spec, spec_template(name, args.scope, args.max_iterations)),
               (state, state_template(name, args.max_iterations))]

    if args.install_adapters:
        harnesses = set(args.harness or ("codex", "claude", "opencode"))
        if args.scope == "project":
            agents_base = root / ".agents" / "skills"
            claude_base = root / ".claude" / "skills"
        else:
            agents_base = Path.home() / ".agents" / "skills"
            claude_base = Path.home() / ".claude" / "skills"

        if harnesses & {"codex", "opencode"}:
            outputs.append(
                (agents_base / f"loop-{name}" / "SKILL.md",
                 adapter_skill(name, spec_rel, "codex")))
        if "claude" in harnesses:
            outputs.append(
                (claude_base / f"loop-{name}" / "SKILL.md",
                 adapter_skill(name, spec_rel, "claude")))

    existing_paths = [p for p, _ in outputs]
    check_existing(existing_paths, args.force)
    for p, c in outputs:
        write_atomically(p, c)
        print(p)
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    spec = Path(args.spec).expanduser().resolve()
    errs = validate(spec, args.allow_draft)
    if errs:
        print(f"Validação falhou: {len(errs)} erro(s) em {spec}", file=sys.stderr)
        for i, e in enumerate(errs, 1):
            print(f"  {i}. {e}", file=sys.stderr)
        n_ready = sum(1 for e in errs if "ready" in e)
        n_marker = sum(1 for e in errs if "Marcador" in e)
        n_section = sum(1 for e in errs if "Seção" in e)
        if n_ready:
            print(f"\n  Dica: troque status: draft → ready no frontmatter e state.json", file=sys.stderr)
        if n_marker:
            print(f"  Dica: substitua [PREENCHER] por conteúdo real", file=sys.stderr)
        if n_section:
            print(f"  Dica: adicione as seções obrigatórias listadas", file=sys.stderr)
        return 1
    print("OK: especificação e estado válidos ✓")
    return 0


def cmd_quickstart(args: argparse.Namespace) -> int:
    template = QUICKSTART_TEMPLATES.get(args.template)
    if not template:
        available = ", ".join(QUICKSTART_TEMPLATES.keys())
        print(f"Templates disponíveis: {available}", file=sys.stderr)
        return 1

    name = slugify(args.name or f"{args.template}-{os.urandom(2).hex()}")
    scope = args.scope
    max_iter = args.max_iterations

    if scope == "project":
        root = Path(args.root).resolve() if args.root else git_root(Path.cwd())
        loop_dir = root / "loops" / name
        spec_rel = f"loops/{name}/{name}-loop.md"
    else:
        root = (Path(args.root).expanduser().resolve()
                if args.root else Path.home() / ".agent-loops")
        loop_dir = root / name
        spec_rel = str(loop_dir / f"{name}-loop.md")

    spec = loop_dir / f"{name}-loop.md"
    state = loop_dir / "state.json"

    spec_content = f"""---
name: {name}
schema-version: 1
scope: {scope}
status: draft
owner: human
base-teorica: 2305.19118
template: {args.template}
---

# Loop {name} — {template['desc']}

## Descrição
{template['desc']} para {args.alvo or '[PREENCHER alvo]'}.

## Use quando
Precisar {template['desc'].lower()} em {args.alvo or '[PREENCHER]'}.
Não usar quando: tarefa única sem verificação.

## Entradas
{args.alvo or '[PREENCHER alvo ou "Não se aplica"]'}

## Meta
{template['pronto']}. Verificável? sim.

## Verificação
- Check primário: `{template['check']}`
- Evidência registrada: código de saída + resumo em state.json.
- Pronto = {template['pronto']}.
- Regressão: `git diff --stat`
- Falha/timeout: registrar; nunca tratar como sucesso.

## Passos da volta
1. Reconciliar state.json com repositório.
2. Medir linha de base.
3. Escolher maior gargalo.
4. Aplicar UMA mudança.
5. Rodar check + regressão.
6. Aceitar/reverter.
7. Persistir.
8. Avaliar parada.

## Estados de parada
- sucesso: {template['pronto']}.
- sem-progresso: 2 voltas sem ganho.
- bloqueado: erro externo ou conflito.
- esgotado: {max_iter} voltas.

## Guardrails
- Teto: {max_iter} voltas.
- Aprovação antes de: produção, exclusão.

## Memória / estado
state.json ao lado.

## Sub-loops
Não se aplica.

## Como acionar
/goal Use o loop {name}. Até {template['pronto']}. Pare se bloqueado ou após {max_iter} turnos.

## Métrica de saúde
tokens / mudanças aceitas.
"""

    outputs = [
        (spec, spec_content),
        (state, state_template(name, max_iter)),
    ]

    if args.install_adapters:
        harnesses = set(args.harness or ("codex", "claude", "opencode"))
        if scope == "project":
            agents_base = root / ".agents" / "skills"
            claude_base = root / ".claude" / "skills"
        else:
            agents_base = Path.home() / ".agents" / "skills"
            claude_base = Path.home() / ".claude" / "skills"
        if harnesses & {"codex", "opencode"}:
            outputs.append(
                (agents_base / f"loop-{name}" / "SKILL.md",
                 adapter_skill(name, spec_rel, "codex")))
        if "claude" in harnesses:
            outputs.append(
                (claude_base / f"loop-{name}" / "SKILL.md",
                 adapter_skill(name, spec_rel, "claude")))

    check_existing([p for p, _ in outputs], args.force)
    for p, c in outputs:
        write_atomically(p, c)
        print(p)
    return 0


def cmd_install(args: argparse.Namespace) -> int:
    spec = Path(args.spec).expanduser().resolve()
    if not spec.is_file():
        raise ValueError(f"Especificação não encontrada: {spec}")

    text = spec.read_text("utf-8")
    fm = parse_frontmatter(text)
    name = fm.get("name", "")
    scope = fm.get("scope", "")
    if not name or slugify(name) != name:
        raise ValueError("spec.name inválido no frontmatter")
    if scope not in ("project", "global"):
        raise ValueError("spec.scope deve ser project ou global")

    harnesses = set(args.harness or ("codex", "claude", "opencode"))

    if scope == "project":
        # spec path: /.../projeto/loops/<nome>/<nome>-loop.md
        if len(spec.parents) < 3:
            raise ValueError("Não foi possível determinar a raiz do projeto")
        root = spec.parents[2]
        spec_rel = f"loops/{name}/{name}-loop.md"
        agents_dir = root / ".agents" / "skills"
        claude_dir = root / ".claude" / "skills"
    else:
        root = spec.parents[0]
        spec_rel = str(spec)
        agents_dir = Path.home() / ".agents" / "skills"
        claude_dir = Path.home() / ".claude" / "skills"

    outputs = []
    if harnesses & {"codex", "opencode"}:
        outputs.append((agents_dir / f"loop-{name}" / "SKILL.md",
                        adapter_skill(name, spec_rel, "codex")))
    if "claude" in harnesses:
        outputs.append((claude_dir / f"loop-{name}" / "SKILL.md",
                        adapter_skill(name, spec_rel, "claude")))

    check_existing([p for p, _ in outputs], args.force)
    for p, c in outputs:
        write_atomically(p, c)
        print(p)
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    spec = Path(args.spec).expanduser().resolve()
    if not spec.is_file():
        print(f"Especificação não encontrada: {spec}", file=sys.stderr)
        return 1

    text = spec.read_text("utf-8")
    fm = parse_frontmatter(text)
    name = fm.get("name", "?")
    status = fm.get("status", "?")
    scope = fm.get("scope", "?")

    state_p = spec.with_name("state.json")
    if state_p.is_file():
        st = json.loads(state_p.read_text("utf-8"))
        iteration = st.get("iteration", 0)
        max_iter = st.get("max_iterations", 0)
        state_st = st.get("status", "?")
        n_accepted = len(st.get("accepted_changes", []))
        n_attempts = len(st.get("attempts", []))
        last_check = st.get("last_check", None)
        terminal = st.get("terminal_reason", None)
    else:
        iteration = max_iter = state_st = n_accepted = n_attempts = 0
        last_check = terminal = None

    print(f"╔══════════════════════════════════════╗")
    print(f"║ Sandeco Loop Status — {name:<20} ║")
    print(f"╠══════════════════════════════════════╣")
    print(f"║ Spec:       {str(spec):<30} ║")
    print(f"║ Status:     {status:<30} ║")
    print(f"║ Scope:      {scope:<30} ║")
    print(f"║ Iteração:   {iteration}/{max_iter:<26} ║")
    print(f"║ State.json: {state_st:<30} ║")
    print(f"║ Mudanças:   {n_accepted} aceitas / {n_attempts} tentativas        ║")
    if last_check:
        lc = str(last_check)[:30]
        print(f"║ Último check: {lc:<30} ║")
    if terminal:
        print(f"║ Terminal:   {str(terminal):<30} ║")
    health = "SAUDÁVEL" if n_accepted >= max(1, n_attempts // 2) else (
        "ATENÇÃO" if n_accepted > 0 else "CRÍTICO")
    print(f"║ Saúde:      {health:<30} ║")
    print(f"╚══════════════════════════════════════╝")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Sandeco Loop — scaffold e validação")
    sub = p.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="Cria especificação + state.json [+ adaptadores]")
    init.add_argument("--name", required=True)
    init.add_argument("--scope", choices=("project", "global"), default="project")
    init.add_argument("--root", help="Raiz explícita (default: git root ou ~/.agent-loops)")
    init.add_argument("--max-iterations", type=int, default=12)
    init.add_argument("--install-adapters", action="store_true")
    init.add_argument("--harness", action="append", choices=("codex", "claude", "opencode"))
    init.add_argument("--force", action="store_true")
    init.set_defaults(func=cmd_init)

    val = sub.add_parser("validate", help="Valida especificação + state.json")
    val.add_argument("--spec", required=True)
    val.add_argument("--allow-draft", action="store_true")
    val.set_defaults(func=cmd_validate)

    inst = sub.add_parser("install-adapters", help="Instala adaptadores sem alterar spec")
    inst.add_argument("--spec", required=True)
    inst.add_argument("--harness", action="append", choices=("codex", "claude", "opencode"))
    inst.add_argument("--force", action="store_true")
    inst.set_defaults(func=cmd_install)

    st = sub.add_parser("status", help="Exibe status e métricas de saúde do loop")
    st.add_argument("--spec", required=True)
    st.set_defaults(func=cmd_status)

    qs = sub.add_parser("quickstart", help="Cria loop a partir de template pronto")
    qs.add_argument("--template", required=True, choices=list(QUICKSTART_TEMPLATES.keys()))
    qs.add_argument("--name", help="Nome do loop (default: <template>-<hash>)")
    qs.add_argument("--alvo", help="Alvo do loop (ex: modulo, endpoint, diretório)")
    qs.add_argument("--scope", choices=("project", "global"), default="project")
    qs.add_argument("--root", help="Raiz explícita")
    qs.add_argument("--max-iterations", type=int, default=12)
    qs.add_argument("--install-adapters", action="store_true")
    qs.add_argument("--harness", action="append", choices=("codex", "claude", "opencode"))
    qs.add_argument("--force", action="store_true")
    qs.set_defaults(func=cmd_quickstart)

    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except (ValueError, FileExistsError, OSError) as e:
        print(f"ERRO: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
