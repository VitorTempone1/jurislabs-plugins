#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = ["holidays>=0.60"]
# ///
"""Suite do motor de prazo. Roda: python3 test_prazo_cpc.py

REGRA (ESPEC-PRAZOS §II.8), e ela e o motivo desta suite ter sido reescrita:
**teste de prazo que passa sem calendario nao e teste de prazo.**

A suite anterior tinha 5 testes e todos os 5 passavam com a `holidays` bloqueada
e com os quatro defeitos de calendario no lugar. Dois eram ativamente nocivos:
um usava o proprio `_em_recesso` como oraculo de si mesmo, e o outro cravava
`venc >= 21/01`, o que CONGELAVA o Defeito 1 (consertar o recesso mantinha o
teste verde).

Aqui nao ha data derivada do codigo sob teste: **toda data esperada foi contada
a mao, com o artigo no comentario**. E a suite EXIGE a lib `holidays` - se ela
sumir do ambiente, a suite morre em vez de passar mentindo.
"""
import json
from datetime import date, timedelta
from pathlib import Path

from prazo_cpc import (DIR_FERIADOS_PADRAO, REGIMES, CalendarioForense,
                       aviso_assinatura, calcular, carregar_calendario,
                       feriados_forenses_federais, pascoa)

try:
    import holidays  # noqa: F401
except ImportError:
    raise SystemExit(
        "FALHA: a lib `holidays` nao esta instalada.\n"
        "Esta suite testa CALENDARIO. Sem a lib ela nao tem o que verificar e\n"
        "passar seria mentira (foi exatamente o que a suite antiga fazia).\n"
        "Instale com: pip install holidays")

TJSP = dict(tribunal="TJSP")
DISP = dict(natureza="disponibilizacao")
# Justica Federal: e SO aqui (e nos Tribunais Superiores) que a Lei 5.010/66
# art. 62 vale. TRF3 cobre SP, entao o feriado ESTADUAL de 09/07 continua
# entrando e as contas ficam comparaveis linha a linha com as do TJSP.
TRF3 = dict(tribunal="TRF3", uf="SP")


def _venc(data, dias, regime, **kw):
    return calcular(data, dias, regime, **kw)["dataVencimento"]


def _sem_expediente(cal, *iso):
    for s in iso:
        d = date.fromisoformat(s)
        assert not cal.tem_expediente(d), f"{s} deveria ser SEM expediente"


def _cal_trib(tribunal, **kw):
    """CalendarioForense COM a camada 4 carregada - e o que `calcular` monta.
    `CalendarioForense(tribunal=...)` puro nao le o JSON do tribunal."""
    c = carregar_calendario(DIR_FERIADOS_PADRAO, tribunal)
    return CalendarioForense(tribunal=tribunal, feriados_extra=c.get("feriados", {}),
                             exclusoes=c.get("exclusoes", set()), **kw)


def _com_expediente(cal, *iso):
    for s in iso:
        d = date.fromisoformat(s)
        assert cal.tem_expediente(d), (
            f"{s} deveria TER expediente, motivo dado: {cal.motivo_sem_expediente(d)}")


# ==========================================================================
# 0. Calendario congelado - o teste que MORRE se a `holidays` sumir (§II.8.1)
# ==========================================================================
def test_calendario_civil_congelado_2026_TJSP():
    """Lista literal. Se a lib sumir ou a subdiv=SP quebrar, isto morre.

    09/07 (Revolucao Constitucionalista) e ESTADUAL de SP: e o canario. O
    `except Exception` do construtor cai para nacionais em silencio, e era
    invisivel para a suite antiga.
    """
    cal = CalendarioForense(**TJSP)
    _sem_expediente(cal,
                    "2026-01-01",   # Confraternizacao
                    "2026-04-03",   # Sexta-feira Santa
                    "2026-04-21",   # Tiradentes
                    "2026-05-01",   # Trabalho
                    "2026-07-09",   # Revolucao Constitucionalista (SO SP)
                    "2026-09-07",   # Independencia
                    "2026-10-12",   # Aparecida
                    "2026-11-15",   # Republica (domingo, mas vale)
                    "2026-11-20",   # Consciencia Negra
                    "2026-12-25")   # Natal
    assert cal.uf_carregada, "subdiv=SP nao carregou - o except engoliu"


def test_pascoa_literal():
    # Conferencia externa: Pascoa 2025=20/04, 2026=05/04, 2027=28/03.
    assert pascoa(2025) == date(2025, 4, 20)
    assert pascoa(2026) == date(2026, 4, 5)
    assert pascoa(2027) == date(2027, 3, 28)


