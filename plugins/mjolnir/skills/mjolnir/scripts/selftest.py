#!/usr/bin/env python3
"""Self-test gate for Mjolnir. Run before trusting the tools or shipping a change.

    python3 selftest.py

Exercises every module against known-good/known-bad cases (including a golden
table for each filters.json shortcut, so a broken regex fails loudly instead of
silently). Exits 1 on any failure. No dependencies, no network.
"""
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import common
import symbols
import graph
import filter_output as fo

PASS, FAIL = 0, 0


def check(name, cond):
    global PASS, FAIL
    if cond:
        PASS += 1
    else:
        FAIL += 1
        print(f"  FAIL: {name}")


def run(args, stdin=None):
    p = subprocess.run([sys.executable] + args, input=stdin,
                       capture_output=True, text=True, cwd=HERE)
    return p.returncode, p.stdout


# --- common: secret guard ---------------------------------------------------
for path, expect in [(".env", True), (".env.local", True), ("id_rsa", True),
                     ("x/.aws/creds", True), ("server.key", True),
                     ("password.txt", True), ("src/auth/token.ts", False),
                     ("src/app.ts", False), ("keyboard.ts", False)]:
    check(f"is_sensitive({path})={expect}", common.is_sensitive(path) == expect)

# --- common: classifier -----------------------------------------------------
for name, kind in [("a.md", "prose"), ("a.py", "code"), ("a.json", "config"),
                   ("Dockerfile", "code"), ("a.rs", "code"), ("a.yaml", "config")]:
    check(f"classify({name})={kind}", common.classify(name) == kind)

# --- common: normalize_line masks volatile tokens ---------------------------
a = common.normalize_line("2026-07-15T10:00:01 ERROR 0xAF id=12345")
b = common.normalize_line("2026-07-15T11:22:33 ERROR 0xBC id=99999")
check("normalize collapses volatile lines", a == b)

# --- common: size estimate + arg parser -------------------------------------
check("estimate_from_size(4000)=1000", common.estimate_from_size(4000) == 1000)
sys.argv = ["x", "root", "--top", "5", "--cluster", "--empty"]
pos, opts = common.parse_args(value_flags=("top",))
check("parse_args positionals", pos == ["root"])
check("parse_args value flag", opts.get("top") == "5")
check("parse_args bool flag", opts.get("cluster") is True)
sys.argv = ["x", "--top"]                       # missing value must not crash
_, o2 = common.parse_args(value_flags=("top",))
check("parse_args missing value -> None", o2.get("top") is None)

# --- common: cache roundtrip (atomic) ---------------------------------------
with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as tf:
    tf.write("hello")
    tmp = tf.name
common.cache_set(tmp, "t", {"v": 1})
check("cache hit on unchanged file", common.cache_get(tmp, "t") == {"v": 1})
with open(tmp, "w") as f:
    f.write("changed now")
check("cache miss after edit", common.cache_get(tmp, "t") is None)
os.unlink(tmp)

# --- symbols: extraction ----------------------------------------------------
fix = tempfile.mkdtemp(prefix="mjselftest_")
with open(os.path.join(fix, "m.py"), "w") as f:
    f.write("import os\ndef alpha():\n    pass\nclass Beta:\n    def gamma(self):\n        pass\n")
syms = " ".join(s for _, s in symbols.extract(os.path.join(fix, "m.py")))
check("symbols finds def alpha", "def alpha" in syms)
check("symbols finds class Beta", "class Beta" in syms)

# --- graph: alias + relative resolution -------------------------------------
os.makedirs(os.path.join(fix, "src/a"), exist_ok=True)
os.makedirs(os.path.join(fix, "src/b"), exist_ok=True)
with open(os.path.join(fix, "tsconfig.json"), "w") as f:
    f.write('{"compilerOptions":{"baseUrl":".","paths":{"@/*":["src/*"]}}}')
with open(os.path.join(fix, "src/b/user.ts"), "w") as f:
    f.write("export class User {}\n")
with open(os.path.join(fix, "src/a/login.ts"), "w") as f:
    f.write('import { User } from "@/b/user";\n')
with open(os.path.join(fix, "src/a/form.ts"), "w") as f:
    f.write('import { User } from "../b/user";\n')
files, importers, out_edges = graph.build(fix)
user = os.path.join(fix, "src/b/user.ts")
check("graph resolves alias + relative import (in-degree 2)",
      len(importers.get(user, ())) == 2)

# --- filter_output: generic dedup + anti-inflation --------------------------
digest = fo.generic("ERR boom\nERR boom\nERR boom\nPASS ok\n", 200, False)
check("generic dedups repeats", "(x3)" in digest)
check("generic drops passing noise", "PASS ok" not in digest)
tiny = "x"
check("anti-inflation returns input when digest not smaller",
      len(fo.generic(tiny, 200, False)) <= len(tiny) + 40)

# --- filters.json golden table ----------------------------------------------
GOLDEN = [
    ("git status", "On branch main\nnothing to commit, working tree clean", "clean working tree"),
    ("git commit -m x", "[main a1b2c3d] msg\n 1 file changed, 2 insertions", "committed"),
    ("git push origin main", "Everything up-to-date", "up to date"),
    ("pytest tests/", "collected 5 items\n5 passed, 0 failed in 0.4s", "all tests passed"),
    ("npm install", "added 12 packages in 3s\nup to date", "dependencies installed"),
]
for cmd, raw, expect in GOLDEN:
    out, _ = fo.apply_registry(raw, cmd)
    check(f"filter '{cmd}' collapses to '{expect}'", out is not None and expect in out)
