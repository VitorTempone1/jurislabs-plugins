#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = ["yt-dlp>=2024.1.1"]
# ///
"""legendas_youtube.py - baixa a legenda de um video do YouTube e devolve texto limpo.

Nao baixa o video, nao precisa de ffmpeg: pega so o arquivo de legenda (VTT) e
converte pra texto na propria linguagem Python. Roda igual em Mac, Windows e Linux.

Uso:
    uv run legendas_youtube.py <url> [--idiomas pt,en] [--tempos] [--saida ARQUIVO]
    uv run legendas_youtube.py --autoteste
"""
from __future__ import annotations

import argparse
import re
import sys
import tempfile
from pathlib import Path

# Linha de tempo do VTT: 00:00:01.000 --> 00:00:03.500 align:start position:0%
LINHA_TEMPO = re.compile(
    r"^(\d{2}:)?\d{2}:\d{2}[.,]\d{3}\s*-->\s*(\d{2}:)?\d{2}:\d{2}[.,]\d{3}"
)
TAG_INLINE = re.compile(r"<[^>]*>")
CABECALHO = re.compile(r"^(WEBVTT|Kind:|Language:|NOTE\b|STYLE\b|REGION\b)")


def inicio_do_bloco(linha: str) -> str:
    """'00:01:02.500 --> ...' vira '1:02'. String vazia se nao for linha de tempo."""
    if not LINHA_TEMPO.match(linha):
        return ""
    bruto = linha.split("-->")[0].strip().replace(",", ".")
    partes = bruto.split(":")
    if len(partes) == 3:
        h, m, s = int(partes[0]), int(partes[1]), int(float(partes[2]))
    else:
        h, m, s = 0, int(partes[0]), int(float(partes[1]))
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def vtt_para_texto(vtt: str, com_tempos: bool = False) -> str:
    """Converte VTT em texto corrido, sem tags, sem cabecalho e sem repeticao.

    Legenda automatica do YouTube repete a linha anterior em cada bloco (efeito
    rolagem). Por isso a deduplicacao nao e opcional: sem ela o texto sai 2x.
    """
    saida: list[str] = []
    vistas: set[str] = set()
    tempo_atual = ""

    for linha_bruta in vtt.splitlines():
        linha = linha_bruta.strip()
        if not linha or CABECALHO.match(linha):
            continue
        marca = inicio_do_bloco(linha)
        if marca:
            tempo_atual = marca
            continue
        if linha.isdigit():  # numero sequencial do bloco (formato SRT)
            continue
        texto = TAG_INLINE.sub("", linha).strip()
        if not texto or texto in vistas:
            continue
        vistas.add(texto)
        saida.append(f"[{tempo_atual}] {texto}" if com_tempos else texto)

    if com_tempos:
        return "\n".join(saida)
    return " ".join(saida)


def baixar_legenda(url: str, idiomas: list[str], destino: Path) -> tuple[str, str]:
    """Baixa a melhor legenda disponivel. Devolve (titulo, conteudo VTT)."""
    import yt_dlp

    opcoes = {
        "skip_download": True,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": idiomas,
        "subtitlesformat": "vtt",
        "outtmpl": str(destino / "%(id)s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(opcoes) as ydl:
        info = ydl.extract_info(url, download=True)

    titulo = info.get("title", "sem titulo")
    # Preferencia: a ordem pedida em --idiomas; legenda manual antes da automatica.
    arquivos = sorted(destino.glob("*.vtt"))
    if not arquivos:
        raise SystemExit(
            "ERRO: esse video nao tem legenda nos idiomas pedidos "
            f"({', '.join(idiomas)}).\n"
            "Tente outro idioma com --idiomas, ou use a skill transcrever-video, "
            "que transcreve o audio na sua propria maquina."
        )
    manuais = info.get("subtitles") or {}
    for idioma in idiomas:
        for arquivo in arquivos:
            if f".{idioma}." in arquivo.name and idioma in manuais:
                return titulo, arquivo.read_text(encoding="utf-8", errors="replace")
    for idioma in idiomas:
        for arquivo in arquivos:
            if f".{idioma}." in arquivo.name:
                return titulo, arquivo.read_text(encoding="utf-8", errors="replace")
    return titulo, arquivos[0].read_text(encoding="utf-8", errors="replace")


def autoteste() -> None:
    amostra = """WEBVTT
Kind: captions
Language: pt

00:00:01.000 --> 00:00:03.500 align:start position:0%
bom dia <c>doutor</c>

00:00:03.500 --> 00:00:06.000
bom dia doutor
o prazo vence sexta

00:01:02.500 --> 00:01:04.000
protocolei ontem
"""
    corrido = vtt_para_texto(amostra)
    assert corrido == "bom dia doutor o prazo vence sexta protocolei ontem", corrido
    assert "<c>" not in corrido and "WEBVTT" not in corrido

    com_tempos = vtt_para_texto(amostra, com_tempos=True).splitlines()
    assert com_tempos[0] == "[0:01] bom dia doutor", com_tempos
    assert com_tempos[-1] == "[1:02] protocolei ontem", com_tempos

    assert inicio_do_bloco("01:02:03.000 --> 01:02:04.000") == "1:02:03"
    assert inicio_do_bloco("00:09.000 --> 00:11.000") == "0:09"
    assert inicio_do_bloco("bom dia") == ""
    print("autoteste OK")


def main() -> None:
    p = argparse.ArgumentParser(description="Legenda de video do YouTube em texto limpo.")
    p.add_argument("url", nargs="?", help="endereco do video")
    p.add_argument("--idiomas", default="pt,pt-BR,en", help="ordem de preferencia")
    p.add_argument("--tempos", action="store_true", help="prefixar cada trecho com [M:SS]")
    p.add_argument("--saida", help="gravar em arquivo em vez de imprimir")
    p.add_argument("--autoteste", action="store_true", help="roda a checagem interna")
    args = p.parse_args()

    if args.autoteste:
        autoteste()
        return
    if not args.url:
        p.error("informe o endereco do video (ou use --autoteste)")

    idiomas = [i.strip() for i in args.idiomas.split(",") if i.strip()]
    with tempfile.TemporaryDirectory() as tmp:
        titulo, vtt = baixar_legenda(args.url, idiomas, Path(tmp))

    texto = vtt_para_texto(vtt, com_tempos=args.tempos)
    cabecalho = f"--- {titulo} ---\n\n"

    if args.saida:
        Path(args.saida).write_text(cabecalho + texto + "\n", encoding="utf-8")
        print(f"gravado em {args.saida} ({len(texto)} caracteres)", file=sys.stderr)
    else:
        print(cabecalho + texto)


if __name__ == "__main__":
    main()