# ==========================================================================
# 1. DEFEITO 1 - recesso: duas janelas, nao uma
#    Res. CNJ 244/2016: art. 1º recesso 20/12-06/01 (tribunal FECHADO);
#    art. 3º par. unico "o expediente forense sera executado normalmente no
#    periodo de 7 a 20 de janeiro, inclusive, mesmo com a suspensao de prazos".
#    O codigo antigo devolvia True para 20/12-20/01 inteiro dentro de eh_util,
#    e com isso empurrava a PUBLICACAO para depois de 20/01.
# ==========================================================================
def test_defeito1_de_07_a_20_de_janeiro_o_tribunal_ESTA_ABERTO():
    cal = CalendarioForense(**TJSP)
    # Fechado (art. 1º). Dias uteis dentro de 20/12-06/01:
    _sem_expediente(cal, "2026-12-21", "2026-12-22", "2026-12-23", "2026-12-24",
                    "2026-12-28", "2026-12-29", "2026-12-30", "2026-12-31",
                    "2027-01-04", "2027-01-05", "2027-01-06")
    # ABERTO (art. 3º par. unico). O codigo antigo dizia "sem expediente" aqui:
    _com_expediente(cal, "2027-01-07", "2027-01-08", "2027-01-11", "2027-01-12",
                    "2027-01-13", "2027-01-14", "2027-01-15", "2027-01-18",
                    "2027-01-19", "2027-01-20")


def test_defeito1_publica_em_07_01_mas_o_prazo_so_corre_em_21_01():
    # Disponibilizado no ultimo dia do recesso fechado (qua 06/01/2027).
    # §2: publica no 1º dia com expediente = qui 07/01 (art. 3º par. unico).
    # §3 + art. 220: a contagem so pode comecar em 21/01, 1º dia util depois
    # da suspensao (20/01 e quarta; 21/01 e quinta).
    r = calcular(date(2027, 1, 6), 1, "cpc", **DISP, **TJSP)
    assert r["publicacao"] == "2027-01-07", r["publicacao"]
    assert r["inicioContagem"] == "2027-01-21", r["inicioContagem"]
    assert r["dataVencimento"] == "2027-01-21", r["dataVencimento"]


def test_defeito1_tres_casos_da_auditoria():
    # Contados a mao com a Res. CNJ 244/2016 (Parte I.2 da ESPEC-PRAZOS).
    # (a) disp sex 18/12/2026, 15d: pub 07/01/27, ini 21/01.
    #     21,22 | 25,26,27,28,29 | 01,02,03,04,05/02 | 08,09,10/02
    #     -> 15º = qua 10/02/2027 no TJSP.
    #     O Carnaval de 08 e 09/02/2027 e Lei 5.010/66 art. 62, III: NAO se
    #     aplica a TJ estadual. Na Justica Federal ele volta e adia dois dias
    #     uteis, para sex 12/02/2027 - e e essa a linha da auditoria original.
    assert _venc(date(2026, 12, 18), 15, "cpc", **DISP, **TJSP) == "2027-02-10"
    assert _venc(date(2026, 12, 18), 15, "cpc", **DISP, **TRF3) == "2027-02-12"
    # (b) disp qui 07/01/2027, 15d: pub sex 08/01, ini 21/01 - mesma contagem.
    assert _venc(date(2027, 1, 7), 15, "cpc", **DISP, **TJSP) == "2027-02-10"
    assert _venc(date(2027, 1, 7), 15, "cpc", **DISP, **TRF3) == "2027-02-12"
    # (c) disp seg 11/01/2027, 5d: pub ter 12/01, ini 21/01.
    #     21(1),22(2),25(3),26(4),27(5) -> qua 27/01/2027. Sem Carnaval no
    #     caminho, estadual e federal batem - e tem que bater mesmo.
    assert _venc(date(2027, 1, 11), 5, "cpc", **DISP, **TJSP) == "2027-01-27"
    assert _venc(date(2027, 1, 11), 5, "cpc", **DISP, **TRF3) == "2027-01-27"


# ==========================================================================
# 2. DEFEITO 2 - ponto facultativo civil nao e feriado forense
#    Lei 5.010/66 art. 62, III: "os dias de segunda e terca-feira de Carnaval".
#    E para ai. A Quarta de Cinzas depende de portaria do tribunal.
#    O codigo antigo usava categories=("public","optional") e apagava o dia.
# ==========================================================================
def test_defeito2_quarta_de_cinzas_tem_expediente():
    cal = CalendarioForense(**TJSP)
    fed = CalendarioForense(**TRF3)
    _sem_expediente(fed, "2026-02-16", "2026-02-17")   # Carnaval seg e ter
    _com_expediente(fed, "2026-02-18")                 # Quarta de Cinzas
    # No TJSP o Carnaval do art. 62, III nao alcanca; vem da portaria (camada 4)
    # e o TJSP nao tem JSON aqui - logo, dia util e o motor AVISANDO.
    _com_expediente(cal, "2026-02-16", "2026-02-17", "2026-02-18")
    # Os outros facultativos civis que a categoria `optional` trazia e que
    # tambem sumiram do calendario (24 e 31/12 ficam de fora da lista: caem
    # dentro do recesso, entao a assercao provaria a coisa errada).
    _com_expediente(cal, "2026-06-04",   # Corpus Christi (nao esta no art. 62)
                    "2026-10-28")        # Dia do Servidor Publico


