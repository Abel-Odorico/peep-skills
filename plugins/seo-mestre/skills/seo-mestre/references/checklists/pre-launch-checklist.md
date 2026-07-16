# Checklist Pré-Lançamento — SEO MESTRE

Rodar antes de publicar ou trocar o ambiente de staging para produção.

## Indexação e rastreamento

- [ ] `robots.txt` de staging removido/ajustado (não bloquear produção)
- [ ] Nenhum `noindex` remanescente de staging
- [ ] `sitemap.xml` gerado e enviado ao Search Console/Bing Webmaster
- [ ] Canonical apontando para a URL final (https, com/sem www definido)
- [ ] Redirecionamento 301 de URLs antigas (em caso de migração)

## Metadados e conteúdo

- [ ] Title e description únicos em todas as páginas estratégicas
- [ ] H1 único por página
- [ ] Open Graph e Twitter Card configurados
- [ ] Favicon e ícones instalados
- [ ] Textos revisados (ortografia, dados, links quebrados)

## Técnico

- [ ] HTTPS ativo e sem conteúdo misto
- [ ] 404 e 5xx tratados com página amigável
- [ ] Formulários testados (envio real, validação, mensagem de sucesso)
- [ ] Links internos e externos verificados
- [ ] Testado em mobile, tablet e desktop

## Performance

- [ ] Imagens otimizadas (WebP/AVIF, tamanho correto)
- [ ] Lighthouse rodado em produção (ou staging equivalente)
- [ ] Cache e compressão ativos
- [ ] Fontes carregando sem bloquear renderização

## Schema e IA

- [ ] Schema JSON-LD validado (Organization/LocalBusiness/Service/FAQPage conforme caso)
- [ ] Estratégia de crawlers de IA definida e aplicada no `robots.txt`
- [ ] `llms.txt` publicado, se decidido usar

## Mensuração

- [ ] Google Analytics/GA4 instalado e disparando
- [ ] Google Search Console verificado
- [ ] Bing Webmaster Tools verificado
- [ ] Eventos de conversão configurados (WhatsApp, formulário, compra)

## Veredito

- [ ] Todos os itens acima concluídos ou justificados
- [ ] Nenhum bloqueador crítico da `quality-gate-85-plus.md` pendente
