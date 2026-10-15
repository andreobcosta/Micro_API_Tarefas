// Textos apresentados ao usuário, centralizados em português do Brasil
// (equivalente front-end de app/core/messages.py).
//
// Mensagens de validação (`mensagem` e `detalhes`) NÃO ficam aqui: vêm da API
// e são exibidas exatamente como ela devolve.

export const ROUTES = {
  "#/tarefas": { title: "Tarefas", wide: false },
  "#/painel": {
    title: "Painel",
    description: "O painel gerencial aparece aqui.",
    wide: true,
  },
};

export const DEFAULT_ROUTE = "#/tarefas";

// Valor do status no contrato da API -> rótulo e classe do selo.
export const STATUS = {
  pendente: { label: "Pendente", badge: "selo--pendente" },
  em_andamento: { label: "Em andamento", badge: "selo--em-andamento" },
  concluida: { label: "Concluída", badge: "selo--concluida" },
};

export const UNKNOWN_STATUS = { badge: "selo--desconhecido" };

// Uma única ação rápida por status: rótulo e status de destino.
export const QUICK_ACTIONS = {
  pendente: { label: "Iniciar", next: "em_andamento" },
  em_andamento: { label: "Concluir", next: "concluida" },
  concluida: { label: "Reabrir", next: "pendente" },
};

// Limites dos campos (maxlength). A validação em si é da API.
export const LIMITS = { title: 100, description: 500 };

// `value: null` significa "Todas": o parâmetro `status` não é enviado.
export const FILTERS = [
  { value: null, label: "Todas" },
  { value: "pendente", label: "Pendentes" },
  { value: "em_andamento", label: "Em andamento" },
  { value: "concluida", label: "Concluídas" },
];

export const TEXTS = {
  listTitle: "Tarefas",
  filterGroup: "Filtrar por status",
  loading: "Carregando tarefas…",
  empty: "Nenhuma tarefa encontrada.",
  emptyHint: "Crie uma tarefa no formulário acima ou escolha outro filtro.",
  noDescription: "Sem descrição.",
  newTask: "Nova tarefa",
  titleLabel: "Título",
  descriptionLabel: "Descrição (opcional)",
  create: "Criar tarefa",
  edit: "Editar",
  remove: "Excluir",
  save: "Salvar",
  cancel: "Cancelar",
  confirmQuestion: "Excluir esta tarefa?",
  confirmRemove: "Confirmar exclusão",
  retry: "Tentar de novo",
  previous: "Anterior",
  next: "Próxima",
  pagination: "Paginação da lista",
  // Mensagens próprias do front (a API não participa delas).
  networkError:
    "Não foi possível falar com o servidor. Verifique a conexão e tente novamente.",
  notFoundError: "Esta tarefa não existe mais. A lista foi atualizada.",
  unknownError: "Algo deu errado. Tente novamente.",
};

// Avisos de ação concluída (visíveis e anunciados em aria-live).
export const NOTICES = {
  created: "Tarefa criada.",
  createdHidden: "Tarefa criada com status pendente. Ela não aparece no filtro atual.",
  updated: "Tarefa atualizada.",
  updatedHidden: "Tarefa atualizada. Ela não aparece mais neste filtro.",
  deleted: "Tarefa excluída.",
};

/** Nome acessível de um botão de cartão: "Editar: Título da tarefa". */
export function actionLabel(action, title) {
  return `${action}: ${title}`;
}

/** Texto da paginação: "Página X de Y · N tarefas". */
export function pageSummary(page, pages, total) {
  const noun = total === 1 ? "tarefa" : "tarefas";
  return `Página ${page} de ${pages} · ${total} ${noun}`;
}
