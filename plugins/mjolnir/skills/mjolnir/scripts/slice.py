#!/usr/bin/env python3
"""Extract ONE symbol's body from a file — Level 2, the "just this method" load.

    python3 slice.py <file> <name>

Reading a 600-line file to see one function is the most common token waste this
skill exists to stop. slice pulls only the named function/class/method: exact
via AST for Python, brace-matched for C-family languages. Prints its line range
and body — nothing else.
"""
import ast
import os
import re
import sys
from common import read_text, parse_args

BRACE_LANGS = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".go", ".rs",
               ".java", ".php", ".c", ".cpp", ".cs", ".swift", ".kt"}


def py_slice(src, name):
    try:
        tree = ast.parse(src)
    except (SyntaxError, ValueError):
        return None
    lines = src.splitlines()
    out = []
    for node in ast.walk(tree):
        if (isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                and node.name == name):
            start = node.lineno - 1
            end = getattr(node, "end_lineno", node.lineno)
            out.append((node.lineno, "\n".join(lines[start:end])))
    return out


def brace_slice(src, name):
    lines = src.splitlines()
    named = re.compile(r"\b" + re.escape(name) + r"\b")
    is_def = re.compile(r"\b(function|class|const|let|var|func|fn|def|interface"
                        r"|type|enum|struct|trait|public|private|protected|static)\b")
    out = []
    for i, line in enumerate(lines):
        if not (named.search(line) and is_def.search(line)):
            continue
        depth, opened, buf = 0, False, []
        for j in range(i, len(lines)):
            buf.append(lines[j])
            depth += lines[j].count("{") - lines[j].count("}")
            if "{" in lines[j]:
                opened = True
            if opened and depth <= 0:
                break
            if not opened and lines[j].rstrip().endswith(";"):  # one-liner decl
                break
        out.append((i + 1, "\n".join(buf)))
        break
    return out


def main():
    pos, _ = parse_args()
    if len(pos) < 2:
        print(__doc__)
        sys.exit(2)
    path, name = pos[0], pos[1]
    src = read_text(path)
    matches = py_slice(src, name) if path.endswith(".py") else None
    if matches is None:
        matches = brace_slice(src, name)

    if not matches:
        print(f"# '{name}' not found in {path} — try symbols.py {path} to list names")
        sys.exit(1)
    for lineno, body in matches:
        span = body.count("\n") + 1
        print(f"# {path}:{lineno}  ({span} lines)")
        print(body)


if __name__ == "__main__":
    main()
