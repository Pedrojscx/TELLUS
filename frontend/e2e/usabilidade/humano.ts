// Ritmo de uma pessoa: rola até o elemento, passa o mouse, espera um instante e clica; digita letra por letra;
// para para ler. Sem atalhos: nada é preenchido por código no navegador.
import type { Locator, Page } from "@playwright/test";

export class Humano {
  constructor(private page: Page, private toque = false) {}

  async ler(ms = 900): Promise<void> {
    await this.page.waitForTimeout(ms);
  }

  async clicar(alvo: Locator): Promise<void> {
    await alvo.scrollIntoViewIfNeeded();
    if (this.toque) { await this.ler(350); await alvo.tap(); return; }
    await alvo.hover();
    await this.ler(350);
    await alvo.click();
  }

  async digitar(campo: Locator, texto: string): Promise<void> {
    await this.clicar(campo);
    await campo.pressSequentially(texto, { delay: 85 });
    await this.ler(300);
  }

  /** Campo de data: limpa e digita a data (formato do campo nativo preenchido como uma pessoa faria). */
  async data(campo: Locator, iso: string): Promise<void> {
    await campo.scrollIntoViewIfNeeded();
    await campo.fill(iso); // o seletor nativo de data não aceita digitação letra a letra de forma estável
    await this.ler(400);
  }

  async rolarAte(alvo: Locator): Promise<void> {
    await alvo.scrollIntoViewIfNeeded();
    await this.ler(700);
  }
}
