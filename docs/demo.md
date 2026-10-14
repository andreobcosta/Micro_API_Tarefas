# Roteiro de demonstração — Micro-API de Tarefas

Roteiro de 10 passos para demonstrar a API de ponta a ponta. Cada passo traz o comando em **curl** e em **PowerShell 5.1** e a saída esperada. As saídas abaixo foram obtidas contra um servidor `uvicorn` real; os `id` e as datas mudam a cada execução (use o `id` que a sua execução devolver).

Requisitos: ambiente instalado (ver [README](../README.md#instalação-e-configuração)).

## Preparação

**Terminal 1 — servidor** (banco novo, para a saída ficar igual à deste roteiro):

```powershell
$env:DATABASE_URL = "sqlite:///./demo.db"
python -m uvicorn app.main:app
```

```bash
DATABASE_URL="sqlite:///./demo.db" python -m uvicorn app.main:app
```

Ao terminar, pare o servidor (Ctrl+C), apague `demo.db` e limpe a variável (`Remove-Item Env:DATABASE_URL`).

**Terminal 2 — cliente.** No PowerShell 5.1, defina antes uma vez:

```powershell
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$B = "http://127.0.0.1:8000"
function J($o) { , [Text.Encoding]::UTF8.GetBytes(($o | ConvertTo-Json -Compress)) }
```

> Por que `J`? O PS 5.1 envia *strings* com acento em Latin-1 e a API (corretamente) recusa com `400`. Enviar bytes UTF-8 evita o problema. Os objetos são exibidos com `Format-List` porque o `ConvertTo-Json` do PS 5.1 reescreve datas como `\/Date(...)\/`; o JSON bruto em UTC aparece nos exemplos de curl.

No bash: `B=http://127.0.0.1:8000`.

---

## 1. Ver a documentação interativa

Abra no navegador `http://127.0.0.1:8000/documentacao` (Swagger UI) ou `/referencia` (ReDoc). Títulos, descrições e exemplos estão em português; os rótulos da interface permanecem em inglês (framework).

## 2. Verificar a saúde

```bash
curl -i $B/saude
```

```powershell
Invoke-RestMethod "$B/saude"
```

Saída esperada: `HTTP/1.1 200 OK` e (no PowerShell, o objeto aparece como tabela com `status = operacional`)

```json
{"status":"operacional"}
```

## 3. Criar tarefas

```bash
curl -i -X POST $B/tarefas -H "Content-Type: application/json" \
  -d '{"titulo": "Estudar pytest", "descricao": "Ler a documentação de fixtures"}'
curl -X POST $B/tarefas -H "Content-Type: application/json" -d '{"titulo": "Revisar o README", "status": "em_andamento"}'
curl -X POST $B/tarefas -H "Content-Type: application/json" -d '{"titulo": "Publicar a release", "status": "concluida"}'
```

```powershell
$t = Invoke-RestMethod -Method Post -Uri "$B/tarefas" -ContentType "application/json; charset=utf-8" `
       -Body (J @{ titulo = "Estudar pytest"; descricao = "Ler a documentação de fixtures" })
$t | Format-List
Invoke-RestMethod -Method Post -Uri "$B/tarefas" -ContentType "application/json; charset=utf-8" -Body (J @{ titulo = "Revisar o README"; status = "em_andamento" }) | Out-Null
Invoke-RestMethod -Method Post -Uri "$B/tarefas" -ContentType "application/json; charset=utf-8" -Body (J @{ titulo = "Publicar a release"; status = "concluida" }) | Out-Null
```

Saída esperada do primeiro (`201 Created`; `status` assume `pendente` por padrão). **Atenção (PS 5.1):** o `Format-List` exibe `descricao` como `Ler a documentaÃ§Ã£o de fixtures`; é só a exibição (o PS 5.1 lê `application/json` sem `charset` como ISO-8859-1), o dado no servidor está correto, como o curl mostra. Isso se repete nos passos 4, 6 e demais que exibam `descricao`.

```json
{"id":"dc471170-7c0c-4d6e-aaa6-6dcc991970ca","titulo":"Estudar pytest","descricao":"Ler a documentação de fixtures","status":"pendente","criado_em":"2026-10-14T16:54:04.641063Z","atualizado_em":"2026-10-14T16:54:04.641063Z"}
```

Guarde o `id` (`ID=dc471170-...` no bash; `$t.id` no PowerShell). Os dois `curl` seguintes devolvem `201`.

## 4. Listar com filtro por status

```bash
curl "$B/tarefas?status=pendente&limite=5&deslocamento=0"
```

```powershell
$l = Invoke-RestMethod "$B/tarefas?status=pendente&limite=5&deslocamento=0"
$l | Format-List total, limite, deslocamento
$l.itens | Format-List
```

Saída esperada: só a tarefa pendente, e `total` reflete o filtro.

```json
{"itens":[{"id":"dc471170-7c0c-4d6e-aaa6-6dcc991970ca","titulo":"Estudar pytest","descricao":"Ler a documentação de fixtures","status":"pendente","criado_em":"2026-10-14T16:54:04.641063Z","atualizado_em":"2026-10-14T16:54:04.641063Z"}],"total":1,"limite":5,"deslocamento":0}
```

## 5. Paginar

```bash
curl "$B/tarefas?limite=2&deslocamento=1"
```

```powershell
$p = Invoke-RestMethod "$B/tarefas?limite=2&deslocamento=1"
$p | Format-List total, limite, deslocamento
$p.itens | Format-List titulo, status
```

Saída esperada: `total` 3, `limite` 2, `deslocamento` 1 e duas tarefas, da mais recente para a mais antiga (pulando a primeira): "Revisar o README" e "Estudar pytest".

## 6. Consultar por id

```bash
curl $B/tarefas/$ID
```

```powershell
Invoke-RestMethod "$B/tarefas/$($t.id)" | Format-List
```

Saída esperada: `200` com a tarefa criada no passo 3.

## 7. Substituir (PUT)

`descricao` ausente vira `null`; `atualizado_em` avança.

```bash
curl -X PUT $B/tarefas/$ID -H "Content-Type: application/json" \
  -d '{"titulo": "Estudar pytest e cobertura", "status": "em_andamento"}'
```

```powershell
Invoke-RestMethod -Method Put -Uri "$B/tarefas/$($t.id)" -ContentType "application/json; charset=utf-8" `
  -Body (J @{ titulo = "Estudar pytest e cobertura"; status = "em_andamento" }) | Format-List
```

```json
{"id":"dc471170-7c0c-4d6e-aaa6-6dcc991970ca","titulo":"Estudar pytest e cobertura","descricao":null,"status":"em_andamento","criado_em":"2026-10-14T16:54:04.641063Z","atualizado_em":"2026-10-14T16:54:06.106072Z"}
```

## 8. Atualizar parcialmente (PATCH)

```bash
curl -X PATCH $B/tarefas/$ID -H "Content-Type: application/json" -d '{"status": "concluida"}'
```

```powershell
Invoke-RestMethod -Method Patch -Uri "$B/tarefas/$($t.id)" -ContentType "application/json; charset=utf-8" `
  -Body (J @{ status = "concluida" }) | Format-List
```

Saída esperada: só `status` muda para `concluida` e `atualizado_em` é atualizado:

```json
{"id":"dc471170-7c0c-4d6e-aaa6-6dcc991970ca","titulo":"Estudar pytest e cobertura","descricao":null,"status":"concluida","criado_em":"2026-10-14T16:54:04.641063Z","atualizado_em":"2026-10-14T16:54:06.243543Z"}
```

## 9. Provocar erros de validação

Todo erro segue `{codigo, mensagem, detalhes[]}`, em português.

```bash
curl -i -X POST $B/tarefas -H "Content-Type: application/json" -d '{"titulo": "ab"}'
curl "$B/tarefas?status=invalido"
curl -X PATCH $B/tarefas/$ID -H "Content-Type: application/json" -d '{}'
```

```powershell
try { Invoke-RestMethod -Method Post -Uri "$B/tarefas" -ContentType "application/json; charset=utf-8" -Body (J @{ titulo = "ab" }) }
catch { [int]$_.Exception.Response.StatusCode; $_.ErrorDetails.Message }
try { Invoke-RestMethod "$B/tarefas?status=invalido" } catch { $_.ErrorDetails.Message }
```

Saídas esperadas (`422`):

```json
{"codigo":"VALIDACAO_INVALIDA","mensagem":"Os dados enviados são inválidos.","detalhes":[{"campo":"titulo","mensagem":"Deve ter no mínimo 3 caracteres."}]}
{"codigo":"VALIDACAO_INVALIDA","mensagem":"Os dados enviados são inválidos.","detalhes":[{"campo":"status","mensagem":"Valor inválido. Valores aceitos: pendente, em_andamento, concluida."}]}
{"codigo":"VALIDACAO_INVALIDA","mensagem":"Os dados enviados são inválidos.","detalhes":[{"campo":"corpo","mensagem":"Informe ao menos um campo para atualizar."}]}
```

Bônus: `curl $B/tarefas/abc` devolve `422` com `{"campo":"id","mensagem":"Identificador inválido. Informe um UUID válido."}`; `curl $B/inexistente` devolve `404` `ROTA_NAO_ENCONTRADA`.

## 10. Excluir e confirmar

```bash
curl -i -X DELETE $B/tarefas/$ID
curl -i $B/tarefas/$ID
```

```powershell
(Invoke-WebRequest -Method Delete -Uri "$B/tarefas/$($t.id)" -UseBasicParsing).StatusCode
try { Invoke-RestMethod "$B/tarefas/$($t.id)" } catch { [int]$_.Exception.Response.StatusCode; $_.ErrorDetails.Message }
```

Saídas esperadas: `204 No Content` e, em seguida, `404`:

```json
{"codigo":"TAREFA_NAO_ENCONTRADA","mensagem":"Tarefa não encontrada.","detalhes":[]}
```

---

**Persistência (extra):** pare o servidor e suba-o de novo com o mesmo `DATABASE_URL`; `GET /tarefas` devolve as mesmas tarefas, com os mesmos `id`, títulos e datas em UTC (verificado: 3 tarefas antes e depois do reinício, idênticas).
