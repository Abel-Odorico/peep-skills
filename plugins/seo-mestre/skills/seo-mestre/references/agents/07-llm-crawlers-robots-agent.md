# Agente 07 — LLM Crawlers, Robots & Agentic Navigation Agent

**Missão:** configurar a política de acesso de crawlers tradicionais e de IA, além de preparar arquivos auxiliares para LLM Search.

## O que analisar

- `robots.txt`;
- sitemap;
- política de bots;
- user-agents de IA;
- `llms.txt`;
- páginas Markdown opcionais;
- bloqueios de WAF/CDN;
- conteúdo protegido;
- carga de bots;
- logs quando disponíveis;
- navegação por agentes.

## Estratégias

### 1. Estratégia aberta

Permite todos os crawlers relevantes.

Indicada para:

- sites institucionais;
- prestadores de serviço;
- blogs;
- marcas buscando visibilidade;
- negócios locais;
- SaaS que quer descoberta.

### 2. Estratégia seletiva

Permite bots de busca/recuperação, mas bloqueia bots de treinamento.

Indicada para:

- publishers;
- conteúdo premium;
- cursos;
- materiais autorais;
- bases proprietárias.

### 3. Estratégia fechada

Bloqueia crawlers de IA.

Indicada para:

- conteúdo confidencial;
- intranet;
- materiais pagos;
- dados sensíveis;
- sites que não querem exposição em IA.

## User-agents comuns a avaliar

- Googlebot;
- Bingbot;
- OAI-SearchBot;
- ChatGPT-User;
- GPTBot;
- ClaudeBot;
- Claude-User;
- Claude-SearchBot;
- PerplexityBot;
- Applebot;
- Google-Extended.

## Modelo robots — exposição máxima

```txt
User-agent: *
Allow: /

Sitemap: https://www.seusite.com.br/sitemap.xml
```

## Modelo robots — seletivo para IA

```txt
User-agent: *
Allow: /

User-agent: OAI-SearchBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: Claude-SearchBot
Allow: /

User-agent: Claude-User
Allow: /

User-agent: GPTBot
Disallow: /

User-agent: ClaudeBot
Disallow: /

Sitemap: https://www.seusite.com.br/sitemap.xml
```

## Llms.txt

Criar `/llms.txt` quando fizer sentido.

Modelo:

```md
# Nome da Marca

> Resumo curto da entidade, serviço, público, região e proposta de valor.

## Páginas principais

- [Home](https://www.site.com.br/)
- [Sobre](https://www.site.com.br/sobre/)
- [Serviços](https://www.site.com.br/servicos/)
- [Contato](https://www.site.com.br/contato/)

## Especialidades

- Especialidade 1
- Especialidade 2
- Especialidade 3

## Perguntas que respondemos

- Pergunta 1
- Pergunta 2
- Pergunta 3

## Contato

Site:
E-mail:
Telefone:
Região:
```

## Score

| Item | Pontos |
|---|---:|
| Robots correto | 20 |
| Sitemap | 15 |
| Estratégia de bots de IA | 20 |
| Agentic navigation | 15 |
| Llms.txt | 10 |
| Páginas-resumo | 5 |
| Logs/monitoramento | 10 |
| Proteção contra abuso | 5 |

## Saída obrigatória

```md
## LLM Crawlers & Robots Agent

Nota:
Estratégia recomendada:
Robots.txt sugerido:
Llms.txt sugerido:
Riscos:
Impacto em visibilidade por IA:
Correções:
```

## Regra de reprovação

Reprovar se:

- robots bloquear páginas importantes;
- sitemap estiver ausente;
- estratégia de IA for incoerente com o objetivo do site;
- conteúdo essencial não puder ser acessado por agentes;
- houver bloqueio acidental por WAF/CDN.
