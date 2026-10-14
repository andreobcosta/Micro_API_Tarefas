# Requisitos — Micro-API de Gerenciamento de Tarefas
 
**Versão:** 1.2 (regra de idioma redefinida por Andreo em 2026-10-13) · **Esforço-alvo:** ~30h
**Stack:** Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.x, SQLite, pytest
 
## 1. Visão
 
API REST para **criar, listar (com filtro por status e paginação), consultar, atualizar (PUT/PATCH) e excluir tarefas**, com persistência em banco, testes automatizados (cobertura ≥ 80%) e documentação — entregue como repositório público no GitHub, desenvolvido com apoio de IA generativa em todas as etapas (projeto da pós "Engenharia de Software Aplicado com IA").
 
## 2. Decisões de requisitos (fechadas)
 
| # | Decisão | Origem |
|---|---|---|
| D1 | `status` é **enum** com três valores: `pendente`, `em_andamento`, `concluida` (padrão `pendente`) | Andreo |
| D2 | Filtro por **status** na listagem | Andreo |
| D3 | **Filtro e paginação entram no MVP** | Andreo |
| D4 | Inclui **PATCH** (além de PUT) | Andreo |
| D5 | Cobertura de testes **≥ 80%** (verificada no `make test`) | Andreo |
| D6 | **Idioma: o código pode ser em inglês; tudo o que é apresentado no sistema é em português do Brasil** (v1.2) | Andreo |
 
### Regra de idioma (D6) — detalhamento
 
**Em português (BR) — "tudo o que o sistema apresenta":**
- **Contrato público da API:** nomes de campos do JSON, valores do enum, rotas, parâmetros de consulta e chaves do contrato de erro.
- Mensagens de erro, validação, logs e respostas.
- Documentação OpenAPI (títulos, resumos, descrições, tags, exemplos) e rotas de documentação.
- README, ADRs, documentos em `docs/` e descrição/corpo das mensagens de commit.
- Docstrings e comentários *(padrão assumido; inglês também seria aceitável)*.
**Em inglês — código interno:**
- Módulos, pastas, classes, funções, variáveis, constantes, nomes de testes.
- Tabelas e colunas do banco, variáveis de ambiente, alvos do Makefile.
- Nomes de branches de trabalho e tipos do Conventional Commits (`feat`, `fix`, `docs`, `test`, `refactor`, `chore`).
**Mapeamento contrato ↔ código** (separa a API pública da implementação):
- Campos: `Field(alias="titulo")` no Pydantic, com `populate_by_name=True`; a serialização da resposta usa o alias.
- Enum: `PENDING = "pendente"` — nome em inglês, **valor** em português.
- Parâmetros de consulta: `Query(alias="limite")` etc.
- Rotas em português definidas no `APIRouter(prefix="/tarefas")`.
- Efeito colateral útil: o `loc` dos erros de validação do Pydantic já traz os nomes do contrato (ex.: `titulo`).
**Exceção inevitável:** a interface do Swagger UI/ReDoc (rótulos de botões) é do framework e permanece em inglês; mitigação: títulos, descrições e exemplos em português e rotas de documentação renomeadas (RNF07).
 
## 3. Escopo
 
**Dentro:** RF01–RF07, RNF01–RNF13.
**Fora (vai para "Próximos Passos" do README):** autenticação/autorização, multiusuário, front-end, deploy, migrações (Alembic), PostgreSQL, ordenação configurável, busca textual, recursos com LLM (ex.: sugerir subtarefas), exclusão lógica.
 
## 4. Glossário de nomenclatura
 
### 4.1 Contrato público (português) ↔ código interno (inglês)
 
