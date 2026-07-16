#!/usr/bin/env python3
"""Self-check do prazo_cpc.py. Roda: python3 test_prazo_cpc.py

Nao depende da lib `holidays` (usa janelas sem feriado nacional), entao passa
mesmo sem ela instalada. Verifica a regra do CPC e propriedades do calendario.
"""
from datetime import date

from prazo_cpc import CalendarioForense, calcular


def test_caso_concreto_julho():
    # Disp. sexta 2026-07-03, ato de 5 dias uteis, sem feriado no periodo.
    # §2: publica seg 06/07. §3: inicia ter 07/07.
    # art. 219: 07(1),08(2),09(3),10(4),13(5) -> vence seg 2026-07-13.
    r = calcular(date(2026, 7, 3), 5, tribunal="TJMG")
    assert r["publicacao"] == "2026-07-06", r["publicacao"]
    assert r["inicioContagem"] == "2026-07-07", r["inicioContagem"]
    assert r["dataVencimento"] == "2026-07-13", r["dataVencimento"]


def test_ja_publicado_pula_paragrafo2():
    # Se a data JA e a publicacao (seg 06/07), inicio = ter 07/07, igual acima.
    r = calcular(date(2026, 7, 6), 5, tribunal="TJMG", ja_publicado=True)
    assert r["publicacao"] == "2026-07-06"
    assert r["dataVencimento"] == "2026-07-13"


def test_vencimento_sempre_util_e_fora_do_recesso():
    cal = CalendarioForense(tribunal="TJSP")
    for dia_disp in range(1, 29):
        r = calcular(date(2026, 6, dia_disp), 15, tribunal="TJSP")
        venc = date.fromisoformat(r["dataVencimento"])
        assert venc.weekday() < 5, f"venceu no fim de semana: {venc}"
        assert not cal._em_recesso(venc), f"venceu no recesso: {venc}"


def test_recesso_empurra_para_depois_de_20_01():
    # Prazo curto que cairia dentro do recesso deve pular para depois de 20/01.
    r = calcular(date(2026, 12, 18), 5, tribunal="TJRS")
    venc = date.fromisoformat(r["dataVencimento"])
    assert venc >= date(2027, 1, 21), venc


def test_contagem_bate_com_prazo():
    # Entre (inicio - 1) e vencimento deve haver exatamente `dias` uteis.
    cal = CalendarioForense(tribunal="TJMG")
    r = calcular(date(2026, 8, 10), 15, tribunal="TJMG")
    inicio = date.fromisoformat(r["inicioContagem"])
    venc = date.fromisoformat(r["dataVencimento"])
    # uteis_entre exclui `a` e inclui `b`; comeca a contar em inicio, entao
    # a base e o dia util anterior ao inicio.
    anterior = inicio - __import__("datetime").timedelta(days=1)
    assert cal.uteis_entre(anterior, venc) == 15


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for fn in fns:
        fn()
        print(f"ok  {fn.__name__}")
    print(f"\n{len(fns)} testes passaram.")
