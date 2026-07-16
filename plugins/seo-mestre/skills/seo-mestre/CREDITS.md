# Créditos

Framework original **SEO MESTRE Multiagente v2.0.0** por **Dante Testa** — https://www.dantetesta.com.br

Adaptado para o formato de skill do Claude Code (frontmatter, orquestração via `references/` lidas sob demanda, uso de ferramentas reais como WebFetch/Bash em vez de dados inventados) por Abel Odorico.

Durante a adaptação, 4 arquivos do pacote original chegaram corrompidos/vazios na transferência e foram reconstruídos com base no padrão dos demais arquivos do pacote (mesmo nível de detalhe e formato):

- `references/agents/10-wordpress-cms-seo-agent.md` (seção final: Score/Saída obrigatória/Regra de reprovação)
- `references/checklists/pre-launch-checklist.md` (estava vazio)
- `references/config/agent-routing.md` (estava vazio; reconstruído a partir da seção 3 do `SKILL.md` original)
- `references/checklists/audit-intake-questions.md` (2 caracteres corrompidos corrigidos)

O restante do conteúdo é fiel ao pacote original.
