#!/usr/bin/env python3
"""Self-check do juris_sources.py (offline). Roda: python3 test_juris_sources.py

Nao faz rede: testa o parsing (contra fixtures do schema real), a deteccao de
bloqueio e as normalizacoes. A validacao ao vivo das APIs precisa de IP limpo
(residencial) ou proxy, e fica fora deste self-check.
"""
from datetime import date

import juris_sources as js
from juris_sources import (
    _alias_datajud,
    _montar_urn,
    _normalizar_djen,
    _parece_bloqueio,
    _parse_datajud,
    _parse_norma,
    _so_digitos,
)

# Fixture no formato JSON-LD que o normas.leg.br devolve (subset real do CDC).
NORMA_JSON = {
    "@type": "Legislation",
    "name": "Lei nº 8.078 de 11/09/1990",
    "alternateName": ["LEI-8078-1990-09-11", "Código de Defesa do Consumidor (CDC)"],
    "abstract": "Dispõe sobre a proteção do consumidor e dá outras providências.",
    "keywords": ["PROTEÇÃO", "CONSUMIDOR"],
    "legislationIdentifier": "urn:lex:br:federal:lei:1990-09-11;8078",
    "legislationDate": "1990-09-11",
    "datePublished": "1990-09-12",
    "encoding": [{"contentUrl": "https://normas.leg.br/api/binario/abc/texto"}],
}


def test_montar_urn_ano_so():
    assert _montar_urn("8078", "1990") == "urn:lex:br:federal:lei:1990;8078"
    assert _montar_urn("3.689", "1941", "decreto-lei") == "urn:lex:br:federal:decreto.lei:1941;3689"
    assert _montar_urn("55", "2020", "medida provisoria", "estadual") == \
        "urn:lex:br:estadual:medida.provisoria:2020;55"


def test_parse_norma_encontrada():
    r = _parse_norma(NORMA_JSON, "urn:lex:br:federal:lei:1990;8078")
    assert r["encontrado"] is True
    assert r["nome"].startswith("Lei nº 8.078")
    assert any("CDC" in a for a in r["apelidos"])
    assert r["ementa"].startswith("Dispõe sobre a proteção")
    assert r["data"] == "1990-09-11"
    assert r["textoIntegral"].endswith("/texto")
    assert r["link"] == "https://normas.leg.br/?urn=urn:lex:br:federal:lei:1990;8078"


def test_parse_norma_nao_encontrada():
    assert _parse_norma({"status": 404}, "urn:x")["encontrado"] is False
    assert _parse_norma({}, "urn:x")["encontrado"] is False


DATAJUD_JSON = {
    "hits": {"hits": [{"_source": {
        "numeroProcesso": "00008323520184013202",
        "tribunal": "TRF1", "grau": "G1",
        "classe": {"nome": "Procedimento Comum Civel"},
        "assuntos": [{"nome": "Indenizacao por Dano Moral"}],
        "orgaoJulgador": {"nome": "2a Vara Federal"},
        "dataAjuizamento": "2018-05-03T00:00:00.000Z",
        "movimentos": [
            {"nome": "Distribuicao", "dataHora": "2018-05-03T10:00:00.000Z"},
            {"nome": "Conclusao", "dataHora": "2019-01-10T09:00:00.000Z"},
            {"nome": "Sentenca", "dataHora": "2020-06-01T14:00:00.000Z"},
        ],
    }}]}
}


def test_parse_datajud_ordena_movimentos_desc():
    r = _parse_datajud(DATAJUD_JSON)
    assert len(r) == 1
    p = r[0]
    assert p["classe"] == "Procedimento Comum Civel"
    assert p["assuntos"] == ["Indenizacao por Dano Moral"]
    # movimento mais recente primeiro
    assert p["ultimosMovimentos"][0]["movimento"] == "Sentenca"
    assert p["ultimosMovimentos"][-1]["movimento"] == "Distribuicao"


def test_parse_datajud_vazio():
    assert _parse_datajud({"hits": {"hits": []}}) == []


def test_deteccao_de_bloqueio():
    assert _parece_bloqueio(200, "text/html", b"<!DOCTYPE html><title>desafio</title>")
    assert _parece_bloqueio(403, "application/json", b"{}")
    assert not _parece_bloqueio(200, "application/json", b'{"ok":true}')
    assert not _parece_bloqueio(200, "text/xml", b"<xml/>")


def test_alias_datajud():
    assert _alias_datajud("TJMG") == "tjmg"
    assert _alias_datajud("api_publica_tjsp") == "tjsp"
    assert _alias_datajud("TRF1") == "trf1"
    try:
        _alias_datajud("tj-mg!")
    except Exception:
        pass
    else:
        raise AssertionError("deveria rejeitar tribunal invalido")


def test_so_digitos():
    assert _so_digitos("0000832-35.2018.4.01.3202") == "00008323520184013202"
    assert _so_digitos("OAB 123.456") == "123456"


