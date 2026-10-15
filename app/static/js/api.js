// Acesso à API da Micro-API de Tarefas (mesma origem, caminhos relativos).

import { TEXTS } from "./messages.js";

const TASKS_PATH = "/tarefas";

/**
 * Erro de chamada à API.
 *
 * `kind`: "api" (resposta no contrato `{codigo, mensagem, detalhes}`),
 * "rede" (a requisição nem chegou ao servidor) ou "desconhecido" (resposta
 * fora do contrato, por exemplo vinda de um proxy).
 */
export class ApiError extends Error {
  constructor({ kind, status = 0, codigo = "", mensagem = "", detalhes = [] }) {
    super(mensagem || kind);
    this.name = "ApiError";
    this.kind = kind;
    this.status = status;
    this.codigo = codigo;
    this.mensagem = mensagem;
    this.detalhes = detalhes;
  }
}

function isErrorContract(payload) {
  return (
    payload !== null &&
    typeof payload === "object" &&
    typeof payload.codigo === "string" &&
    typeof payload.mensagem === "string" &&
    Array.isArray(payload.detalhes)
  );
}

async function request(path, { method = "GET", body } = {}) {
  const headers = { Accept: "application/json" };
  const init = { method, headers };
  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    init.body = JSON.stringify(body);
  }

  let response;
  try {
    response = await fetch(path, init);
  } catch {
    throw new ApiError({ kind: "rede" });
  }

  // DELETE bem-sucedido: 204, sem corpo.
  if (response.status === 204) return null;

  let payload = null;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }

  if (response.ok && payload !== null) return payload;
  if (isErrorContract(payload)) {
    throw new ApiError({ kind: "api", status: response.status, ...payload });
  }
  throw new ApiError({ kind: "desconhecido", status: response.status });
}

/**
 * Lista tarefas (GET /tarefas).
 *
 * @param {{status: string|null, limit: number, offset: number}} query
 *   `status` nulo não envia o parâmetro (todas as tarefas).
 * @returns {Promise<{itens: object[], total: number, limite: number, deslocamento: number}>}
 */
export function listTasks({ status, limit, offset }) {
  const params = new URLSearchParams();
  if (status) params.set("status", status);
  params.set("limite", String(limit));
  params.set("deslocamento", String(offset));
  return request(`${TASKS_PATH}?${params.toString()}`);
}

/**
 * Cria uma tarefa (POST /tarefas).
 *
 * O corpo é enviado como o usuário digitou; a validação é da API.
 *
 * @param {{titulo: string, descricao?: string}} body
 * @returns {Promise<object>} A tarefa criada.
 */
export function createTask(body) {
  return request(TASKS_PATH, { method: "POST", body });
}

/**
 * Atualiza parcialmente uma tarefa (PATCH /tarefas/{id}).
 *
 * @param {string} id
 * @param {{titulo?: string, descricao?: string|null, status?: string}} patch
 * @returns {Promise<object>} A tarefa atualizada.
 */
export function updateTask(id, patch) {
  return request(`${TASKS_PATH}/${encodeURIComponent(id)}`, { method: "PATCH", body: patch });
}

/**
 * Exclui uma tarefa (DELETE /tarefas/{id}).
 *
 * @param {string} id
 * @returns {Promise<null>}
 */
export function deleteTask(id) {
  return request(`${TASKS_PATH}/${encodeURIComponent(id)}`, { method: "DELETE" });
}

/** Indica se o erro é "tarefa não encontrada" (404 no contrato da API). */
export function isNotFound(error) {
  return error instanceof ApiError && error.kind === "api" && error.status === 404;
}

/**
 * Indica se algum detalhe de validação aponta para o campo informado.
 *
 * @param {unknown} error
 * @param {string} field Nome do campo no contrato (ex.: "titulo").
 */
export function hasFieldError(error, field) {
  if (!(error instanceof ApiError)) return false;
  return error.detalhes.some(
    (item) =>
      typeof item.campo === "string" &&
      (item.campo === field || item.campo.endsWith(`.${field}`)),
  );
}

/**
 * Converte um erro em texto para a tela.
 *
 * Mensagens de validação vêm da API e são mostradas como ela devolve
 * (`mensagem` e cada detalhe como "campo: mensagem"); rede, 404 e respostas
 * fora do contrato usam textos definidos no front.
 *
 * @param {unknown} error
 * @returns {{message: string, details: string[]}}
 */
export function describeError(error) {
  if (!(error instanceof ApiError)) {
    return { message: TEXTS.unknownError, details: [] };
  }
  if (error.kind === "rede") {
    return { message: TEXTS.networkError, details: [] };
  }
  if (error.kind === "api" && error.status === 404) {
    return { message: TEXTS.notFoundError, details: [] };
  }
  if (error.kind === "api") {
    return {
      message: error.mensagem,
      details: error.detalhes.map((item) => `${item.campo}: ${item.mensagem}`),
    };
  }
  return { message: TEXTS.unknownError, details: [] };
}
