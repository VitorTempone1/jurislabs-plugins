#!/usr/bin/env python3
"""Baixa os calendarios forenses do pacote pago pra ${CLAUDE_PLUGIN_DATA}/feriados.

Roda como hook SessionStart do plugin `jurislabs-prazos`. Tres regras valem mais
que o codigo:

1. **Nunca apaga o cache.** Assinatura vencida (404/403) mantem o que ja foi
   baixado. Quem avisa que envelheceu e o motor: pelo `vigencia` de cada JSON e
   pelo `_assinatura.json` que este script grava. Degrada avisando, nunca some
   em silencio.
2. **Nunca quebra a sessao.** Qualquer erro sai 0 e calado. Hook de sessao que
   estoura vira ruido em toda abertura do Claude Code.
3. **Nunca aceita JSON malformado por cima de um bom.** Chave escrita errada faz
   `carregar_calendario()` devolver lista vazia SEM erro, e o motor calcula
   feliz, sem nenhum feriado local: prazo errado, que e o unico dano
   irreversivel do produto. Arquivo que nao passa na conferencia e descartado e
   o anterior fica.

O token so chega aqui: `userConfig` com `sensitive: true` nao interpola em
skill, agent nem comando de shell (rejeitado desde a v2.1.207). O processo de
hook e o unico que recebe, como CLAUDE_PLUGIN_OPTION_CALENDARIO_TOKEN.

Uso (o hooks.json passa o ${CLAUDE_PLUGIN_DATA} como argumento):

    python3 baixar_calendarios.py <pasta-de-dados>
    python3 baixar_calendarios.py --autoteste
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path

# Endpoint estatico na VPS: servico proprio (`juris-cal`, 127.0.0.1:8899) atras
# do mesmo Cloudflare Tunnel do juris-motor. Nao e o motor: aquele e fail-closed
# com Bearer e processa documento de cliente. Layout servido:
# <URL_BASE>/<token>/index.json e <URL_BASE>/<token>/<TRIBUNAL>.json.
# Revogar assinatura = apagar a pasta do token no servidor.
URL_PADRAO = "https://calendario.jurislabs.com.br"
URL_BASE = (os.environ.get("JURISLABS_CAL_URL") or URL_PADRAO).rstrip("/")

INTERVALO_HORAS = 24          # SessionStart roda o tempo todo; 1 sync por dia basta
TIMEOUT = 8                   # segundos por arquivo
MARCA = "_assinatura.json"    # `_` na frente: o test_calendarios.py ignora


# --------------------------------------------------------------------------
def _baixar(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "jurislabs-prazos"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:   # noqa: S310
        return r.read()


def _fresco(marca: Path, agora: datetime | None = None) -> bool:
    """Ja sincronizou nas ultimas INTERVALO_HORAS?"""
    if not marca.is_file():
        return False
    agora = agora or datetime.now()
    idade = agora - datetime.fromtimestamp(marca.stat().st_mtime)
    return idade < timedelta(hours=INTERVALO_HORAS)


def calendario_valido(bruto: bytes) -> bool:
    """Conferencia minima antes de sobrescrever um calendario que ja funciona.

    Pega o modo de falha silencioso: `feriados_forense` no singular, `vigencia`
    faltando, data invalida. O `test_calendarios.py` (que roda ANTES de semear,
    do nosso lado) e o cinto; isto aqui e o suspensorio.
    """
    try:
        dados = json.loads(bruto)
        feriados = dados["feriados_forenses"]
        if not isinstance(feriados, list):
            return False
        for s in feriados:
            date.fromisoformat(s)
        return bool(dados.get("tribunal")) and bool(dados.get("vigencia"))
    except Exception:
        return False


def _escrever(destino: Path, conteudo: bytes) -> None:
    """Grava atomico: nunca deixa arquivo pela metade se a sessao morrer no meio."""
    tmp = destino.with_suffix(destino.suffix + ".tmp")
    tmp.write_bytes(conteudo)
    os.replace(tmp, destino)


def sincronizar(base: str, token: str, pasta_dados: Path,
                agora: datetime | None = None) -> list[str]:
    """Baixa o indice e cada calendario listado nele. Devolve as siglas baixadas."""
    destino = Path(pasta_dados) / "feriados"
    marca = destino / MARCA
    if _fresco(marca, agora):
        return []

    indice = json.loads(_baixar(f"{base}/{token}/index.json"))
    destino.mkdir(parents=True, exist_ok=True)

    baixados = []
    for trib in indice.get("calendarios", []):
        sigla = str(trib).upper()
        try:
            bruto = _baixar(f"{base}/{token}/{sigla}.json")
        except Exception:
            continue                      # faltou um: mantem o que ja tem
        if not calendario_valido(bruto):
            continue                      # malformado NAO substitui o bom
        _escrever(destino / f"{sigla}.json", bruto)
        baixados.append(sigla)

    _escrever(marca, json.dumps({
        "expira": indice.get("expira", ""),
        "calendarios": baixados,
        "sincronizado": (agora or datetime.now()).date().isoformat(),
    }, ensure_ascii=False, indent=2).encode("utf-8"))
    return baixados


# --------------------------------------------------------------------------
def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "--autoteste":
        return _autoteste()

    token = os.environ.get("CLAUDE_PLUGIN_OPTION_CALENDARIO_TOKEN", "").strip()
    pasta = argv[0] if argv else os.environ.get("CLAUDE_PLUGIN_DATA", "")
    if not (token and URL_BASE and pasta):
        return 0                          # sem assinatura configurada: nada a fazer
    try:
        sincronizar(URL_BASE, token, Path(pasta))
    except Exception:
        pass                              # rede fora, 404, disco cheio: silencio
    return 0


# --------------------------------------------------------------------------
def _autoteste() -> int:
    """Roda o fluxo inteiro contra file:// — sem rede, sem servidor."""
    import tempfile

    BOM = {"tribunal": "TJXX", "vigencia": "2026",
           "feriados_forenses": ["2026-04-01"], "exclusoes": []}
    RUIM = {"tribunal": "TJYY", "vigencia": "2026",
            "feriados_forense": ["2026-04-01"]}          # singular: o erro silencioso

    with tempfile.TemporaryDirectory() as tmp:
        raiz = Path(tmp)
        servidor = raiz / "cal" / "tok-123"
        servidor.mkdir(parents=True)
        (servidor / "index.json").write_text(json.dumps(
            {"expira": "2027-08-18", "calendarios": ["TJXX", "TJYY", "TJZZ"]}))
        (servidor / "TJXX.json").write_text(json.dumps(BOM))
        (servidor / "TJYY.json").write_text(json.dumps(RUIM))
        # TJZZ.json nao existe de proposito: um 404 no meio nao pode parar o resto

        dados = raiz / "dados"
        feriados = dados / "feriados"
        feriados.mkdir(parents=True)
        antigo = json.dumps({**BOM, "tribunal": "TJYY", "vigencia": "2025"})
        (feriados / "TJYY.json").write_text(antigo)      # o bom que nao pode ser perdido

        base = (raiz / "cal").as_uri()
        baixados = sincronizar(base, "tok-123", dados)

        assert baixados == ["TJXX"], f"esperado ['TJXX'], veio {baixados}"
        assert (feriados / "TJXX.json").is_file(), "TJXX bom nao foi gravado"
        assert (feriados / "TJYY.json").read_text() == antigo, \
            "calendario malformado SOBRESCREVEU o bom — e o dano irreversivel"
        assert not (feriados / "TJZZ.json").exists(), "gravou arquivo que deu 404"

        marca = json.loads((feriados / MARCA).read_text())
        assert marca["expira"] == "2027-08-18", marca

        # 2a chamada no mesmo dia nao vai na rede (URL quebrada de proposito)
        assert sincronizar("file:///nao/existe", "tok-123", dados) == [], \
            "sincronizou de novo dentro das 24h"
        # e 25h depois vai
        try:
            sincronizar("file:///nao/existe", "tok-123", dados,
                        agora=datetime.now() + timedelta(hours=25))
        except Exception:
            pass
        else:
            raise AssertionError("passadas 24h, deveria ter tentado a rede")

        # token vazio = no-op, mesmo com URL configurada
        os.environ.pop("CLAUDE_PLUGIN_OPTION_CALENDARIO_TOKEN", None)
        assert main([str(dados)]) == 0

    print("autoteste OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
