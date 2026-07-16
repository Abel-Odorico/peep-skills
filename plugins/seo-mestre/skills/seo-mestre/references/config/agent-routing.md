# Roteamento de Agentes — SEO MESTRE

## Ordem padrão de execução

1. `01-technical-seo-crawler-agent.md` — sempre.
2. `02-pagespeed-core-web-vitals-agent.md` — sempre.
3. `03-semantic-accessibility-agent.md` — sempre.
4. `04-information-architecture-intent-agent.md` — sempre.
5. `05-content-copy-aeo-agent.md` — sempre.
6. `06-geo-aio-ai-citation-agent.md` — sempre.
7. `07-llm-crawlers-robots-agent.md` — sempre.
8. `08-schema-entity-trust-agent.md` — sempre.
9. `09-local-seo-authority-agent.md` — só se houver atuação local (empresa física, atendimento por cidade/bairro).
10. `10-wordpress-cms-seo-agent.md` — só se o site for WordPress/CMS.
11. `11-commerce-saas-conversion-agent.md` — só se for e-commerce, SaaS, curso, infoproduto, landing ou página de venda.
12. `12-quality-gate-final-review-agent.md` — sempre, por último.

## Regra de condicionamento

Antes de rodar os agentes 09, 10 e 11, confirmar com o usuário (ou inferir do intake) se o critério de ativação se aplica. Se não se aplicar, pular o agente e não computar seu peso na nota final — redistribuir a expectativa de nota entre os agentes aplicáveis, deixando isso explícito no relatório.

## Regra de delegação

Cada agente deve entregar, no formato definido em sua própria seção "Saída obrigatória":

- Nota individual;
- Diagnóstico;
- Evidências;
- Correções;
- Prioridade;
- Impacto esperado;
- Bloqueios.

A orquestradora (`SKILL.md`) consolida tudo no relatório final, usando `templates/audit-report-template.md` ou `templates/new-site-architecture-template.md` conforme o modo.
