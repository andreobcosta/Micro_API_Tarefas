// Tela "Tarefas" (#/tarefas): criação, lista, filtro, paginação, edição,
// mudança de status e exclusão.

import { errorAlert } from "./alerta.js";
import { createTask, deleteTask, listTasks, updateTask } from "./api.js";
import { taskCard } from "./cartao.js";
import { el } from "./dom.js";
import { createTaskForm } from "./formulario.js";
import { FILTERS, NOTICES, TEXTS, pageSummary } from "./messages.js";

const PAGE_SIZE = 10;

/** Deslocamento da última página que existe para `total` itens. */
function lastPageOffset(total) {
  return (Math.ceil(total / PAGE_SIZE) - 1) * PAGE_SIZE;
}

/** Anuncia o texto na região aria-live da página. */
function announce(text) {
  const region = document.getElementById("avisos");
  if (!region) return;
  // Limpar antes garante que um texto repetido seja anunciado de novo.
  region.textContent = "";
  setTimeout(() => {
    region.textContent = text;
  }, 50);
}

/**
 * Monta a tela de tarefas dentro de `root`.
 *
 * O estado vive nesta chamada: cada visita à rota começa do zero (filtro
 * "Todas", primeira página, nenhuma edição aberta).
 */
export function mountTasks(root) {
  const state = {
    filter: null,
    offset: 0,
    ticket: 0,
    view: "loading",
    data: null,
    error: null,
    editing: null,
    confirming: null,
  };

  const heading = el("h2", {
    class: "tarefas__titulo",
    text: TEXTS.listTitle,
    attrs: { tabindex: "-1" },
  });

  const form = createTaskForm({ submit: createTask, onCreated: handleCreated });

  // Aviso visível da última ação; o anúncio para leitores de tela vai em #avisos.
  const notice = el("p", { class: "nota", attrs: { hidden: true } });

  const filterButtons = FILTERS.map((filter) =>
    el("button", {
      class: "botao botao--filtro",
      text: filter.label,
      attrs: { type: "button", "aria-pressed": "false" },
      on: { click: () => changeFilter(filter.value) },
    }),
  );
  const filterBar = el(
    "div",
    { class: "filtros", attrs: { role: "group", "aria-label": TEXTS.filterGroup } },
    filterButtons,
  );

  const list = el("div", { class: "lista" });

  const previous = el("button", {
    class: "botao",
    text: TEXTS.previous,
    attrs: { type: "button" },
    on: { click: () => goTo(state.offset - PAGE_SIZE) },
  });
  const next = el("button", {
    class: "botao",
    text: TEXTS.next,
    attrs: { type: "button" },
    on: { click: () => goTo(state.offset + PAGE_SIZE) },
  });
  const summary = el("p", { class: "paginacao__resumo secundario" });
  const pagination = el(
    "nav",
    { class: "paginacao", attrs: { "aria-label": TEXTS.pagination } },
    previous,
    summary,
    next,
  );

  root.replaceChildren(
    el("section", { class: "tarefas" }, heading, form, notice, filterBar, list, pagination),
  );

  function showNotice(text, kind = "ok") {
    notice.textContent = text;
    notice.className = `nota nota--${kind}`;
    notice.removeAttribute("hidden");
    announce(text);
  }

  function clearNotice() {
    notice.textContent = "";
    notice.setAttribute("hidden", "");
  }

  function modeOf(task) {
    if (state.editing === task.id) return "edit";
    if (state.confirming === task.id) return "confirm";
    return "view";
  }

  function findCard(id) {
    return [...list.children].find((child) => child.dataset && child.dataset.id === id) ?? null;
  }

  /** Foca um elemento do cartão (`data-foco`); sem ele, o título da tela. */
  function focusCard(id, target) {
    const card = findCard(id);
    const node = card ? card.querySelector(`[data-foco="${target}"]`) : null;
    (node ?? heading).focus();
  }

  function renderFilters() {
    FILTERS.forEach((filter, index) => {
      const pressed = filter.value === state.filter;
      filterButtons[index].setAttribute("aria-pressed", String(pressed));
    });
  }

  function renderList() {
    list.setAttribute("aria-busy", String(state.view === "loading"));

    if (state.view === "loading") {
      list.replaceChildren(el("p", { class: "estado secundario", text: TEXTS.loading }));
      return null;
    }

    if (state.view === "error") {
      const retry = el("button", {
        class: "botao",
        text: TEXTS.retry,
        attrs: { type: "button" },
        on: { click: () => load() },
      });
      const alert = errorAlert(state.error, { retry });
      list.replaceChildren(alert);
      return alert;
    }

    const items = state.data.itens;
    if (items.length === 0) {
      list.replaceChildren(
        el(
          "div",
          { class: "estado" },
          el("p", { class: "estado__titulo", text: TEXTS.empty }),
          el("p", { class: "secundario", text: TEXTS.emptyHint }),
        ),
      );
      return null;
    }
    list.replaceChildren(...items.map((task) => taskCard(task, modeOf(task), actions)));
    return null;
  }

  function renderPagination() {
    // Durante o carregamento mantém o estado anterior: desabilitar o botão
    // apertado faria o foco se perder.
    if (state.view === "loading") return;
    if (state.view !== "ready") {
      summary.textContent = "";
      previous.disabled = true;
      next.disabled = true;
      return;
    }
    const { total, limite, deslocamento } = state.data;
    const pages = Math.max(1, Math.ceil(total / limite));
    const page = Math.floor(deslocamento / limite) + 1;
    summary.textContent = pageSummary(page, pages, total);
    previous.disabled = deslocamento <= 0;
    next.disabled = deslocamento + limite >= total;
  }

  function render() {
    renderFilters();
    const alert = renderList();
    renderPagination();
    return alert;
  }

  async function load() {
    const ticket = ++state.ticket;
    state.view = "loading";
    render();

    try {
      const data = await listTasks({
        status: state.filter,
        limit: PAGE_SIZE,
        offset: state.offset,
      });
      if (ticket !== state.ticket) return;

      // Página vazia depois de excluir ou mudar de filtro: vai para a última
      // página que existe.
      if (data.itens.length === 0 && data.total > 0 && state.offset > 0) {
        const target = lastPageOffset(data.total);
        if (target < state.offset) {
          state.offset = target;
          await load();
          return;
        }
      }

      state.data = data;
      state.view = "ready";
      render();
    } catch (error) {
      if (ticket !== state.ticket) return;
      state.error = error;
      state.view = "error";
      render().focus();
    }
  }

  /** Mantém o foco útil quando o botão que o tinha ficou desabilitado. */
  function recoverFocus() {
    const active = document.activeElement;
    if (active === document.body || (active instanceof HTMLButtonElement && active.disabled)) {
      heading.focus();
    }
  }

  function resetInteraction() {
    state.editing = null;
    state.confirming = null;
    clearNotice();
  }

  async function changeFilter(value) {
    if (value === state.filter) return;
    state.filter = value;
    state.offset = 0;
    resetInteraction();
    await load();
    recoverFocus();
  }

  async function goTo(offset) {
    state.offset = Math.max(0, offset);
    resetInteraction();
    await load();
    recoverFocus();
  }

  /** Depois de criar: volta à primeira página, mantendo o filtro. */
  async function handleCreated(task) {
    resetInteraction();
    state.offset = 0;
    const hidden = state.filter !== null && task.status !== state.filter;
    showNotice(hidden ? NOTICES.createdHidden : NOTICES.created);
    await load();
  }

  /** Depois de PATCH: recarrega a lista e devolve o foco ao cartão. */
  async function handleUpdated(id, updated) {
    state.editing = null;
    state.confirming = null;
    const hidden = state.filter !== null && updated.status !== state.filter;
    showNotice(hidden ? NOTICES.updatedHidden : NOTICES.updated);
    await load();
    focusCard(id, "cartao");
  }

  // Ações dos cartões. Abrir uma edição fecha a anterior sem salvar.
  const actions = {
    startEdit(task) {
      clearNotice();
      state.editing = task.id;
      state.confirming = null;
      renderList();
      focusCard(task.id, "titulo");
    },
    cancelEdit(task) {
      state.editing = null;
      renderList();
      focusCard(task.id, "editar");
    },
    async save(task, patch) {
      clearNotice();
      await handleUpdated(task.id, await updateTask(task.id, patch));
    },
    async changeStatus(task, status) {
      clearNotice();
      await handleUpdated(task.id, await updateTask(task.id, { status }));
    },
    askDelete(task) {
      clearNotice();
      state.confirming = task.id;
      state.editing = null;
      renderList();
      focusCard(task.id, "cancelar");
    },
    cancelDelete(task) {
      state.confirming = null;
      renderList();
      focusCard(task.id, "excluir");
    },
    async confirmDelete(task) {
      clearNotice();
      await deleteTask(task.id);
      resetInteraction();
      showNotice(NOTICES.deleted);
      await load();
      heading.focus();
    },
    /** A tarefa não existe mais (404): avisa e atualiza a lista. */
    async gone() {
      resetInteraction();
      showNotice(TEXTS.notFoundError, "erro");
      await load();
      heading.focus();
    },
  };

  return load();
}
