"""Spec 002 (#20, #21, #22, #24, #30, #31, #32): seis modos de entrada, erros nomeados e limites da D-009."""

import copy
import math

import pytest
from fastapi.testclient import TestClient

from tellus.api.app import app
from tellus.car import servico as car
from tellus.contrato import regras as contrato
from tellus.lavoura import servico as lavoura

from .conftest import ANEL, GERADORES, geojson, geom_car, kml, kmz, zip_shp

FORMATOS = sorted(GERADORES)


def _erro(fn, *a) -> car.ErroCar:
    with pytest.raises(car.ErroCar) as e:
        fn(*a)
    return e.value


# ---------------------------------------------------------------- #22: cada formato válido → mesmo resumo


@pytest.mark.parametrize("nome", FORMATOS)
def test_formato_valido_gera_resumo_e_confirma(nome, poligono):
    r = lavoura.de_arquivo(GERADORES[nome]([poligono]), nome)
    c = r["candidato"]
    assert c["origem"] == "arquivo" and c["estado"] == "aguardando_confirmacao"
    assert c["area_ha"] == pytest.approx(117.6, rel=0.02)
    assert [m["nome"] for m in c["municipios"]] == ["Rio Verde"]
    assert len(c["id_geometria"]) == 64 and c["proveniencia"]["formato"] == r["arquivo"]["formato"]
    lav = car.confirmar(c["geometria"], c["id_geometria"], "arquivo", c["proveniencia"])
    assert lav["estado"] == "confirmada" and lav["localizacao"]["local"]["municipio"]["codigo_ibge"] == "5218805"


@pytest.mark.parametrize("nome", FORMATOS)
def test_geometria_real_do_car_em_cada_formato(nome):
    g = geom_car()
    c = lavoura.de_arquivo(GERADORES[nome]([g]), nome)["candidato"]
    assert c["area_ha"] == pytest.approx(35.0003, rel=0.01)  # área declarada no CAR
    assert c["id_geometria"] == car.candidato(g, "car", {})["id_geometria"]


def test_id_geometria_igual_entre_formatos_e_desenho(poligono):
    ids = {nome: lavoura.de_arquivo(GERADORES[nome]([poligono]), nome)["candidato"]["id_geometria"] for nome in FORMATOS}
    ids["desenho"] = lavoura.de_desenho(poligono)["candidato"]["id_geometria"]
    assert len(set(ids.values())) == 1, ids


@pytest.mark.parametrize("como", ["FeatureCollection", "Feature", "Geometry"])
def test_geojson_nas_tres_formas(como, poligono):
    assert lavoura.de_arquivo(geojson([poligono], como), "a.json")["candidato"]["area_ha"] > 0


def test_multipolygon_e_uma_lavoura_em_partes(poligono):
    outro = [[x + 0.02, y] for x, y in ANEL]
    mp = {"type": "MultiPolygon", "coordinates": [[ANEL], [outro]]}
    for nome in FORMATOS:
        c = lavoura.de_arquivo(GERADORES[nome]([mp]), nome)["candidato"]
        assert c["area_ha"] == pytest.approx(2 * 117.6, rel=0.02), nome


def test_kml_com_buraco_desconta_area():
    furo = [[-51.098, -17.888], [-51.092, -17.888], [-51.092, -17.882], [-51.098, -17.882], [-51.098, -17.888]]
    com = lavoura.de_arquivo(kml([{"type": "Polygon", "coordinates": [ANEL, furo]}]), "a.kml")["candidato"]["area_ha"]
    assert com < 117.6 * 0.8


# ---------------------------------------------------------------- #24 / #32: erros nomeados


@pytest.mark.parametrize("conteudo,nome,codigo", [
    (b"qualquer", "area.shp", "formato_nao_aceito"),
    (b"qualquer", "area.pdf", "formato_nao_aceito"),
    (b"qualquer", "", "formato_nao_aceito"),
    (b"<kml", "a.kml", "arquivo_invalido"),
    (b'<?xml version="1.0"?><html/>', "a.kml", "arquivo_invalido"),
    (b'<?xml version="1.0"?><!DOCTYPE kml [<!ENTITY x "y">]><kml/>', "a.kml", "arquivo_invalido"),
    (b"nao e zip", "a.kmz", "arquivo_invalido"),
    (kmz(b"<kml/>", "leiame.txt"), "a.kmz", "arquivo_invalido"),
    (b"{nao json", "a.geojson", "arquivo_invalido"),
    (b"[1, 2]", "a.geojson", "arquivo_invalido"),
    (b'{"type":"Polygon","coordinates":[[[0,0],[1,1],[0,0]]],"crs":{"properties":{"name":"EPSG:31982"}}}', "a.geojson", "projecao_nao_suportada"),
    (b"nao e zip", "a.zip", "arquivo_invalido"),
])
def test_arquivo_invalido_tem_erro_nomeado(conteudo, nome, codigo):
    e = _erro(lavoura.de_arquivo, conteudo, nome)
    assert e.codigo == codigo and e.mensagem and e.campo == "arquivo"


