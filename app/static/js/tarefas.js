// Tela "Tarefas" (#/tarefas): lista, filtro por status e paginação.

import { describeError, listTasks } from "./api.js";
import { el } from "./dom.js";
import {
  FILTERS,
  STATUS,
  TEXTS,
  UNKNOWN_STATUS,
  pageSummary,
} from "./messages.js";

const PAGE_SIZE = 10;

/** Deslocamento da última página que existe para `total` itens. */
function lastPageOffset(total) {
  return (Math.ceil(total / PAGE_SIZE) - 1) * PAGE_SIZE;
}

function statusBadge(status) {
  const known = Object.hasOwn(STATUS, status) ? STATUS[status] : null;
  return el("span", {
    class: `selo ${(known ?? UNKNOWN_STATUS).badge}`,
    text: known ? known.label : String(status),
  });
}

function taskCard(task) {
  const finished = task.status === "concluida";
  const description =
    task.descricao === null
      ? el("p", { class: "cartao__descricao secundario", text: TEXTS.noDescription })
      : el("p", { class: "cartao__descricao", text: task.descricao });

  return el(
    "article",
    { class: "cartao", dataset: { id: task.id } },
    el(
      "div",
      { class: "cartao__cabecalho" },
      el("h3", {
        class: finished ? "cartao__titulo riscado" : "cartao__titulo",
        text: task.titulo,
      }),
      statusBadge(task.status),
    ),
    description,
  );
}

/**
 * Monta a tela de tarefas dentro de `root`.
 *
 * O estado vive nesta chamada: cada visita à rota começa do zero (filtro
 * "Todas", primeira página).
 */
export function mountTasks(root) {
  const state = { filter: null, offset: 0, ticket: 0, view: "loading", data: null, error: null };

  const heading = el("h2", {
    class: "tarefas__titulo",
    text: TEXTS.listTitle,
    attrs: { tabindex: "-1" },
  });

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

  root.replaceChildren(el("section", { class: "tarefas" }, heading, filterBar, list, pagination));

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
      const { message, details } = describeError(state.error);
      const alert = el(
        "div",
        { class: "alerta", attrs: { role: "alert", tabindex: "-1" } },
        el("p", { class: "alerta__mensagem", text: message }),
        details.length > 0
          ? el(
              "ul",
              { class: "alerta__detalhes" },
              details.map((detail) => el("li", { text: detail })),
            )
          : null,
        el("button", {
          class: "botao",
          text: TEXTS.retry,
          attrs: { type: "button" },
          on: { click: () => load() },
        }),
      );
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
    list.replaceChildren(...items.map(taskCard));
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

  async function changeFilter(value) {
    if (value === state.filter) return;
    state.filter = value;
    state.offset = 0;
    await load();
    recoverFocus();
  }

  async function goTo(offset) {
    state.offset = Math.max(0, offset);
    await load();
    recoverFocus();
  }

  return load();
}
