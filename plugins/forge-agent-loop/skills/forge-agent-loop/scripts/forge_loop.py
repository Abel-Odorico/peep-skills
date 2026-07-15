#!/usr/bin/env python3
"""Scaffold and validate portable agent-loop specifications."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


REQUIRED_HEADINGS = (
    "Descrição",
    "Use quando",
    "Entradas",
    "Meta e critérios de aceite",
    "Verificação",
    "Passos da volta",
    "Estados de parada",
    "Guardrails e aprovações",
    "Memória e retomada",
    "Skills e sub-loops",
    "Como executar",
    "Métricas de saúde",
)
TERMINAL_STATES = ("sucesso", "sem-progresso", "bloqueado", "esgotado")
PENDING_MARKERS = ("[PREENCHER]", "[TODO]", "<preencher>")


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    if not value or len(value) > 48:
        raise ValueError("o nome deve gerar um slug de 1 a 48 caracteres")
    return value


def git_root(cwd: Path) -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    return Path(result.stdout.strip()) if result.returncode == 0 else cwd.resolve()


def write_new(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def preflight(paths: list[Path], force: bool) -> None:
    existing = [path for path in paths if path.exists()]
    if existing and not force:
        joined = "\n".join(f"- {path}" for path in existing)
        raise FileExistsError(
            "os destinos abaixo já existem; nada foi alterado. "
            f"Use --force somente para substituir intencionalmente:\n{joined}"
        )


def spec_template(name: str, scope: str, max_iterations: int) -> str:
    return f"""---
name: {name}
schema-version: 1
scope: {scope}
status: draft
owner: human
---

# Loop {name}

## Descrição
[PREENCHER] O que melhora a cada volta, em até duas frases.

## Use quando
[PREENCHER] Situação concreta. Não usar quando: [PREENCHER].

## Entradas
[PREENCHER] Liste as entradas fixadas antes da primeira volta, ou escreva “Não se aplica” e justifique.

## Meta e critérios de aceite
- Meta observável: [PREENCHER]
- Critérios obrigatórios: [PREENCHER]
- Guardrails que não podem regredir: [PREENCHER]

## Verificação
- Check primário: `[PREENCHER]`
- Evidência registrada: código de saída, métricas e caminho do artefato em `state.json`.
- Pronto = [PREENCHER predicado exato sobre a evidência].
- Checks de regressão: `[PREENCHER]`
- Timeout ou erro: registrar a falha; nunca tratar como sucesso.

## Passos da volta
1. Reconciliar `state.json` com o repositório atual.
2. Medir ou recuperar a linha de base.
3. Escolher o maior gargalo ainda não tentado.
4. Aplicar uma mudança reversível.
5. Rodar o check primário e os checks de regressão; registrar a evidência.
6. Aceitar a mudança somente se houver avanço sem regressão; caso contrário, reverter apenas a própria mudança.
7. Persistir estado e avaliar a parada.

## Estados de parada
- sucesso: [PREENCHER condição comprovada pelo check].
- sem-progresso: [PREENCHER número] voltas consecutivas sem ganho mensurável.
- bloqueado: falta de permissão, entrada ou dependência externa necessária.
- esgotado: {max_iterations} voltas, ou [PREENCHER teto de tempo/custo].

## Guardrails e aprovações
- Teto rígido: {max_iterations} voltas.
- Aprovação humana antes de: produção, publicação, comunicação externa, gastos, exclusões e [PREENCHER].
- Preservar mudanças pré-existentes e nunca registrar segredos no estado.

## Memória e retomada
- Estado: `state.json` ao lado desta especificação.
- Reconciliação após interrupção: [PREENCHER].
- Uma tentativa é identificada por: [PREENCHER].

## Skills e sub-loops
[PREENCHER] Liste skills e sub-loops, ou escreva “Não se aplica”. Proibir ciclos e contabilizar o teto aninhado.

## Como executar
1. Validar esta especificação.
2. Ler `state.json`.
3. Executar uma volta por vez até um estado terminal ou aprovação necessária.
4. Relatar evidência e motivo terminal.

- Codex: mencione `$loop-{name}` se o adaptador estiver instalado.
- Claude Code: execute `/loop-{name}` se o adaptador estiver instalado.
- OpenCode: peça explicitamente para usar a skill `loop-{name}`.

## Métricas de saúde
- mudanças aceitas / voltas;
- tempo ou custo / mudança aceita;
- voltas sem progresso;
- regressões interceptadas antes de merge ou publicação.
"""


def state_template(name: str, max_iterations: int) -> str:
    state = {
        "schema_version": 1,
        "loop": name,
        "status": "draft",
        "iteration": 0,
        "max_iterations": max_iterations,
        "baseline": None,
        "last_check": None,
        "accepted_changes": [],
        "attempts": [],
        "terminal_reason": None,
    }
    return json.dumps(state, ensure_ascii=False, indent=2) + "\n"


def portable_adapter(name: str, spec_relative: str) -> str:
    return f"""---
