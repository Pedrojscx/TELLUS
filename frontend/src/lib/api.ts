// Cliente do contrato da spec 001 (specs/001-localizacao/contracts/localizacao.openapi.yaml).

export const API_URL: string = import.meta.env.PUBLIC_API_URL ?? "http://localhost:8000";

export interface MunicipioResumo {
  codigo_ibge: string;
  nome: string;
  uf: string;
}

export interface Procedencia {
  fonte: string;
  url: string;
  obtido_em: string;
  status: "fonte" | "hipotese";
}

export interface Aviso {
  codigo: string;
  mensagem: string;
  referencia: string | null;
}

export type TipoReferencia =
  | "celula_power"
  | "celula_imerg"
  | "estacao_inmet"
  | "praca_conab"
  | "municipio_zarc";

export interface Referencia {
  tipo: TipoReferencia;
  identificador: string;
  nome: string | null;
  lat: number;
  lon: number;
  distancia_km: number;
  detalhes: Record<string, any>;
  procedencia: Procedencia;
  avisos: Aviso[];
}

export interface ResultadoLocalizacao {
  local: {
    lat: number;
    lon: number;
    meio: "busca" | "coordenadas" | "mapa" | "padrao";
    municipio: MunicipioResumo;
    municipio_alternativo: MunicipioResumo | null;
  };
  referencias: Referencia[];
  avisos: Aviso[];
  versao_referencias: string;
  eh_demo: boolean;
}

export interface ErroApi {
  codigo: string;
  mensagem: string;
  campo?: string | null;
}

export class FalhaApi extends Error {
  constructor(public erro: ErroApi) {
    super(erro.mensagem);
  }
}

async function obter<T>(caminho: string): Promise<T> {
  let resp: Response;
  try {
    resp = await fetch(`${API_URL}${caminho}`);
  } catch {
    throw new FalhaApi({
      codigo: "sem_conexao",
      mensagem: "Não foi possível falar com o servidor do TELLUS. Ele está rodando?",
    });
  }
  const corpo = await resp.json();
  if (!resp.ok) throw new FalhaApi(corpo.erro ?? { codigo: "erro", mensagem: "Erro inesperado." });
  return corpo as T;
}

export const api = {
  buscarMunicipios: (texto: string, limite = 8) =>
    obter<{ resultados: MunicipioResumo[] }>(
      `/api/municipios?busca=${encodeURIComponent(texto)}&limite=${limite}`,
    ).then((r) => r.resultados),
  padrao: () => obter<ResultadoLocalizacao>("/api/localizacao/padrao"),
  porMunicipio: (codigo: string) =>
    obter<ResultadoLocalizacao>(`/api/localizacao/municipio/${encodeURIComponent(codigo)}`),
  porPonto: (lat: string | number, lon: string | number, meio: "coordenadas" | "mapa") =>
    obter<ResultadoLocalizacao>(
      `/api/localizacao?lat=${encodeURIComponent(String(lat))}&lon=${encodeURIComponent(String(lon))}&meio=${meio}`,
    ),
};
