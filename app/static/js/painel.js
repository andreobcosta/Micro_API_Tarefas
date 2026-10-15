// Tela "Painel" (#/painel): indicadores, distribuição por status, progresso de
// conclusão e últimas tarefas. Tudo calculado no navegador a partir de
// GET /tarefas (4 chamadas em paralelo); nenhum endpoint novo.

import { errorAlert } from "./alerta.js";
import { listTasks } from "./api.js";
import { announce, el } from "./dom.js";
import { PANEL, STATUS, UNKNOWN_STATUS } from "./messages.js";

const LATEST_COUNT = 5;
const TIME_ZONE = "America/Sao_Paulo";

// Ordem de exibição e classe da barra de cada status.
const STATUS_ORDER = [
  { value: "pendente", bar: "barra--pendente" },
  { value: "em_andamento", bar: "barra--em-andamento" },
  { value: "concluida", bar: "barra--concluida" },
];

const dateFormat = new Intl.DateTimeFormat("pt-BR", {
  timeZone: TIME_ZONE,
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
  hourCycle: "h23",
});

/**
 * Formata um instante ISO como "dd/mm/aaaa hh:mm" em America/Sao_Paulo.
 *
 * As partes são montadas à mão para não depender da vírgula que o Intl
 * insere entre data e hora. Valor ausente ou inválido vira "—".
 *
 * @param {string|null|undefined} iso
 * @returns {string}
 */
export function formatDate(iso) {
  const date = new Date(iso);
  if (!iso || Number.isNaN(date.getTime())) return PANEL.noDate;
  const parts = {};
  for (const part of dateFormat.formatToParts(date)) parts[part.type] = part.value;
  return `${parts.day}/${parts.month}/${parts.year} ${parts.hour}:${parts.minute}`;
}

/**
 * Calcula os números do painel a partir dos totais por status.
 *
 * O total geral é a SOMA dos três totais, de modo que os indicadores são
 * coerentes entre si. Percentuais são inteiros arredondados (a soma pode dar
 * 99% ou 101%); com total 0 todos valem 0.
 *
 * @param {{pendente: number, em_andamento: number, concluida: number}} totals
 * @returns {{total: number, rows: {status: string, count: number, percent: number}[], completedPercent: number}}
 */
export function buildSummary(totals) {
  const total = STATUS_ORDER.reduce((sum, { value }) => sum + totals[value], 0);
  const percentOf = (count) => (total === 0 ? 0 : Math.round((count * 100) / total));
  return {
    total,
    rows: STATUS_ORDER.map(({ value }) => ({
      status: value,
      count: totals[value],
      percent: percentOf(totals[value]),
    })),
    completedPercent: percentOf(totals.concluida),
  };
}

/** Busca os dados do painel: 3 totais por status e as últimas tarefas. */
export async function fetchDashboard() {
  const [pending, inProgress, done, latest] = await Promise.all([
    listTasks({ status: "pendente", limit: 1, offset: 0 }),
    listTasks({ status: "em_andamento", limit: 1, offset: 0 }),
    listTasks({ status: "concluida", limit: 1, offset: 0 }),
    listTasks({ status: null, limit: LATEST_COUNT, offset: 0 }),
  ]);
  return {
    totals: {
      pendente: pending.total,
      em_andamento: inProgress.total,
      concluida: done.total,
    },
    latest: latest.itens,
  };
}

function statusInfo(status) {
  return Object.hasOwn(STATUS, status) ? STATUS[status] : null;
}

function statusBadge(status) {
  const known = statusInfo(status);
  return el("span", {
    class: `selo ${(known ?? UNKNOWN_STATUS).badge}`,
    text: known ? known.label : String(status),
  });
}

/** Trilho com preenchimento; a largura vai por CSSOM (compatível com a CSP). */
function bar(percent, fillClass, trackAttrs = {}) {
  const fill = el("div", { class: `barra__preenchimento ${fillClass}` });
  fill.style.width = `${percent}%`;
  return el("div", { class: "barra", attrs: trackAttrs }, fill);
}

function indicators(summary) {
  const cards = [
    { label: PANEL.total, value: summary.total },
    ...summary.rows.map((row) => ({ label: STATUS[row.status].label, value: row.count })),
  ];
  return el(
    "ul",
    { class: "indicadores" },
    cards.map((card) =>
      el(
        "li",
        { class: "cartao indicador" },
        el("span", { class: "indicador__valor", text: String(card.value) }),
        el("span", { class: "indicador__rotulo secundario", text: card.label }),
      ),
    ),
  );
}