| Conceito | Contrato da API (PT-BR) | Código / banco (EN) |
|---|---|---|
| Tarefa | `Tarefa` (nome do schema na doc) | `Task` |
| id | `id` | `id` |
| título | `titulo` | `title` |
| descrição | `descricao` | `description` |
| status | `status` | `status` |
| criado em | `criado_em` | `created_at` |
| atualizado em | `atualizado_em` | `updated_at` |
| valores do enum | `pendente` / `em_andamento` / `concluida` | `PENDING` / `IN_PROGRESS` / `DONE` |
| itens / total / limite / deslocamento | `itens` / `total` / `limite` / `deslocamento` | `items` / `total` / `limit` / `offset` |
| erro: código / mensagem / detalhes / campo | `codigo` / `mensagem` / `detalhes` / `campo` | `code` / `message` / `details` / `field` |
| schemas no OpenAPI | `Tarefa`, `CriacaoDeTarefa`, `SubstituicaoDeTarefa`, `AtualizacaoDeTarefa`, `ListaDeTarefas`, `StatusDaTarefa`, `Erro`, `DetalheDoErro`, `RespostaDeSaude` | `TaskResponse`, `TaskCreate`, `TaskReplace`, `TaskUpdate`, `TaskListResponse`, `TaskStatus`, `ErrorResponse`, `ErrorDetail`, `HealthResponse` |
| `operationId` / parâmetro de rota | `criar_tarefa`, `listar_tarefas`, `consultar_tarefa`, `substituir_tarefa`, `atualizar_tarefa`, `excluir_tarefa`, `verificar_saude` / `{id}` | `task_id` (alias `id`) |
 
### 4.2 Rotas (português)
 
| Rota | Finalidade |
|---|---|
| `/tarefas` | coleção |
| `/tarefas/{id}` | item |
| `/saude` | verificação de saúde |
| `/documentacao` | Swagger UI (`docs_url`) |
| `/referencia` | ReDoc (`redoc_url`) |
| `/esquema-openapi.json` | esquema OpenAPI (`openapi_url`) |
 
### 4.3 Código (inglês)
 
| Elemento | Nome |
|---|---|
| Enum | `TaskStatus` |
| Schemas | `TaskCreate`, `TaskReplace` (PUT), `TaskUpdate` (PATCH), `TaskResponse`, `TaskListResponse`, `ErrorResponse` |
| Entidade ORM | `TaskModel` (tabela `tasks`; colunas `id`, `title`, `description`, `status`, `created_at`, `updated_at`) |
| Contrato de repositório | `TaskRepository` (Protocol) |
| Implementações | `SqlTaskRepository`, `InMemoryTaskRepository` |
| Serviço | `TaskService` (`create`, `list`, `get`, `replace`, `update`, `delete`) |
| Exceções de domínio | `TaskNotFoundError` (`InvalidDataError` será criada quando houver regra que a use) |
| Variáveis de ambiente | `DATABASE_URL`, `APP_ENV`, `LOG_LEVEL` |
| Alvos do Makefile | `install`, `run`, `test`, `format` |
| Testes | `tests/**/test_*.py`, funções `test_*` (padrão do pytest, sem configuração especial) |
 
### 4.4 Estrutura de pastas
 
```
projeto/
├─ app/
│  ├─ main.py                      # cria a aplicação e registra rotas/handlers
│  ├─ api/
│  │  ├─ tasks.py                  # APIRouter(prefix="/tarefas")
│  │  ├─ health.py                 # GET /saude
│  │  ├─ dependencies.py           # get_task_service (Depends; repositório em app.state)
│  │  ├─ openapi.py                # nomes dos componentes do OpenAPI em português
│  │  └─ error_handlers.py         # handlers de erro no contrato em português
│  ├─ schemas/
│  │  ├─ task.py                   # aliases PT-BR do contrato
│  │  ├─ error.py                  # ErrorResponse/ErrorDetail (documentam o contrato de erro)
│  │  └─ health.py
│  ├─ services/
│  │  └─ task_service.py
│  ├─ repositories/
│  │  ├─ base.py                   # TaskRepository (Protocol)
│  │  ├─ in_memory.py
│  │  └─ sql_repository.py         # evitar nomear "sqlalchemy.py" (sombreia o pacote)
│  ├─ models/
│  │  └─ task.py
│  ├─ core/
│  │  ├─ config.py
│  │  ├─ errors.py
│  │  └─ messages.py               # TODOS os textos em PT-BR centralizados
│  └─ db/
│     └─ session.py
├─ tests/
│  ├─ unit/
│  └─ integration/
├─ docs/
│  ├─ architecture.md
│  └─ adr/
├─ .env.example
├─ .gitignore
├─ .gitattributes
├─ LICENSE
├─ Makefile
└─ README.md
```
 