name: loop-{name}
description: Executa, somente por pedido explícito do usuário, o loop {name} definido em {spec_relative}; valida a especificação, retoma state.json e para apenas por sucesso comprovado, sem-progresso, bloqueio ou esgotamento.
---

# Executar loop {name}

1. Localizar a raiz do Git e ler `{spec_relative}` integralmente.
2. Validar a especificação com o `forge_loop.py` disponível na skill `forge-agent-loop`.
3. Ler o `state.json` ao lado da especificação e reconciliá-lo com o repositório.
4. Executar uma volta por vez, persistindo a evidência do check depois de cada volta.
5. Continuar até um estado terminal ou até uma aprovação humana ser necessária.
6. Nunca ampliar permissões, tratar erro como sucesso ou alterar trabalho pré-existente fora do escopo.
7. Entregar o estado terminal, a evidência final, as voltas consumidas e as mudanças aceitas.
"""


def claude_adapter(name: str, spec_relative: str) -> str:
    body = portable_adapter(name, spec_relative)
    return body.replace(
        "description:",
        "disable-model-invocation: true\ndescription:",
        1,
    )


def parse_frontmatter(text: str) -> dict[str, str]:
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not match:
        return {}
    data: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip()
    return data


def validate_spec(path: Path, allow_draft: bool = False) -> list[str]:
    errors: list[str] = []
    if not path.is_file():
        return [f"especificação não encontrada: {path}"]
    text = path.read_text(encoding="utf-8")
    frontmatter = parse_frontmatter(text)
    for key in ("name", "schema-version", "scope", "status", "owner"):
        if not frontmatter.get(key):
            errors.append(f"frontmatter sem `{key}`")
    name = frontmatter.get("name", "")
    if name and (name != slugify(name)):
        errors.append("`name` deve estar em kebab-case")
    if frontmatter.get("schema-version") != "1":
        errors.append("`schema-version` deve ser 1")
    if frontmatter.get("scope") not in {"project", "global"}:
        errors.append("`scope` deve ser project ou global")
    if frontmatter.get("status") not in {"draft", "ready", "running", "retired"}:
        errors.append("`status` inválido")
    if not allow_draft and frontmatter.get("status") != "ready":
        errors.append("entrega final exige `status: ready`")
    for heading in REQUIRED_HEADINGS:
        if f"## {heading}" not in text:
            errors.append(f"seção ausente: {heading}")
    lower = text.lower()
    for state in TERMINAL_STATES:
        if state not in lower:
            errors.append(f"estado terminal ausente: {state}")
    for phrase in ("check primário:", "evidência registrada:", "pronto ="):
        if phrase not in lower:
            errors.append(f"contrato de verificação sem `{phrase}`")
    if not allow_draft:
        for marker in PENDING_MARKERS:
            if marker.lower() in lower:
                errors.append(f"marcador pendente encontrado: {marker}")
    state_path = path.with_name("state.json")
    if not state_path.is_file():
        errors.append(f"estado ausente: {state_path}")
    else:
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
            if state.get("loop") != name:
                errors.append("state.json não corresponde ao nome do loop")
            state_status = state.get("status")
            if state_status not in {"draft", "ready", "running", "success", "no-progress", "blocked", "exhausted"}:
                errors.append("state.json contém status inválido")
            if not allow_draft and state_status == "draft":
                errors.append("entrega final exige state.json com status ready ou posterior")
            if not isinstance(state.get("max_iterations"), int) or state.get("max_iterations", 0) < 1:
                errors.append("state.json precisa de max_iterations positivo")
        except (json.JSONDecodeError, OSError) as exc:
            errors.append(f"state.json inválido: {exc}")
    return errors


def cmd_init(args: argparse.Namespace) -> int:
    name = slugify(args.name)
    if args.max_iterations < 1:
        raise ValueError("--max-iterations deve ser positivo")
    if args.scope == "project":
        root = Path(args.root).resolve() if args.root else git_root(Path.cwd())
        loop_dir = root / "loops" / name
        spec_relative = f"loops/{name}/{name}-loop.md"
    else:
        root = Path(args.root).expanduser().resolve() if args.root else Path.home() / ".agent-loops"
        loop_dir = root / name
        spec_relative = str(loop_dir / f"{name}-loop.md")
    spec = loop_dir / f"{name}-loop.md"
    state_path = loop_dir / "state.json"
    outputs: list[tuple[Path, str]] = [
        (spec, spec_template(name, args.scope, args.max_iterations)),
        (state_path, state_template(name, args.max_iterations)),
    ]

    if args.install_adapters:
        harnesses = set(args.harness or ("codex", "claude", "opencode"))
        if args.scope == "project":
            agent_skill = root / ".agents" / "skills" / f"loop-{name}" / "SKILL.md"
            claude_skill = root / ".claude" / "skills" / f"loop-{name}" / "SKILL.md"
        else:
            agent_skill = Path.home() / ".agents" / "skills" / f"loop-{name}" / "SKILL.md"
            claude_skill = Path.home() / ".claude" / "skills" / f"loop-{name}" / "SKILL.md"
        if harnesses & {"codex", "opencode"}:
            outputs.append((agent_skill, portable_adapter(name, spec_relative)))
        if "claude" in harnesses:
            outputs.append((claude_skill, claude_adapter(name, spec_relative)))

    preflight([path for path, _ in outputs], args.force)
    for path, content in outputs:
        write_new(path, content)
        print(path)
    return 0


def adapter_outputs(spec: Path, harnesses: set[str]) -> list[tuple[Path, str]]:
    text = spec.read_text(encoding="utf-8")
    frontmatter = parse_frontmatter(text)
    name = frontmatter.get("name", "")
    scope = frontmatter.get("scope", "")
    if not name or name != slugify(name):
        raise ValueError("a especificação precisa de `name` válido em kebab-case")
    if scope == "project":
        expected_suffix = Path("loops") / name / f"{name}-loop.md"
        if len(spec.parents) < 3 or Path(*spec.parts[-3:]) != expected_suffix:
            raise ValueError(f"especificação de projeto deve terminar em {expected_suffix}")
        root = spec.parents[2]
        spec_reference = str(expected_suffix)
        agent_skill = root / ".agents" / "skills" / f"loop-{name}" / "SKILL.md"
        claude_skill = root / ".claude" / "skills" / f"loop-{name}" / "SKILL.md"
    elif scope == "global":
        spec_reference = str(spec)
        agent_skill = Path.home() / ".agents" / "skills" / f"loop-{name}" / "SKILL.md"
        claude_skill = Path.home() / ".claude" / "skills" / f"loop-{name}" / "SKILL.md"
    else:
        raise ValueError("a especificação precisa de `scope: project` ou `scope: global`")

    outputs: list[tuple[Path, str]] = []
    if harnesses & {"codex", "opencode"}:
        outputs.append((agent_skill, portable_adapter(name, spec_reference)))
    if "claude" in harnesses:
        outputs.append((claude_skill, claude_adapter(name, spec_reference)))
    return outputs


def cmd_install_adapters(args: argparse.Namespace) -> int:
    spec = Path(args.spec).expanduser().resolve()
    if not spec.is_file():
        raise ValueError(f"especificação não encontrada: {spec}")
    harnesses = set(args.harness or ("codex", "claude", "opencode"))
    outputs = adapter_outputs(spec, harnesses)
    preflight([path for path, _ in outputs], args.force)
    for path, content in outputs:
        write_new(path, content)
        print(path)
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    errors = validate_spec(Path(args.spec).expanduser().resolve(), args.allow_draft)
    if errors:
        for error in errors:
            print(f"ERRO: {error}", file=sys.stderr)
        return 1
    print("OK: especificação e estado válidos")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    init = subparsers.add_parser("init", help="criar especificação, estado e adaptadores opcionais")
    init.add_argument("--name", required=True)
    init.add_argument("--scope", choices=("project", "global"), default="project")
    init.add_argument("--root", help="raiz explícita; por padrão usa a raiz Git ou ~/.agent-loops")
    init.add_argument("--max-iterations", type=int, default=12)
    init.add_argument("--install-adapters", action="store_true")
    init.add_argument(
        "--harness",
        action="append",
        choices=("codex", "claude", "opencode"),
        help="harness a instalar; pode repetir. Sem esta opção, instala os três",
    )
    init.add_argument("--force", action="store_true")
    init.set_defaults(func=cmd_init)

    validate = subparsers.add_parser("validate", help="validar uma especificação existente")
    validate.add_argument("--spec", required=True)
    validate.add_argument("--allow-draft", action="store_true")
    validate.set_defaults(func=cmd_validate)

    adapters = subparsers.add_parser(
        "install-adapters",
        help="instalar adaptadores sem alterar especificação ou estado",
    )
    adapters.add_argument("--spec", required=True)
    adapters.add_argument(
        "--harness",
        action="append",
        choices=("codex", "claude", "opencode"),
        help="harness a instalar; pode repetir. Sem esta opção, instala os três",
    )
    adapters.add_argument("--force", action="store_true")
    adapters.set_defaults(func=cmd_install_adapters)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except (ValueError, FileExistsError, OSError) as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