def test_defeito2_caso_medido_13_02_2026():
    # disp sex 13/02/2026, 5 dias. Carnaval 16-17/02, Cinzas 18/02.
    # Na Justica Federal (art. 62, III): §2 pub = 1º dia com expediente =
    # qua 18/02 (Cinzas E dia util). §3 ini qui 19/02.
    # 19(1),20(2),23(3),24(4),25(5) -> qua 25/02/2026.
    # O motor antigo dava 26/02 - um dia TARDE, prazo perdido.
    assert _venc(date(2026, 2, 13), 5, "cpc", **DISP, **TRF3) == "2026-02-25"
    # No TJSP o Carnaval nao vem do art. 62: pub seg 16/02, ini ter 17/02.
    # 17(1),18(2),19(3),20(4),23(5) -> seg 23/02/2026. Dois dias uteis mais
    # CEDO que o federal - a direcao segura de errar.
    assert _venc(date(2026, 2, 13), 5, "cpc", **DISP, **TJSP) == "2026-02-23"


# ==========================================================================
# 3. DEFEITO 3 - feriados forenses de verdade que faltavam
#    Lei 5.010/66 art. 62: II Semana Santa (quarta ao Domingo de Pascoa);
#    IV 11/08, 1º e 2/11 e 8/12 (redacao da Lei 6.741/1979).
# ==========================================================================
def test_defeito3_feriados_do_art_62_estao_no_calendario():
    fed = CalendarioForense(**TRF3)
    _sem_expediente(fed, "2026-08-11", "2026-11-02", "2026-12-08")
    # 1º/11/2026 cai num domingo; use 2027 (segunda-feira) para provar o inciso.
    _sem_expediente(CalendarioForense(**TRF3), "2027-11-01")
    # Semana Santa 2026: Pascoa 05/04 -> quarta 01/04 ao domingo 05/04.
    _sem_expediente(fed, "2026-04-01", "2026-04-02", "2026-04-03")
    _com_expediente(fed, "2026-03-31", "2026-04-06")   # antes e depois: uteis
    fer = feriados_forenses_federais(2026)
    assert date(2026, 2, 16) in fer and date(2026, 2, 17) in fer   # Carnaval
    assert date(2026, 2, 18) not in fer, "Cinzas NAO esta no art. 62"


def test_defeito3_casos_medidos():
    """Cada caso e medido DUAS vezes: no federal (art. 62 vale) e no estadual
    (art. 62 nao vale). A diferenca entre as duas colunas E o bug de direcao."""
    # disp seg 03/08/2026, 10d: pub ter 04/08, ini qua 05/08.
    # federal:  05,06,07,10 | [11/08 art. 62, IV] | 12,13,14,17,18,19 -> 19/08.
    assert _venc(date(2026, 8, 3), 10, "cpc", **DISP, **TRF3) == "2026-08-19"
    # estadual: 05,06,07,10,11,12,13,14,17,18 -> 10º = ter 18/08/2026.
    assert _venc(date(2026, 8, 3), 10, "cpc", **DISP, **TJSP) == "2026-08-18"
    # disp qui 26/11/2026, 10d: pub sex 27/11, ini seg 30/11.
    # federal:  30/11,01,02,03,04,07/12 | [08/12 art. 62, IV] | 09,10,11,14.
    assert _venc(date(2026, 11, 26), 10, "cpc", **DISP, **TRF3) == "2026-12-14"
    # estadual: 30/11,01,02,03,04,07,08,09,10,11/12 -> 10º = sex 11/12/2026.
    assert _venc(date(2026, 11, 26), 10, "cpc", **DISP, **TJSP) == "2026-12-11"
    # disp seg 30/03/2026, 5d: pub ter 31/03. §3 manda para qua 01/04, que e
    # Semana Santa (art. 62, II, "compreendidos entre a quarta-feira e o
    # Domingo de Pascoa") -> ini seg 06/04. 06,07,08,09,10 -> sex 10/04/2026.
    # NOTA: a Parte I.2 da ESPEC dava 09/04 nessa linha, contando SO a quinta
    # santa. O inciso II abrange a quarta tambem; 10/04 e o que o texto legal
    # produz. Divergencia registrada de proposito, para o Vitor cruzar.
    assert _venc(date(2026, 3, 30), 5, "cpc", **DISP, **TRF3) == "2026-04-10"
    # estadual sem portaria: 01 e 02/04 sao uteis (03/04 e Sexta-feira Santa,
    # feriado CIVIL nacional, esse fica). pub 31/03, ini qua 01/04:
    # 01(1),02(2),[03 civil],06(3),07(4),08(5) -> qua 08/04/2026.
    assert _venc(date(2026, 3, 30), 5, "cpc", **DISP, **TJSP) == "2026-04-08"


# ==========================================================================
# 3-B. DEFEITO 5 - o art. 62 e FEDERAL, nao nacional
#      Lei 5.010/66, ementa: "Organiza a Justica Federal de primeira
#      instancia". Art. 62: "serao feriados na Justica Federal, INCLUSIVE nos
#      Tribunais Superiores". Aplicar isso num TJ inventa feriado que nao
#      existe e adia o vencimento - a unica direcao que faz perder prazo.
#      Texto conferido no planalto (l5010.htm).
# ==========================================================================
def test_defeito5_11_08_e_dia_util_no_TJ_e_nao_e_na_justica_federal():
    """Dia do Advogado (art. 62, IV). O caso literal do bug."""
    _com_expediente(CalendarioForense(tribunal="TJMG"), "2026-08-11")
    _com_expediente(CalendarioForense(**TJSP), "2026-08-11")
    for sigla in ("STJ", "STF", "TST", "TSE", "STM", "TRF6", "TRF1", "JFMG"):
        _sem_expediente(CalendarioForense(tribunal=sigla), "2026-08-11")


