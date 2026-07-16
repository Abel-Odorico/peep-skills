"""Shared helpers for Mjolnir token-saving scripts. Stdlib only."""
import ast
import hashlib
import json
import os
import re
import sys
import tempfile

# A file bigger than this is never worth loading whole into context — reading
# it here would defeat the point (and could blow up memory). Content readers
# cap at this; size-based estimators use the real byte size instead.
MAX_READ_BYTES = 2_000_000


def parse_args(value_flags=()):
    """Tiny, consistent argv parser shared by every script.

    Returns (positionals, options). Flags named in value_flags consume the next
    token as their value (missing value -> None, never an IndexError); all other
    --flags are booleans. Keeps arg handling uniform and crash-free across tools.
    """
    value_flags = set(value_flags)
    argv = sys.argv[1:]
    positionals, options, i = [], {}, 0
    while i < len(argv):
        arg = argv[i]
        if arg.startswith("--"):
            key = arg[2:]
            if key in value_flags:
                nxt = argv[i + 1] if i + 1 < len(argv) else None
                options[key] = None if (nxt or "").startswith("--") else nxt
                i += 2
            else:
                options[key] = True
                i += 1
        else:
            positionals.append(arg)
            i += 1
    return positionals, options

# Directories/files never worth loading — pure token waste.
IGNORE_DIRS = {
    "node_modules", "vendor", "build", "dist", ".next", "out",
    "coverage", ".cache", "cache", ".git", ".svn", "logs", "log",
    "__pycache__", ".venv", "venv", ".idea", ".vscode", "target",
    "bin", "obj", ".turbo", ".parcel-cache", "tmp",
}
IGNORE_EXT = {
    # lock files handled by name below
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".svg",
    ".mp4", ".mov", ".avi", ".webm", ".mp3", ".wav",
    ".pdf", ".zip", ".gz", ".tar", ".rar", ".7z",
    ".woff", ".woff2", ".ttf", ".eot", ".otf",
    ".so", ".dll", ".dylib", ".exe", ".bin", ".wasm",
    ".map", ".min.js", ".min.css",
}
IGNORE_NAMES = {
    "Cargo.lock", "Gemfile.lock", "poetry.lock", "composer.lock",
    "pdm.lock", "bun.lockb", "yarn.lock", "pnpm-lock.yaml",
    "package-lock.json", "npm-shrinkwrap.json",
}


def is_ignored(path, name):
    if name in IGNORE_NAMES:
        return True
    lower = name.lower()
    for ext in IGNORE_EXT:
        if lower.endswith(ext):
            return True
    return False


# --- Secret guard -----------------------------------------------------------
# A context selector must NEVER pull credentials into the window or hand them
# to a subagent. Layered so a rename can't dodge every check. The filenames
# themselves are facts (an ssh key is always id_rsa); the layering is ours.

_KEY_SUFFIXES = (".pem", ".key", ".pfx", ".p12", ".jks", ".keystore",
                 ".crt", ".cer", ".asc", ".gpg")
_VAULT_DIRS = frozenset((".ssh", ".gnupg", ".aws", ".kube", ".docker"))
_EXACT_SECRETS = frozenset((
    ".env", ".netrc", ".htpasswd", ".pgpass", "known_hosts", "authorized_keys",
    "id_rsa", "id_dsa", "id_ecdsa", "id_ed25519",
))
# Substring words kept deliberately narrow: a bare "token" or "key" matches
# legit source (auth/token.ts, keyboard.ts), so only strong compounds here.
_SECRET_WORDS = ("password", "passwd", "credential",
                 "apikey", "accesskey", "privatekey", "secretkey")


def _alnum(text):
    return "".join(c for c in text.lower() if c.isalnum())


def is_sensitive(path):
    """True if the path looks like a secret — refuse to load it into context."""
    low = os.path.basename(path).lower()
    if low in _EXACT_SECRETS or low.startswith(".env.") or low.startswith("id_"):
        return True
    if low.endswith(_KEY_SUFFIXES):
        return True
    segments = {seg.lower() for seg in path.replace("\\", "/").split("/")}
    if segments & _VAULT_DIRS:
        return True
    squashed = _alnum(low)               # so "api-key" and "api_key" both hit
    return any(word in squashed for word in _SECRET_WORDS)


# --- File-kind classifier ---------------------------------------------------
# code wants symbols, prose can be summarized, config loads as schema. Some
# build files carry no useful suffix, so the name is checked before the ext.

_NAMED_CODE = frozenset("""
    dockerfile containerfile makefile gnumakefile rakefile gemfile brewfile
    procfile justfile vagrantfile jenkinsfile cmakelists.txt
""".split())
_PROSE_SUFFIX = frozenset((".md", ".markdown", ".rst", ".txt", ".adoc", ".tex"))
_CONFIG_SUFFIX = frozenset((".json", ".yaml", ".yml", ".toml", ".ini", ".cfg",
                            ".conf", ".env", ".properties"))
_LOOKS_CODE = re.compile(r"""^\s*(?:
      (?:import|from|export|require|use|package|module)\b
    | (?:def|fn|func|function|class|struct|interface|enum|trait)\b
    | (?:if|for|while|switch|match|try)\s*[({]
    | [@#]\w+
    | [\w$]+\s*[:=]\s*[\[{("'`]
    | [)\]};,]+\s*$
)""", re.X)


