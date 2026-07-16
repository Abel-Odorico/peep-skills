# Exemplos de Schema JSON-LD — SEO MESTRE

## Organization

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "Nome da Empresa",
  "url": "https://www.seusite.com.br",
  "logo": "https://www.seusite.com.br/logo.png",
  "sameAs": [
    "https://www.instagram.com/perfil",
    "https://www.linkedin.com/company/perfil"
  ]
}
</script>
```

## LocalBusiness

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "LocalBusiness",
  "name": "Nome da Empresa",
  "image": "https://www.seusite.com.br/fachada.jpg",
  "url": "https://www.seusite.com.br",
  "telephone": "+55 19 99999-9999",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "Rua Exemplo, 123",
    "addressLocality": "Jaguariúna",
    "addressRegion": "SP",
    "postalCode": "00000-000",
    "addressCountry": "BR"
  },
  "areaServed": "Região Metropolitana de Campinas"
}
</script>
```

## Service

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Service",
  "name": "Nome do Serviço",
  "description": "Descrição objetiva do serviço.",
  "provider": {
    "@type": "Organization",
    "name": "Nome da Empresa",
    "url": "https://www.seusite.com.br"
  },
  "areaServed": "Brasil"
}
</script>
```

## FAQPage

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "Pergunta real do usuário?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Resposta curta, clara e verdadeira."
      }
    }
  ]
}
</script>
```

## Regras

- Não inventar reviews.
- Não marcar conteúdo invisível.
- Não usar schema incompatível.
- Validar o JSON-LD antes de publicar.