def test_defeito5_08_12_no_TJMG_vem_da_portaria_e_nao_do_art_62():
    """08/12 fecha o TJMG - mas por LC estadual 59/2001, camada 4, nao pelo
    art. 62, IV. Se o motivo citar a Lei 5.010/66, o vazamento voltou."""
    motivo = _cal_trib("TJMG").motivo_sem_expediente(date(2026, 12, 8))
    assert motivo, "08/12 deveria fechar o TJMG pela portaria (camada 4)"
    assert "5.010" not in motivo, f"art. 62 vazou para o TJMG: {motivo}"
    # No TJSP, que nao tem portaria carregada aqui, 08/12 e dia util.
    _com_expediente(CalendarioForense(**TJSP), "2026-12-08")
    # E na Justica Federal continua sendo art. 62, IV.
    fed = CalendarioForense(tribunal="STJ").motivo_sem_expediente(date(2026, 12, 8))
    assert "5.010" in fed and "62" in fed, fed


def test_defeito5_semana_santa_so_alcanca_a_justica_federal():
    # Pascoa 2026 = 05/04. Art. 62, II: quarta 01/04 ao domingo 05/04.
    _sem_expediente(CalendarioForense(tribunal="TRF6"), "2026-04-01", "2026-04-02")
    # No TJSP (sem portaria) 01 e 02/04 sao uteis. 03/04 continua fechado:
    # Sexta-feira Santa e feriado CIVIL nacional, outra camada.
    _com_expediente(CalendarioForense(**TJSP), "2026-04-01", "2026-04-02")
    _sem_expediente(CalendarioForense(**TJSP), "2026-04-03")
    # No TJMG a portaria (PC 1764/2026) cobre 01 e 02/04 - camada 4, nao 62.
    motivo = _cal_trib("TJMG").motivo_sem_expediente(date(2026, 4, 1))
    assert motivo and "1764" in motivo, f"esperava a portaria do TJMG: {motivo}"
    assert "5.010" not in motivo, f"art. 62 vazou para o TJMG: {motivo}"
    # E a conta fecha igual a federal: disp seg 30/03/2026, 5d, pub ter 31/03,
    # ini seg 06/04 (01 e 02 pela portaria, 03 civil) -> sex 10/04/2026.
    assert _venc(date(2026, 3, 30), 5, "cpc", **DISP, tribunal="TJMG") == "2026-04-10"


def test_defeito5_recesso_continua_fechando_o_TJ_estadual():
    """O inciso I NAO cai junto: 20/12-06/01 segue fechado em TJ por Res. CNJ
    244/2016 art. 1º + portaria. Tirar isso junto seria o erro simetrico."""
    for foro in (dict(tribunal="TJMG"), TJSP):
        cal = CalendarioForense(**foro)
        _sem_expediente(cal, "2026-12-21", "2026-12-22", "2026-12-23",
                        "2026-12-28", "2026-12-30", "2027-01-04", "2027-01-06")
        motivo = cal.motivo_sem_expediente(date(2026, 12, 21))
        assert "244/2016" in motivo, motivo
        assert "5.010" not in motivo, f"art. 62 vazou no recesso estadual: {motivo}"
    # Na Justica Federal o recesso tem os DOIS fundamentos.
    fed = CalendarioForense(tribunal="TRF6").motivo_sem_expediente(date(2026, 12, 21))
    assert "244/2016" in fed and "5.010" in fed, fed


def test_defeito5_caso_medido_04_08_2026_TJMG_bate_com_a_producao():
    """O caso que expos o bug. disp ter 04/08/2026, 15 dias uteis, TJMG.
    pub qua 05/08 (§2), ini qui 06/08 (§3).
    06,07,10,11,12,13,14,17,18,19,20,21,24,25,26 -> 15º = qua 26/08/2026.
    O plugin dava 27/08 (contava 11/08 como feriado); a producao do JurisTools
    da 26/08 e esta certa."""
    r = calcular(date(2026, 8, 4), 15, "cpc", **DISP, tribunal="TJMG")
    assert r["publicacao"] == "2026-08-05"
    assert r["inicioContagem"] == "2026-08-06"
    assert r["dataVencimento"] == "2026-08-26", r["dataVencimento"]
    assert not any("11/08" in e["data"] or "5.010" in e["motivo"]
                   for e in r["excluidos"]), r["excluidos"]


def test_defeito5_o_aviso_de_calendario_faltando_continua_saindo():
    """Perder Carnaval e Semana Santa num TJ e a direcao SEGURA, mas so se o
    advogado for avisado. Os dois avisos tem que aparecer."""
    r = calcular(date(2026, 2, 13), 5, "cpc", **DISP, **TJSP)
    assert any("Sem calendario do TJSP" in a for a in r["avisos"]), r["avisos"]
    assert any("Carnaval" in a and "Semana Santa" in a for a in r["avisos"]), r["avisos"]
    assert any("ESTADUAL" in a and "5.010/66 art. 62" in a for a in r["avisos"]), r["avisos"]
    assert r["justica"] == "estadual" and r["art62Aplicado"] is False
    # Na Justica Federal o aviso de escopo NAO aparece (nada foi tirado).
    f = calcular(date(2026, 2, 13), 5, "cpc", **DISP, **TRF3)
    assert not any("ESTADUAL" in a for a in f["avisos"]), f["avisos"]
    assert f["justica"] == "federal" and f["art62Aplicado"] is True