@pytest.mark.parametrize("nome", FORMATOS)
def test_sem_geometria(nome):
    if nome == "area.zip":  # shapefile sem polígono: tipo ponto
        import io, zipfile, shapefile
        shp, shx, dbf = io.BytesIO(), io.BytesIO(), io.BytesIO()
        w = shapefile.Writer(shp=shp, shx=shx, dbf=dbf, shapeType=shapefile.POINT)
        w.field("x", "C"); w.point(-51.1, -17.9); w.record("p"); w.close()
        out = io.BytesIO()
        with zipfile.ZipFile(out, "w") as z:
            for n, b in (("a.shp", shp), ("a.shx", shx), ("a.dbf", dbf)):
                z.writestr(n, b.getvalue())
        conteudo = out.getvalue()
    elif nome == "area.geojson":
        conteudo = b'{"type":"Feature","geometry":{"type":"Point","coordinates":[-51.1,-17.9]},"properties":{}}'
    else:
        vazio = b'<?xml version="1.0"?><kml xmlns="http://www.opengis.net/kml/2.2"><Document><Placemark><Point><coordinates>-51.1,-17.9</coordinates></Point></Placemark></Document></kml>'
        conteudo = vazio if nome == "area.kml" else kmz(vazio)
    assert _erro(lavoura.de_arquivo, conteudo, nome).codigo == "sem_geometria"


@pytest.mark.parametrize("nome", FORMATOS)
def test_mais_de_uma_lavoura(nome, poligono):
    outro = {"type": "Polygon", "coordinates": [[[x + 0.05, y] for x, y in ANEL]]}
    e = _erro(lavoura.de_arquivo, GERADORES[nome]([poligono, outro]), nome)
    assert e.codigo == "varias_lavouras" and "uma lavoura por arquivo" in e.mensagem


@pytest.mark.parametrize("nome", FORMATOS)
def test_geometria_invalida(nome):
    oito = {"type": "Polygon", "coordinates": [[[-51.10, -17.89], [-51.09, -17.88], [-51.10, -17.88], [-51.09, -17.89], [-51.10, -17.89]]]}
    e = _erro(lavoura.de_arquivo, GERADORES[nome]([oito]), nome)
    assert e.codigo == "geometria_invalida" and "cruza" in e.mensagem


# ---------------------------------------------------------------- limites da D-009 (lidos do arquivo único)


def _quadrado(lado, n=1, x0=-51.10, y0=-17.89):
    p = [[x0 + lado * i / n, y0] for i in range(n)] + [[x0 + lado, y0 + lado * i / n] for i in range(n)]
    p += [[x0 + lado - lado * i / n, y0 + lado] for i in range(n)] + [[x0, y0 + lado - lado * i / n] for i in range(n)]
    return p + [list(p[0])]


def _multi(ns):
    return {"type": "MultiPolygon", "coordinates": [[_quadrado(0.001, n, x0=-51.10 + k * 0.01)] for k, n in enumerate(ns)]}


def test_vertices_no_limite_passa_e_acima_falha():
    lim = contrato.limites()["vertices_total_max"]["valor"]
    assert lim == 10000
    no_limite = _multi([625] * 3 + [624])  # 4 anéis de 4n+1 = 10.000
    acima = _multi([500] * 4 + [499])  # 5 anéis = 10.001
    assert sum(len(p[0]) for p in no_limite["coordinates"]) == lim
    assert lavoura.de_desenho(no_limite)["candidato"]
    assert lavoura.de_arquivo(geojson([no_limite]), "a.geojson")["candidato"]
    for fn, args in ((lavoura.de_desenho, (acima,)), (lavoura.de_arquivo, (geojson([acima]), "a.geojson"))):
        e = _erro(fn, *args)
        assert e.codigo == "vertices_excedidos" and "Simplifique" in e.mensagem


@pytest.mark.parametrize("lado,codigo", [(0.28, None), (0.30, "area_excedida")])  # ≈ 91 mil ha e ≈ 105 mil ha
def test_area_no_limite_e_acima(lado, codigo):
    g = {"type": "Polygon", "coordinates": [_quadrado(lado)]}
    if codigo is None:
        assert lavoura.de_desenho(g)["candidato"]["area_ha"] < contrato.limites()["area_max_ha"]["valor"]
    else:
        e = _erro(lavoura.de_desenho, g)
        assert e.codigo == codigo and "Divida" in e.mensagem and e.campo == "geometria"


def test_confirmacao_tambem_barra_limites_so_para_desenho_e_arquivo():
    g = {"type": "Polygon", "coordinates": [_quadrado(0.30)]}
    gid = car.candidato(g, "desenho", {})["id_geometria"]
    assert _erro(car.confirmar, g, gid, "desenho").codigo == "area_excedida"


# ---------------------------------------------------------------- rotas: 413, desenho, confirmação, limites


@pytest.fixture
def cli():
    return TestClient(app)


