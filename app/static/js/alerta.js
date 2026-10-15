// Alerta de erro reutilizado por lista, formulário e cartões.

import { describeError, hasFieldError } from "./api.js";
import { el } from "./dom.js";

/**
 * Monta o alerta (`role="alert"`) com a mensagem e os detalhes do erro.
 *
 * @param {unknown} error
 * @param {{id?: string, retry?: HTMLElement}} [options]
 *   `retry`: botão "Tentar de novo" exibido dentro do alerta.
 * @returns {HTMLElement} Elemento focável (`tabindex="-1"`).
 */
export function errorAlert(error, { id, retry } = {}) {
  const { message, details } = describeError(error);
  return el(
    "div",
    { class: "alerta", attrs: { role: "alert", tabindex: "-1", id } },
    el("p", { class: "alerta__mensagem", text: message }),
    details.length > 0
      ? el(
          "ul",
          { class: "alerta__detalhes" },
          details.map((detail) => el("li", { text: detail })),
        )
      : null,
    retry ?? null,
  );
}

/**
 * Marca como inválidos os controles cujo campo a API apontou.
 *
 * Sem `error` (ou sem `alertId`), apenas limpa as marcas.
 *
 * @param {unknown} error
 * @param {Record<string, HTMLElement>} controls Campo do contrato -> controle.
 * @param {string} [alertId] `id` do alerta, ligado por aria-describedby.
 */
export function markFieldErrors(error, controls, alertId) {
  for (const [field, control] of Object.entries(controls)) {
    if (error && hasFieldError(error, field)) {
      control.setAttribute("aria-invalid", "true");
      if (alertId) control.setAttribute("aria-describedby", alertId);
    } else {
      control.removeAttribute("aria-invalid");
      control.removeAttribute("aria-describedby");
    }
  }
}