def test_defeito5_justica_explicita_vence_a_sigla():
    """A sigla e deducao; --justica e declaracao. Declaracao ganha - inclusive
    para orgao sem sigla conhecida (TRT, TRE, vara federal com nome exotico)."""
    # TJMG forcado a federal: 11/08 volta a fechar.
    _sem_expediente(CalendarioForense(tribunal="TJMG", federal=True), "2026-08-11")
    # STJ forcado a estadual: 11/08 abre.
    _com_expediente(CalendarioForense(tribunal="STJ", federal=False), "2026-08-11")
    # Pela API publica, o mesmo caso de 03/08 muda de resposta.
    assert _venc(date(2026, 8, 3), 10, "cpc", **DISP, tribunal="TJMG",
                 justica="federal") == "2026-08-19"
    assert _venc(date(2026, 8, 3), 10, "cpc", **DISP, tribunal="TJMG") == "2026-08-18"
    # Sem sigla nenhuma, o motor assume ESTADUAL (a direcao segura).
    assert not CalendarioForense().federal
    _erro(lambda: calcular(date(2026, 8, 3), 10, "cpc", **DISP, justica="civel"),
          "justica so aceita")


# ==========================================================================
# 4. DEFEITO 4 - da para corrigir o calendario pela skill
# ==========================================================================
def test_defeito4_feriado_extra_e_exclusao_chegam_no_calculo():
    # Sem nada: disp qua 01/07/2026 TJSP, 5d -> pub 02/07, ini 03/07.
    # 03 | [09/07 e feriado estadual de SP] -> 03(1),06(2),07(3),08(4),10(5).
    assert _venc(date(2026, 7, 1), 5, "cpc", **DISP, **TJSP) == "2026-07-10"
    # Excluindo 09/07 (o tribunal abriu): 03,06,07,08,09 -> 09/07.
    assert _venc(date(2026, 7, 1), 5, "cpc", **DISP, **TJSP,
                 exclusoes={date(2026, 7, 9)}) == "2026-07-09"
    # Acrescentando 06/07 como feriado local: 03,07,08,09?,10... com 09 fora:
    # 03(1),07(2),08(3),10(4),13(5) -> 13/07.
    assert _venc(date(2026, 7, 1), 5, "cpc", **DISP, **TJSP,
                 feriados_extra={date(2026, 7, 6)}) == "2026-07-13"


def test_defeito4_calendario_do_tribunal_por_json():
    # feriados/TJMG.json traz 20/04/2026 (emenda de Tiradentes, PC 1764/2026).
    # disp sex 17/04/2026, 5d: sem o JSON, pub seria seg 20/04 -> ini 22/04
    # (21/04 Tiradentes) -> 22,23,24,27,28 -> 28/04.
    # Com o JSON, 20/04 nao tem expediente -> pub qua 22/04 -> ini qui 23/04
    # -> 23,24,27,28,29 -> qua 29/04/2026.
    assert _venc(date(2026, 4, 17), 5, "cpc", **DISP, tribunal="TJMG") == "2026-04-29"
    r = calcular(date(2026, 4, 17), 5, "cpc", **DISP, tribunal="TJMG")
    assert r["fonteCalendario"] and "1764" in r["fonteCalendario"]
    # Sem calendario do tribunal, o motor AVISA (nao cala).
    r2 = calcular(date(2026, 4, 17), 5, "cpc", **DISP, tribunal="TJSP")
    assert any("Sem calendario do TJSP" in a for a in r2["avisos"]), r2["avisos"]


# ==========================================================================
# 5. As travas (§II.4) - sao codigo, nao aviso em texto
# ==========================================================================
def _erro(fn, trecho):
    try:
        fn()
    except ValueError as e:
        assert trecho.lower() in str(e).lower(), f"mensagem inesperada: {e}"
        return
    raise AssertionError(f"deveria ter falhado por: {trecho}")


def test_trava_sem_regime_nao_calcula():
    _erro(lambda: calcular(date(2026, 7, 3), 15, ""), "regime obrigatorio")
    _erro(lambda: calcular(date(2026, 7, 3), 15, None), "regime obrigatorio")
    _erro(lambda: calcular(date(2026, 7, 3), 15, "civel"), "regime desconhecido")


def test_trava_sem_natureza_da_data_nao_calcula():
    # O risco do §I.4: "publicou dia 6" tratado como disponibilizacao vira
    # +1 dia util, na direcao TARDE.
    _erro(lambda: calcular(date(2026, 7, 6), 15, "cpc", tribunal="TJMG"),
          "natureza da data")


