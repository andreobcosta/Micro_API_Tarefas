// Navegação por hash (#/tarefas e #/painel), sem recarregar a página.

import { DEFAULT_ROUTE, ROUTES } from "./messages.js";
import { mountDashboard } from "./painel.js";
import { mountTasks } from "./tarefas.js";

const NAV_LINKS = document.querySelectorAll("a[data-rota]");
const MAIN = document.getElementById("conteudo");

// Tela de cada rota (as chaves coincidem com as de ROUTES em messages.js).
const VIEWS = {
  "#/tarefas": mountTasks,
  "#/painel": mountDashboard,
};

/** Rota atual; hash desconhecido ou vazio cai na rota padrão. */
export function currentRoute() {
  return Object.hasOwn(ROUTES, window.location.hash)
    ? window.location.hash
    : DEFAULT_ROUTE;
}

function markCurrentLink(route) {
  for (const link of NAV_LINKS) {
    if (link.dataset.rota === route) {
      link.setAttribute("aria-current", "page");
    } else {
      link.removeAttribute("aria-current");
    }
  }
}

function render(route) {
  const config = ROUTES[route];
  MAIN.classList.toggle("largo", config.wide);
  document.title = `${config.title} · Micro-API de Tarefas`;
  VIEWS[route](MAIN);
}

function navigate() {
  const route = currentRoute();
  markCurrentLink(route);
  render(route);
}

/** Liga o roteador ao evento de mudança de hash e desenha a rota inicial. */
export function startRouter() {
  window.addEventListener("hashchange", navigate);
  navigate();
}