def classify(path):
    """Return 'code' | 'prose' | 'config' for a path."""
    name = os.path.basename(path).lower()
    if name in _NAMED_CODE:
        return "code"
    suffix = os.path.splitext(name)[1]
    if suffix in _CONFIG_SUFFIX:
        return "config"
    if suffix in _PROSE_SUFFIX:
        return "prose"
    if suffix:
        return "code"
    sample = [ln for ln in read_text(path).splitlines()[:40] if ln.strip()]
    if not sample:
        return "prose"
    if sample[0].startswith("#!"):
        return "code"
    hits = sum(1 for ln in sample if _LOOKS_CODE.match(ln))
    return "code" if hits / len(sample) >= 0.4 else "prose"


# --- Volatile-token masking (for log dedup) ---------------------------------
# Two log lines that differ only by a timestamp/uuid/hex/address are "the same"
# line for dedup purposes. Mask the volatile bits, then collapse duplicates.

_MASKS = [
    (re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:?\d{2})?"), "<ts>"),
    (re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.I), "<uuid>"),
    (re.compile(r"\b0x[0-9a-f]+\b", re.I), "<hex>"),
    (re.compile(r"\b[0-9a-f]{12,}\b", re.I), "<hash>"),
    (re.compile(r"\b\d{4,}\b"), "<n>"),
]


def normalize_line(line):
    out = line
    for rx, repl in _MASKS:
        out = rx.sub(repl, out)
    return out


# Generic identifiers that pollute an import/call graph — they mean "everywhere"
# and should never be ranked as a hub.
GENERIC_SYMBOLS = {
    "string", "number", "boolean", "object", "array", "promise", "map", "set",
    "print", "len", "str", "dict", "list", "int", "float", "bool", "any",
    "console", "error", "exception", "index", "main", "default", "type",
}


def estimate_tokens(text):
    """Cheap token estimate. ~4 chars/token is a good rule of thumb for code."""
    return max(1, len(text) // 4)


def walk_files(root):
    """Yield (path, size_bytes) for every non-ignored file under root."""
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS and not d.startswith(".")
                       or d in (".github",)]
        for name in filenames:
            if is_ignored(dirpath, name):
                continue
            full = os.path.join(dirpath, name)
            if is_sensitive(full):
                continue
            try:
                yield full, os.path.getsize(full)
            except OSError:
                continue


def read_text(path, limit=MAX_READ_BYTES):
    """Read a file as text, capped at `limit` bytes so a giant file can't blow
    up memory. Signatures/terms live near the top; the cap is generous."""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read(limit)
    except OSError:
        return ""


def estimate_from_size(size_bytes):
    """Token estimate straight from byte size — no read needed, and correct even
    for files past the read cap."""
    return max(1, size_bytes // 4)


# --- Precise Python extraction (real AST, not regex) ------------------------
# For .py the stdlib `ast` module gives exact symbols and imports — no false
# hits from strings/comments. Other languages fall back to regex. Both return
# None on a parse failure so the caller can degrade gracefully.

def py_symbols(path):
    try:
        tree = ast.parse(read_text(path))
    except (SyntaxError, ValueError):
        return None
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            bases = ", ".join(b.id for b in node.bases if isinstance(b, ast.Name))
            out.append((node.lineno, f"class {node.name}" + (f"({bases})" if bases else "")))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            args = ", ".join(a.arg for a in node.args.args)
            kw = "async " if isinstance(node, ast.AsyncFunctionDef) else ""
            out.append((node.lineno, f"{kw}def {node.name}({args})"))
    out.sort()
    return out


def py_imports(path):
    try:
        tree = ast.parse(read_text(path))
    except (SyntaxError, ValueError):
        return None
    mods = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mods.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            mods.add(node.module.split(".")[0])
    return mods


# --- Content-hash incremental cache -----------------------------------------
# Never re-spend compute (and, downstream, tokens) on a file that hasn't
# changed. Keyed by absolute path + content hash; a hash miss means stale.

_CACHE_PATH = os.path.join(tempfile.gettempdir(), "mjolnir_cache.json")


def file_hash(path):
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            block = f.read(1 << 20)
            while block:
                h.update(block)
                block = f.read(1 << 20)
    except OSError:
        return None
    return h.hexdigest()


def _cache_read():
    try:
        with open(_CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _stat_sig(path):
    try:
        st = os.stat(path)
        return [st.st_size, st.st_mtime_ns]
    except OSError:
        return None


def cache_get(path, kind):
    """Return cached payload for (path, kind) if unchanged, else None.

    Fast path: if size+mtime match, trust it and skip re-reading to hash.
    Slow path: verify by content hash (catches touch-without-edit / mtime lies).
    """
    key = os.path.abspath(path) + "::" + kind
    entry = _cache_read().get(key)
    if not entry:
        return None
    if entry.get("stat") == _stat_sig(path):
        return entry.get("payload")
    if entry.get("hash") == file_hash(path):
        return entry.get("payload")
    return None


def cache_set(path, kind, payload):
    data = _cache_read()
    key = os.path.abspath(path) + "::" + kind
    data[key] = {"hash": file_hash(path), "stat": _stat_sig(path), "payload": payload}
    # Atomic write: a concurrent run must never see (or leave) a half-written
    # JSON. Write a temp file in the same dir, then rename over the target.
    try:
        fd, tmp = tempfile.mkstemp(prefix="mjcache_", dir=os.path.dirname(_CACHE_PATH))
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f)
        os.replace(tmp, _CACHE_PATH)
    except OSError:
        pass
