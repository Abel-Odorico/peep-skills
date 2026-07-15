# Playbooks de correção — o fix mínimo que fecha a falha sem mudar comportamento

Princípio: a correção certa muda o **mecanismo**, não o comportamento legítimo.
Usuário válido não pode perceber diferença. Sempre o menor diff possível.

## SQL Injection
**Fix:** prepared statement / parameter binding. NUNCA "escapar melhor".
```php
// antes
$q = "SELECT * FROM users WHERE id = " . $_GET['id'];
// depois
$stmt = $pdo->prepare("SELECT * FROM users WHERE id = ?");
$stmt->execute([$_GET['id']]);
```
Node: placeholders (`?`/`$1`) do driver ou ORM. Python: params do cursor, nunca f-string.
Identificador dinâmico (nome de coluna/tabela não parametrizável): allowlist explícita.
Cuidado: binding muda tipo implícito — se o código dependia de cast, os testes acusam.

## XSS
**Fix:** escapar na SAÍDA, no contexto certo.
- PHP: `htmlspecialchars($v, ENT_QUOTES, 'UTF-8')` em todo `echo` de dado do usuário.
- React: remover `dangerouslySetInnerHTML`; se HTML é requisito real → sanitizer
  (DOMPurify) e anotar dependência nova no relatório.
- Template engines: usar o escape nativo ({{ }} no Blade/Jinja), remover `| safe`/`{!! !!}`.
Não corrija XSS com blacklist de tags — sempre escape/sanitizer.

## Command Injection
**Fix:** eliminar o shell; argumentos como array.
```js
// antes
exec(`convert ${userFile} out.png`);
// depois
execFile('convert', [userFile, 'out.png']);
```
PHP: preferir função nativa à shell; inevitável → `escapeshellarg()` em CADA argumento.
Python: `subprocess.run([...], shell=False)`.

## Secret hardcoded
**Fix em 3 passos, nesta ordem:**
1. Mover o valor para variável de ambiente / `.env` (garantir `.env` no `.gitignore`).
2. Código lê do ambiente com erro claro se ausente (nunca fallback para o valor antigo).
3. **Tarefa humana obrigatória** no relatório: rotacionar a chave exposta — ela está no
   histórico do git e continua válida. Remover do código NÃO é rotação.
Secret no histórico git: informe; reescrever histórico (`filter-repo`) só com decisão
explícita do usuário — é BLOQUEIO, não fix automático.

## Path Traversal
**Fix:** resolver e validar prefixo, ou allowlist.
```python
base = Path(UPLOAD_DIR).resolve()
alvo = (base / nome_usuario).resolve()
if not alvo.is_relative_to(base):
    abort(400)
```
Basename simples (`os.path.basename`) só quando subdiretórios não são feature.

## SSRF
**Fix:** allowlist de hosts/esquemas de destino; bloquear IPs privados/metadata
(169.254.169.254, 10/8, 172.16/12, 192.168/16, localhost) APÓS resolver DNS.
Redirect também valida (follow manual ou desligar follow).

## IDOR / BOLA
**Fix:** checagem de dono junto à query, não antes dela.
```php
// antes: busca por id vindo da URL
$fatura = Fatura::find($id);
// depois: escopo do usuário autenticado
$fatura = Fatura::where('id', $id)->where('user_id', auth()->id())->firstOrFail();
```
Padrão repetido em N endpoints: corrija um por iteração, cada um com seu check.

## JWT fraco
- `alg: none` aceito → fixar allowlist de algoritmos na verificação.
- Secret fraco/hardcoded → env var forte (tarefa humana: invalida sessões ativas — avisar).
- Sem checagem de expiração → validar `exp` (biblioteca já faz; não desligar).
Troca de secret derruba sessões: registrar impacto no relatório antes de aplicar.

## CSRF
**Fix:** habilitar o middleware nativo do framework (Laravel `VerifyCsrfToken`,
Django `CsrfViewMiddleware`) e token nos forms. API por token Bearer sem cookie: CSRF
não se aplica — não "corrigir" o que não é vulnerável.

## Criptografia fraca
- MD5/SHA1 para senha → `password_hash()`/bcrypt/argon2. **Migração compatível**:
  novo hash no próximo login; rehash transparente (`password_needs_rehash`). NUNCA
  invalidar todas as senhas de uma vez sem decisão do usuário.
- `Math.random()`/`rand()`/`uniqid()` para token → `crypto.randomBytes`,
  `random_bytes()`, `secrets.token_urlsafe()`.
- TLS verify desligado (`CURLOPT_SSL_VERIFYPEER=false`, `rejectUnauthorized:false`,
  `verify=False`) → religar. Se quebrar por certificado interno: adicionar CA ao
  trust store, nunca deixar verify off. Quebrou e sem CA disponível → BLOQUEIO.

## Dependência vulnerável
- Patch/minor com fix de CVE → bump + regenerar lockfile + checks completos.
- Major version → NUNCA automático; vira BLOQUEIO com nota de breaking changes.
- Pacote abandonado sem fix → reportar com alternativa sugerida; troca de lib é decisão humana.

## Desserialização insegura
`unserialize`/`pickle.loads`/`yaml.load` em input externo → trocar por JSON quando o
dado é estrutural (`json_decode`, `yaml.safe_load`). Formato precisa de objetos
arbitrários → redesenho, BLOQUEIO.

## Regras transversais

1. **Um achado, um diff, um commit.** Padrão repetido em 10 arquivos = 10 iterações.
2. Sem drive-by: não renomear variável, não formatar, não "aproveitar".
3. Fix que exige dependência nova (DOMPurify etc.): instalar, lockfile, checks; anotar
   no relatório.
4. Fix que muda contrato observável (formato de erro, status code, sessões derrubadas):
   só se era o comportamento vulnerável; senão BLOQUEIO com proposta.
5. Comentário inline no fix apenas quando a restrição não é óbvia no código
   (ex.: `// allowlist: nomes de coluna não são parametrizáveis em SQL`).
