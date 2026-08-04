#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# ///
"""test_calendarios.py - quebra se um calendario forense estiver VENCIDO ou MALFORMADO.

    python3 test_calendarios.py                  # valida ../feriados
    python3 test_calendarios.py CAMINHO [...]    # valida outras pastas (o pacote pago)
    python3 test_calendarios.py --ano 2027       # finge que hoje e 2027
    python3 test_calendarios.py --autoteste      # testa o proprio validador

Por que existe: feriado errado = prazo errado, e prazo e o unico erro
irreversivel do produto. O motor ja avisa em tempo de calculo quando a
`vigencia` nao bate com o ano do vencimento - mas aviso na saida so vale se
alguem estiver lendo. Este arquivo falha ANTES, no repositorio, sem depender
de ninguem ler nada.

Os dois modos de falha que ele existe pra pegar:

  VENCIDO      calendario de 2026 ainda no lugar em 2027. Emenda de feriado,
               Dia do Servidor transferido e ponte mudam TODO ano. Usar o do
               ano passado calado e mentir com cara de dado.
  MALFORMADO   chave escrita errada ("feriados_forense", no singular) faz
               `carregar_calendario()` devolver lista vazia EM SILENCIO: o
               motor segue, calcula, e o advogado ganha um calendario sem
               nenhum feriado local. Erro engolido vira vazio, e vazio parece
               dado.

Nao importa `holidays` nem `prazo_cpc`: isto e conferencia de DADO, nao de
contagem. A contagem tem a suite ao lado (test_prazo_cpc.py). Saida em ASCII
puro porque metade da turma roda no PowerShell do Windows.
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

DIR_PADRAO = Path(__file__).resolve().parent.parent / "feriados"

# Chave fora desta lista (e que nao comece com "_") e erro, nao enfeite: e
# assim que "feriados_forense" passa despercebido e o calendario vira vazio.
CHAVES = {"tribunal", "vigencia", "feriados_forenses", "exclusoes"}


def _datas(dados: dict, chave: str, erros: list) -> list:
    """Le uma lista de datas ISO. Devolve o que deu pra ler; enche `erros`."""
    bruto = dados.get(chave, [])
    if not isinstance(bruto, list):
        erros.append(f"`{chave}` tem que ser uma lista, veio {type(bruto).__name__}")
        return []
    out, vistas = [], set()
    for item in bruto:
        if not isinstance(item, str):
            erros.append(f"`{chave}`: {item!r} nao e texto. Use \"AAAA-MM-DD\"")
            continue
        try:
            d = date.fromisoformat(item)
        except ValueError:
            erros.append(f"`{chave}`: {item!r} nao e uma data AAAA-MM-DD valida")
            continue
        if item in vistas:
            erros.append(f"`{chave}`: {item} aparece duas vezes")
            continue
        vistas.add(item)
        out.append((item, d))
    return out


def validar_arquivo(caminho: Path, ano_ref: int) -> tuple[list, list]:
    """Devolve (erros, avisos). Lista de erros vazia = calendario aprovado."""
    erros: list = []
    avisos: list = []
    try:
        dados = json.loads(caminho.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [f"JSON invalido: {e}"], []
    if not isinstance(dados, dict):
        return ["o arquivo tem que ser um objeto JSON"], []

    sobrando = {k for k in dados if not k.startswith("_")} - CHAVES
    if sobrando:
        erros.append(
            f"chave desconhecida: {', '.join(sorted(sobrando))}. O motor ignora o "
            f"que nao reconhece, entao um nome errado vira calendario VAZIO em "
            f"silencio. Esperadas: {', '.join(sorted(CHAVES))} (ou prefixo _)")

    trib = dados.get("tribunal", "")
    if not isinstance(trib, str) or not trib.strip():
        erros.append("`tribunal` ausente ou vazio")
    elif trib != trib.upper():
        erros.append(f"`tribunal` tem que ser maiusculo ({trib!r}): o motor procura "
                     f"o arquivo por `{trib.upper()}.json`")
    elif trib != caminho.stem.upper():
        erros.append(f"`tribunal` e {trib!r} mas o arquivo se chama "
                     f"{caminho.name!r}. O motor abre pelo NOME do arquivo: "
                     f"quem manda e {caminho.stem.upper()!r}, e o resto nunca "
                     f"seria carregado")

    vig = str(dados.get("vigencia", "")).strip()
    if not (len(vig) == 4 and vig.isdigit()):
        erros.append(f"`vigencia` tem que ser o ano com 4 digitos, veio {vig!r}. "
                     "Sem ela o motor nao consegue avisar que o calendario venceu")
        ano_vig = None
    else:
        ano_vig = int(vig)
        if ano_vig < ano_ref:
            erros.append(
                f"VENCIDO: vigencia {ano_vig}, estamos em {ano_ref}. Emendas, "
                f"pontes e o Dia do Servidor mudam todo ano - atualizar pela "
                f"portaria do calendario forense de {ano_ref} e so entao "
                f"trocar a `vigencia`")

    fonte = dados.get("_fonte", "")
    if not isinstance(fonte, str) or len(fonte.strip()) < 20 or not any(
            c.isdigit() for c in fonte):
        erros.append("`_fonte` tem que citar o ato: numero da portaria/resolucao "
                     "e a data. Sem fonte o dado nao e conferivel, e feriado nao "
                     "conferivel e prazo perdido")

    ref: dict = {}
    for k, v in dados.items():
        if k.startswith("_referencia") and isinstance(v, dict):
            ref.update(v)

    feriados = _datas(dados, "feriados_forenses", erros)
    exclusoes = _datas(dados, "exclusoes", erros)

    conflito = {s for s, _ in feriados} & {s for s, _ in exclusoes}
    if conflito:
        erros.append(f"{', '.join(sorted(conflito))} esta em `feriados_forenses` E "
                     "em `exclusoes` ao mesmo tempo. A exclusao vence no motor, "
                     "entao o feriado nunca valeria: decida qual dos dois e verdade")

    for chave, itens in (("feriados_forenses", feriados), ("exclusoes", exclusoes)):
        for s, d in itens:
            if ano_vig is not None and d.year != ano_vig:
                erros.append(f"`{chave}`: {s} esta fora da vigencia {ano_vig}. "
                             "Um arquivo por ano - data de outro ano aqui nao e "
                             "coberta por nenhuma revisao anual")
            if s not in ref:
                erros.append(f"`{chave}`: {s} nao tem entrada em `_referencia_{ano_vig or 'AAAA'}`. "
                             "Toda data precisa dizer de onde saiu (portaria, "
                             "artigo, inciso) - e o que permite conferir a mao")
            if chave == "feriados_forenses" and d.weekday() >= 5:
                avisos.append(f"{s} cai em {'sabado' if d.weekday() == 5 else 'domingo'}: "
                              "o motor ja exclui fim de semana, entao a linha nao "
                              "faz nada. Confira se nao e erro de digitacao")

    if not feriados and "feriados_forenses" in dados:
        avisos.append("`feriados_forenses` esta vazio. Todo tribunal tem pelo menos "
                      "uma emenda ou um feriado local - confira se a portaria foi "
                      "lida mesmo")
    return erros, avisos


def validar_pasta(pasta: Path, ano_ref: int) -> int:
    """Imprime o resultado. Devolve o numero de arquivos reprovados."""
    if not pasta.is_dir():
        print(f"FALHA {pasta}: pasta de calendarios nao existe")
        return 1
    # `_` = arquivo nosso (ex.: _assinatura.json do pacote pago).
    # `.` = lixo do sistema de arquivos: no SSD exFAT do dono o macOS deixa um
    # `._TJMG.json` AppleDouble ao lado de cada arquivo, que e binario e fazia
    # este validador MORRER de UnicodeDecodeError em vez de validar.
    arquivos = sorted(p for p in pasta.glob("*.json")
                      if not p.name.startswith(("_", ".")))
    if not arquivos:
        # Sem isto a suite passaria verde numa pasta vazia - que e o mesmo
        # "passa sem calendario" que condenou a suite anterior do motor.
        print(f"FALHA {pasta}: nenhum calendario .json na pasta")
        return 1
    reprovados = 0
    for p in arquivos:
        erros, avisos = validar_arquivo(p, ano_ref)
        for a in avisos:
            print(f"aviso {p.name}: {a}")
        if erros:
            reprovados += 1
            for e in erros:
                print(f"FALHA {p.name}: {e}")
        else:
            print(f"ok    {p.name}")
    return reprovados


# --------------------------------------------------------------------------
# Autoteste: o validador tem que pegar cada um destes. Sem isto ele e so mais
# um arquivo que passa verde.
# --------------------------------------------------------------------------
BOM = {
    "tribunal": "TJXX", "vigencia": "2026",
    "_fonte": "Portaria Conjunta 1/PR/2026 (DJe 13/1/2026), art. 1o.",
    "feriados_forenses": ["2026-10-30"],
    "exclusoes": ["2026-10-28"],
    "_referencia_2026": {"2026-10-30": "Dia do Funcionario Publico",
                         "2026-10-28": "EXCLUSAO: ha expediente"},
}


def autoteste() -> int:
    import tempfile
    casos = [
        ("vencido", {**BOM, "vigencia": "2025",
                     "feriados_forenses": ["2025-10-30"], "exclusoes": [],
                     "_referencia_2025": {"2025-10-30": "x"}}, "VENCIDO"),
        ("chave_no_singular", {**{k: v for k, v in BOM.items()
                                  if k != "feriados_forenses"},
                               "feriados_forense": ["2026-10-30"]},
         "chave desconhecida"),
        ("data_quebrada", {**BOM, "feriados_forenses": ["30/10/2026"]},
         "nao e uma data"),
        ("data_de_outro_ano", {**BOM, "feriados_forenses": ["2025-10-30"]},
         "fora da vigencia"),
        ("sem_referencia", {**BOM, "feriados_forenses": ["2026-12-08"]},
         "nao tem entrada em `_referencia"),
        ("sem_fonte", {**BOM, "_fonte": "portaria"}, "`_fonte`"),
        ("feriado_e_exclusao", {**BOM, "exclusoes": ["2026-10-30", "2026-10-28"]},
         "ao mesmo tempo"),
        ("duplicada", {**BOM, "feriados_forenses": ["2026-10-30", "2026-10-30"]},
         "duas vezes"),
        ("sem_vigencia", {k: v for k, v in BOM.items() if k != "vigencia"},
         "`vigencia`"),
    ]
    falhas = 0
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        bom = base / "TJXX.json"
        bom.write_text(json.dumps(BOM), encoding="utf-8")
        erros, _ = validar_arquivo(bom, 2026)
        if erros:
            falhas += 1
            print(f"FALHA autoteste[calendario_bom]: reprovou um arquivo valido: {erros}")
        else:
            print("ok    autoteste[calendario_bom]")

        for nome, payload, esperado in casos:
            p = base / "TJXX.json"
            p.write_text(json.dumps(payload), encoding="utf-8")
            erros, _ = validar_arquivo(p, 2026)
            if any(esperado in e for e in erros):
                print(f"ok    autoteste[{nome}]")
            else:
                falhas += 1
                print(f"FALHA autoteste[{nome}]: esperava um erro com "
                      f"{esperado!r}, veio {erros}")

        (base / "TJXX.json").unlink()
        if validar_pasta(base, 2026) == 0:
            falhas += 1
            print("FALHA autoteste[pasta_vazia]: pasta sem calendario passou verde")
        else:
            print("ok    autoteste[pasta_vazia]")

        p = base / "TJSP.json"
        p.write_text(json.dumps(BOM), encoding="utf-8")   # diz TJXX dentro
        if any("abre pelo NOME do arquivo" in e for e in validar_arquivo(p, 2026)[0]):
            print("ok    autoteste[nome_do_arquivo]")
        else:
            falhas += 1
            print("FALHA autoteste[nome_do_arquivo]: TJXX dentro de TJSP.json passou")
    return falhas


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    ano_ref = date.today().year
    if "--ano" in argv:
        i = argv.index("--ano")
        ano_ref = int(argv[i + 1])
        del argv[i:i + 2]
    if "--autoteste" in argv:
        falhas = autoteste()
        print(f"\nautoteste: {falhas} falha(s).")
        return 1 if falhas else 0
    pastas = [Path(a) for a in argv] or [DIR_PADRAO]
    reprovados = sum(validar_pasta(p, ano_ref) for p in pastas)
    print(f"\n{reprovados} calendario(s) reprovado(s). Ano de referencia: {ano_ref}.")
    return 1 if reprovados else 0


if __name__ == "__main__":
    raise SystemExit(main())