def test_trava_cpp_recusa_dias_uteis():
    _erro(lambda: calcular(date(2026, 8, 10), 5, "cpp-processual", unidade="uteis"),
          "nao admite contagem em dias uteis")
    _erro(lambda: calcular(date(2026, 8, 10), 5, "cp-material", unidade="uteis"),
          "nao admite contagem em dias uteis")


def test_trava_art_229_par_2_exige_saber_o_tipo_de_autos():
    _erro(lambda: calcular(date(2026, 7, 3), 15, "cpc", **DISP, tribunal="TJMG",
                           litisconsortes=True), "art. 229")


# ==========================================================================
# 6. Um caso por regime, com a conta a mao
# ==========================================================================
def test_regime_cpc_cadeia_de_dois_saltos():
    # disp sex 03/07/2026 TJMG, 15d. §2 pub seg 06/07, §3 ini ter 07/07.
    # 07,08,09,10,13,14,15,16,17,20,21,22,23,24,27 -> 15º = seg 27/07/2026.
    r = calcular(date(2026, 7, 3), 15, "cpc", **DISP, tribunal="TJMG")
    assert r["publicacao"] == "2026-07-06"
    assert r["inicioContagem"] == "2026-07-07"
    assert r["dataVencimento"] == "2026-07-27"
    # A mesma conta com a data ja sendo a publicacao: um salto a menos.
    r2 = calcular(date(2026, 7, 6), 15, "cpc", natureza="publicacao", tribunal="TJMG")
    assert r2["dataVencimento"] == "2026-07-27", r2["dataVencimento"]
    # E o erro do §I.4, se alguem mentir a natureza, custa um dia util:
    r3 = calcular(date(2026, 7, 6), 15, "cpc", **DISP, tribunal="TJMG")
    assert r3["dataVencimento"] == "2026-07-28"


def test_regime_clt_dias_uteis_art_775():
    # Recurso ordinario, 8 dias uteis. disp sex 03/07/2026 TJMG.
    # pub 06/07, ini 07/07: 07,08,09,10,13,14,15,16 -> qui 16/07/2026.
    assert _venc(date(2026, 7, 3), 8, "clt", **DISP, tribunal="TJMG") == "2026-07-16"


def test_regime_clt_suspende_por_775_A():
    # disp sex 18/12/2026 TJMG, 8 dias uteis. Recesso: pub 07/01/27, ini 21/01.
    # 21,22,25,26,27,28,29/01 = 7; 01/02 = 8 -> seg 01/02/2027.
    assert _venc(date(2026, 12, 18), 8, "clt", **DISP, tribunal="TJMG") == "2027-02-01"


def test_regime_jec_dias_uteis_art_12_A():
    # Recurso inominado 10 dias uteis. disp sex 03/07/2026 TJSP.
    # pub 06/07, ini 07/07: 07,08,[09 feriado SP],10,13,14,15,16,17,20,21
    # -> 10º = ter 21/07/2026.
    assert _venc(date(2026, 7, 3), 10, "jec", **DISP, **TJSP) == "2026-07-21"


def test_regime_cpp_dias_corridos_nao_param_no_fim_de_semana():
    # Apelacao criminal, 5 dias. Ciencia ter 04/08/2026.
    # art. 798 §1: exclui o dia do comeco -> ini qua 05/08.
    # art. 798: continuos. 05,06,07,08(sab),09(dom) -> 5º = domingo 09/08.
    # art. 798 §3: vencendo em domingo, prorroga -> seg 10/08/2026.
    r = calcular(date(2026, 8, 4), 5, "cpp-processual", **TJSP)
    assert r["inicioContagem"] == "2026-08-05"
    assert r["vencimentoAntesDaProtracao"] == "2026-08-09"
    assert r["dataVencimento"] == "2026-08-10"
    assert r["excluidos"] == [], "dias corridos nao excluem nada fora da suspensao"


def test_regime_cpp_798A_recesso_e_a_excecao_do_reu_preso():
    # Ciencia ter 15/12/2026, 30 dias corridos.
    # Com suspensao (798-A): 16,17,18,19/12 = 4 dias; para em 20/12; volta
    # 21/01 = 5º; 30º = 21/01 + 25 = seg 15/02/2027.
    assert _venc(date(2026, 12, 15), 30, "cpp-processual", **TJSP) == "2027-02-15"
    # Reu preso vinculado a prisao (798-A, I): o prazo NAO se suspende.
    # 16/12 + 29 = qui 14/01/2027.
    assert _venc(date(2026, 12, 15), 30, "cpp-processual", **TJSP,
                 sem_suspensao="reu preso (CPP art. 798-A, I)") == "2027-01-14"


def test_regime_cp_material_art_10_contra_cpp_798_MESMA_DATA():
    """O caso que prova que o motor distingue os dois. Mesma data, 5 dias."""
    proc = calcular(date(2026, 8, 10), 5, "cpp-processual", **TJSP)
    mat = calcular(date(2026, 8, 10), 5, "cp-material", **TJSP)
    # CPP art. 798 §1 EXCLUI o dia do comeco: ini ter 11/08.
    # 11,12,13,14,15 -> 5º = sabado 15/08 -> §3 prorroga -> seg 17/08/2026.
    assert proc["inicioContagem"] == "2026-08-11"
    assert proc["dataVencimento"] == "2026-08-17"
    # CP art. 10 INCLUI o dia do comeco: ini seg 10/08.
    # 10,11,12,13,14 -> 5º = sex 14/08/2026. Prazo material nao se prorroga.
    assert mat["inicioContagem"] == "2026-08-10"
    assert mat["dataVencimento"] == "2026-08-14"
    assert proc["dataVencimento"] != mat["dataVencimento"], (
        "CP art. 10 e CPP art. 798 sao regras OPOSTAS; se derem igual, "
        "o motor voltou a tratar prazo material como processual")