# negative: a real failure must NOT collapse to success
neg, _ = fo.apply_registry("collected 4 items\n3 passed, 1 failed in 0.4s", "pytest")
check("filter does not swallow a real failure", not (neg and "all tests passed" in neg))

# --- AST precision (Python) -------------------------------------------------
apath = os.path.join(fix, "ast_case.py")
with open(apath, "w") as f:
    f.write('x = "class Fake:"  # not a real class\n'
            "class Real(Base):\n    async def go(self, n):\n        pass\n")
asyms = common.py_symbols(apath)
rendered = " ".join(s for _, s in asyms)
check("AST finds real class with base", "class Real(Base)" in rendered)
check("AST captures async def + args", "async def go(self, n)" in rendered)
check("AST ignores class name inside a string", "class Fake" not in rendered)
badpy = os.path.join(fix, "bad.py")
with open(badpy, "w") as f:
    f.write("def (:\n")               # deliberate syntax error
check("py_symbols returns None on syntax error", common.py_symbols(badpy) is None)

# --- structured filter parsers ----------------------------------------------
tsc_raw = ("src/a.ts(3,5): error TS2322: Type X is not assignable\n"
           "src/a.ts(9,1): error TS2345: bad arg\n"
           "src/b.ts(1,1): error TS2322: nope\n")
tsc_out = fo.parse_tsc(tsc_raw)
check("parse_tsc counts total + files", tsc_out and "3 error(s) in 2 file(s)" in tsc_out)
check("parse_tsc counts by code", tsc_out and "TS2322 (x2)" in tsc_out)
test_raw = "test_a PASSED\ntest_b FAILED\ntest_c PASSED\n1 failed, 2 passed in 0.1s\n"
test_out = fo.parse_tests(test_raw)
check("parse_tests keeps failures", test_out and "test_b FAILED" in test_out)
check("parse_tests drops passes", test_out and "test_a PASSED" not in test_out)
check("parse_tests keeps summary", test_out and "1 failed, 2 passed" in test_out)

# --- CLI: verify pass/fail exit codes ---------------------------------------
o = os.path.join(fix, "o.md")
c = os.path.join(fix, "c.md")
with open(o, "w") as f:
    f.write("see http://x.io and `code`\n")
with open(c, "w") as f:
    f.write("http://x.io `code` trimmed\n")
rc, _ = run(["verify.py", o, c])
check("verify passes when must-keeps preserved (exit 0)", rc == 0)
with open(c, "w") as f:
    f.write("nothing preserved\n")
rc, _ = run(["verify.py", o, c])
check("verify fails when URL+code lost (exit 1)", rc == 1)

# --- CLI: harvest flags no-trigger marker -----------------------------------
with open(os.path.join(fix, "note.py"), "w") as f:
    f.write("# mjolnir: skipped legacy.js\n# mjolnir: skipped x, load if bug\n")
rc, out = run(["harvest.py", fix])
check("harvest reports markers", "2 markers" in out)
check("harvest flags no-trigger", "no-trigger" in out)

# --- slice.py: single-symbol extraction -------------------------------------
big = os.path.join(fix, "big.py")
with open(big, "w") as f:
    f.write("def one():\n    return 1\n\n\ndef two(x):\n    y = x + 1\n    return y\n\n\ndef three():\n    pass\n")
rc, out = run(["slice.py", big, "two"])
check("slice extracts the named function", "def two(x)" in out and "return y" in out)
check("slice omits other functions", "def one" not in out and "def three" not in out)
jbig = os.path.join(fix, "b.ts")
with open(jbig, "w") as f:
    f.write("export function keep() {\n  return 1;\n}\nfunction other() { return 2; }\n")
rc, out = run(["slice.py", jbig, "keep"])
check("slice brace-matches JS function", "function keep()" in out and "other" not in out)

# --- find.py: concept search returns enclosing symbol -----------------------
rc, out = run(["find.py", "return y", fix])
check("find reports the enclosing symbol", "def two(x)" in out)

# --- dna.py: framework + location detection ---------------------------------
with open(os.path.join(fix, "package.json"), "w") as f:
    f.write('{"dependencies":{"next":"14","react":"18"}}')
rc, out = run(["dna.py", fix])
check("dna detects framework", "Next.js" in out)
check("dna suggests locations", "app/" in out)

# --- graph.py --orphans -----------------------------------------------------
with open(os.path.join(fix, "src/a/lonely.ts"), "w") as f:
    f.write("export const unused = 1;\n")   # imported by nobody
rc, out = run(["graph.py", fix, "--orphans"])
check("orphans lists an unimported file", "lonely.ts" in out)

# --- CLI smoke: everything runs clean ---------------------------------------
for args in (["index.py", fix], ["token_estimate.py", fix], ["graph.py", fix],
             ["score.py", fix, "user login"], ["dna.py", fix], ["bench.py", fix]):
    rc, _ = run(args)
    check(f"{args[0]} exits 0", rc == 0)

# cleanup
import shutil
shutil.rmtree(fix, ignore_errors=True)

print(f"\n{PASS} passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
