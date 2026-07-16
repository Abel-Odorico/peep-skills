# Framework Focus — where relevant code lives per stack

Use this to jump straight to high-signal paths and skip token sinks. Load a
framework's block only when that stack is detected. Run `dna.py` first — it
detects the stack + architecture and names these likely locations for you.

## Next.js
- **Prioritize:** `app/`, `pages/`, `components/`, `lib/`, `actions/`, server actions, route handlers (`route.ts`), `middleware.ts`
- **Ignore:** `.next/`, `public/` binaries
- **Entity trail:** page/route → server action → service/lib → schema

## Laravel
- **Prioritize:** `app/Models`, `app/Http/Controllers`, `routes/`, `resources/views`, `database/migrations`, `config/`
- **Ignore:** `vendor/`, `storage/`, `bootstrap/cache`
- **Entity trail:** route → controller → model → migration

## React (SPA)
- **Prioritize:** components, hooks (`use*`), contexts, providers, services/api clients
- **Entity trail:** component → hook → service → type

## WordPress
- **Prioritize:** `wp-content/plugins`, `wp-content/themes`, snippets, templates
- **Ignore:** `wp-content/uploads` (unless media task), core `wp-admin`/`wp-includes`

## Supabase
- **Prioritize:** `supabase/migrations`, schema, RLS policies, RPC functions, `supabase/functions` (edge)
- **Entity trail:** table → policy → RPC → edge function

## Always ignore (every stack)
`node_modules`, `vendor`, `build`, `dist`, `.next`, `out`, `coverage`, cache
dirs, `logs`, lock files, binaries, images, video, fonts, `.map`, `*.min.*`
— unless the task explicitly targets them.