def test_regime_cp_material_nao_para_no_recesso_nem_prorroga():
    # Fato em 15/12/2026, decadencia de 30 dias (art. 10 inclui o dia).
    # 15/12 = 1º; 30º = 15/12 + 29 = qui 13/01/2027. Recesso nao importa.
    r = calcular(date(2026, 12, 15), 30, "cp-material", **TJSP)
    assert r["inicioContagem"] == "2026-12-15"
    assert r["dataVencimento"] == "2027-01-13"
    # E nao prorroga vencendo em domingo: fato sex 07/08/2026, 2 dias ->
    # 07(1), 08(2) = sabado. Vence no sabado mesmo.
    assert _venc(date(2026, 8, 7), 2, "cp-material", **TJSP) == "2026-08-08"


def test_regime_adm_previdenciario_30_dias_corridos():
    # Dec. 3.048/99 art. 305 §1º, II: 30 dias da ciencia da decisao.
    # Ciencia ter 15/12/2026 -> exclui o comeco, ini qua 16/12.
    # 16..31/12 = 16 dias; 01..14/01 = mais 14 -> 30º = qui 14/01/2027.
    # O CRPS nao tem recesso do Judiciario, e feriado FORENSE (11/08, 8/12)
    # nao fecha reparticao administrativa.
    r = calcular(date(2026, 12, 15), 30, "adm-previdenciario")
    assert r["inicioContagem"] == "2026-12-16"
    assert r["dataVencimento"] == "2027-01-14"


def test_regime_paf_fiscal_federal_LC227_2026():
    # Dec. 70.235/72 na redacao da LC 227/2026.
    # (a) regra geral, art. 5º, I: dias corridos, com o recesso do art. 5º-A.
    #     Ciencia 15/12/2026, 30 dias: ini 16/12; 16,17,18,19 = 4; suspende
    #     20/12-20/01; volta 21/01 = 5º; 30º = 21/01 + 25 = seg 15/02/2027.
    assert _venc(date(2026, 12, 15), 30, "adm-fiscal-federal") == "2027-02-15"
    # (b) impugnacao (art. 15) e recurso ao CARF (art. 33): 20 dias UTEIS.
    #     ini qua 16/12: 16,17,18 = 3 (19 e sabado); suspende; volta qui 21/01
    #     = 4º; 22(5); 25,26,27,28,29(10); 01,02,03,04,05/02(15);
    #     08,09,10,11,12/02(20) -> sex 12/02/2027.
    #     Carnaval NAO entra: orgao administrativo segue calendario civil.
    assert _venc(date(2026, 12, 15), 20, "adm-fiscal-federal",
                 unidade="uteis") == "2027-02-12"


def test_regime_adm_federal_prorroga_para_dia_util():
    # Lei 9.784/99 art. 66: continuos, e prorroga se vencer sem expediente.
    # Ciencia ter 04/08/2026, 5 dias: ini 05/08; 05,06,07,08,09 -> domingo
    # 09/08 -> prorroga para seg 10/08/2026.
    assert _venc(date(2026, 8, 4), 5, "adm-federal") == "2026-08-10"


# ==========================================================================
# 7. CPC art. 229 §2º - a pegadinha dos autos eletronicos
# ==========================================================================
def test_art_229_par_2_autos_eletronicos_NAO_dobram():
    base = _venc(date(2026, 7, 3), 15, "cpc", **DISP, tribunal="TJMG")
    ele = calcular(date(2026, 7, 3), 15, "cpc", **DISP, tribunal="TJMG",
                   litisconsortes=True, autos="eletronicos")
    assert ele["prazoDias"] == 15
    assert ele["dataVencimento"] == base == "2026-07-27"
    assert any("229 §2º" in a for a in ele["avisos"]), ele["avisos"]
    # Autos FISICOS: ai sim dobra (art. 229 caput). 30 dias uteis de 07/07 no
    # TJMG. 11/08 e art. 62, IV: NAO se aplica a TJ -> seg 17/08/2026.
    fis = calcular(date(2026, 7, 3), 15, "cpc", **DISP, tribunal="TJMG",
                   litisconsortes=True, autos="fisicos")
    assert fis["prazoDias"] == 30
    assert fis["dataVencimento"] == "2026-08-17"


# ==========================================================================
# 8. Saida
# ==========================================================================
def test_protocolar_ate_e_D_menos_2_uteis():
    # Venc seg 27/07/2026. D-1 = sex 24/07, D-2 = qui 23/07/2026.
    r = calcular(date(2026, 7, 3), 15, "cpc", **DISP, tribunal="TJMG")
    assert r["protocolarAte"] == "2026-07-23", r["protocolarAte"]


