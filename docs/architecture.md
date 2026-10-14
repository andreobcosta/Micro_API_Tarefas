# Arquitetura — Micro-API de Tarefas

Visão da arquitetura em camadas. Requisitos em [requisitos.md](requisitos.md); decisão de stack em [adr/0001-miniprojeto-e-stack.md](adr/0001-miniprojeto-e-stack.md).

## 1. Componentes

A regra de negócio fica somente em `services`. O serviço depende da interface `TaskRepository` (Protocol), nunca de uma implementação concreta; a implementação é injetada via `Depends`.

```mermaid
flowchart LR
    Cliente["Cliente HTTP"]
    API["api<br/>(APIRouter /tarefas)"]
    Services["services<br/>(TaskService)"]
    Contract{{"TaskRepository<br/>(Protocol)"}}
    Sql["repositories<br/>SqlTaskRepository"]
    Mem["repositories<br/>InMemoryTaskRepository<br/>(testes)"]
    DB[("SQLite")]

    Cliente -- "HTTP/JSON" --> API
    API -- "schemas Pydantic" --> Services
    Services -- "chama" --> Contract
    Contract -. "implementado por" .-> Sql
    Contract -. "implementado por" .-> Mem
    Sql -- "SQL" --> DB

    style Contract fill:#fff3cd,stroke:#b58900,stroke-width:3px
```

## 2. Sequência — `GET /tarefas?status=&limite=&deslocamento=`

```mermaid
sequenceDiagram
    actor Cliente
    participant API as api (tasks.py)
    participant Servico as TaskService
    participant Repo as TaskRepository
    participant DB as SQLite

    Cliente->>API: GET /tarefas?status=pendente&limite=10&deslocamento=0
    API->>API: valida parâmetros (status, limite 1–100, deslocamento ≥ 0)
    alt parâmetros inválidos
        API-->>Cliente: 422 {codigo: VALIDACAO_INVALIDA, mensagem, detalhes[]}
    else parâmetros válidos
        API->>Servico: list(status, limit, offset)
        Servico->>Repo: list(status, limit, offset)
        Repo->>DB: SELECT ... WHERE status = ? ORDER BY created_at DESC LIMIT ? OFFSET ?
        DB-->>Repo: linhas
        Repo->>DB: SELECT COUNT(*) WHERE status = ?
        DB-->>Repo: total
        Repo-->>Servico: (items, total)
        Servico-->>API: (items, total)
        API-->>Cliente: 200 {itens, total, limite, deslocamento}
    end
```

## 3. Entidade `Task` — contrato (PT-BR) ↔ código (EN)

O contrato público usa português (via `Field(alias=...)` e valores do enum); o código e o banco usam inglês (§4.1 do requisitos).

```mermaid
classDiagram
    class Task {
        +UUID id  «contrato: id»
        +str title  «contrato: titulo · 3–100, trim»
        +str|None description  «contrato: descricao · ≤ 500»
        +TaskStatus status  «contrato: status · padrão PENDING»
        +datetime created_at  «contrato: criado_em · UTC»
        +datetime updated_at  «contrato: atualizado_em · UTC»
    }
    class TaskStatus {
        <<enumeration>>
        PENDING  «valor: pendente»
        IN_PROGRESS  «valor: em_andamento»
        DONE  «valor: concluida»
    }
    class TaskModel {
        <<ORM · tabela tasks>>
        id
        title
        description
        status
        created_at
        updated_at
    }
    Task --> TaskStatus : status
    TaskModel ..> Task : persiste
```

## 4. Decisões e trade-offs

- **Camadas `api` → `services` → `repositories`:** isolam regra de negócio de HTTP e de banco; custo é um pouco mais de código para um CRUD pequeno.
- **`TaskRepository` como Protocol:** permite testar os serviços com `InMemoryTaskRepository`, sem banco, e trocar o SQLite por PostgreSQL no futuro (Próximo Passo).
- **SQLite via SQLAlchemy 2.x:** zero setup e sem segredos; não cobre concorrência de produção.
- **Contrato em português, código em inglês:** aliases do Pydantic e enum com valor em português separam API pública da implementação; a camada de tradução é protegida por testes de contrato.
- **Erros do framework em inglês:** exigem handlers globais e mensagens centralizadas em `app/core/messages.py`, com teste automatizado de idioma.
- **Swagger UI/ReDoc:** os rótulos da interface permanecem em inglês (framework); mitigado com títulos, descrições e exemplos em português.
- **Listagem sempre paginada** (limite máximo 100), ordenada por `criado_em` decrescente: evita respostas ilimitadas, sem ordenação configurável no MVP.
