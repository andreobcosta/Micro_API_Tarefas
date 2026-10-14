# ADR-002: Persistência com SQLAlchemy 2.x e SQLite

**Status:** aceito
**Data:** 2026-10-14
**Decisor:** Andreo

## Contexto
A API rodava sobre `InMemoryTaskRepository`. É preciso persistir de verdade sem alterar rotas nem `TaskService` (RNF02), com testes herméticos (RNF05) e configuração por ambiente (RNF06).

## Decisão
- **Repositório SQL** (`SqlTaskRepository`) atrás do mesmo Protocol `TaskRepository`. Uma única suíte de contrato roda contra as duas implementações; o repositório devolve a entidade de domínio, nunca o modelo ORM.
- **Sessão e transação:** uma sessão curta por operação do repositório, com `commit` ao fim de cada escrita. Sem unidade de trabalho entre operações: o serviço faz uma escrita por caso de uso. Leituras não fazem `commit`.
- **Datas:** o SQLite não guarda fuso. O tipo `UtcDateTime` converte para UTC ao gravar (recusa data sem fuso) e devolve `tzinfo=UTC` ao ler. Assim a entidade sempre tem datas UTC com fuso.
- **Status:** gravado pelo **valor** do enum (`pendente`, `em_andamento`, `concluida`) em coluna de texto, não pelo nome.
- **Ordenação:** `created_at` decrescente com desempate por `id` decrescente, nas duas implementações (paginação determinística).
- **Configuração:** `DATABASE_URL`, `APP_ENV` e `LOG_LEVEL` lidas só de variáveis de ambiente (sem `python-dotenv`, uma dependência a menos). Padrão: `sqlite:///./tasks.db`.
- **Criação das tabelas:** `create_all` no *lifespan* da aplicação; o engine é criado sem abrir conexão, então importar `app.main` não toca o disco.
- **Somente SQLite no MVP:** `create_db_engine` recusa qualquer outro banco (ou URL malformada) com erro em português que não repete a URL (pode conter senha). PostgreSQL é Próximo Passo.
- **Migrações:** fora de escopo (sem Alembic). Mudança de esquema exige recriar o banco; vira Próximo Passo.

## Consequências
**Positivas:** troca de banco por `DATABASE_URL`; testes herméticos (SQLite em memória, `StaticPool`); contrato único para as duas implementações.
**Negativas / trade-offs:** sem migrações; SQLite não cobre concorrência de produção; sessão por operação impede transações que abranjam várias operações do repositório.
