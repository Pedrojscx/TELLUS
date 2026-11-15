import { describe, expect, it } from "vitest";
import { areaDoPedido, montarPedido, usaTalhao } from "./contrato";
import type { EntradasComparacao } from "./contrato-provisorio";
import type { LavouraConfirmada } from "./lavoura";

const entradas: EntradasComparacao = {
  area: { id_geometria: "x", area_ha: 142.89, municipio: "Rio Verde", uf: "GO", confirmada: true, real: true },
  colheita_soja: "2026-01-20", solo: { modo: "textura", textura: "media" }, grupo: "nao_sei",
  metodologia: "comparar_alternativas", cultura: null,
};
const geometria = { type: "Polygon", coordinates: [[[-50.986, -17.758], [-50.974, -17.757], [-50.973, -17.767], [-50.985, -17.768], [-50.986, -17.758]]] };
const talhao: LavouraConfirmada = {
  tipo: "geometria", lat: -17.7625, lon: -50.9795, codigo_ibge: "5218805", municipio: "Rio Verde", uf: "GO",
  area_ha: 142.89, geometria, id_geometria: "abc123", origem: "desenho", confirmada_em: "2026-11-15",
};
const ponto: LavouraConfirmada = {
  tipo: "ponto", lat: -17.785278, lon: -50.965, codigo_ibge: "5218805", municipio: "Rio Verde", uf: "GO",
  area_ha: null, confirmada_em: "2026-11-15",
};

describe("área do pedido ao contrato", () => {
  it("lavoura confirmada por desenho manda a geometria, não o ponto", () => {
    const pedido = montarPedido(entradas, talhao, []);
    expect(pedido.area).toEqual({ tipo: "geometria", geometria, id_geometria: "abc123", origem: "desenho", confirmada: true });
    expect(usaTalhao(talhao)).toBe(true);
  });

  it("lavoura confirmada por arquivo ou CAR também manda a geometria, com a origem dela", () => {
    const car = { ...talhao, origem: "car" as const, id_geometria: "car-1" };
    expect(areaDoPedido(car)).toEqual({ tipo: "geometria", geometria, id_geometria: "car-1", origem: "car", confirmada: true });
  });

  it("modo ponto (localizado por município ou coordenadas) manda o ponto", () => {
    const pedido = montarPedido(entradas, ponto, []);
    expect(pedido.area).toEqual({ tipo: "ponto", lat: -17.785278, lon: -50.965, confirmada: true, codigo_ibge: "5218805" });
    expect(usaTalhao(ponto)).toBe(false);
  });

  it("geometria sem id não conta como talhão: cai no ponto", () => {
    const sem = { ...talhao, id_geometria: undefined };
    expect(usaTalhao(sem)).toBe(false);
    expect((montarPedido(entradas, sem, []).area as { tipo: string }).tipo).toBe("ponto");
  });
});