## 5. Modelo de dados
 
**Tarefa**
 
| Campo (contrato) | Tipo | Regras |
|---|---|---|
| `id` | UUID v4 | gerado pelo sistema; imutável |
| `titulo` | string | obrigatório; espaços nas pontas removidos; 3 a 100 caracteres |
| `descricao` | string \| null | opcional; até 500 caracteres *(padrão assumido)* |
| `status` | enum | `pendente` \| `em_andamento` \| `concluida`; padrão `pendente` |
| `criado_em` | datetime UTC | gerado na criação |
| `atualizado_em` | datetime UTC | atualizado a cada alteração |
 
## 6. Requisitos funcionais
 
| ID | Requisito | Prior. |
|---|---|---|
| RF01 | **Criar tarefa** — `POST /tarefas` → `201` com a tarefa criada | Must |
| RF02 | **Listar tarefas** — `GET /tarefas` com filtro `?status=` e paginação `?limite=&deslocamento=`; resposta com `itens`, `total`, `limite`, `deslocamento`; ordenada por `criado_em` decrescente | Must |
| RF03 | **Consultar tarefa** — `GET /tarefas/{id}` → `200` ou `404` | Must |
| RF04 | **Substituir tarefa** — `PUT /tarefas/{id}`; exige `titulo` e `status`; `descricao` ausente vira `null` | Must |
| RF05 | **Atualizar parcialmente** — `PATCH /tarefas/{id}`; qualquer subconjunto de `titulo`, `descricao`, `status`; corpo vazio é inválido | Must |
| RF06 | **Excluir tarefa** — `DELETE /tarefas/{id}` → `204` ou `404` | Must |
| RF07 | **Verificação de saúde** — `GET /saude` → `200` `{"status": "operacional"}` | Could |
 
### Parâmetros de listagem (RF02)
 
| Parâmetro | Tipo | Regra | Padrão |
|---|---|---|---|
| `status` | enum | um dos valores válidos; inválido → `422` | sem filtro |
| `limite` | inteiro | 1 a 100 | 10 |
| `deslocamento` | inteiro | ≥ 0 | 0 |
 
### Critérios de aceite (Dado / Quando / Então)
 
**RF01**
- Dado `{"titulo": "Estudar pytest"}`, quando `POST /tarefas`, então `201` com `id`, `status="pendente"`, `criado_em` e `atualizado_em` preenchidos.
- Dado `{"titulo": "ab"}`, então `422` com mensagem em português indicando o campo `titulo`.
- Dado `{"titulo": "   Estudar   "}`, então o título é salvo sem os espaços das pontas.
**RF02**
- Dadas 25 tarefas, quando `GET /tarefas?limite=10&deslocamento=20`, então `itens` tem 5 elementos e `total=25`.
- Dadas tarefas em vários status, quando `GET /tarefas?status=concluida`, então só retornam tarefas `concluida` e `total` reflete o filtro.
- Quando `GET /tarefas?status=invalido`, então `422` com mensagem em português listando os valores aceitos (`pendente`, `em_andamento`, `concluida`).
- Quando `limite=0`, `limite=101` ou `deslocamento=-1`, então `422`.
- Sem tarefas, então `200` com `itens=[]` e `total=0`.
**RF03 / RF06**
- Dado um `id` inexistente, então `404` com `{"codigo": "TAREFA_NAO_ENCONTRADA", "mensagem": "Tarefa não encontrada.", "detalhes": []}` (todo erro traz `detalhes`, vazio quando não há itens).
- Dado um `id` que não é UUID, então `422`.
- Após `DELETE` com sucesso, um novo `GET` do mesmo `id` retorna `404`.
**RF04**
- Dado corpo sem `status`, então `422`. Dado corpo completo válido, então `200` e `atualizado_em` maior que o anterior.
**RF05**
- Dado `{"status": "em_andamento"}`, então só `status` muda; `titulo` e `descricao` permanecem; `atualizado_em` é atualizado.
- Dado `{}`, então `422` com `mensagem` de topo "Os dados enviados são inválidos." e `detalhes[0] = {"campo": "corpo", "mensagem": "Informe ao menos um campo para atualizar."}`.
- Dado `{"titulo": "x"}`, então `422` (mesma regra de validação do título).
- Regra de `null` no PATCH: `titulo: null` e `status: null` são inválidos (`422`); `descricao: null` é válido e limpa a descrição. Campos ausentes não são alterados.
**RF07** — `GET /saude` retorna `200`.
 
