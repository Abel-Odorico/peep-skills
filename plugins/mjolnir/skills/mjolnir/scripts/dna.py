#!/usr/bin/env python3
"""Read a repo's DNA — stack + architecture — so you search where this kind of
project keeps things, instead of scanning blind.

    python3 dna.py [path]

Detects language, framework, and architecture markers from manifest files and
top-level layout, then names the likely locations for your task. Heuristic and
honest: it reports what it sees, not a guarantee.
"""
import json
import os
from common import read_text, parse_args

# dependency name (substring) -> framework label
DEP_FRAMEWORK = {
    "@nestjs/core": "NestJS", "next": "Next.js", "nuxt": "Nuxt",
    "@sveltejs/kit": "SvelteKit", "@angular/core": "Angular",
    "react": "React", "vue": "Vue", "svelte": "Svelte",
    "express": "Express", "fastify": "Fastify", "@remix-run": "Remix",
    "astro": "Astro",
}
# framework -> where its code usually lives (mirrors references/frameworks.md)
LOCATIONS = {
    "NestJS": ["src/modules/", "src/common/", "src/config/"],
    "Next.js": ["app/", "pages/", "components/", "lib/", "actions/"],
    "Nuxt": ["pages/", "components/", "composables/", "server/"],
    "Angular": ["src/app/", "src/app/services/", "src/app/guards/"],
    "React": ["src/components/", "src/hooks/", "src/services/"],
    "Vue": ["src/components/", "src/composables/", "src/stores/"],
    "Laravel": ["app/Http/Controllers/", "app/Models/", "routes/", "database/migrations/"],
    "Symfony": ["src/Controller/", "src/Entity/", "config/"],
    "Django": ["*/models.py", "*/views.py", "*/urls.py"],
    "Rails": ["app/models/", "app/controllers/", "config/routes.rb"],
    "Spring": ["src/main/java/**/controller", "src/main/java/**/service"],
}


def detect(root):
    lang = fw = None

    pkg = read_text(os.path.join(root, "package.json"))
    if pkg:
        lang = "TypeScript" if os.path.exists(os.path.join(root, "tsconfig.json")) else "JavaScript"
        try:
            data = json.loads(pkg)
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
        except ValueError:
            deps = {}
        for dep, label in DEP_FRAMEWORK.items():
            if any(dep in k for k in deps):
                fw = label
                break

    if not fw and read_text(os.path.join(root, "composer.json")):
        lang = "PHP"
        comp = read_text(os.path.join(root, "composer.json"))
        fw = "Laravel" if "laravel/framework" in comp else ("Symfony" if "symfony/" in comp else "PHP")
    if not fw and (read_text(os.path.join(root, "pyproject.toml"))
                   or read_text(os.path.join(root, "requirements.txt"))):
        lang = "Python"
        blob = read_text(os.path.join(root, "pyproject.toml")) + read_text(os.path.join(root, "requirements.txt"))
        fw = "Django" if "django" in blob.lower() else ("FastAPI" if "fastapi" in blob.lower()
              else ("Flask" if "flask" in blob.lower() else "Python"))
    if not fw and read_text(os.path.join(root, "Gemfile")):
        lang, fw = "Ruby", ("Rails" if "rails" in read_text(os.path.join(root, "Gemfile")) else "Ruby")
    if not fw and read_text(os.path.join(root, "go.mod")):
        lang, fw = "Go", "Go"
    if not fw and read_text(os.path.join(root, "Cargo.toml")):
        lang, fw = "Rust", "Rust"
    return lang, fw


def architecture(root):
    """Cheap structural hints from top-level folder names."""
    try:
        dirs = {d.lower() for d in os.listdir(root)
                if os.path.isdir(os.path.join(root, d))}
    except OSError:
        dirs = set()
    hints = []
    if {"domain", "application", "infrastructure"} & dirs:
        hints.append("DDD / hexagonal (domain/application/infrastructure)")
    if "modules" in dirs or os.path.isdir(os.path.join(root, "src", "modules")):
        hints.append("feature-module layout (modules/)")
    if {"controllers", "models", "views"} & dirs:
        hints.append("MVC (controllers/models/views)")
    if "packages" in dirs or "apps" in dirs:
        hints.append("monorepo (packages/ or apps/)")
    return hints


def main():
    pos, _ = parse_args()
    root = os.path.abspath(pos[0] if pos else ".")
    lang, fw = detect(root)
    hints = architecture(root)

    print(f"# Mjolnir DNA — {root}")
    print(f"language: {lang or 'unknown'}")
    print(f"framework: {fw or 'unknown'}")
    if hints:
        print("architecture: " + "; ".join(hints))
    locs = LOCATIONS.get(fw)
    if locs:
        print("\nlikely locations to search first:")
        for loc in locs:
            print(f"  {loc}")
    else:
        print("\nno framework signature — fall back to graph.py --cluster to find subsystems.")


if __name__ == "__main__":
    main()
