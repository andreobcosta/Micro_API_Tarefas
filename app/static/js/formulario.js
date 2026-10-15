// Formulário "Nova tarefa".
//
// Não valida nada no front: envia o que foi digitado e mostra a `mensagem` e
// os `detalhes` devolvidos pela API.

import { errorAlert, markFieldErrors } from "./alerta.js";
import { el, labeledField } from "./dom.js";
import { LIMITS, TEXTS } from "./messages.js";

const ERROR_ID = "nova-erro";

/**
 * Cria o formulário de nova tarefa.
 *
 * @param {object} options
 * @param {(body: object) => Promise<object>} options.submit Envia a criação.
 * @param {(task: object) => Promise<void>} options.onCreated Chamado após o
 *   sucesso (recarrega a lista e anuncia o aviso).
 * @returns {HTMLFormElement}
 */
export function createTaskForm({ submit, onCreated }) {
  const titleInput = el("input", {
    attrs: {
      id: "nova-titulo",
      type: "text",
      name: "titulo",
      maxlength: LIMITS.title,
      autocomplete: "off",
    },
  });
  const descriptionInput = el("textarea", {
    attrs: {
      id: "nova-descricao",
      name: "descricao",
      rows: 3,
      maxlength: LIMITS.description,
    },
  });
  const controls = { titulo: titleInput, descricao: descriptionInput };
  const errorBox = el("div", { class: "formulario__erro" });
  const button = el("button", {
    class: "botao botao--primario",
    text: TEXTS.create,
    attrs: { type: "submit" },
  });

  async function handleSubmit(event) {
    event.preventDefault();
    button.disabled = true;
    errorBox.replaceChildren();
    markFieldErrors(null, controls);

    const body = { titulo: titleInput.value };
    if (descriptionInput.value !== "") body.descricao = descriptionInput.value;

    try {
      const task = await submit(body);
      titleInput.value = "";
      descriptionInput.value = "";
      await onCreated(task);
      titleInput.focus();
    } catch (error) {
      const alert = errorAlert(error, { id: ERROR_ID });
      errorBox.replaceChildren(alert);
      markFieldErrors(error, controls, ERROR_ID);
      alert.focus();
    } finally {
      button.disabled = false;
    }
  }

  return el(
    "form",
    {
      class: "cartao formulario",
      attrs: { novalidate: true, "aria-labelledby": "nova-secao" },
      on: { submit: handleSubmit },
    },
    el("h3", { class: "formulario__titulo", text: TEXTS.newTask, attrs: { id: "nova-secao" } }),
    labeledField(TEXTS.titleLabel, titleInput),
    labeledField(TEXTS.descriptionLabel, descriptionInput),
    errorBox,
    button,
  );
}
