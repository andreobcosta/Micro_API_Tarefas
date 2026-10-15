// Criação segura de elementos.
//
// Único ponto da interface que cria nós do DOM. Dados vindos da API entram
// SOMENTE como texto (textContent / nós de texto); nada é interpretado como HTML.

/**
 * Cria um elemento.
 *
 * @param {string} tag Nome da tag.
 * @param {object} [options]
 * @param {string} [options.class] Valor do atributo class.
 * @param {string} [options.text] Texto do elemento (via textContent).
 * @param {Record<string, string|boolean|null|undefined>} [options.attrs]
 *   Atributos; `true` define um atributo booleano, `false`/`null` o omite.
 * @param {Record<string, string>} [options.dataset] Atributos data-*.
 * @param {Record<string, EventListener>} [options.on] Ouvintes de evento.
 * @param {...(Node|string|null|false|undefined|Array)} children Filhos; textos
 *   viram nós de texto.
 * @returns {HTMLElement}
 */
export function el(tag, options = {}, ...children) {
  const node = document.createElement(tag);
  const { class: className, text, attrs, dataset, on } = options;

  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;

  for (const [name, value] of Object.entries(attrs ?? {})) {
    if (value === false || value === null || value === undefined) continue;
    node.setAttribute(name, value === true ? "" : String(value));
  }
  for (const [name, value] of Object.entries(dataset ?? {})) {
    node.dataset[name] = String(value);
  }
  for (const [type, listener] of Object.entries(on ?? {})) {
    node.addEventListener(type, listener);
  }

  const valid = children
    .flat()
    .filter((child) => child !== null && child !== undefined && child !== false);
  node.append(...valid);
  return node;
}

/**
 * Campo de formulário com rótulo associado (`label for` + `id` do controle).
 *
 * @param {string} labelText Texto do rótulo.
 * @param {HTMLElement} control Controle que já tem o atributo `id`.
 * @returns {HTMLElement}
 */
export function labeledField(labelText, control) {
  return el(
    "div",
    { class: "campo" },
    el("label", { class: "campo__rotulo", text: labelText, attrs: { for: control.id } }),
    control,
  );
}
