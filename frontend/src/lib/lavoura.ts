// Cliente das rotas de lavoura da spec 002: desenho no mapa e arquivo (KML, KMZ, GeoJSON, Shapefile .zip).
// A confirmação continua em apiCar.confirmar (/api/lavoura/confirmar), a mesma do CAR.

import { API_URL, FalhaApi, type CandidatoLavoura } from "./api";

export interface RespostaLavoura {
  candidato: CandidatoLavoura;
  arquivo?: { formato: string; nome_formato: string; arquivo: string; bytes: number };
  avisos: { codigo: string; mensagem: string }[];
}

export type PoligonoGeoJSON = { type: "Polygon"; coordinates: number[][][] };

async function postar<T>(caminho: string, init: RequestInit): Promise<T> {
  let resp: Response;
  try {
    resp = await fetch(`${API_URL}${caminho}`, { method: "POST", ...init });
  } catch {
    throw new FalhaApi({ codigo: "sem_conexao", mensagem: "Não foi possível falar com o servidor do TELLUS. Ele está rodando?" });
  }
  let corpo: any = null;
  try {
    corpo = await resp.json();
  } catch {
    /* corpo vazio ou não-JSON */
  }
  if (!resp.ok) throw new FalhaApi(corpo?.erro ?? { codigo: "erro", mensagem: `Erro inesperado (HTTP ${resp.status}).` });
  return corpo as T;
}

export const apiLavoura = {
  desenho: (geometria: PoligonoGeoJSON) =>
    postar<RespostaLavoura>("/api/lavoura/desenho", {
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ geometria }),
    }),
  arquivo: (arquivo: File) => {
    const dados = new FormData();
    dados.append("arquivo", arquivo);
    return postar<RespostaLavoura>("/api/lavoura/arquivo", { body: dados });
  },
};

/** Vértices [lat, lng] do Leaflet → Polygon GeoJSON fechado (lon, lat), sem simplificar. */
export function poligonoDosVertices(vertices: { lat: number; lng: number }[]): PoligonoGeoJSON {
  const anel = vertices.map((v) => [Number(v.lng.toFixed(6)), Number(v.lat.toFixed(6))]);
  if (anel.length) anel.push([...anel[0]]);
  return { type: "Polygon", coordinates: [anel] };
}