## 7. Contrato de erro (padronizado, em português)
 
```json
{
  "codigo": "VALIDACAO_INVALIDA",
  "mensagem": "Os dados enviados são inválidos.",
  "detalhes": [
    {"campo": "titulo", "mensagem": "Deve ter no mínimo 3 caracteres."}
  ]
}
```
 
Toda resposta de erro traz `codigo`, `mensagem` e `detalhes` (`[]` quando não há itens). Cada item de `detalhes` tem só `campo` e `mensagem`; nunca `input`, `ctx`, `url` nem stack trace. O `campo` sai sem o prefixo de origem (`body`, `query`, `path`); o parâmetro de rota aparece como `id`, e erros do corpo inteiro (JSON malformado, PATCH `{}`) usam `corpo`.
 
| Situação | HTTP | `codigo` |
|---|---|---|
| Validação (corpo, parâmetros, UUID) | 422 | `VALIDACAO_INVALIDA` |
| Tarefa inexistente | 404 | `TAREFA_NAO_ENCONTRADA` |
| Rota inexistente | 404 | `ROTA_NAO_ENCONTRADA` |
| Método não permitido | 405 | `METODO_NAO_PERMITIDO` (mantém o cabeçalho `Allow`) |
| Outro erro HTTP do framework | o do erro | `ERRO_HTTP` |
| Erro inesperado | 500 | `ERRO_INTERNO` (sem vazar detalhes internos; o detalhe vai só para o log) |
 
> **Atenção técnica:** o FastAPI/Pydantic gera mensagens em **inglês** por padrão (validação, 404/405 de rota, `detail`). Para cumprir D6 é preciso *exception handlers* para `RequestValidationError`, `StarletteHTTPException` (404/405) e `Exception` (500), mapeando os tipos de erro do Pydantic (`missing`, `string_too_short`, `string_too_long`, `enum`, `uuid_parsing`, `greater_than_equal`, `less_than_equal`, `int_parsing`, `json_invalid`…) para mensagens em português. Centralizar todos os textos em `app/core/messages.py`.
 
## 8. Requisitos não funcionais
 
| ID | Requisito |
|---|---|
| RNF01 | **Arquitetura em camadas**: `api` → `services` → `repositories` → banco; regra de negócio somente em `services` |
| RNF02 | **Repositório atrás de interface** (`Protocol`) com implementação SQLAlchemy e implementação **em memória** para testes; injeção via `Depends` |
| RNF03 | **Qualidade de código**: tipagem estática, PEP 8, docstrings estilo Google, Black (e Ruff, opcional) |
| RNF04 | **Testes**: pytest; unitários dos serviços (repositório em memória) + integração da API (`TestClient`, SQLite em memória); **cobertura ≥ 80%** com `--cov-fail-under=80` |
| RNF05 | **Testes herméticos**: sem rede, sem dependência de ordem, banco isolado por teste |
| RNF06 | **Configuração por ambiente** (`DATABASE_URL`, `APP_ENV`, `LOG_LEVEL`); `.env` no `.gitignore`; `.env.example` versionado |
| RNF07 | **Documentação**: OpenAPI com título, resumos, descrições, tags e exemplos em PT-BR; rotas `/documentacao`, `/referencia` e `/esquema-openapi.json` |
| RNF08 | **Datas em UTC** com timezone (`datetime.now(timezone.utc)`) |
| RNF09 | **Pydantic v2** (`model_config = ConfigDict(...)`) — sem `class Config` legado |
| RNF10 | **Empacotamento**: `requirements.txt` com versões reais (`pip freeze`), `Makefile` (`install`, `run`, `test`, `format`), licença |
| RNF11 | **Segurança básica**: validação de toda entrada; sem segredos no repositório; respostas de erro sem stack trace |
| RNF12 | **Desempenho**: sem requisito formal; listagem sempre paginada (limite máximo 100) |
| RNF13 | **Idioma (D6)**: nada em inglês no que o sistema apresenta (contrato JSON, mensagens, logs, OpenAPI); verificado por **teste automatizado de idioma** (afirma chaves e mensagens em português, incluindo erros do framework) |
 
