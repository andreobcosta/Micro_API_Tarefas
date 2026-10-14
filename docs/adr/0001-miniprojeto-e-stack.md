# ADR-001: Miniprojeto Micro-API de Tarefas com FastAPI, SQLite e arquitetura em camadas
 
**Status:** aceito
**Data:** 2026-10-13 (revisado em 2026-10-13: regra de idioma v1.2)
**Decisor:** Andreo
 
## Contexto
A disciplina exige um MVP de ~30h, com uso de GenAI em várias etapas, testes automatizados, boa documentação e entrega pública no GitHub (≥5 commits Conventional Commits, README, tag e licença). Opções do livro: Micro-API de Tarefas, Chatbot RAG, Dashboard de Clima, Gerador de Senhas.
 
## Decisão
Construir a **Micro-API de Gerenciamento de Tarefas** em **Python 3.11+ / FastAPI / Pydantic v2 / SQLAlchemy 2.x / SQLite**, com **arquitetura em camadas** (`api` → `services` → `repositories`) e **repositório atrás de interface** (injeção de dependência). Testes com **pytest** e cobertura mínima de **80%**. **Idioma: código interno em inglês; tudo o que o sistema apresenta em português do Brasil** — contrato público da API (campos do JSON, valores do enum, rotas, parâmetros, chaves de erro), mensagens, logs, documentação OpenAPI, README e docs. O mapeamento é feito com aliases do Pydantic e valores de enum em português (detalhes em `docs/requisitos.md`, §2 e §4).
 
## Alternativas consideradas
| Alternativa | Motivo da rejeição |
|---|---|
| Gerador de Senhas | Escopo pequeno demais para justificar camadas, refatoração e testes de integração |
| Dashboard de Clima | Depende de API externa/chave e de front-end; mais risco de prazo |
| Chatbot RAG | Maior custo/risco (embeddings, mocks de LLM, prompt injection) para 30h |
| Node.js/Express | Stack com a qual os exemplos do livro e o foco em pytest/Pydantic casam menos |
| PostgreSQL desde o início | Aumenta setup sem ganho para o MVP; fica como Próximo Passo (troca via `DATABASE_URL` + nova implementação do repositório) |
 
## Consequências
**Positivas:** escopo controlável; ótima testabilidade; reaproveita os exemplos do livro (modelo Pydantic de tarefa, Repository Pattern); sem custo nem segredos externos; OpenAPI automática.
**Negativas / trade-offs:** menor "apelo" de IA no produto final (mitigado: IA é usada no processo de desenvolvimento e há extensão opcional com LLM em Próximos Passos); mapeamento alias ↔ campo adiciona uma camada de tradução (mitigada por testes de contrato); validação e erros do framework em inglês exigem tradução manual (handlers globais + teste de idioma); parte da interface do Swagger UI permanece em inglês (framework); SQLite não cobre concorrência de produção.
**Riscos:** ver §10 do documento de requisitos.
 
## Referências
`docs/requisitos.md`, Book Aula 4 (Unidades II e IV).