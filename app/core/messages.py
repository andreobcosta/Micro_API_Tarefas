"""Textos apresentados ao usuário, centralizados em português do Brasil."""

# --- Domínio e erros ---
PATCH_EMPTY_BODY = "Informe ao menos um campo para atualizar."
TASK_NOT_FOUND = "Tarefa não encontrada."

# --- Códigos do contrato de erro ---
CODE_TASK_NOT_FOUND = "TAREFA_NAO_ENCONTRADA"

# --- Saúde ---
HEALTH_OK = "operacional"

# --- OpenAPI: aplicação ---
APP_TITLE = "Micro-API de Tarefas"
APP_DESCRIPTION = (
    "API REST para criar, listar (com filtro por status e paginação), consultar, "
    "atualizar e excluir tarefas."
)
APP_VERSION = "0.1.0"
TAG_TASKS = "Tarefas"
TAG_TASKS_DESCRIPTION = "Operações sobre tarefas."
TAG_HEALTH = "Saúde"
TAG_HEALTH_DESCRIPTION = "Verificação de saúde da aplicação."

# --- OpenAPI: operações ---
SUMMARY_CREATE_TASK = "Criar tarefa"
DESCRIPTION_CREATE_TASK = (
    "Cria uma tarefa. O status padrão é `pendente`; o título é aparado nas pontas."
)
RESPONSE_CREATE_TASK = "Tarefa criada."

SUMMARY_LIST_TASKS = "Listar tarefas"
DESCRIPTION_LIST_TASKS = (
    "Lista as tarefas da mais recente para a mais antiga, com filtro opcional "
    "por status e paginação por `limite` e `deslocamento`."
)
RESPONSE_LIST_TASKS = "Página de tarefas com o total que atende ao filtro."
PARAM_STATUS = "Filtra por status: `pendente`, `em_andamento` ou `concluida`."
PARAM_LIMIT = "Quantidade máxima de itens na página (1 a 100)."
PARAM_OFFSET = "Quantidade de itens a pular antes da página (a partir de 0)."

SUMMARY_GET_TASK = "Consultar tarefa"
DESCRIPTION_GET_TASK = "Devolve uma tarefa pelo seu identificador."
RESPONSE_GET_TASK = "Tarefa encontrada."

SUMMARY_REPLACE_TASK = "Substituir tarefa"
DESCRIPTION_REPLACE_TASK = (
    "Substitui título, descrição e status. Exige `titulo` e `status`; "
    "`descricao` ausente vira `null`."
)
RESPONSE_REPLACE_TASK = "Tarefa substituída."

SUMMARY_DELETE_TASK = "Excluir tarefa"
DESCRIPTION_DELETE_TASK = "Remove uma tarefa pelo seu identificador."
RESPONSE_DELETE_TASK = "Tarefa excluída (sem conteúdo)."

SUMMARY_HEALTH = "Verificar saúde"
DESCRIPTION_HEALTH = "Indica se a aplicação está respondendo."
RESPONSE_HEALTH = "Aplicação operacional."