def test_resumo_traz_a_conta_inteira():
    r = calcular(date(2026, 8, 3), 10, "cpc", **DISP, **TRF3)
    s = r["resumo"]
    for pedaco in ("disponibilizado em 03/08/2026", "publicado em 04/08/2026",
                   "CPC art. 224 §2º", "inicio em 05/08/2026", "§3º",
                   "10 dias uteis", "CPC", "11/08", "vence em 19/08/2026"):
        assert pedaco in s, f"faltou '{pedaco}' no resumo:\n{s}"
    assert r["ressalva"], "a ressalva e obrigatoria em todo modo de saida"
    # E o mesmo caso no TJSP nao pode NEM CITAR 11/08 na conta: se citar, o
    # art. 62 voltou a vazar para a justica estadual.
    e = calcular(date(2026, 8, 3), 10, "cpc", **DISP, **TJSP)
    assert "11/08" not in e["resumo"], e["resumo"]
    assert "vence em 18/08/2026" in e["resumo"], e["resumo"]


def test_todo_regime_declara_a_base_legal():
    for chave, reg in REGIMES.items():
        assert reg.base_contagem and reg.base_suspensao and reg.base_protracao, chave


def test_vencimento_nunca_cai_em_dia_sem_expediente_nos_regimes_que_protraem():
    # Varredura, com oraculo INDEPENDENTE: uma lista literal de nao-uteis.
    # (A suite antiga usava o proprio _em_recesso como oraculo - circular.)
    # 11/08 e 08/12 saem da lista do TJSP: sao art. 62, IV, que so alcanca a
    # Justica Federal. A varredura federal logo abaixo cobre os dois.
    casos = ((TJSP, ("2026-12-25", "2027-01-01", "2026-11-02")),
             (TRF3, ("2026-12-25", "2027-01-01", "2026-11-02",
                     "2026-12-08", "2026-08-11")))
    for foro, isos in casos:
        cal = CalendarioForense(**foro)
        fechados = {date.fromisoformat(s) for s in isos}
        d = date(2026, 7, 20)
        while d <= date(2026, 12, 20):
            venc = date.fromisoformat(_venc(d, 15, "cpc", **DISP, **foro))
            assert venc.weekday() < 5, f"disp {d}: venceu no fim de semana ({venc})"
            assert venc not in fechados, f"disp {d}: venceu em feriado ({venc})"
            assert cal.tem_expediente(venc), f"disp {d}: venceu sem expediente ({venc})"
            d += timedelta(days=1)


# ==========================================================================
# 9. Pacote pago: fallback pra pasta embutida e aviso da assinatura
# ==========================================================================
def test_pacote_pago_cai_na_pasta_embutida_quando_falta_o_tribunal():
    """`--feriados <pasta paga>` com tribunal que nao esta la NAO pode virar
    "sem calendario": tem que cair no que vem embutido no plugin (hoje, TJMG)."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        pasta = Path(tmp)                       # pasta paga, vazia de TJMG
        (pasta / "TJXX.json").write_text(json.dumps(
            {"tribunal": "TJXX", "vigencia": "2026", "feriados_forenses": []}),
            encoding="utf-8")
        cal = carregar_calendario(pasta, "TJMG")
        assert cal, "nao caiu na pasta embutida: o TJMG sumiu do pacote"
        assert "1764" in cal["fonte"], f"fonte inesperada: {cal['fonte']}"
        # e o que ESTA no pacote pago continua vencendo do embutido
        assert carregar_calendario(pasta, "TJXX")["feriados"] == {}
        # tribunal que nao existe em lugar nenhum continua devolvendo vazio
        assert carregar_calendario(pasta, "TJZZ") == {}


def test_aviso_de_assinatura_em_d30_d7_e_vencida():
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        pasta = Path(tmp)
        marca = pasta / "_assinatura.json"
        hoje = date(2026, 8, 4)

        assert aviso_assinatura(pasta, hoje) == "", "avisou sem assinatura nenhuma"

        for dias, trecho in ((60, ""), (30, "30 dia"), (7, "7 dia"), (0, "0 dia")):
            marca.write_text(json.dumps(
                {"expira": (hoje + timedelta(days=dias)).isoformat()}), encoding="utf-8")
            av = aviso_assinatura(pasta, hoje)
            assert trecho in av, f"D-{dias}: esperava {trecho!r}, veio {av!r}"
            if dias == 60:
                assert av == "", f"D-60 nao devia avisar: {av!r}"

        marca.write_text(json.dumps({"expira": "2026-07-01"}), encoding="utf-8")
        assert "VENCIDA" in aviso_assinatura(pasta, hoje)

        # marca ilegivel nunca vira erro no meio de um calculo de prazo
        marca.write_text("{lixo", encoding="utf-8")
        assert aviso_assinatura(pasta, hoje) == ""


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    falhas = 0
    for fn in fns:
        try:
            fn()
            print(f"ok    {fn.__name__}")
        except AssertionError as e:
            falhas += 1
            print(f"FALHA {fn.__name__}: {e}")
    print(f"\n{len(fns) - falhas}/{len(fns)} testes passaram.")
    raise SystemExit(1 if falhas else 0)
