#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = ["holidays>=0.100"]
# ///
"""prazo_cpc.py - calcula prazo processual pelo CPC (dias uteis).

Versao standalone e enxuta da logica do motor de intimacoes do JurisTools.
Só stdlib; feriados nacionais/estaduais/facultativos entram se a lib opcional
`holidays` estiver instalada (senao, cai para o calendario conservador:
fins de semana + recesso, e AVISA que faltam os feriados).

Regras aplicadas:
- CPC art. 224 §2: publicado no 1o dia util seguinte a disponibilizacao (DJE/DJEN).
- CPC art. 224 §3: prazo comeca no 1o dia util seguinte a publicacao.
- CPC art. 219: contam-se so os dias uteis.
- CPC art. 220: recesso de 20/12 a 20/01 (suspende).

REGRA INEGOCIAVEL: o calculo e APOIO. Nunca substitui a conferencia oficial
no PJe/autos. Feriado municipal da comarca e portaria do tribunal podem nao
estar aqui; confira sempre.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta

try:
    import holidays as _holidays
except ImportError:  # holidays e opcional
    _holidays = None

RESSALVA = "CONFERIR no PJe/autos antes de agir. O calculo e apoio, nao e oficial."

# Tribunal estadual -> UF (para feriados estaduais/facultativos).
_TRIBUNAL_UF = {
    "TJAC": "AC", "TJAL": "AL", "TJAM": "AM", "TJAP": "AP", "TJBA": "BA",
    "TJCE": "CE", "TJDFT": "DF", "TJES": "ES", "TJGO": "GO", "TJMA": "MA",
    "TJMG": "MG", "TJMS": "MS", "TJMT": "MT", "TJPA": "PA", "TJPB": "PB",
    "TJPE": "PE", "TJPI": "PI", "TJPR": "PR", "TJRJ": "RJ", "TJRN": "RN",
    "TJRO": "RO", "TJRR": "RR", "TJRS": "RS", "TJSC": "SC", "TJSE": "SE",
    "TJSP": "SP", "TJTO": "TO",
}


class CalendarioForense:
    """Decide se uma data e dia util forense."""

    def __init__(self, tribunal: str = "", uf: str = "",
                 feriados_extra: set[date] | None = None):
        self.tribunal = (tribunal or "").upper()
        self.uf = (uf or _TRIBUNAL_UF.get(self.tribunal, "")).upper()
        self.extra = feriados_extra or set()
        self.tem_facultativos = False
        self.nacionais = {}
        if _holidays is not None:
            if self.uf:
                try:
                    self.nacionais = _holidays.Brazil(
                        subdiv=self.uf, categories=("public", "optional"))
                    self.tem_facultativos = True
                except Exception:
                    self.nacionais = _holidays.Brazil()
            else:
                self.nacionais = _holidays.Brazil()

    @staticmethod
    def _em_recesso(d: date) -> bool:
        # CPC art. 220: 20/12 a 20/01 (inclusive).
        return (d.month == 12 and d.day >= 20) or (d.month == 1 and d.day <= 20)

    def eh_util(self, d: date) -> bool:
        if d.weekday() >= 5:            # sabado(5)/domingo(6)
            return False
        if self._em_recesso(d):
            return False
        if d in self.extra:
            return False
        if d in self.nacionais:
            return False
        return True

    def proximo_util(self, d: date, incluir: bool = False) -> date:
        cur = d if incluir else d + timedelta(days=1)
        while not self.eh_util(cur):
            cur += timedelta(days=1)
        return cur

    def somar_uteis(self, inicio_util: date, n: int) -> date:
        """Data do n-esimo dia util contando inicio_util como o 1o dia."""
        if n <= 1:
            return inicio_util
        cur = inicio_util
        restam = n - 1
        while restam > 0:
            cur = self.proximo_util(cur)
            restam -= 1
        return cur

    def uteis_entre(self, a: date, b: date) -> int:
        """Dias uteis em (a, b]: exclui `a`, inclui `b`. Negativo se b<a."""
        if b == a:
            return 0
        sinal = 1
        if b < a:
            a, b = b, a
            sinal = -1
        cont = 0
        cur = a + timedelta(days=1)
        while cur <= b:
            if self.eh_util(cur):
                cont += 1
            cur += timedelta(days=1)
        return sinal * cont


def calcular(disponibilizacao: date, dias: int, tribunal: str = "", uf: str = "",
             ja_publicado: bool = False, hoje: date | None = None,
             feriados_extra: set[date] | None = None) -> dict:
    """Calcula o vencimento a partir da disponibilizacao (ou publicacao)."""
    cal = CalendarioForense(tribunal=tribunal, uf=uf, feriados_extra=feriados_extra)

    if ja_publicado:
        # A data informada JA e a publicacao (art. 224 §3 a partir dela).
        publicacao = disponibilizacao
    else:
        publicacao = cal.proximo_util(disponibilizacao)   # §2

    inicio = cal.proximo_util(publicacao)                 # §3
    venc = cal.somar_uteis(inicio, dias)                  # art. 219

    restantes = cal.uteis_entre(hoje, venc) if hoje else None

    aviso = None
    if _holidays is None:
        aviso = ("Lib de feriados nao instalada (pip install holidays): so "
                 "entraram fins de semana e recesso, nao os feriados nacionais/"
                 "estaduais. Calculo conservador; conferir.")
    elif not cal.tem_facultativos:
        aviso = ("Sem tribunal/UF: feriados estaduais/facultativos (Carnaval, "
                 "Corpus Christi, feriado local) nao entraram. Informe o "
                 "tribunal ou a UF. Calculo conservador; conferir.")

    return {
        "disponibilizacao": disponibilizacao.isoformat(),
        "publicacao": publicacao.isoformat(),
        "inicioContagem": inicio.isoformat(),
        "prazoDias": dias,
        "dataVencimento": venc.isoformat(),
        "diasUteisRestantes": restantes,
        "tribunal": cal.tribunal or None,
        "uf": cal.uf or None,
        "avisoCalendario": aviso,
        "ressalva": RESSALVA,
    }


def _fmt(r: dict) -> str:
    linhas = [
        f"Disponibilizacao : {r['disponibilizacao']}",
        f"Publicacao (§2)  : {r['publicacao']}",
        f"Inicio (§3)      : {r['inicioContagem']}",
        f"Prazo            : {r['prazoDias']} dias uteis (art. 219)",
        f"VENCIMENTO       : {r['dataVencimento']}",
    ]
    if r["diasUteisRestantes"] is not None:
        linhas.append(f"Dias uteis rest. : {r['diasUteisRestantes']}")
    if r["tribunal"] or r["uf"]:
        linhas.append(f"Calendario       : {r['tribunal'] or ''} {r['uf'] or ''}".rstrip())
    if r["avisoCalendario"]:
        linhas.append(f"AVISO            : {r['avisoCalendario']}")
    linhas.append(f"RESSALVA         : {r['ressalva']}")
    return "\n".join(linhas)


def _parse_data(s: str) -> date:
    return date.fromisoformat(s)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        description="Calcula prazo processual pelo CPC (dias uteis).")
    p.add_argument("--disponibilizacao", "--disp", dest="disp", required=True,
                   help="data de disponibilizacao no DJE/DJEN (YYYY-MM-DD)")
    p.add_argument("--dias", type=int, required=True,
                   help="prazo em dias uteis")
    p.add_argument("--tribunal", default="", help="sigla, ex.: TJMG, TJSP")
    p.add_argument("--uf", default="", help="UF, ex.: MG (se nao passar tribunal)")
    p.add_argument("--ja-publicado", action="store_true",
                   help="a data informada JA e a publicacao (pula o §2)")
    p.add_argument("--hoje", help="data de referencia YYYY-MM-DD (default: nao calcula restantes)")
    p.add_argument("--json", action="store_true", help="saida em JSON")
    args = p.parse_args(argv)

    r = calcular(
        disponibilizacao=_parse_data(args.disp),
        dias=args.dias,
        tribunal=args.tribunal,
        uf=args.uf,
        ja_publicado=args.ja_publicado,
        hoje=_parse_data(args.hoje) if args.hoje else None,
    )
    print(json.dumps(r, ensure_ascii=False, indent=2) if args.json else _fmt(r))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
