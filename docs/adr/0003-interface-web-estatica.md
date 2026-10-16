# ADR-003: Interface web estática servida pela própria API

**Status:** aceito
**Data:** 2026-10-15
**Decisor:** Andreo

## Contexto
A v1.0.0 entrega só a API. Surgiu a necessidade de uma interface simples para operar as tarefas e de um painel gerencial, sem alterar o contrato da API, os serviços, os repositórios nem os testes existentes, e sem criar endpoints novos. O projeto é um MVP: ferramentas extras de build e dependências de rede aumentam o custo de manter e de demonstrar.

## Decisão
- **Arquivos estáticos puros** (HTML, CSS e JavaScript com módulos ES) em `app/static/`, **sem build, sem Node, sem framework e sem CDN**. Funciona offline.
- **Servida pela própria API**, na mesma origem, com `StaticFiles` montado em `/app` dentro de `create_app()`. Não há CORS a configurar.
- **Só a API existente:** a interface consome `GET/POST /tarefas` e `GET/PATCH/DELETE /tarefas/{id}`. Nenhum endpoint novo.
- **Segurança por construção:** DOM montado só com `createElement` e `textContent` (nunca `innerHTML`); CSP `default-src 'self'` em `<meta>`, o que proíbe script e estilo inline (a largura das barras do painel vai por CSSOM). Um teste de integração percorre os `.js` e falha se aparecer `innerHTML`, `eval`, estilo inline etc.
- **Idioma:** todos os textos da interface ficam em `js/messages.js` (equivalente de `app/core/messages.py`). Mensagens de validação não são reescritas: vêm da API e são exibidas como devolvidas, sem pré-validação no navegador (uma única fonte de regras).
- **Painel calculado no cliente:** 4 chamadas paralelas a `GET /tarefas` (3 com `status` e `limite=1` para os totais, 1 com `limite=5` para as últimas). O total é a soma dos três totais.

## Alternativas consideradas
- **SPA com Node e framework (React, Vue etc.):** rejeitada. Exigiria build, `node_modules` e outra cadeia de dependências, fora do escopo do MVP.
- **Servidor separado para a interface:** rejeitada. Exigiria CORS, dois processos e mais configuração.
- **Endpoint de resumo na API:** adiado. Resolveria o painel em uma chamada e permitiria tempo médio e séries por dia, mas altera o contrato; fica como Próximo Passo.

## Consequências
**Positivas:** nenhuma dependência nova; um único processo; a API da v1.0.0 permanece intacta; interface auditável (poucos arquivos, sem código gerado).
**Negativas / trade-offs:** o JavaScript não tem testes automatizados (apenas servimento e segurança do código; o comportamento é validado manualmente; Playwright é Próximo Passo); o painel é uma fotografia, sem tempo médio nem séries por dia, e as 4 chamadas não são atômicas; sem rascunho: a edição aberta é descartada em qualquer recarga da lista.
