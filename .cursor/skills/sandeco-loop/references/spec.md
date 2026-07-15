# Contrato da especificação de loop (Sandeco Loop)

## Índice

1. Artefatos
2. Frontmatter
3. Seções obrigatórias
4. Gabarito do documento `<nome>-loop.md`
5. Gabarito do comando `/loop-<nome>`

---

## 1. Artefatos

Fonte única da verdade:

```text
loops/<nome>/
├── <nome>-loop.md   # especificação (estável)
└── state.json       # estado mutável entre voltas
```

O documento é estável. O `state.json` muda a cada volta.
Nunca registrar lógica operacional no adaptador SKILL.md.

---

## 2. Frontmatter

```yaml
---
name: nome-em-kebab-case
schema-version: 1
scope: project          # project | global
status: draft           # draft | ready | running | retired
owner: human
base-teorica: <papers que sustentam o desenho, ex: 2305.19118>
---
```

---

## 3. Seções obrigatórias

### Descrição
1-2 frases sobre o que melhora a cada volta.

### Use quando
Situação concreta + caso em que NÃO usar.

### Entradas (opcional)
Listar valores fixados antes da 1ª volta. Se autônomo, escrever "Não se aplica".

### Meta
Estado final concreto. Verificável? Sim (número/comando) ou não (juízo — especificar endurecimento).

### Verificação (o check que manda)
- **Check primário:** comando determinístico ou juiz endurecido (rubrica + painel N + voto majoritário)
- **Pronto =** predicado exato sobre a evidência

### Passos da volta
1. Reconciliar estado com repositório.
2. Fotografar linha de base.
3. Ranquear gargalo de maior impacto.
4. Aplicar UMA mudança reversível.
5. Rodar check primário + checks de regressão.
6. Aceitar se avançou E nada regrediu; senão reverter.
7. Persistir estado e evidência.
8. Avaliar parada.

### Estados de parada
- sucesso: condição comprovada.
- sem-progresso: N voltas sem ganho.
- bloqueado: precisa de humano.
- esgotado: teto de voltas/custo.

### Guardrails
Teto finito. Aprovação humana antes de produção/gasto/exclusão.

### Memória / estado
Arquivo `state.json` ao lado da especificação. Incluir progresso, decisões, tentativas.

### Sub-loops (opcional)
Nome do documento de cada sub-loop (na mesma pasta). Teto multiplicativo. Ciclos proibidos.

### Como acionar
`/goal` para loop curto/médio. Esqueleto Ralph para loop longo.

### Métrica de saúde
Custo por mudança aceita = tokens ou R$ / mudanças que passaram no check.

---

## 4. Gabarito do documento `<nome>-loop.md`

```markdown
---
name: <nome>
schema-version: 1
scope: <project|global>
status: ready
owner: human
base-teorica: <papers>
---

# <Nome legível>

## Descrição
<1-2 frases>

## Use quando
<quando usar>. Não usar quando: <contra-indicação>.

## Entradas (opcional)
1. <entrada 1>
Se não informada, padrão: <padrão>.

## Meta
<estado final>. Verificável? <sim/não>.

## Verificação
- Check primário: `<comando>`.
- Evidência registrada: código de saída, métricas, artefato.
- Pronto = <predicado sobre a evidência>.
- Regressão: `<comando>`.
- Timeout/erro: registrar falha; nunca tratar como sucesso.

## Passos da volta
1. Reconciliar `state.json` com repositório.
2. Medir linha de base.
3. Escolher o maior gargalo ainda não tentado.
4. Aplicar UMA mudança reversível.
5. Rodar check primário e regressão.
6. Aceitar se avançou sem regredir; senão reverter.
7. Persistir estado e evidência.
8. Avaliar parada.

## Estados de parada
- sucesso: <condição>.
- sem-progresso: <N> voltas sem ganho.
- bloqueado: <motivo típico>.
- esgotado: <N voltas / R$ X>.

## Guardrails
- Teto: <N voltas>.
- Aprovação antes de: <ações>.

## Memória / estado
`state.json` ao lado desta especificação. <detalhes de reconciliação>.

## Sub-loops (opcional)
- `<sub>-loop.md` — passo <N> da volta.

## Como acionar
- `/goal Use o loop <nome>. Continue até <condição>. Pare se <bloqueio> ou após <N> turnos.`

## Métrica de saúde
custo/mudança = tokens / mudanças aceitas.
```

---

## 5. Gabarito do comando `/loop-<nome>` (adaptador)

```markdown
---
description: Roda o loop <nome> definido em <caminho>. Valida, retoma state.json, executa até parada.
disable-model-invocation: true
---

Execute o loop especificado em `<caminho absoluto do <nome>-loop.md>`.
Leia o documento, valide, carregue state.json e execute uma volta por vez.

<Resumo: entradas, check, condição de parada. Erro ou teto NUNCA é sucesso.>
```
