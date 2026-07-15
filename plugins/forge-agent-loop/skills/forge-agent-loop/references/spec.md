# Contrato da especificação de loop

## Índice

1. Artefatos
2. Frontmatter
3. Seções obrigatórias
4. Regras de verificação
5. Estado em disco
6. Sub-loops

## 1. Artefatos

Manter uma única fonte da verdade:

```text
loops/<nome>/
├── <nome>-loop.md   # contrato humano e operacional
└── state.json       # estado mutável entre voltas
```

O documento é estável. O `state.json` muda a cada volta. Não registrar o histórico operacional no `SKILL.md` do adaptador.

## 2. Frontmatter

Usar somente:

```yaml
---
name: nome-em-kebab-case
schema-version: 1
scope: project
status: ready
owner: human
---
```

- `scope`: `project` ou `global`.
- `status`: `draft`, `ready`, `running` ou `retired`.
- `owner`: pessoa ou equipe responsável por aprovar ações protegidas.

## 3. Seções obrigatórias

### Descrição

Explicar em até duas frases o que melhora a cada volta.

### Use quando

Dar a situação concreta e também um caso em que o loop não deve ser usado.

### Entradas

Listar valores fixados antes da primeira volta. Se não houver, escrever `Não se aplica` e justificar.

### Meta e critérios de aceite

Definir o estado final observável. Separar critérios obrigatórios de guardrails.

### Verificação

Declarar:

- `Check primário:` comando ou aferição externa;
- `Evidência registrada:` código de saída, números e caminho do artefato;
- `Pronto =` predicado exato sobre a evidência;
- checks de regressão;
- tratamento de timeout e erro.

### Passos da volta

Usar esta ordem:

1. reconciliar estado e repositório;
2. medir linha de base;
3. escolher o maior gargalo ainda não tentado;
4. aplicar uma mudança reversível;
5. rodar check primário e guardrails;
6. aceitar ou reverter;
7. persistir estado e evidência;
8. avaliar parada.

### Estados de parada

Definir sem sobreposição:

- `sucesso`: todos os critérios de aceite comprovados;
- `sem-progresso`: limite explícito de voltas sem ganho;
- `bloqueado`: falta de permissão, informação ou dependência externa;
- `esgotado`: teto de voltas, tempo ou custo.

Erro nunca equivale a sucesso.

### Guardrails e aprovações

Definir teto finito e ações protegidas. Produção, publicação, comunicação externa, gasto e destruição exigem aprovação explícita, salvo autorização prévia inequívoca.

### Memória e retomada

Definir como reconciliar um estado antigo com o Git atual, como evitar repetir tentativas e como recuperar uma gravação interrompida.

### Skills e sub-loops

Listar skills compostas. Listar sub-loops por caminho e impedir ciclos. Incluir o custo máximo do aninhamento no teto do pai.

### Como executar

Incluir uma instrução neutra e as invocações específicas dos harnesses instalados. A execução deve começar pela validação.

### Métricas de saúde

Registrar ao menos:

- mudanças aceitas / voltas;
- custo ou tempo / mudança aceita;
- voltas sem progresso;
- regressões detectadas antes de merge/publicação.

## 4. Regras de verificação

Preferir, nesta ordem:

1. testes determinísticos;
2. lint, typecheck e build;
3. consultas e métricas reproduzíveis;
4. comparação por fixture ou snapshot;
5. juiz humano ou LLM com rubrica congelada.

Se usar juiz LLM, não compartilhar justificativas do gerador antes do veredito. Registrar rubrica, amostra, resultado e divergências.

## 5. Estado em disco

O `state.json` deve conter no mínimo:

```json
{
  "schema_version": 1,
  "loop": "nome",
  "status": "draft",
  "iteration": 0,
  "max_iterations": 12,
  "baseline": null,
  "last_check": null,
  "accepted_changes": [],
  "attempts": [],
  "terminal_reason": null
}
```

Atualizar por gravação atômica quando o harness permitir. Não incluir segredos nem despejos enormes; apontar para artefatos no disco.

## 6. Sub-loops

Representar o grafo antes da execução. Rejeitar qualquer aresta que retorne a um ancestral. Se o pai aceita `P` voltas e o filho `F`, reservar orçamento para até `P × F` voltas internas ou reduzir os tetos.