## 9. Conformidade com a disciplina
 
| Exigência | Como atendemos |
|---|---|
| Repositório público | GitHub, `main` limpa |
| ≥ 5 commits Conventional Commits | Plano de 11 commits (§11), descrições em português |
| README completo | Em português; inclui seção de IA e "Limitações e Próximos Passos" |
| Dependências | `requirements.txt` |
| Testes passando | `make test` com cobertura ≥ 80% |
| Sem segredos | `.env` ignorado; `.env.example` |
| Release/Tag + licença | `v1.0.0` + `LICENSE` |
 
## 10. Riscos e mitigação
 
| Risco | Mitigação |
|---|---|
| Mensagens do framework em inglês vazando para o usuário | Handlers globais + teste de idioma (RNF13) |
| Campo/valor em inglês escapando para o contrato público | Aliases no Pydantic + teste que compara as chaves do JSON e o esquema OpenAPI com o glossário §4.1 |
| Mapeamento alias ↔ campo confuso (erros de serialização) | Testes de contrato: resposta usa `titulo`. **Limitação assumida:** com `populate_by_name=True` a entrada também aceita o nome interno em inglês (ex.: `{"title": ...}`); o comportamento é mantido de propósito, documentado por teste e listado em "Limitações" do README |
| Mensagens misturadas PT/EN nos logs | Logs também centralizados em `messages.py` |
| Versões/APIs inexistentes sugeridas pela IA | Validar com `pip install`/`pip freeze`; revisão crítica de 5 passos |
| Estilo Pydantic v1 do exemplo do livro | RNF09 no `CLAUDE.md` |
| Cobertura inflada por testes fracos | Revisar asserts; cobrir erros e bordas |
| Scope creep | Itens fora de escopo só como Próximos Passos |
 
## 11. Plano de entrega (commits-alvo e estimativa)
 
| # | Commit (tipo em inglês; descrição em português) | Estim. |
|---|---|---|
| 1 | `chore: estrutura inicial, .gitignore, licença e .env.example` | 1h |
| 2 | `docs: requisitos, arquitetura (Mermaid) e ADR-001` | 2h |
| 3 | `feat(core): esquemas Pydantic com aliases em português e enum de status` | 2h |
| 4 | `feat(repositories): contrato e implementação em memória` (TDD) | 3h |
| 5 | `feat(services): regras de negócio das tarefas` (TDD) | 4h |
| 6 | `feat(api): rotas de tarefas com filtro e paginação` | 5h |
| 7 | `feat(api): PATCH e tratamento de erros em português` | 3h |
| 7b | `feat(api): nomes em português no esquema OpenAPI` (commit extra, sem renumerar os demais) | 1h |
| 8 | `feat(db): repositório SQLAlchemy com SQLite` | 3h |
| 9 | `test: testes de integração, de idioma e cobertura mínima de 80%` | 3h |
| 10 | `docs: README, demonstração e seção "Como a IA acelerou este projeto"` | 3h |
| 11 | `chore: Makefile, dependências e release v1.0.0` | 1h |
| | **Total** | **~30h** |
 
## 12. Padrões assumidos (baixo impacto; me avise se quiser mudar)
 
1. `descricao` com até 500 caracteres.
2. Ordenação padrão: `criado_em` decrescente.
3. `limite` padrão 10 e máximo 100.
4. Licença MIT.
5. Campo de situação chama-se `status` no contrato (alternativa: `situacao`).
6. Docstrings e comentários em português.
## Histórico de versões
- **1.0** — requisitos iniciais (status como enum, filtro, paginação, PATCH, cobertura ≥ 80%).
- **1.1** — tudo em português, inclusive identificadores (substituída).
- **1.2** — contrato público e textos em português; código interno em inglês (**vigente**).