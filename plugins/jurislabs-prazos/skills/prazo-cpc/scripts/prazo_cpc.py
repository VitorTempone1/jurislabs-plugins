#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = ["holidays>=0.60"]
# ///
"""prazo_cpc.py - motor de prazo MULTIRREGIME (CPC, CLT, CPP, CP, JEC, administrativo).

O nome do arquivo e da skill continua `prazo-cpc` por compatibilidade com o que
ja aponta pra ca, mas o motor NAO tem regime padrao: sem `--regime` ele recusa
calcular e pergunta. Chutar CPC num prazo penal erra por dias.

So stdlib. A lib opcional `holidays` entra so pra feriado CIVIL (nacional e
estadual, categoria `public`). Sem ela, o calculo degrada AVISANDO.

Tres calendarios separados, nao um (o erro-raiz da versao anterior):

  1. HA EXPEDIENTE FORENSE?  decide a publicacao (CPC 224 §2) e o termo inicial
     (§3). Fecha em 20/12-06/01 (Res. CNJ 244/2016 art. 1º; Lei 5.010/66 art. 62, I).
  2. O PRAZO CORRE?          decide a contagem. Suspenso em 20/12-20/01 (CPC 220,
     CLT 775-A, CPP 798-A, Dec. 70.235 art. 5º-A). De 07 a 20/01 o tribunal
     ESTA ABERTO e publicando (Res. CNJ 244/2016 art. 3º, par. unico) e mesmo
     assim o prazo nao corre. Sao duas janelas, nao uma.
  3. O DIA CONTA NO REGIME?  dias uteis x dias corridos (a unidade e propriedade
     do PRAZO, nao do regime - ver o fiscal federal apos a LC 227/2026).

Camadas de feriado (§II.6 da ESPEC-PRAZOS):
  1-2. civil nacional/estadual  -> lib `holidays`, categoria `public` APENAS.
       `optional` (ponto facultativo civil: Quarta de Cinzas, Corpus Christi,
       Dia do Servidor, vesperas) NAO e suspensao forense e ficou de fora.
  3.   forense nacional         -> Lei 5.010/66 art. 62, tabela nossa aqui.
  4-5. forense do tribunal      -> feriados/<TRIBUNAL>.json (portaria) + exclusoes.
  6.   comarca                  -> nao automatizavel; vira ressalva.

REGRA INEGOCIAVEL: o calculo e APOIO. Nunca substitui a conferencia oficial no
PJe/autos. Feriado municipal da comarca, portaria pontual e indisponibilidade do
sistema (CPC 224 §1) podem nao estar aqui.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, replace
from datetime import date, timedelta
from pathlib import Path

try:
    import holidays as _holidays
except ImportError:  # holidays e opcional
    _holidays = None

RESSALVA = ("CONFERIR no PJe/autos antes de agir. O calculo e apoio, nao e oficial. "
            "Feriado municipal da comarca, portaria pontual do tribunal e "
            "indisponibilidade do sistema (CPC 224 §1) podem nao estar aqui.")

DIAS_SEMANA = ("seg", "ter", "qua", "qui", "sex", "sab", "dom")

# --- II.7: parametrizavel, nunca fixo no meio do codigo ----------------------
# Recesso COM tribunal fechado (nao ha expediente, nao ha publicacao nem intimacao).
# Res. CNJ 244/2016 art. 1º e art. 2º; Lei 5.010/66 art. 62, I.
RECESSO_SEM_EXPEDIENTE = ((12, 20), (1, 6))
# Suspensao da CONTAGEM. Janela diferente e maior. De 07 a 20/01 ha expediente.
RECESSO_SUSPENSAO = ((12, 20), (1, 20))
# `PROTOCOLAR ATE` = vencimento menos N dias uteis (AGENTS.md §4.6).
FOLGA_PROTOCOLO = 2

_TRIBUNAL_UF = {
    "TJAC": "AC", "TJAL": "AL", "TJAM": "AM", "TJAP": "AP", "TJBA": "BA",
    "TJCE": "CE", "TJDFT": "DF", "TJES": "ES", "TJGO": "GO", "TJMA": "MA",
    "TJMG": "MG", "TJMS": "MS", "TJMT": "MT", "TJPA": "PA", "TJPB": "PB",
    "TJPE": "PE", "TJPI": "PI", "TJPR": "PR", "TJRJ": "RJ", "TJRN": "RN",
    "TJRO": "RO", "TJRR": "RR", "TJRS": "RS", "TJSC": "SC", "TJSE": "SE",
    "TJSP": "SP", "TJTO": "TO",
}

DIR_FERIADOS_PADRAO = Path(__file__).resolve().parent.parent / "feriados"


# --------------------------------------------------------------------------
# Regimes
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Regime:
    chave: str
    nome: str
    unidade: str                  # "uteis" | "corridos"
    unidade_travada: bool         # True = recusa trocar a unidade
    base_contagem: str
    inclui_dia_comeco: bool       # CP art. 10
    cadeia_224: bool              # aplica CPC 224 §§2-3 (disponibilizacao -> publicacao)
    inicio_exige_expediente: bool
    suspensao: tuple | None       # RECESSO_SUSPENSAO ou None
    base_suspensao: str
    protrai_vencimento: bool
    base_protracao: str
    excecoes_suspensao: str = ""
    # True  = calendario FORENSE (Lei 5.010/66 art. 62 + recesso do tribunal).
    # False = orgao administrativo (INSS, CARF, Receita): so o calendario CIVIL.
    # O feriado forense nao fecha reparticao administrativa; aplicar 11/08 ou o
    # recesso do Judiciario a um prazo de CARF empurra o vencimento pra frente,
    # que e a direcao fatal.
    calendario_forense: bool = True


REGIMES: dict[str, Regime] = {
    "cpc": Regime(
        chave="cpc", nome="CPC - processo civil",
        unidade="uteis", unidade_travada=False,
        base_contagem="CPC art. 219 (so dias uteis, prazo processual)",
        inclui_dia_comeco=False, cadeia_224=True, inicio_exige_expediente=True,
        suspensao=RECESSO_SUSPENSAO, base_suspensao="CPC art. 220",
        protrai_vencimento=True, base_protracao="CPC art. 224 §1",
    ),
    "clt": Regime(
        chave="clt", nome="CLT - processo do trabalho",
        unidade="uteis", unidade_travada=False,
        base_contagem="CLT art. 775 (dias uteis, Lei 13.467/2017)",
        inclui_dia_comeco=False, cadeia_224=True, inicio_exige_expediente=True,
        suspensao=RECESSO_SUSPENSAO,
        base_suspensao="CLT art. 775-A (Lei 13.545/2017)",
        protrai_vencimento=True, base_protracao="CLT art. 775 c/c CPC art. 224 §1",
    ),
    "jec": Regime(
        chave="jec", nome="JEC - Juizados Especiais Civeis",
        unidade="uteis", unidade_travada=False,
        base_contagem="Lei 9.099/95 art. 12-A (Lei 13.728/2018)",
        inclui_dia_comeco=False, cadeia_224=True, inicio_exige_expediente=True,
        suspensao=RECESSO_SUSPENSAO, base_suspensao="CPC art. 220",
        protrai_vencimento=True, base_protracao="CPC art. 224 §1",
    ),
    "cpp-processual": Regime(
        chave="cpp-processual", nome="CPP - penal PROCESSUAL",
        unidade="corridos", unidade_travada=True,
        base_contagem=("CPP art. 798 (continuos e peremptorios, nao se "
                       "interrompem por ferias, domingo ou feriado)"),
        inclui_dia_comeco=False, cadeia_224=False, inicio_exige_expediente=False,
        suspensao=RECESSO_SUSPENSAO,
        base_suspensao="CPP art. 798-A (Lei 14.365/2022)",
        protrai_vencimento=True, base_protracao="CPP art. 798 §3",
        excecoes_suspensao=("NAO se suspende: I reu preso, nos processos "
                            "vinculados a essa prisao; II Lei 11.340/2006 "
                            "(Maria da Penha); III medidas urgentes, por "
                            "despacho fundamentado. Use --sem-suspensao MOTIVO."),
    ),
    "cp-material": Regime(
        chave="cp-material", nome="CP - penal MATERIAL (prescricao, decadencia)",
        unidade="corridos", unidade_travada=True,
        base_contagem="CP art. 10 (calendario comum)",
        inclui_dia_comeco=True, cadeia_224=False, inicio_exige_expediente=False,
        suspensao=None,
        base_suspensao="prazo material nao se suspende por recesso nem feriado",
        protrai_vencimento=False,
        base_protracao="prazo material nao se prorroga (nao ha CPP 798 §3 aqui)",
    ),
    "adm-federal": Regime(
        chave="adm-federal", nome="Administrativo federal geral (Lei 9.784/1999)",
        unidade="corridos", unidade_travada=False,
        base_contagem="Lei 9.784/99 art. 66 (prazos continuos)",
        inclui_dia_comeco=False, cadeia_224=False, inicio_exige_expediente=True,
        suspensao=None, base_suspensao="nao ha recesso na Lei 9.784/99",
        protrai_vencimento=True, base_protracao="Lei 9.784/99 art. 66 §1",
        calendario_forense=False,
    ),
    "adm-previdenciario": Regime(
        chave="adm-previdenciario",
        nome="Administrativo previdenciario (INSS / CRPS)",
        unidade="corridos", unidade_travada=False,
        base_contagem=("Dec. 3.048/99 art. 305 §1º (30 dias) c/c Lei 9.784/99 "
                       "art. 66 (continuos)"),
        inclui_dia_comeco=False, cadeia_224=False, inicio_exige_expediente=True,
        suspensao=None, base_suspensao="nao ha recesso no rito do CRPS",
        protrai_vencimento=True, base_protracao="Lei 9.784/99 art. 66 §1",
        excecoes_suspensao=("Prazos de RITO do CRPS vem do Regimento Interno "
                            "(Portaria MPS 125/2026, ja alterada em 2026) e "
                            "mudam por portaria - conferir, nao estao aqui."),
        calendario_forense=False,
    ),
    "adm-fiscal-federal": Regime(
        chave="adm-fiscal-federal",
        nome="Fiscal federal - PAF (Dec. 70.235/72, redacao da LC 227/2026)",
        unidade="corridos", unidade_travada=False,
        base_contagem=("Dec. 70.235/72 art. 5º, I (dias corridos, SALVO "
                       "disposicao em contrario) e II (exclui o dia do inicio)"),
        inclui_dia_comeco=False, cadeia_224=False, inicio_exige_expediente=True,
        suspensao=RECESSO_SUSPENSAO,
        base_suspensao="Dec. 70.235/72 art. 5º-A (incluido pela LC 227/2026)",
        protrai_vencimento=True, base_protracao="Dec. 70.235/72 art. 5º",
        excecoes_suspensao=(
            "REGIME MISTO. Sao 20 DIAS UTEIS: impugnacao (art. 15) e recurso "
            "voluntario ao CARF (art. 33); e 10 dias uteis o prazo residual "
            "(art. 5º-B) - tudo na redacao da LC 227/2026, em vigor desde a "
            "publicacao (DOU 14/01/2026). Nesses casos passe --unidade uteis. "
            "Direito intertemporal de prazo em curso em 14/01/2026 esta em "
            "aberto na LC - conferir antes de recalcular processo antigo."),
        calendario_forense=False,
    ),
}


# --------------------------------------------------------------------------
# Camada 3: feriado forense nacional (Lei 5.010/66 art. 62)
# --------------------------------------------------------------------------
def pascoa(ano: int) -> date:
    """Domingo de Pascoa (algoritmo gregoriano anonimo)."""
    a = ano % 19
    b, c = divmod(ano, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mes, dia = divmod(h + l - 7 * m + 114, 31)
    return date(ano, mes, dia + 1)


def feriados_forenses_nacionais(ano: int) -> dict[date, str]:
    """Lei 5.010/66 art. 62, incisos II, III e IV.

    O inciso I (20/12 a 06/01) e janela, nao data solta: vive em
    RECESSO_SEM_EXPEDIENTE. Note o que a lei NAO lista: Quarta-feira de Cinzas
    e Corpus Christi. Esses dependem de portaria do tribunal (camada 4).
    """
    p = pascoa(ano)
    fer: dict[date, str] = {}
    for n in range(4, -1, -1):  # quarta-feira ... domingo de Pascoa
        fer[p - timedelta(days=n)] = "Semana Santa (Lei 5.010/66 art. 62, II)"
    fer[p - timedelta(days=48)] = "Carnaval - segunda (Lei 5.010/66 art. 62, III)"
    fer[p - timedelta(days=47)] = "Carnaval - terca (Lei 5.010/66 art. 62, III)"
    for mes, dia, nome in ((8, 11, "Dia do Advogado / criacao dos cursos juridicos"),
                           (11, 1, "1º de novembro"),
                           (11, 2, "Finados"),
                           (12, 8, "8 de dezembro")):
        fer[date(ano, mes, dia)] = f"{nome} (Lei 5.010/66 art. 62, IV)"
    return fer


def _na_janela(d: date, janela: tuple) -> bool:
    (m1, d1), (m2, d2) = janela
    return (d.month == m1 and d.day >= d1) or (d.month == m2 and d.day <= d2)


# --------------------------------------------------------------------------
# Calendario
# --------------------------------------------------------------------------
class CalendarioForense:
    """Responde UMA pergunta: nesta data ha expediente forense?

    Nao sabe nada de contagem de prazo - quem decide se o prazo corre e o
    regime. Fundir as duas coisas foi o Defeito 1 da versao anterior.
    """

    def __init__(self, tribunal: str = "", uf: str = "",
                 feriados_extra=None, exclusoes=None,
                 fonte: str = "", vigencia: str = "", forense: bool = True):
        self.forense = forense
        self.tribunal = (tribunal or "").upper()
        self.uf = (uf or _TRIBUNAL_UF.get(self.tribunal, "")).upper()
        self.fonte = fonte
        self.vigencia = vigencia
        if isinstance(feriados_extra, (set, list, tuple)):
            self.extra = {d: "feriado informado (--feriado-extra)" for d in feriados_extra}
        else:
            self.extra = dict(feriados_extra or {})
        self.exclusoes = set(exclusoes or ())
        self.uf_carregada = False
        # None, nao {}: um objeto `holidays` ainda nao populado e FALSY, entao
        # `if self._civis` engoliria o calendario civil inteiro em silencio.
        self._civis = None
        self._forenses: dict[int, dict[date, str]] = {}
        if _holidays is not None:
            if self.uf:
                try:
                    self._civis = _holidays.Brazil(subdiv=self.uf, categories=("public",))
                    self.uf_carregada = True
                except Exception:
                    self._civis = _holidays.Brazil(categories=("public",))
            else:
                self._civis = _holidays.Brazil(categories=("public",))

    def _forense(self, ano: int) -> dict[date, str]:
        if ano not in self._forenses:
            self._forenses[ano] = feriados_forenses_nacionais(ano)
        return self._forenses[ano]

    def motivo_sem_expediente(self, d: date) -> str | None:
        """None = tem expediente. Senao, o motivo, ja citado."""
        if d in self.exclusoes:          # camada 5 vence tudo: o tribunal abriu
            return None
        if d.weekday() >= 5:
            return "sabado/domingo"
        if self.forense and _na_janela(d, RECESSO_SEM_EXPEDIENTE):
            return ("recesso forense - tribunal fechado (Res. CNJ 244/2016 "
                    "arts. 1º e 2º; Lei 5.010/66 art. 62, I)")
        if d in self.extra:
            return self.extra[d]
        f = self._forense(d.year).get(d) if self.forense else None
        if f:
            return f
        nome = self._civis.get(d) if self._civis is not None else None
        if nome:
            return f"{nome} (feriado civil)"
        return None

    def tem_expediente(self, d: date) -> bool:
        return self.motivo_sem_expediente(d) is None

    def proximo_expediente(self, d: date, incluir: bool = False) -> date:
        cur = d if incluir else d + timedelta(days=1)
        while not self.tem_expediente(cur):
            cur += timedelta(days=1)
        return cur


# --------------------------------------------------------------------------
# Calendario do tribunal (camadas 4 e 5)
# --------------------------------------------------------------------------
def carregar_calendario(caminho, tribunal: str = "") -> dict:
    """Le feriados/<TRIBUNAL>.json. `caminho` pode ser o arquivo ou a pasta."""
    p = Path(caminho)
    if p.is_dir():
        if not tribunal:
            return {}
        p = p / f"{tribunal.upper()}.json"
    if not p.is_file():
        return {}
    dados = json.loads(p.read_text(encoding="utf-8"))
    ref = dados.get("_referencia", {})
    for k, v in dados.items():          # aceita _referencia_2026, _referencia_2027...
        if k.startswith("_referencia") and isinstance(v, dict):
            ref = {**ref, **v}
    feriados = {}
    for s in dados.get("feriados_forenses", []):
        d = date.fromisoformat(s)
        motivo = ref.get(s) or f"feriado forense do {dados.get('tribunal', tribunal)}"
        feriados[d] = motivo
    return {
        "feriados": feriados,
        "exclusoes": {date.fromisoformat(s) for s in dados.get("exclusoes", [])},
        "fonte": dados.get("_fonte", ""),
        "vigencia": str(dados.get("vigencia", "")),
        "arquivo": str(p),
    }


# --------------------------------------------------------------------------
# Motor
# --------------------------------------------------------------------------
def _conta_no_prazo(cal: CalendarioForense, regime: Regime, d: date,
                    suspende: bool) -> bool:
    if suspende and regime.suspensao and _na_janela(d, regime.suspensao):
        return False
    if regime.unidade == "uteis":
        return cal.tem_expediente(d)
    return True                       # corridos: todo dia conta


def _motivo_nao_conta(cal, regime, d, suspende) -> str:
    if suspende and regime.suspensao and _na_janela(d, regime.suspensao):
        return f"prazo suspenso ({regime.base_suspensao})"
    return cal.motivo_sem_expediente(d) or "?"


def calcular(data: date, dias: int, regime: str, *, natureza: str = "",
             tribunal: str = "", uf: str = "", unidade: str = "",
             hoje: date | None = None, feriados_extra=None, exclusoes=None,
             dir_feriados=None, sem_suspensao: str = "",
             litisconsortes: bool = False, autos: str = "",
             folga: int = FOLGA_PROTOCOLO) -> dict:
    """Calcula o vencimento. `regime` e OBRIGATORIO e nao tem valor padrao.

    A trava do §II.4 e tecnica, nao aviso em texto: sem regime, levanta erro.
    """
    if not regime:
        raise ValueError(
            "Regime obrigatorio - o motor nao tem padrao e nao chuta CPC. "
            "Escolha: " + ", ".join(REGIMES))
    if regime not in REGIMES:
        raise ValueError(f"Regime desconhecido: {regime!r}. Use um de: "
                         + ", ".join(REGIMES))
    reg = REGIMES[regime]
    if dias < 1:
        raise ValueError("dias tem que ser >= 1")

    if unidade and unidade != reg.unidade:
        if reg.unidade_travada:
            raise ValueError(
                f"{reg.nome} nao admite contagem em dias {unidade}. "
                f"Base: {reg.base_contagem}")
        reg = replace(reg, unidade=unidade)

    if reg.cadeia_224 and natureza not in ("disponibilizacao", "publicacao"):
        raise ValueError(
            "Informe a natureza da data: 'disponibilizacao' (o que o DJEN "
            "devolve) ou 'publicacao'. Errar aqui vale um dia util de prazo, "
            "e o motor nao adivinha.")

    dobro_nota = None
    if litisconsortes:
        if autos not in ("fisicos", "eletronicos"):
            raise ValueError(
                "Prazo em dobro por litisconsortes (CPC art. 229) exige saber "
                "se os autos sao 'fisicos' ou 'eletronicos': o §2º do art. 229 "
                "EXCLUI o dobro em autos eletronicos. Passe --autos.")
        if autos == "eletronicos":
            dobro_nota = ("Litisconsortes com procuradores diferentes, mas autos "
                          "ELETRONICOS: prazo NAO dobra (CPC art. 229 §2º). "
                          "Prazo simples aplicado.")
        else:
            dias *= 2
            dobro_nota = (f"Autos FISICOS + litisconsortes com procuradores "
                          f"diferentes: prazo em dobro (CPC art. 229). "
                          f"{dias // 2} -> {dias} dias.")

    cal_trib = carregar_calendario(
        dir_feriados if dir_feriados is not None else DIR_FERIADOS_PADRAO, tribunal)
    fer = dict(cal_trib.get("feriados", {}))
    if feriados_extra:
        if isinstance(feriados_extra, dict):
            fer.update(feriados_extra)
        else:
            fer.update({d: "feriado informado (--feriado-extra)" for d in feriados_extra})
    exc = set(cal_trib.get("exclusoes", set())) | set(exclusoes or ())

    cal = CalendarioForense(tribunal=tribunal, uf=uf, feriados_extra=fer,
                            exclusoes=exc, fonte=cal_trib.get("fonte", ""),
                            vigencia=cal_trib.get("vigencia", ""),
                            forense=reg.calendario_forense)

    suspende = reg.suspensao is not None and not sem_suspensao

    # --- termo inicial -----------------------------------------------------
    publicacao = None
    if reg.cadeia_224:
        publicacao = data if natureza == "publicacao" else cal.proximo_expediente(data)
        inicio = cal.proximo_expediente(publicacao)          # §3
    elif reg.inclui_dia_comeco:
        inicio = data                                        # CP art. 10
    else:
        inicio = data + timedelta(days=1)                    # exclui o dia do comeco
        if reg.inicio_exige_expediente:
            inicio = cal.proximo_expediente(inicio, incluir=True)
    inicio_224 = inicio
    while not _conta_no_prazo(cal, reg, inicio, suspende):   # recesso / suspensao
        inicio += timedelta(days=1)

    # --- contagem ----------------------------------------------------------
    excluidos: list[tuple[date, str]] = []
    contados, cur, venc = 0, inicio, inicio
    while contados < dias:
        if _conta_no_prazo(cal, reg, cur, suspende):
            contados += 1
            venc = cur
        else:
            excluidos.append((cur, _motivo_nao_conta(cal, reg, cur, suspende)))
        cur += timedelta(days=1)

    venc_bruto = venc
    if reg.protrai_vencimento and not cal.tem_expediente(venc):
        venc = cal.proximo_expediente(venc)

    # --- protocolar ate (D-N uteis) ----------------------------------------
    protocolar = venc
    for _ in range(max(folga, 0)):
        protocolar -= timedelta(days=1)
        while not cal.tem_expediente(protocolar):
            protocolar -= timedelta(days=1)

    restantes = None
    if hoje:
        restantes, c = 0, hoje + timedelta(days=1)
        while c <= venc:
            if _conta_no_prazo(cal, reg, c, suspende):
                restantes += 1
            c += timedelta(days=1)

    # --- avisos ------------------------------------------------------------
    avisos = []
    if _holidays is None:
        avisos.append("Lib de feriados civis nao instalada (pip install holidays): "
                      "entraram fins de semana, o recesso e os feriados forenses da "
                      "Lei 5.010/66, mas NAO os feriados civis nacionais/estaduais. "
                      "Calculo conservador; conferir.")
    elif not cal.uf_carregada:
        avisos.append("Sem tribunal/UF valido: feriado ESTADUAL nao entrou. "
                      "Informe --tribunal ou --uf. Calculo conservador; conferir.")
    if not cal_trib:
        avisos.append(
            f"Sem calendario do {cal.tribunal or 'tribunal'} "
            f"(feriados/{(cal.tribunal or 'TJXX')}.json nao encontrado): Quarta de "
            "Cinzas, Corpus Christi, emendas, Dia do Servidor transferido e "
            "feriado local NAO entraram. O vencimento pode sair mais CEDO que o "
            "real. Conferir no PJe.")
    elif cal.vigencia and cal.vigencia != str(venc.year):
        avisos.append(f"Calendario do {cal.tribunal} tem vigencia {cal.vigencia} e o "
                      f"prazo vence em {venc.year}. Calendario vencido nao vale; "
                      "atualizar pela portaria do ano.")
    if sem_suspensao:
        avisos.append(f"Suspensao do recesso DESLIGADA a pedido: {sem_suspensao}. "
                      f"Base da excecao: {reg.excecoes_suspensao or reg.base_suspensao}")
    if reg.chave == "cpp-processual" and suspende:
        avisos.append("CPP art. 798-A tem excecoes (reu preso vinculado a prisao, "
                      "Maria da Penha, medidas urgentes). Se for o caso, use "
                      "--sem-suspensao MOTIVO: o prazo corre no recesso.")
    if dobro_nota:
        avisos.append(dobro_nota)

    resumo = _resumo(reg, data, natureza, publicacao, inicio, dias, excluidos, venc)

    return {
        "regime": reg.chave,
        "regimeNome": reg.nome,
        "baseContagem": reg.base_contagem,
        "unidade": reg.unidade,
        "natureza": natureza or "ciencia/intimacao",
        "dataInformada": data.isoformat(),
        "publicacao": publicacao.isoformat() if publicacao else None,
        "inicioContagem": inicio.isoformat(),
        "inicioAntesDaSuspensao": inicio_224.isoformat(),
        "prazoDias": dias,
        "dataVencimento": venc.isoformat(),
        "vencimentoAntesDaProtracao": venc_bruto.isoformat(),
        "protrairam": venc != venc_bruto,
        "protocolarAte": protocolar.isoformat(),
        "folgaDiasUteis": folga,
        "diasRestantes": restantes,
        "excluidos": [{"data": d.isoformat(), "motivo": m} for d, m in excluidos],
        "tribunal": cal.tribunal or None,
        "uf": cal.uf or None,
        "fonteCalendario": cal.fonte or None,
        "vigenciaCalendario": cal.vigencia or None,
        "avisos": avisos,
        "resumo": resumo,
        "ressalva": RESSALVA,
    }


def _br(d: date) -> str:
    return f"{DIAS_SEMANA[d.weekday()]} {d.strftime('%d/%m/%Y')}"


def _resumo(reg, data, natureza, publicacao, inicio, dias, excluidos, venc) -> str:
    """A linha obrigatoria: a conta inteira, sempre visivel."""
    feriados = [f"{d.strftime('%d/%m')} ({m})" for d, m in excluidos
                if "sabado/domingo" not in m]
    lista = ", ".join(feriados) if feriados else "nenhum feriado no periodo"
    if publicacao:
        cabeca = (f"{'publicado' if natureza == 'publicacao' else 'disponibilizado'} "
                  f"em {data.strftime('%d/%m/%Y')}")
        if natureza != "publicacao":
            cabeca += f" -> publicado em {publicacao.strftime('%d/%m/%Y')} (CPC art. 224 §2º)"
        cabeca += f" -> inicio em {inicio.strftime('%d/%m/%Y')} (§3º)"
    else:
        rotulo = ("o proprio dia do fato, CP art. 10 INCLUI o dia do comeco"
                  if reg.inclui_dia_comeco else "exclui o dia do comeco")
        cabeca = (f"ciencia em {data.strftime('%d/%m/%Y')} -> inicio em "
                  f"{inicio.strftime('%d/%m/%Y')} ({rotulo})")
    return (f"{cabeca} -> {dias} dias {reg.unidade} no regime "
            f"{reg.chave.upper()}, excluidos {lista} -> vence em "
            f"{venc.strftime('%d/%m/%Y')}")


def _fmt(r: dict) -> str:
    L = [f"REGIME       : {r['regimeNome']} - dias {r['unidade']}",
         f"               {r['baseContagem']}"]
    cal = " ".join(x for x in (r["tribunal"], f"({r['uf']})" if r["uf"] else "") if x)
    L.append(f"Tribunal     : {cal or 'NAO INFORMADO'}"
             + (f" - calendario: {r['fonteCalendario']}" if r["fonteCalendario"] else ""))
    L.append("")
    rotulo = {"disponibilizacao": "Disponibilizado em",
              "publicacao": "Publicado em"}.get(r["natureza"], "Ciencia / intimacao em")
    L.append(f"{rotulo:<20}: {_br(date.fromisoformat(r['dataInformada']))}")
    if r["publicacao"] and r["natureza"] != "publicacao":
        L.append(f"{'Publicado em':<20}: {_br(date.fromisoformat(r['publicacao']))}"
                 "   (CPC art. 224 §2 - 1º dia util seguinte)")
    if r["publicacao"]:
        L.append(f"{'Inicio da contagem':<20}: "
                 f"{_br(date.fromisoformat(r['inicioContagem']))}"
                 "   (CPC art. 224 §3)")
    else:
        L.append(f"{'Inicio da contagem':<20}: "
                 f"{_br(date.fromisoformat(r['inicioContagem']))}")
    L.append(f"{'Prazo':<20}: {r['prazoDias']} dias {r['unidade']}")
    L.append("")
    if r["excluidos"]:
        L.append("Excluidos da contagem:")
        fds = [e for e in r["excluidos"] if "sabado/domingo" in e["motivo"]]
        outros = [e for e in r["excluidos"] if "sabado/domingo" not in e["motivo"]]
        if fds:
            L.append(f"  sab/dom            {len(fds)} dias")
        for e in outros:
            L.append(f"  {date.fromisoformat(e['data']).strftime('%d/%m/%Y')}"
                     f"         {e['motivo']}")
    else:
        L.append("Nenhum dia excluido - prazo continuo.")
    L.append("")
    for a in r["avisos"]:
        L.append(f"AVISO        : {a}")
    if r["avisos"]:
        L.append("")
    L.append(f"VENCE EM            : {_br(date.fromisoformat(r['dataVencimento']))}")
    if r["protrairam"]:
        L.append(f"  (protraido de {r['vencimentoAntesDaProtracao']} - caiu em dia "
                 "sem expediente)")
    L.append(f"PROTOCOLAR ATE      : {_br(date.fromisoformat(r['protocolarAte']))}"
             f"   (D-{r['folgaDiasUteis']} uteis)")
    if r["diasRestantes"] is not None:
        L.append(f"Dias restantes      : {r['diasRestantes']}")
    L.append("")
    L.append(f"CONTA: {r['resumo']}")
    L.append("")
    L.append(f"RESSALVA: {r['ressalva']}")
    return "\n".join(L)


def _parse_data(s: str) -> date:
    return date.fromisoformat(s)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        description="Motor de prazo multirregime. SEM --regime ele nao calcula.",
        epilog="Regimes: " + ", ".join(REGIMES))
    p.add_argument("--regime", choices=sorted(REGIMES),
                   help="OBRIGATORIO. Nao ha padrao: chutar CPC num prazo penal "
                        "erra por dias.")
    p.add_argument("--data", "--disp", dest="data", required=True,
                   help="a data de referencia (YYYY-MM-DD)")
    p.add_argument("--natureza", choices=("disponibilizacao", "publicacao", "ciencia"),
                   default="", help="o que a data e. Obrigatorio em CPC/CLT/JEC.")
    p.add_argument("--dias", type=int, required=True, help="tamanho do prazo")
    p.add_argument("--unidade", choices=("uteis", "corridos"), default="",
                   help="sobrepoe a unidade do regime (ex.: PAF art. 15/33 = uteis)")
    p.add_argument("--tribunal", default="", help="sigla, ex.: TJMG, TJSP")
    p.add_argument("--uf", default="", help="UF, se nao passar tribunal")
    p.add_argument("--feriados", default="",
                   help="arquivo ou pasta com <TRIBUNAL>.json (default: ../feriados)")
    p.add_argument("--feriado-extra", action="append", default=[], metavar="AAAA-MM-DD",
                   help="feriado forense a mais (repetivel)")
    p.add_argument("--excluir", action="append", default=[], metavar="AAAA-MM-DD",
                   help="data que a lib marca como feriado mas TEM expediente (repetivel)")
    p.add_argument("--sem-suspensao", default="", metavar="MOTIVO",
                   help="desliga o recesso (CPP 798-A: reu preso, Maria da Penha, "
                        "medida urgente)")
    p.add_argument("--litisconsortes", action="store_true",
                   help="litisconsortes com procuradores diferentes (CPC art. 229)")
    p.add_argument("--autos", choices=("fisicos", "eletronicos"), default="",
                   help="exigido com --litisconsortes: o §2º do art. 229 exclui o "
                        "dobro em autos eletronicos")
    p.add_argument("--folga", type=int, default=FOLGA_PROTOCOLO,
                   help=f"dias uteis de folga do PROTOCOLAR ATE (default {FOLGA_PROTOCOLO})")
    p.add_argument("--hoje", help="data de referencia para os dias restantes")
    p.add_argument("--json", action="store_true", help="saida em JSON")
    args = p.parse_args(argv)

    if not args.regime:
        p.error(
            "--regime e obrigatorio e nao tem padrao.\n"
            "  cpc                 civel, dias UTEIS, para no recesso 20/12-20/01\n"
            "  clt                 trabalhista, dias uteis (art. 775)\n"
            "  jec                 juizado especial civel, dias uteis (art. 12-A)\n"
            "  cpp-processual      penal, dias CORRIDOS (art. 798), nao para em feriado\n"
            "  cp-material         prescricao/decadencia, corridos e INCLUI o dia do "
            "comeco (art. 10)\n"
            "  adm-federal         Lei 9.784/99, corridos\n"
            "  adm-previdenciario  INSS/CRPS, corridos (Dec. 3.048/99 art. 305 §1º)\n"
            "  adm-fiscal-federal  PAF, Dec. 70.235/72 na redacao da LC 227/2026\n"
            "Chutar CPC num prazo penal atrasa o calculo em dias e faz perder o prazo.")

    natureza = args.natureza
    if natureza == "ciencia":
        natureza = ""
    try:
        r = calcular(
            data=_parse_data(args.data), dias=args.dias, regime=args.regime,
            natureza=natureza, tribunal=args.tribunal, uf=args.uf,
            unidade=args.unidade,
            hoje=_parse_data(args.hoje) if args.hoje else None,
            feriados_extra={_parse_data(s): "feriado informado (--feriado-extra)"
                            for s in args.feriado_extra},
            exclusoes={_parse_data(s) for s in args.excluir},
            dir_feriados=args.feriados or None,
            sem_suspensao=args.sem_suspensao,
            litisconsortes=args.litisconsortes, autos=args.autos,
            folga=args.folga,
        )
    except ValueError as e:
        print(f"ERRO: {e}", file=sys.stderr)
        return 2
    print(json.dumps(r, ensure_ascii=False, indent=2) if args.json else _fmt(r))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
