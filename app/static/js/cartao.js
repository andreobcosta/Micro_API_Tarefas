// Cartão de tarefa em três modos: visualização, edição inline e confirmação
// de exclusão. Os efeitos (PATCH, DELETE, estado da lista) ficam em `actions`,
// fornecidas por tarefas.js.

import { errorAlert, markFieldErrors } from "./alerta.js";
import { isNotFound } from "./api.js";
import { el, labeledField } from "./dom.js";
import {
  LIMITS,
  QUICK_ACTIONS,
  STATUS,
  TEXTS,
  UNKNOWN_STATUS,
  actionLabel,
} from "./messages.js";

function statusBadge(status) {
  const known = Object.hasOwn(STATUS, status) ? STATUS[status] : null;
  return el("span", {
    class: `selo ${(known ?? UNKNOWN_STATUS).badge}`,
    text: known ? known.label : String(status),
  });
}

function descriptionParagraph(task) {
  return task.descricao === null
    ? el("p", { class: "cartao__descricao secundario", text: TEXTS.noDescription })
    : el("p", { class: "cartao__descricao", text: task.descricao });
}

/**
 * Executa uma ação do cartão com os botões desabilitados (impede duplo clique).
 *
 * Erro 404: delega a `onGone` (a tarefa não existe mais). Qualquer outro erro
 * vira alerta dentro do cartão, com o foco nele.
 */
async function guarded({ buttons, errorBox, run, onGone, fields = null, errorId = null }) {
  for (const button of buttons) button.disabled = true;
  errorBox.replaceChildren();
  if (fields) markFieldErrors(null, fields);
  try {
    await run();
  } catch (error) {
    if (isNotFound(error)) {
      await onGone();
      return;
    }
    const alert = errorAlert(error, { id: errorId ?? undefined });
    errorBox.replaceChildren(alert);
    if (fields) markFieldErrors(error, fields, errorId ?? undefined);
    alert.focus();
  } finally {
    for (const button of buttons) button.disabled = false;
  }
}

function viewCard(task, actions) {
  const finished = task.status === "concluida";
  const errorBox = el("div", { class: "cartao__erro" });
  const buttons = [];
  const guard = (run) =>
    guarded({ buttons, errorBox, run, onGone: () => actions.gone(task) });

  const quick = Object.hasOwn(QUICK_ACTIONS, task.status) ? QUICK_ACTIONS[task.status] : null;
  if (quick) {
    buttons.push(
      el("button", {
        class: "botao",
        text: quick.label,
        attrs: { type: "button", "aria-label": actionLabel(quick.label, task.titulo) },
        dataset: { foco: "rapida" },
        on: { click: () => guard(() => actions.changeStatus(task, quick.next)) },
      }),
    );
  }
  buttons.push(
    el("button", {
      class: "botao",
      text: TEXTS.edit,
      attrs: { type: "button", "aria-label": actionLabel(TEXTS.edit, task.titulo) },
      dataset: { foco: "editar" },
      on: { click: () => actions.startEdit(task) },
    }),
    el("button", {
      class: "botao",
      text: TEXTS.remove,
      attrs: { type: "button", "aria-label": actionLabel(TEXTS.remove, task.titulo) },
      dataset: { foco: "excluir" },
      on: { click: () => actions.askDelete(task) },
    }),
  );

  return el(
    "article",
    { class: "cartao", dataset: { id: task.id } },
    el(
      "div",
      { class: "cartao__cabecalho" },
      el("h3", {
        class: finished ? "cartao__titulo riscado" : "cartao__titulo",
        text: task.titulo,
        attrs: { tabindex: "-1" },
        dataset: { foco: "cartao" },
      }),
      statusBadge(task.status),
    ),
    descriptionParagraph(task),
    el("div", { class: "cartao__acoes" }, buttons),
    errorBox,
  );
}

