"""Cliente SMAP sem rede: HDF5 SINTÉTICO gerado no teste e transporte HTTP simulado."""

import datetime as dt
import io

import h5py
import httpx
import numpy as np
import pytest

from tellus.umidade import cliente, servico

from .conftest import CEL_M09, LAT, LON

FICHA = servico.ficha()["produtos"]["SPL3SMP_E"]


def _h5_recorte(valor_am=0.25, flag_am=0, valor_pm=-9999.0, flag_pm=65534, linha=CEL_M09[0], coluna=CEL_M09[1]) -> bytes:
    """Recorte 1×1 no formato dos grupos do SPL3SMP_E (valores sintéticos)."""
    buf = io.BytesIO()
    with h5py.File(buf, "w") as f:
        for grupo, suf, v, q in (("Soil_Moisture_Retrieval_Data_AM", "", valor_am, flag_am),
                                 ("Soil_Moisture_Retrieval_Data_PM", "_pm", valor_pm, flag_pm)):
            g = f.create_group(grupo)
            d = g.create_dataset(f"soil_moisture{suf}", data=np.array([[v]], dtype="f4"))
            d.attrs["units"] = b"cm**3/cm**3"
            g.create_dataset(f"retrieval_qual_flag{suf}", data=np.array([[q]], dtype="u2"))
            g.create_dataset(f"EASE_row_index{suf}", data=np.array([[linha]], dtype="u2"))
            g.create_dataset(f"EASE_column_index{suf}", data=np.array([[coluna]], dtype="u2"))
    return buf.getvalue()


def test_extrair_celula_do_recorte():
    with h5py.File(io.BytesIO(_h5_recorte()), "r") as h5:
        am = cliente.extrair_celula(h5, FICHA, "AM", *CEL_M09, recorte=True)
        pm = cliente.extrair_celula(h5, FICHA, "PM", *CEL_M09, recorte=True)
    assert am["valor"] == pytest.approx(0.25) and am["qualidade"] == 0 and am["unidade_no_arquivo"] == "cm**3/cm**3"
    assert (am["linha_arquivo"], am["coluna_arquivo"]) == CEL_M09
    assert pm["valor"] == -9999.0 and pm["qualidade"] == 65534


def test_indice_que_nao_confere_e_recusado():
    with h5py.File(io.BytesIO(_h5_recorte(coluna=CEL_M09[1] + 1)), "r") as h5:
        with pytest.raises(ValueError, match="não confere"):
            cliente.extrair_celula(h5, FICHA, "AM", *CEL_M09, recorte=True)


def test_restricao_dap4_pede_so_a_celula():
    ce = cliente.restricao_dap4(FICHA, *CEL_M09)
    assert "/Soil_Moisture_Retrieval_Data_AM/soil_moisture[1059:1:1059][1382:1:1382]" in ce
    assert "/Soil_Moisture_Retrieval_Data_PM/retrieval_qual_flag_pm[1059:1:1059][1382:1:1382]" in ce
    assert ce.count("[1059:1:1059]") == 8


def _cmr(entradas):
    return {"feed": {"entry": [
        {"time_start": f"{d}T00:00:00.000Z", "time_end": f"{d}T23:59:59.999Z", "updated": "2026-11-14",
         "links": [{"href": f"https://data.nsidc.earthdatacloud.nasa.gov/x/SMAP_L3_SM_P_E_{d.replace('-', '')}_R19240_{n}.h5"},
                   {"href": "s3://x/y.h5"}]}
        for d, n in entradas]}}


def test_buscar_granulos_fica_com_o_reprocessamento_mais_recente():
    t = httpx.MockTransport(lambda req: httpx.Response(200, json=_cmr([("2026-11-08", "001"), ("2026-11-08", "002"), ("2026-11-09", "001")])))
    gs = cliente.buscar_granulos(FICHA, dt.date(2026, 11, 8), dt.date(2026, 11, 9), httpx.Client(transport=t))
    assert [g["titulo"] for g in gs] == ["SMAP_L3_SM_P_E_20261108_R19240_002.h5", "SMAP_L3_SM_P_E_20261109_R19240_001.h5"]


def test_sem_token_nao_baixa(monkeypatch):
    monkeypatch.delenv("EARTHDATA_TOKEN", raising=False)
    with pytest.raises(cliente.FonteIndisponivel, match="EARTHDATA_TOKEN"):
        cliente.baixar_recorte(FICHA, {"titulo": "x.h5"}, *CEL_M09)


def test_login_exigido_vira_fonte_indisponivel(monkeypatch):
    monkeypatch.setenv("EARTHDATA_TOKEN", "token-de-teste")
    t = httpx.MockTransport(lambda req: httpx.Response(302, headers={"location": "https://urs.earthdata.nasa.gov/oauth"}))
    with pytest.raises(cliente.FonteIndisponivel, match="HTTP 302"):
        cliente.baixar_recorte(FICHA, {"titulo": "x.h5"}, *CEL_M09, cliente=httpx.Client(transport=t))


def test_atualizar_celula_ponta_a_ponta_e_servico(monkeypatch, tmp_path):
    monkeypatch.setenv("EARTHDATA_TOKEN", "token-de-teste")
    vistos = []

    def responder(req: httpx.Request):
        vistos.append(req)
        if "cmr.earthdata" in req.url.host:
            return httpx.Response(200, json=_cmr([("2026-11-12", "001"), ("2026-11-13", "001")]))
        return httpx.Response(200, content=_h5_recorte(valor_am=0.2 if "20261112" in str(req.url) else 0.3))

    c = httpx.Client(transport=httpx.MockTransport(responder))
    cliente.atualizar_celula(tmp_path, "SPL3SMP_E", FICHA, "EASE2_M09", *CEL_M09, dt.date(2026, 11, 12), dt.date(2026, 11, 13), c)
    opendap = [r for r in vistos if "opendap" in r.url.host]
    assert len(opendap) == 2 and all(r.headers["Authorization"] == "Bearer token-de-teste" for r in opendap)
    linhas, meta = cliente.ler_cache(tmp_path, "SPL3SMP_E", "EASE2_M09", *CEL_M09)
    assert "token" not in str(meta).lower() and meta["versao"] == "006" and meta["sintetico"] is False
    assert len(linhas) == 4
    r = servico.contexto(LAT, LON, dir_cache=tmp_path)
    assert [(i["periodo"]["data"], i["valor"]) for i in r["itens"]] == [("2026-11-12", 0.2), ("2026-11-13", 0.3)]
    assert r["regra_periodo"]["contagem"]["registros_sem_dado"] == 2  # PM com fill nos dois dias


def test_gravar_cache_e_deterministico(tmp_path, cache_sintetico):
    linhas, meta = cliente.ler_cache(cache_sintetico, "SPL3SMP_E", "EASE2_M09", *CEL_M09)
    cliente.gravar_cache(tmp_path, "SPL3SMP_E", "EASE2_M09", *CEL_M09, list(reversed(linhas)), meta)
    a = cliente.arquivo_cache(cache_sintetico, "SPL3SMP_E", "EASE2_M09", *CEL_M09).read_bytes()
    b = cliente.arquivo_cache(tmp_path, "SPL3SMP_E", "EASE2_M09", *CEL_M09).read_bytes()
    assert a == b
