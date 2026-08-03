#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = ["yt-dlp>=2024.1.1", "faster-whisper>=1.0.0"]
# ///
"""transcrever_video.py - transcreve audio de um link OU de um arquivo local.

O audio nao sai da maquina: a transcricao roda local (faster-whisper). Nao
precisa de ffmpeg instalado, porque o faster-whisper decodifica o audio sozinho.

Uso:
    uv run transcrever_video.py <url ou caminho do arquivo> [opcoes]
    uv run transcrever_video.py --autoteste

Opcoes:
    --modelo small|medium|large-v3   padrao: medium
    --idioma pt                      forca o idioma (padrao: detecta)
    --tempos                         prefixa cada trecho com [M:SS]
    --saida ARQUIVO                  grava em arquivo em vez de imprimir
"""
from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

SEGUNDOS_POR_PARAGRAFO = 30


def formatar_tempo(segundos: float) -> str:
    """125.4 vira '2:05'; 3725 vira '1:02:05'."""
    total = int(segundos)
    h, resto = divmod(total, 3600)
    m, s = divmod(resto, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def agrupar_em_paragrafos(trechos: list[dict], janela: int = SEGUNDOS_POR_PARAGRAFO) -> list[str]:
    """Junta trechos curtos em paragrafos de ~janela segundos."""
    paragrafos: list[str] = []
    atual: list[str] = []
    inicio = None
    for t in trechos:
        if inicio is None:
            inicio = t["inicio"]
        if t["inicio"] - inicio >= janela and atual:
            paragrafos.append(" ".join(atual))
            atual = []
            inicio = t["inicio"]
        atual.append(t["texto"])
    if atual:
        paragrafos.append(" ".join(atual))
    return paragrafos


def baixar_audio(url: str, destino: Path) -> tuple[Path, str]:
    """Baixa so a faixa de audio. Devolve (caminho, titulo). Sem converter: o
    faster-whisper le m4a/webm/opus direto, entao ffmpeg nao e necessario."""
    import yt_dlp

    opcoes = {
        "format": "bestaudio/best",
        "outtmpl": str(destino / "%(id)s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
    }
    with yt_dlp.YoutubeDL(opcoes) as ydl:
        info = ydl.extract_info(url, download=True)

    baixados = info.get("requested_downloads") or []
    if baixados and baixados[0].get("filepath"):
        return Path(baixados[0]["filepath"]), info.get("title", "sem titulo")
    arquivos = [p for p in destino.iterdir() if p.is_file()]
    if not arquivos:
        raise SystemExit("ERRO: o download nao produziu nenhum arquivo de audio.")
    return arquivos[0], info.get("title", "sem titulo")


def transcrever(caminho: Path, modelo: str, idioma: str | None) -> tuple[list[dict], object]:
    from faster_whisper import WhisperModel

    whisper = WhisperModel(modelo, device="cpu", compute_type="int8")
    iterador, info = whisper.transcribe(str(caminho), beam_size=5, language=idioma)
    trechos = [
        {
            "inicio": round(t.start, 2),
            "fim": round(t.end, 2),
            "texto": t.text.strip(),
            "marca": formatar_tempo(t.start),
        }
        for t in iterador
    ]
    return trechos, info


def autoteste() -> None:
    assert formatar_tempo(0) == "0:00"
    assert formatar_tempo(9.9) == "0:09"
    assert formatar_tempo(125.4) == "2:05"
    assert formatar_tempo(3725) == "1:02:05"

    trechos = [
        {"inicio": 0.0, "texto": "bom dia"},
        {"inicio": 10.0, "texto": "o prazo vence sexta"},
        {"inicio": 31.0, "texto": "ja protocolei"},
        {"inicio": 70.0, "texto": "obrigado"},
    ]
    paragrafos = agrupar_em_paragrafos(trechos)
    assert paragrafos == ["bom dia o prazo vence sexta", "ja protocolei", "obrigado"], paragrafos
    assert agrupar_em_paragrafos([]) == []
    print("autoteste OK")


def main() -> None:
    p = argparse.ArgumentParser(description="Transcreve video/audio de link ou arquivo local.")
    p.add_argument("origem", nargs="?", help="endereco do video OU caminho de um arquivo")
    p.add_argument("--modelo", default="medium", help="small | medium | large-v3")
    p.add_argument("--idioma", default=None, help="ex.: pt (padrao: detecta sozinho)")
    p.add_argument("--tempos", action="store_true", help="prefixar cada trecho com [M:SS]")
    p.add_argument("--saida", help="gravar em arquivo em vez de imprimir")
    p.add_argument("--autoteste", action="store_true", help="roda a checagem interna")
    args = p.parse_args()

    if args.autoteste:
        autoteste()
        return
    if not args.origem:
        p.error("informe o endereco do video ou o caminho do arquivo (ou use --autoteste)")

    local = Path(args.origem)
    tmp = None
    try:
        if local.exists():
            audio, titulo = local, local.name
        else:
            tmp = tempfile.TemporaryDirectory()
            print("Baixando o audio...", file=sys.stderr)
            audio, titulo = baixar_audio(args.origem, Path(tmp.name))

        print(f"Transcrevendo com o modelo {args.modelo} (roda na sua maquina)...", file=sys.stderr)
        trechos, info = transcrever(audio, args.modelo, args.idioma)

        linhas = [f"--- {titulo} | idioma detectado: {info.language} ---", ""]
        if args.tempos:
            linhas += [f"[{t['marca']}] {t['texto']}" for t in trechos]
        else:
            linhas += ["\n\n".join(agrupar_em_paragrafos(trechos))]
        texto = "\n".join(linhas)

        if args.saida:
            Path(args.saida).write_text(texto + "\n", encoding="utf-8")
            print(f"gravado em {args.saida} ({len(trechos)} trechos)", file=sys.stderr)
        else:
            print(texto)
        print(f"--- fim | {len(trechos)} trechos ---", file=sys.stderr)
    finally:
        if tmp is not None:
            tmp.cleanup()


if __name__ == "__main__":
    main()
