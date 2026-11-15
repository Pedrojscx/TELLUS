// Idioma ativo e tradução da página no navegador (spec 014, FR-001 a FR-003).
// Ordem: ?lang=en|pt na URL > escolha guardada > português. Sem JavaScript, tudo fica em português.
// Em inglês, um observador traduz também o que as telas montam depois (etapas, resultado, erros).

import { traduzirNo, type Idioma } from "./traduzir";

const CHAVE = "tellus.idioma";
const ATRIBUTOS = ["placeholder", "aria-label", "title", "alt"] as const;
const ESCRITO = new WeakMap<Node, string>(); // o que o tradutor já escreveu: nunca traduz de novo
const PULAR = new Set(["SCRIPT", "STYLE", "TEXTAREA", "CODE", "PRE"]);

export function idiomaAtual(): Idioma {
  try {
    const url = new URLSearchParams(location.search).get("lang");
    if (url === "en" || url === "pt") {
      localStorage.setItem(CHAVE, url === "en" ? "en" : "pt-BR");
      return url === "en" ? "en" : "pt-BR";
    }
    return localStorage.getItem(CHAVE) === "en" ? "en" : "pt-BR";
  } catch {
    return "pt-BR";
  }
}

export function definirIdioma(i: Idioma): void {
  try { localStorage.setItem(CHAVE, i); } catch { /* sem armazenamento: vale só pela URL */ }
  const u = new URL(location.href);
  u.searchParams.delete("lang");
  location.replace(u.toString()); // recarrega: lavoura, entradas e premissas já ficam no navegador
}

function traduzirElemento(el: Element): void {
  for (const a of ATRIBUTOS) {
    const v = el.getAttribute(a);
    if (!v || el.getAttribute(`data-en-${a}`) === v) continue;
    const t = traduzirNo(v);
    el.setAttribute(`data-en-${a}`, t);
    if (t !== v) el.setAttribute(a, t);
  }
}

function traduzirArvore(raiz: Node): void {
  if (raiz.nodeType === Node.TEXT_NODE) {
    const p = raiz.parentElement;
    if (p && !PULAR.has(p.tagName) && !p.closest("[data-sem-traducao]")) {
      if (ESCRITO.get(raiz) === raiz.nodeValue) return;
      const t = traduzirNo(raiz.nodeValue ?? "");
      ESCRITO.set(raiz, t);
      if (t !== raiz.nodeValue) raiz.nodeValue = t;
    }
    return;
  }
  if (raiz.nodeType !== Node.ELEMENT_NODE) return;
  const el = raiz as Element;
  if (PULAR.has(el.tagName) || el.closest("[data-sem-traducao]")) return;
  traduzirElemento(el);
  const w = document.createTreeWalker(el, NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT);
  for (let n = w.nextNode(); n; n = w.nextNode()) {
    if (n.nodeType === Node.ELEMENT_NODE) traduzirElemento(n as Element);
    else traduzirArvore(n);
  }
}

export function iniciarIdioma(): void {
  const i = idiomaAtual();
  document.documentElement.lang = i;
  document.querySelectorAll<HTMLButtonElement>("[data-idioma]").forEach((b) => {
    const ativo = b.dataset.idioma === i;
    b.setAttribute("aria-pressed", String(ativo));
    b.addEventListener("click", () => { if (!ativo) definirIdioma(b.dataset.idioma as Idioma); });
  });
  if (i !== "en") return;
  document.title = traduzirNo(document.title);
  traduzirArvore(document.body);
  new MutationObserver((ms) => {
    for (const m of ms) {
      if (m.type === "characterData") traduzirArvore(m.target);
      else if (m.type === "attributes") traduzirElemento(m.target as Element);
      else m.addedNodes.forEach(traduzirArvore);
    }
  }).observe(document.body, { subtree: true, childList: true, characterData: true, attributes: true, attributeFilter: [...ATRIBUTOS] });
}