DJEN_ITEM = {
    "numeroprocessocommascara": "1000452-23.2026.8.13.0073",
    "data_disponibilizacao": "2026-07-15",
    "siglaTribunal": "TJMG",
    "tipoDocumento": "Sentença",
    "nomeClasse": "Procedimento Comum",
    "texto": "<p>Vistos.</p><style>x{}</style> Julgo <b>procedente</b> o pedido &amp; etc. " + "x" * 5000,
}


def test_normalizar_djen_compacto_sem_teor():
    r = _normalizar_djen(DJEN_ITEM)
    assert "teor" not in r  # compacto por padrao
    assert len(r["trecho"]) <= 200
    assert "<" not in r["trecho"] and "style" not in r["trecho"]  # HTML/estilo removidos
    assert r["tipoDocumento"] == "Sentença"


def test_normalizar_djen_com_teor_limitado():
    r = _normalizar_djen(DJEN_ITEM, incluir_teor=True)
    assert "teor" in r and len(r["teor"]) <= 4000  # teor incluso mas limitado


def _item(n: int, texto: str, tipo: str = "Intimação") -> dict:
    return {"numeroprocessocommascara": f"100045{n}-23.2026.8.13.0073",
            "data_disponibilizacao": "2026-07-15", "siglaTribunal": "TJMG",
            "tipoDocumento": tipo, "nomeClasse": "Procedimento Comum",
            "texto": texto}


def _djen_falso(paginas: list[list[dict]]):
    """Substitui a camada de rede: devolve as paginas na ordem, depois vazio."""
    def fake(params, pagina, timeout):
        return paginas[pagina - 1] if pagina <= len(paginas) else []
    return fake


def _rodar_djen(paginas, **kw):
    original = js._pagina_djen
    js._pagina_djen = _djen_falso(paginas)
    try:
        return js.consultar_djen("232913", "MG", hoje=date(2026, 8, 17), **kw)
    finally:
        js._pagina_djen = original


def test_djen_pagina_alem_das_100():
    # 100 na primeira pagina + 30 na segunda: nao pode parar no teto da API.
    paginas = [[_item(i, "teor") for i in range(100)],
               [_item(100 + i, "teor") for i in range(30)]]
    r = _rodar_djen(paginas)
    assert r["total"] == 130, r["total"]


def test_djen_para_na_pagina_incompleta():
    # Pagina curta = fim. Nao pode continuar pedindo pagina a toa.
    chamadas = []
    original = js._pagina_djen
    js._pagina_djen = lambda params, pagina, timeout: (
        chamadas.append(pagina) or [_item(0, "teor")])
    try:
        js.consultar_djen("232913", "MG", hoje=date(2026, 8, 17))
    finally:
        js._pagina_djen = original
    assert chamadas == [1], chamadas


def test_djen_filtro_contendo_le_o_teor_nao_o_rotulo():
    paginas = [[
        _item(1, "Expeca-se ALVARA de levantamento em favor do exequente.", "Intimação"),
        _item(2, "Requisicao de Pequeno Valor expedida.", "Ato ordinatório"),
        _item(3, "Vistos. Homologo o calculo.", "Sentença"),
    ]]
    r = _rodar_djen(paginas, contendo="alvara|requisicao de pequeno valor")
    assert r["total"] == 2, r["total"]
    assert r["resumo_por_tipo"] == {"Intimação": 1, "Ato ordinatório": 1}
    assert r["resumo_por_termo"] == {"alvara": 1, "requisicao de pequeno valor": 1}
    assert "1 de 3" not in r["aviso"] and "2 de 3" in r["aviso"]


def test_djen_termo_duplo_conta_uma_vez_no_total():
    # Publicacao que cita alvara E precatorio: 1 no total, 1 em cada termo.
    paginas = [[_item(1, "Expeca-se alvara referente ao precatorio pago.")]]
    r = _rodar_djen(paginas, contendo="alvara|precatorio")
    assert r["total"] == 1
    assert r["resumo_por_termo"] == {"alvara": 1, "precatorio": 1}


def test_djen_filtro_ignora_acento_e_caixa():
    paginas = [[_item(1, "expedido PRECATÓRIO nos autos", "Intimação")]]
    assert _rodar_djen(paginas, contendo="precatorio")["total"] == 1
    assert _rodar_djen(paginas, contendo="penhora")["total"] == 0


def test_djen_corta_lista_mas_conta_tudo():
    # Lista cortada nao pode virar total menor: o "quantos" tem que continuar certo.
    paginas = [[_item(i, "teor") for i in range(100)],
               [_item(100 + i, "teor") for i in range(80)]]
    r = _rodar_djen(paginas)
    assert r["total"] == 180
    assert len(r["publicacoes"]) == js.DJEN_TETO_ITENS
    assert "omitidos" in r["aviso"]


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} testes passaram.")