function confirmCard(task, actions) {
  const errorBox = el("div", { class: "cartao__erro" });
  const buttons = [];
  const confirm = el("button", {
    class: "botao botao--perigo",
    text: TEXTS.confirmRemove,
    attrs: { type: "button" },
    dataset: { foco: "confirmar" },
    on: {
      click: () =>
        guarded({
          buttons,
          errorBox,
          run: () => actions.confirmDelete(task),
          onGone: () => actions.gone(task),
        }),
    },
  });
  const cancel = el("button", {
    class: "botao",
    text: TEXTS.cancel,
    attrs: { type: "button" },
    dataset: { foco: "cancelar" },
    on: { click: () => actions.cancelDelete(task) },
  });
  buttons.push(confirm, cancel);

  return el(
    "article",
    { class: "cartao cartao--confirmar", dataset: { id: task.id } },
    el(
      "div",
      { class: "cartao__cabecalho" },
      el("h3", {
        class: "cartao__titulo",
        text: task.titulo,
        attrs: { tabindex: "-1" },
        dataset: { foco: "cartao" },
      }),
      statusBadge(task.status),
    ),
    descriptionParagraph(task),
    el("p", { class: "cartao__pergunta", text: TEXTS.confirmQuestion }),
    el("div", { class: "cartao__acoes" }, confirm, cancel),
    errorBox,
  );
}

function editCard(task, actions) {
  const base = `editar-${task.id}`;
  const errorId = `${base}-erro`;

  const titleInput = el("input", {
    attrs: {
      id: `${base}-titulo`,
      type: "text",
      name: "titulo",
      maxlength: LIMITS.title,
      autocomplete: "off",
    },
    dataset: { foco: "titulo" },
  });
  titleInput.value = task.titulo;
  const descriptionInput = el("textarea", {
    attrs: {
      id: `${base}-descricao`,
      name: "descricao",
      rows: 3,
      maxlength: LIMITS.description,
    },
  });
  descriptionInput.value = task.descricao ?? "";
  const fields = { titulo: titleInput, descricao: descriptionInput };

  const errorBox = el("div", { class: "cartao__erro" });
  const buttons = [];

  /** PATCH só com os campos alterados; descrição apagada vira `null`. */
  function buildPatch() {
    const patch = {};
    if (titleInput.value !== task.titulo) patch.titulo = titleInput.value;
    const description = descriptionInput.value === "" ? null : descriptionInput.value;
    if (description !== task.descricao) patch.descricao = description;
    return patch;
  }

  function handleSubmit(event) {
    event.preventDefault();
    const patch = buildPatch();
    if (Object.keys(patch).length === 0) {
      actions.cancelEdit(task);
      return;
    }
    guarded({
      buttons,
      errorBox,
      run: () => actions.save(task, patch),
      onGone: () => actions.gone(task),
      fields,
      errorId,
    });
  }

  const save = el("button", {
    class: "botao botao--primario",
    text: TEXTS.save,
    attrs: { type: "submit" },
  });
  const cancel = el("button", {
    class: "botao",
    text: TEXTS.cancel,
    attrs: { type: "button" },
    dataset: { foco: "cancelar" },
    on: { click: () => actions.cancelEdit(task) },
  });
  buttons.push(save, cancel);

  return el(
    "article",
    { class: "cartao cartao--edicao", dataset: { id: task.id } },
    el(
      "form",
      {
        class: "formulario",
        attrs: { novalidate: true },
        on: {
          submit: handleSubmit,
          keydown: (event) => {
            if (event.key === "Escape" && !cancel.disabled) actions.cancelEdit(task);
          },
        },
      },
      labeledField(TEXTS.titleLabel, titleInput),
      labeledField(TEXTS.descriptionLabel, descriptionInput),
      el("div", { class: "cartao__acoes" }, save, cancel),
      errorBox,
    ),
  );
}

/**
 * Monta o cartão de uma tarefa.
 *
 * @param {object} task Tarefa no contrato da API.
 * @param {"view"|"edit"|"confirm"} mode
 * @param {object} actions Ações fornecidas por tarefas.js.
 * @returns {HTMLElement}
 */
export function taskCard(task, mode, actions) {
  if (mode === "edit") return editCard(task, actions);
  if (mode === "confirm") return confirmCard(task, actions);
  return viewCard(task, actions);
}
