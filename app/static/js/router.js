// Navegação por hash (#/tarefas e #/painel), sem recarregar a página.

import { DEFAULT_ROUTE, ROUTES } from "./messages.js";

const NAV_LINKS = document.querySelectorAll("a[data-rota]");
const MAIN = document.getElementById("conteudo");

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
  const { title, description, wide } = ROUTES[route];
  const heading = document.createElement("h2");
  heading.textContent = title;
  const text = document.createElement("p");
  text.textContent = description;
  MAIN.replaceChildren(heading, text);
  MAIN.classList.toggle("largo", wide);
  document.title = `${title} · Micro-API de Tarefas`;
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