def test_api_arquivo_limite_de_tamanho(cli, monkeypatch):
    from tellus.api import car as rota
    assert rota.MAX_UPLOAD == contrato.limites()["arquivo_max_bytes"]["valor"] == 20 * 1024 * 1024
    chamados = []
    monkeypatch.setattr(lavoura, "de_arquivo", lambda c, n: chamados.append(len(c)) or {"ok": True})
    no_limite = cli.post("/api/lavoura/arquivo", files={"arquivo": ("a.geojson", b"0" * rota.MAX_UPLOAD)})
    acima = cli.post("/api/lavoura/arquivo", files={"arquivo": ("a.geojson", b"0" * (rota.MAX_UPLOAD + 1))})
    assert no_limite.status_code == 200 and chamados == [rota.MAX_UPLOAD]
    assert acima.status_code == 413 and acima.json()["erro"]["codigo"] == "arquivo_grande"


def test_kmz_descompactado_grande_e_recusado(monkeypatch):
    from tellus.contrato import regras as r
    lim = copy.deepcopy(r.limites())
    lim["arquivo_max_bytes"]["valor"] = 1000
    monkeypatch.setattr(lavoura, "limites", lambda: lim)
    bomba = kmz(b"<kml>" + b" " * 5000 + b"</kml>")
    assert len(bomba) < 1000
    e = _erro(lavoura.de_arquivo, bomba, "a.kmz")
    assert e.codigo == "arquivo_grande" and e.status == 413


@pytest.mark.parametrize("nome", FORMATOS)
def test_api_arquivo_e_confirmacao(cli, nome, poligono):
    r = cli.post("/api/lavoura/arquivo", files={"arquivo": (nome, GERADORES[nome]([poligono]))})
    assert r.status_code == 200, r.text
    c = r.json()["candidato"]
    r2 = cli.post("/api/lavoura/confirmar", json={"geometria": c["geometria"], "id_geometria": c["id_geometria"], "origem": "arquivo"})
    assert r2.status_code == 200 and r2.json()["estado"] == "confirmada"


def test_api_desenho_e_confirmacao(cli, poligono):
    r = cli.post("/api/lavoura/desenho", json={"geometria": poligono})
    assert r.status_code == 200
    c = r.json()["candidato"]
    assert c["origem"] == "desenho" and c["municipios"][0]["nome"] == "Rio Verde"
    r2 = cli.post("/api/lavoura/confirmar", json={"geometria": c["geometria"], "id_geometria": c["id_geometria"], "origem": "desenho"})
    assert r2.status_code == 200 and r2.json()["estado"] == "confirmada"


def test_api_erro_nomeado_no_envelope(cli):
    r = cli.post("/api/lavoura/arquivo", files={"arquivo": ("a.pdf", b"x")})
    assert r.status_code == 422
    e = r.json()["erro"]
    assert e["codigo"] == "formato_nao_aceito" and "KML" in e["mensagem"] and e["campo"] == "arquivo"
    r = cli.post("/api/lavoura/desenho", json={"geometria": {"type": "Polygon", "coordinates": [ANEL[:3]]}})
    assert r.status_code == 422 and r.json()["erro"]["codigo"] == "geometria_invalida"


def test_api_limites(cli):
    j = cli.get("/api/lavoura/limites").json()
    assert j["arquivo_formatos"]["valor"] == ["kml", "kmz", "geojson", "shapefile_zip"]
    assert {v["status"] for v in j.values()} == {"hipotese"}


# ---------------------------------------------------------------- #31 / SC-001: seis modos passam por confirmação


def test_seis_modos_exigem_confirmacao_antes_do_calculo(poligono):
    """Desenho e os 4 formatos de arquivo: candidato 'aguardando_confirmacao' → confirmada só pela confirmação.
    Marcação (ponto, entrega 1 da 002): o pedido de cálculo do contrato só aceita área confirmada."""
    from tellus.contrato.versao import ErroContrato

    modos = {"desenho": lavoura.de_desenho(poligono)["candidato"]}
    modos |= {nome: lavoura.de_arquivo(GERADORES[nome]([poligono]), nome)["candidato"] for nome in FORMATOS}
    for nome, c in modos.items():
        assert c["estado"] == "aguardando_confirmacao", nome
        assert car.confirmar(c["geometria"], c["id_geometria"], c["origem"])["estado"] == "confirmada", nome
    pedido = {"versao_contrato": "1.0.0", "data_colheita_soja": "2027-01-20", "solo": {"textura": "media"},
              "grupo": "GRUPO I", "metodologia": "cultura_escolhida", "cultura": "milho_2a_safra"}
    for tipo, area in (("marcacao", {"tipo": "ponto", "lat": -17.785, "lon": -50.965}),
                       ("desenho", {"tipo": "geometria", "geometria": poligono, "id_geometria": modos["desenho"]["id_geometria"],
                                    "origem": "desenho"})):
        with pytest.raises(ErroContrato) as e:
            contrato.normalizar_pedido(pedido | {"area": area | {"confirmada": False}})
        assert "confirmada" in e.value.mensagem, tipo
        assert contrato.normalizar_pedido(pedido | {"area": area | {"confirmada": True}})


def test_determinismo(poligono):
    a = lavoura.de_arquivo(kml([poligono]), "a.kml")["candidato"]
    b = lavoura.de_arquivo(kml([poligono]), "a.kml")["candidato"]
    assert a == b and math.isfinite(a["area_ha"])
