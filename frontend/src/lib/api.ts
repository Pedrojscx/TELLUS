// Cliente do contrato da spec 001 (specs/001-localizacao/contracts/localizacao.openapi.yaml).

// Sem PUBLIC_API_URL, usa o mesmo computador que serviu a página (porta 8000): funciona em localhost e no
// celular aberto pelo IP do computador na rede local (D-010).
export const API_URL: string = import.meta.env.PUBLIC_API_URL ??
  (typeof location !== "undefined" && location.hostname ? `${location.protocol}//${location.hostname}:8000` : "http://localhost:8000");

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

// ---- Spec 001: CAR, upload SICAR e confirmação da lavoura ----

export interface CandidatoLavoura {
  id_geometria: string;
  geometria: { type: "MultiPolygon"; coordinates: number[][][][] };
  origem: "car" | "upload_sicar" | "desenho" | "arquivo";
  area_ha: number;
  municipios: { codigo_ibge: string; nome: string; uf: string; fracao: number }[];
  centroide: { lat: number; lon: number };
  estado: "aguardando_confirmacao" | "confirmada";
  proveniencia: Record<string, any>;
}

export interface ConsultaCar {
  codigo_informado: string;
  codigo: string | null;
  estado: "encontrado" | "geometria_invalida" | "sem_geometria" | "inexistente" | "codigo_invalido" | "fonte_indisponivel";
  mensagem: string;
  consultado_em: string | null;
  proveniencia: Record<string, any> | null;
  qualidade: Record<string, any> | null;
  candidato: CandidatoLavoura | null;
  alternativa: { upload_sicar: boolean; mensagem: string } | null;
  avisos: { codigo: string; mensagem: string }[];
  erros_geometria: string[];
}

export interface Lavoura extends CandidatoLavoura {
  confirmada_em: string;
  localizacao: ResultadoLocalizacao;
}

async function enviar<T>(caminho: string, init: RequestInit): Promise<T> {
  let resp: Response;
  try {
    resp = await fetch(`${API_URL}${caminho}`, init);
  } catch {
    throw new FalhaApi({ codigo: "sem_conexao", mensagem: "Não foi possível falar com o servidor do TELLUS. Ele está rodando?" });
  }
  const corpo = await resp.json();
  if (!resp.ok) throw new FalhaApi(corpo.erro ?? { codigo: "erro", mensagem: "Erro inesperado." });
  return corpo as T;
}

export const apiCar = {
  consultar: (codigo: string) => obter<ConsultaCar>(`/api/car/${encodeURIComponent(codigo.trim())}`),
  upload: (arquivo: File) => {
    const dados = new FormData();
    dados.append("arquivo", arquivo);
    return enviar<{ candidato: CandidatoLavoura; avisos: { codigo: string; mensagem: string }[] }>("/api/car/upload", {
      method: "POST",
      body: dados,
    });
  },
  confirmar: (c: CandidatoLavoura) =>
    enviar<Lavoura>("/api/lavoura/confirmar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ geometria: c.geometria, id_geometria: c.id_geometria, origem: c.origem, proveniencia: c.proveniencia }),
    }),
};
