---
name: sincronizar-catalogo-peep
schema-version: 1
scope: project
status: ready
owner: Abel Odorico
---

# Sincronizar Catálogo Peep

## Descrição
Sincronizar os diretórios de plugins com os marketplaces Claude e Codex e com o README, reduzindo uma classe de divergência por volta até que o catálogo seja verificavelmente consistente.

## Use quando
Usar após adicionar, remover ou portar plugins no repositório `peep-skills`. Não usar para publicar, instalar globalmente, fazer commit ou push.

## Entradas
Não se aplica: a raiz, os catálogos e o limite foram fixados nesta especificação.

## Meta e critérios de aceite
- Meta observável: o check retorna código zero e lista vazia em `errors`.
- Todos os diretórios em `plugins/` aparecem uma vez nos marketplaces Claude e Codex.
- Todos possuem manifestos Claude e Codex válidos, com `name` igual à pasta e caminho de skills existente.
- README contém comando de instalação Claude e seção para cada plugin.
- Guardrails: preservar conteúdo das skills e alterações pré-existentes; não fazer commit, push, instalação ou publicação.

## Verificação
- Check primário: `python3 loops/sincronizar-catalogo-peep/check_catalog.py`
- Evidência registrada: código de saída, contagens e lista `errors` produzida em JSON; resumo salvo em `state.json`.
- Pronto = código de saída zero, 16 plugins nos dois marketplaces, 16 instalações e 16 seções no README, com `errors: []`.
- Checks de regressão: `validate_manifests()` dentro do próprio `check_catalog.py` (não é script separado — cobre nome, versão, descrição, caminho `skills` e interface de cada `.claude-plugin`/`.codex-plugin`), validar cada skill tocada com `plugins/skill-creator/skills/skill-creator/scripts/quick_validate.py <dir-da-skill>`, e `git diff --check`.
- Timeout ou erro: registrar a falha e parar como bloqueado ou sem-progresso; nunca tratar como sucesso.

## Passos da volta
1. Reconciliar `state.json` com o Git sem modificar alterações pré-existentes.
2. Rodar o check e registrar a linha de base ou o resultado anterior.
3. Escolher a classe de divergência com maior impacto ainda não tratada.
4. Aplicar uma mudança reversível limitada a essa classe.
5. Rodar o check primário e os checks proporcionais à mudança.
6. Aceitar apenas se a quantidade de erros cair sem regressão; caso contrário, corrigir ou reverter somente a própria mudança.
7. Persistir evidência e avaliar a parada.

## Estados de parada
- sucesso: check primário retorna zero e todos os checks de regressão passam.
- sem-progresso: duas voltas consecutivas sem reduzir a lista de erros.
- bloqueado: manifesto inválido que exija decisão de produto, permissão externa ou alteração destrutiva.
- esgotado: 15 voltas.

## Guardrails e aprovações
- Teto rígido: 15 voltas.
- Aprovação humana antes de: commit, push, publicação, instalação global, comunicação externa, exclusão ou mudança de licença.
- Não alterar conteúdo funcional de skills para mascarar falhas de catálogo.
- Não registrar segredos no estado.

## Memória e retomada
- Estado: `loops/sincronizar-catalogo-peep/state.json`.
- Reconciliar cada retomada com `git status --short` e nova execução do check.
- Identificar tentativas por número da volta e classe de divergência.

## Skills e sub-loops
- `forge-agent-loop`: contrato, estado e execução do loop.
- `plugin-creator`: contrato e validação dos manifestos Codex.
- Sub-loops: não se aplica; nenhuma chamada recursiva.

## Como executar
1. Validar esta especificação.
2. Ler `state.json` e rodar o check primário.
3. Executar uma volta por classe de divergência.
4. Parar somente em estado terminal e relatar evidência.

## Métricas de saúde
- erros removidos por volta;
- mudanças aceitas por volta;
- voltas sem progresso;
- regressões interceptadas antes de commit ou publicação.