function distribution(summary) {
  const rows = summary.rows.map((row) => {
    const order = STATUS_ORDER.find((item) => item.value === row.status);
    return el(
      "li",
      { class: "distribuicao__linha" },
      el("span", { class: "distribuicao__rotulo", text: STATUS[row.status].label }),
      bar(row.percent, order.bar, { "aria-hidden": "true" }),
      el("span", {
        class: "distribuicao__valor",
        text: `${row.count} · ${row.percent}%`,
      }),
    );
  });
  return el(
    "section",
    { class: "cartao bloco", attrs: { "aria-labelledby": "painel-distribuicao" } },
    el("h3", { class: "bloco__titulo", text: PANEL.distribution, attrs: { id: "painel-distribuicao" } }),
    el("ul", { class: "distribuicao" }, rows),
  );
}

function progress(summary) {
  const empty = summary.total === 0;
  const doneCount = summary.rows.find((row) => row.status === "concluida").count;
  const text = empty
    ? PANEL.noTasksYet
    : PANEL.progressText(doneCount, summary.total, summary.completedPercent);
  const track = bar(summary.completedPercent, "barra--concluida", {
    role: "progressbar",
    "aria-label": PANEL.progress,
    "aria-valuemin": "0",
    "aria-valuemax": "100",
    "aria-valuenow": String(summary.completedPercent),
    "aria-valuetext": text,
  });
  return el(
    "section",
    { class: "cartao bloco", attrs: { "aria-labelledby": "painel-progresso" } },
    el("h3", { class: "bloco__titulo", text: PANEL.progress, attrs: { id: "painel-progresso" } }),
    track,
    el("p", { class: "progresso__texto", text }),
  );
}

function latestTable(tasks) {
  const title = el("h3", { class: "bloco__titulo", text: PANEL.latest, attrs: { id: "painel-ultimas" } });
  if (tasks.length === 0) {
    return el(
      "section",
      { class: "cartao bloco", attrs: { "aria-labelledby": "painel-ultimas" } },
      title,
      el("p", { class: "secundario", text: PANEL.noTasks }),
    );
  }
  const head = el(
    "tr",
    {},
    PANEL.columns.map((name) => el("th", { text: name, attrs: { scope: "col" } })),
  );
  const rows = tasks.map((task) =>
    el(
      "tr",
      {},
      el("th", { text: task.titulo, attrs: { scope: "row" }, class: "tabela__titulo" }),
      el("td", {}, statusBadge(task.status)),
      el("td", { text: formatDate(task.criado_em) }),
      el("td", { text: formatDate(task.atualizado_em) }),
    ),
  );
  return el(
    "section",
    { class: "cartao bloco", attrs: { "aria-labelledby": "painel-ultimas" } },
    title,
    el(
      "div",
      { class: "tabela-rolagem", attrs: { tabindex: "0", role: "region", "aria-labelledby": "painel-ultimas" } },
      el(
        "table",
        { class: "tabela" },
        el("thead", {}, head),
        el("tbody", {}, rows),
      ),
    ),
  );
}

/**
 * Monta o painel dentro de `root`.
 *
 * "Atualizar" refaz as 4 chamadas mantendo os números anteriores na tela até
 * a resposta chegar.
 */
export function mountDashboard(root) {
  const state = { ticket: 0, data: null };

  const heading = el("h2", {
    class: "tarefas__titulo",
    text: PANEL.title,
    attrs: { tabindex: "-1" },
  });
  const refresh = el("button", {
    class: "botao",
    text: PANEL.refresh,
    attrs: { type: "button" },
    on: { click: () => load({ announceDone: true }) },
  });
  const errorBox = el("div", { class: "painel__erro" });
  const content = el("div", { class: "painel__conteudo" });

  root.replaceChildren(
    el(
      "section",
      { class: "painel" },
      el("div", { class: "painel__topo" }, heading, refresh),
      errorBox,
      content,
    ),
  );

  function renderData() {
    const summary = buildSummary(state.data.totals);
    content.replaceChildren(
      indicators(summary),
      distribution(summary),
      progress(summary),
      latestTable(state.data.latest),
      el("p", { class: "nota-fixa secundario", text: PANEL.note }),
    );
  }

  async function load({ announceDone = false } = {}) {
    const ticket = ++state.ticket;
    refresh.disabled = true;
    errorBox.replaceChildren();
    content.setAttribute("aria-busy", "true");
    if (state.data === null) {
      content.replaceChildren(el("p", { class: "estado secundario", text: PANEL.loading }));
    }

    try {
      const data = await fetchDashboard();
      if (ticket !== state.ticket) return;
      state.data = data;
      renderData();
      if (announceDone) announce(PANEL.updated);
    } catch (error) {
      if (ticket !== state.ticket) return;
      const retry = el("button", {
        class: "botao",
        text: PANEL.retry,
        attrs: { type: "button" },
        on: { click: () => load() },
      });
      const alert = errorAlert(error, { retry });
      errorBox.replaceChildren(alert);
      if (state.data === null) content.replaceChildren();
      alert.focus();
    } finally {
      if (ticket === state.ticket) {
        refresh.disabled = false;
        content.setAttribute("aria-busy", "false");
      }
    }
  }

  return load();
}
