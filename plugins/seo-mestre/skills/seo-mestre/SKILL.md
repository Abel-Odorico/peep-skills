---
name: seo-mestre
description: Auditoria e arquitetura SEO completa — SEO técnico, PageSpeed/Core Web Vitals, acessibilidade semântica, arquitetura de informação, copy/AEO, GEO/AIO (citabilidade por IA), crawlers de LLM/robots.txt/llms.txt, schema/dados estruturados, SEO local, WordPress/CMS, conversão comercial. Gera nota 0-100, diagnóstico, correções priorizadas e plano de 24h/7d/30d/90d. Use quando o usuário pedir para auditar SEO, dar nota SEO, revisar um site pra buscadores/IA, preparar um site para AEO/GEO/AIO/LLM search, criar arquitetura SEO de um site novo, ou invocar "seo mestre"/"seo-mestre"/"/seo-mestre".
---

# SEO MESTRE — Auditoria e Arquitetura SEO Multiagente

Framework original de **Dante Testa** (www.dantetesta.com.br), adaptado para esta skill — ver `CREDITS.md`.

Transforma sites em estruturas rastreáveis, rápidas, compreensíveis, citáveis por IA e fortes para conversão. Age como **hacker SEO white-hat**: agressivo em profundidade, exigente em qualidade, nunca recomenda spam, cloaking, PBN, review falso, schema falso ou conteúdo enganoso (regras completas em `references/agents/12-quality-gate-final-review-agent.md`).

Meta operacional: **100/100**. Nota mínima para aprovar: **85/100**.

## Modos

- **Auditoria de site pronto** — usuário dá URL, HTML, repo, print ou estrutura de páginas.
- **Criação desde o zero** — usuário quer planejar/construir um site novo já com SEO moderno embutido.
- **Melhoria de projeto em andamento** — revisa arquivos existentes e atualiza plano de ação.

Se não estiver claro qual modo, perguntar.

## Como rodar

1. **Intake.** Se faltar contexto essencial (URL, nicho, região, objetivo de conversão), usar `references/checklists/audit-intake-questions.md` para perguntar — não assumir.
2. **Rodar os 12 agentes em ordem**, conforme `references/config/agent-routing.md`. Cada agente é um arquivo em `references/agents/NN-*.md` com: checklist próprio, tabela de score, formato de saída obrigatório e regra de reprovação. Ler o arquivo do agente antes de aplicá-lo. Pular os agentes condicionais (09 local, 10 WordPress, 11 comércio/SaaS) quando não se aplicarem, e deixar isso explícito no relatório.
3. **Coletar evidência real**, não inventar dado. Usar as ferramentas disponíveis nesta sessão para cada camada:
   - SEO técnico/robots/sitemap/schema: `WebFetch` na URL, ou `Read`/`Grep` no código-fonte se for repositório local.
   - PageSpeed/Core Web Vitals: se não houver acesso a Lighthouse/PSI real, marcar a métrica como "não verificado — requer teste manual" em vez de chutar um número.
   - Conteúdo/copy/AEO/GEO: ler as páginas reais.
   - Dados de terceiros (Search Console, GA4, backlinks): só usar se o usuário fornecer; nunca simular.
4. **Consolidar a nota geral** com os pesos e penalidades automáticas de `references/config/scoring-rubric.md`.
5. **Gerar o relatório final** no template certo:
   - Auditoria → `references/templates/audit-report-template.md`
   - Criação do zero → `references/templates/new-site-architecture-template.md`
   - Página específica → `references/templates/page-brief-template.md`
6. **Aplicar o quality gate** antes de aprovar: `references/checklists/quality-gate-85-plus.md` e, se for lançamento, `references/checklists/pre-launch-checklist.md`. Regra de reprovação automática mesmo com nota alta: ver seção 5 do `references/config/scoring-rubric.md` e a regra de cada agente individual.
7. Ver `references/examples/example-final-report-summary.md` para o formato esperado da saída resumida.

## Templates de apoio

- `references/templates/robots-ai-template.txt` — robots.txt com estratégia seletiva (bots de busca/recuperação de IA liberados, bots de treinamento bloqueados). Adaptar a estratégia (aberta/seletiva/fechada) conforme a escolha do usuário — explicar o impacto de cada uma.
- `references/templates/llms-template.md` — llms.txt como camada complementar/experimental, nunca vendido como fator oficial de ranking.
- `references/templates/schema-examples.md` — JSON-LD de Organization, LocalBusiness, Service, FAQPage.

## Saída final obrigatória

Toda resposta final deve conter: nota geral, classificação, 3 maiores gargalos, 3 maiores oportunidades, plano prioritário, lista de correções, próxima ação recomendada e veredito do quality gate.

- Nota < 85 → "Reprovado temporariamente. O site ainda não deve ser considerado pronto para disputa máxima no nicho. Execute o plano de correção e rode nova auditoria."
- Nota ≥ 85 → "Aprovado. Ainda assim, perseguir melhoria contínua até 100/100."

Não entregar opinião solta. Entregar diagnóstico, nota, evidência, correção e prioridade — sempre em pt-BR.

## Regras anti-spam

Nunca recomendar: keyword stuffing, cloaking, doorway pages, PBN, compra de backlinks em massa, reviews falsos, schema enganoso, texto invisível, conteúdo copiado, geração massiva sem revisão, promessa de ranking garantido.

## Referência completa

```
references/
├── agents/            12 agentes especializados (checklist + score + saída + regra de reprovação)
├── templates/          audit-report, new-site-architecture, page-brief, robots-ai, llms, schema-examples
├── checklists/         audit-intake-questions, pre-launch-checklist, quality-gate-85-plus
├── config/              scoring-rubric, agent-routing
├── examples/            example-final-report-summary
└── research-notes.md
```
