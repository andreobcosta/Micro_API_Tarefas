"""Textos apresentados ao usuário, centralizados em português do Brasil."""

# --- Domínio e erros ---
PATCH_EMPTY_BODY = "Informe ao menos um campo para atualizar."
TASK_NOT_FOUND = "Tarefa não encontrada."

# --- Códigos do contrato de erro ---
CODE_TASK_NOT_FOUND = "TAREFA_NAO_ENCONTRADA"
CODE_VALIDATION = "VALIDACAO_INVALIDA"
CODE_ROUTE_NOT_FOUND = "ROTA_NAO_ENCONTRADA"
CODE_METHOD_NOT_ALLOWED = "METODO_NAO_PERMITIDO"
CODE_HTTP_ERROR = "ERRO_HTTP"
CODE_INTERNAL_ERROR = "ERRO_INTERNO"

# --- Mensagens de erro do contrato ---
VALIDATION_FAILED = "Os dados enviados são inválidos."
ROUTE_NOT_FOUND = "Rota não encontrada."
METHOD_NOT_ALLOWED = "Método não permitido para esta rota."
HTTP_ERROR = "Não foi possível processar a requisição."
INTERNAL_ERROR = "Erro interno do servidor. Tente novamente mais tarde."
LOG_UNHANDLED_ERROR = "Erro interno não tratado ao processar %s %s."

# --- Validação: campo e mensagem por tipo de erro do Pydantic ---
FIELD_BODY = "corpo"
VALIDATION_FALLBACK = "Valor inválido."
VALIDATION_ENUM = "Valor inválido. Valores aceitos: {values}."
VALIDATION_MESSAGES = {
    "missing": "Campo obrigatório.",
    "string_too_short": "Deve ter no mínimo {min_length} caracteres.",
    "string_too_long": "Deve ter no máximo {max_length} caracteres.",
    "string_type": "Deve ser um texto.",
    "uuid_parsing": "Identificador inválido. Informe um UUID válido.",
    "greater_than_equal": "Deve ser maior ou igual a {ge}.",
    "less_than_equal": "Deve ser menor ou igual a {le}.",
    "int_parsing": "Deve ser um número inteiro.",
    "json_invalid": "JSON malformado.",
}

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

# --- OpenAPI: nomes dos componentes (classe em inglês -> nome no esquema) ---
OPENAPI_COMPONENT_NAMES = {
    "TaskResponse": "Tarefa",
    "TaskCreate": "CriacaoDeTarefa",
    "TaskReplace": "SubstituicaoDeTarefa",
    "TaskUpdate": "AtualizacaoDeTarefa",
    "TaskListResponse": "ListaDeTarefas",
    "TaskStatus": "StatusDaTarefa",
    "ErrorResponse": "Erro",
    "ErrorDetail": "DetalheDoErro",
    "HealthResponse": "RespostaDeSaude",
}

# --- OpenAPI: identificadores das operações ---
OPERATION_ID_CREATE_TASK = "criar_tarefa"
OPERATION_ID_LIST_TASKS = "listar_tarefas"
OPERATION_ID_GET_TASK = "consultar_tarefa"
OPERATION_ID_REPLACE_TASK = "substituir_tarefa"
OPERATION_ID_UPDATE_TASK = "atualizar_tarefa"
OPERATION_ID_DELETE_TASK = "excluir_tarefa"
OPERATION_ID_HEALTH = "verificar_saude"

# --- OpenAPI: operações ---
PARAM_TASK_ID = "Identificador (UUID) da tarefa."
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

SUMMARY_UPDATE_TASK = "Atualizar tarefa parcialmente"
DESCRIPTION_UPDATE_TASK = (
    "Altera apenas os campos enviados. Informe ao menos um campo; "
    "`descricao: null` limpa a descrição, e `titulo` e `status` não aceitam `null`."
)
RESPONSE_UPDATE_TASK = "Tarefa atualizada."

RESPONSE_VALIDATION_ERROR = "Dados inválidos na requisição."

SUMMARY_DELETE_TASK = "Excluir tarefa"
DESCRIPTION_DELETE_TASK = "Remove uma tarefa pelo seu identificador."
RESPONSE_DELETE_TASK = "Tarefa excluída (sem conteúdo)."

SUMMARY_HEALTH = "Verificar saúde"
DESCRIPTION_HEALTH = "Indica se a aplicação está respondendo."
RESPONSE_HEALTH = "Aplicação operacional."

# --- Configuração e persistência ---
CONFIG_INVALID_LOG_LEVEL = (
    "Valor inválido para LOG_LEVEL: {value!r}. Use um de: {allowed}."
)
NAIVE_DATETIME = "A data deve conter fuso horário (UTC)."
