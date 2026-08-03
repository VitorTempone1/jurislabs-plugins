# /// script
# requires-python = ">=3.9"
# dependencies = ["pypdf>=5.0", "pillow>=10.0"]
# ///
"""Mapa de um PDF de processo judicial.

Este script NAO interpreta o processo. Ele so mede e localiza, pra que o
modelo leia as paginas certas em vez de todas. Quatro modos:

  mapa     censo pagina a pagina -> onde comeca cada peca, quais paginas
           nao tem camada de texto (escaneadas)
  texto    despeja o texto de um intervalo de paginas, com marcador de pagina
  busca    acha um termo e devolve pagina + contexto
  imagens  extrai as imagens embutidas de paginas escaneadas, pra leitura visual

Roda igual em Mac e Windows:  uv run mapear_pdf.py mapa "caminho.pdf"

Nada aqui faz rede. O PDF nao sai da maquina.
"""

import argparse
import json
import os
import re
import sys
import unicodedata

try:  # Windows legado abre o console em cp1252 e engasga em acento
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# Rodape que o PJe carimba em TODA pagina, inclusive nas escaneadas.
# "Pag. 1" marca o inicio de uma peca nova; o Num. e o id do documento.
RODAPE_PJE = re.compile(r"Num\.\s*(\d+)\s*-\s*P[áa]g\.\s*(\d+)", re.I)
# Carimbos que sao so metadado de assinatura/paginacao e nao sao conteudo.
CARIMBOS = [
    RODAPE_PJE,
    re.compile(r"Assinado\s+eletronicamente\s+por[^\n]{0,120}", re.I),
    re.compile(r"https?://\S*(pje|eproc|esaj|projudi|jus\.br)\S*", re.I),
    re.compile(r"(documento|processo)\s+(assinado|eletr[ôo]nico)[^\n]{0,120}", re.I),
    re.compile(r"\bfls?\.\s*\d+\b", re.I),
    re.compile(r"\bevento\s+\d+\b", re.I),
]

DATA = re.compile(r"\b([0-3]?\d)/([01]?\d)/((?:19|20)\d{2})\b")

# Tipos de peca, do mais especifico pro mais generico (a ordem decide o empate).
TIPOS = [
    "PETICAO INICIAL", "EMENDA A INICIAL", "ADITAMENTO",
    "CONTESTACAO", "RECONVENCAO", "REPLICA", "IMPUGNACAO",
    "SENTENCA", "ACORDAO", "DECISAO INTERLOCUTORIA", "DECISAO", "DESPACHO",
    "ATA DE AUDIENCIA", "TERMO DE AUDIENCIA", "ASSENTADA",
    "LAUDO PERICIAL", "LAUDO", "PARECER", "QUESITOS",
    "EMBARGOS DE DECLARACAO", "EMBARGOS", "AGRAVO DE INSTRUMENTO", "AGRAVO",
    "APELACAO", "RECURSO ORDINARIO", "RECURSO ESPECIAL", "RECURSO EXTRAORDINARIO",
    "CONTRARRAZOES", "RAZOES",
    "ALEGACOES FINAIS", "MEMORIAIS",
    "CUMPRIMENTO DE SENTENCA", "EXECUCAO", "CALCULO", "PLANILHA",
    "MANDADO", "CERTIDAO", "AVISO DE RECEBIMENTO", "CITACAO", "INTIMACAO",
    "PROCURACAO", "SUBSTABELECIMENTO", "DECLARACAO DE HIPOSSUFICIENCIA",
    "CONTRATO", "NOTA FISCAL", "COMPROVANTE", "EXTRATO", "CTPS",
    "PRONTUARIO", "RECEITUARIO", "ATESTADO", "BOLETIM DE OCORRENCIA",
    "PETICAO",  # generico: so pega se nenhum acima pegou
]

# Pagina CEGA = sem NADA de texto util depois de tirar os carimbos. E o unico
# criterio honesto: pagina digital curta ("Cite-se.") tem pouco texto e mesmo
# assim foi lida. Os 10 chars absorvem lixo solto que o regex de carimbo perdeu.
MIN_CHARS_TEXTO = 10
# Pouco texto + imagem na pagina = provavel digitalizacao com carimbo por cima.
# Nao e cega, mas o advogado precisa saber que pode ter conteudo invisivel.
SUSPEITA_CHARS = 120


def sem_acento(s):
    n = unicodedata.normalize("NFKD", s)
    return "".join(c for c in n if not unicodedata.combining(c))


def limpar_carimbos(txt):
    for c in CARIMBOS:
        txt = c.sub(" ", txt)
    return txt


def detectar_tipo(txt):
    """Tipo da peca pelo cabecalho. So olha o comeco da pagina.

    Vence quem aparece PRIMEIRO (o titulo da peca fica no topo), e no empate
    vence o mais especifico. Sem isso, uma apelacao que fala em "reforma da
    sentenca" na primeira linha era classificada como SENTENCA.
    """
    cab = sem_acento(txt[:500]).upper()
    achados = [(cab.find(t), -len(t), t) for t in TIPOS if t in cab]
    return min(achados)[2] if achados else None


def tem_imagem(pagina):
    try:
        xo = pagina["/Resources"]["/XObject"].get_object()
        for k in xo:
            if xo[k].get_object().get("/Subtype") == "/Image":
                return True
    except Exception:
        pass
    return False


def compactar(nums):
    """[1,2,3,7,8,20] -> '1-3, 7-8, 20'"""
    if not nums:
        return ""
    nums = sorted(nums)
    faixas, ini, ant = [], nums[0], nums[0]
    for n in nums[1:]:
        if n == ant + 1:
            ant = n
            continue
        faixas.append((ini, ant))
        ini = ant = n
    faixas.append((ini, ant))
    return ", ".join(str(a) if a == b else "%d-%d" % (a, b) for a, b in faixas)


class PdfIlegivel(Exception):
    pass


def abrir(caminho):
    """Abre o PDF ou explica em portugues por que nao deu. Nunca traceback."""
    from pypdf import PdfReader

    try:
        leitor = PdfReader(caminho)
    except Exception as e:
        raise PdfIlegivel("nao consegui abrir o PDF (%s). Arquivo corrompido ou "
                          "download incompleto?" % str(e).splitlines()[0][:120])
    if leitor.is_encrypted:
        try:
            if not leitor.decrypt(""):
                raise PdfIlegivel(
                    "PDF protegido por senha. Peca a senha ao advogado ou peca "
                    "que ele reexporte os autos do sistema do tribunal sem protecao.")
        except PdfIlegivel:
            raise
        except Exception as e:
            raise PdfIlegivel("PDF criptografado e nao consegui abrir (%s)."
                              % str(e).splitlines()[0][:120])
    if len(leitor.pages) == 0:
        raise PdfIlegivel("PDF sem paginas.")
    return leitor


def censo(caminho):
    """Uma passada pelo PDF. Devolve uma linha por pagina."""
    leitor = abrir(caminho)
    paginas = []
    for i, pag in enumerate(leitor.pages, 1):
        try:
            txt = pag.extract_text() or ""
        except Exception as e:  # pagina corrompida nao pode derrubar o mapa
            txt = ""
            erro = str(e)[:80]
        else:
            erro = None
        m = RODAPE_PJE.search(txt)
        util = re.sub(r"\s+", " ", limpar_carimbos(txt)).strip()
        img = tem_imagem(pag)
        paginas.append({
            "pagina": i,
            "chars": len(util),
            "tem_texto": len(util) >= MIN_CHARS_TEXTO,
            "tem_imagem": img,
            "suspeita": len(util) >= MIN_CHARS_TEXTO and len(util) < SUSPEITA_CHARS and img,
            "doc_id": m.group(1) if m else None,
            "doc_pag": int(m.group(2)) if m else None,
            "tipo": detectar_tipo(util),
            "datas": sorted({"%02d/%02d/%s" % (int(d), int(mm), a)
                             for d, mm, a in DATA.findall(util)}),
            "inicio": util[:110],
            "erro": erro,
        })
    return paginas


def agrupar(paginas):
    """Junta paginas em documentos. Dois sinais de fronteira:
    1. rodape do PJe com 'Pag. 1' (forte, e o id do documento vem junto)
    2. cabecalho com nome de peca (fraco, mas cobre eproc/e-SAJ/Projudi)
    ponytail: heuristica de 2 sinais, sem parser por tribunal. Se um tribunal
    novo escapar, o modelo cai no modo 'texto' pagina a pagina e ainda funciona.
    """
    docs = []
    for p in paginas:
        nova = False
        if p["doc_pag"] == 1:
            nova = True
        elif p["doc_id"] and docs and p["doc_id"] != docs[-1]["doc_id"]:
            nova = True
        elif not docs:
            nova = True
        elif p["tipo"] and p["tipo"] != docs[-1]["tipo"] and p["doc_id"] is None:
            nova = True
        if nova:
            docs.append({"ini": p["pagina"], "fim": p["pagina"], "doc_id": p["doc_id"],
                         "tipo": p["tipo"], "datas": list(p["datas"]),
                         "com_texto": int(p["tem_texto"]), "paginas": 1,
                         "inicio": p["inicio"]})
        else:
            d = docs[-1]
            d["fim"] = p["pagina"]
            d["paginas"] += 1
            d["com_texto"] += int(p["tem_texto"])
            if d["tipo"] is None:
                d["tipo"] = p["tipo"]
            for x in p["datas"]:
                if x not in d["datas"]:
                    d["datas"].append(x)
    return docs


def cmd_mapa(args):
    paginas = censo(args.pdf)
    docs = agrupar(paginas)
    cegas = [p["pagina"] for p in paginas if not p["tem_texto"]]
    escaneadas = [p["pagina"] for p in paginas if not p["tem_texto"] and p["tem_imagem"]]
    vazias = [p["pagina"] for p in paginas if not p["tem_texto"] and not p["tem_imagem"]]
    suspeitas = [p["pagina"] for p in paginas if p["suspeita"]]
    resumo = {
        "arquivo": os.path.basename(args.pdf),
        "paginas": len(paginas),
        "paginas_sem_texto": len(cegas),
        "pct_sem_texto": round(100.0 * len(cegas) / max(1, len(paginas))),
        "faixas_escaneadas": compactar(escaneadas),
        "faixas_vazias": compactar(vazias),
        "faixas_suspeitas": compactar(suspeitas),
        "documentos": len(docs),
    }
    if args.json:
        print(json.dumps({"resumo": resumo, "documentos": docs}, ensure_ascii=False, indent=1))
        return
    print("ARQUIVO: %s" % resumo["arquivo"])
    print("PAGINAS: %d   DOCUMENTOS DETECTADOS: %d" % (resumo["paginas"], resumo["documentos"]))
    print("SEM CAMADA DE TEXTO: %d pagina(s) = %d%%" % (resumo["paginas_sem_texto"], resumo["pct_sem_texto"]))
    if escaneadas:
        print("  escaneadas (tem imagem, nao tem texto): p. %s" % resumo["faixas_escaneadas"])
    if vazias:
        print("  em branco (sem texto e sem imagem):      p. %s" % resumo["faixas_vazias"])
    if suspeitas:
        print("SUSPEITAS (pouco texto + imagem, pode haver conteudo invisivel): p. %s"
              % resumo["faixas_suspeitas"])
    print("")
    print("%-12s %-12s %-28s %-4s %s" % ("PAGINAS", "ID", "TIPO", "TXT", "DATAS NA PAGINA"))
    for d in docs:
        faixa = str(d["ini"]) if d["ini"] == d["fim"] else "%d-%d" % (d["ini"], d["fim"])
        txt = "%d/%d" % (d["com_texto"], d["paginas"])
        datas = ", ".join(d["datas"][:3]) or "-"
        tipo = d["tipo"] or ("? " + d["inicio"][:24])
        print("%-12s %-12s %-28s %-4s %s" % (faixa, d["doc_id"] or "-", tipo[:28], txt, datas))
    print("")
    print("As datas acima sao datas CITADAS na pagina, nao a data do ato.")
    print("Nada daqui vira fato sem o modelo ler a pagina.")


def _faixa(spec, total):
    paginas = set()
    for parte in spec.split(","):
        parte = parte.strip()
        if "-" in parte:
            a, b = parte.split("-", 1)
            paginas.update(range(int(a), int(b) + 1))
        elif parte:
            paginas.add(int(parte))
    return sorted(p for p in paginas if 1 <= p <= total)


def cmd_texto(args):
    leitor = abrir(args.pdf)
    alvo = _faixa(args.paginas, len(leitor.pages))
    for n in alvo:
        try:
            txt = leitor.pages[n - 1].extract_text() or ""
        except Exception as e:
            txt = "[ERRO AO EXTRAIR: %s]" % str(e)[:100]
        util = txt.strip()
        marca = "" if len(re.sub(r"\s+", " ", limpar_carimbos(util))) >= MIN_CHARS_TEXTO \
            else "   <<< SEM CAMADA DE TEXTO - NAO LIDA"
        print("\n===== p. %d =====%s" % (n, marca))
        print(util)


def cmd_busca(args):
    leitor = abrir(args.pdf)
    alvo = sem_acento(args.termo).lower()
    achados = 0
    for i, pag in enumerate(leitor.pages, 1):
        try:
            txt = pag.extract_text() or ""
        except Exception:
            continue
        plano = re.sub(r"\s+", " ", txt)
        alvo_plano = sem_acento(plano).lower()
        pos = alvo_plano.find(alvo)
        while pos >= 0 and achados < args.limite:
            print("p.%-5d %s" % (i, plano[max(0, pos - 70):pos + len(alvo) + 90].strip()))
            achados += 1
            pos = alvo_plano.find(alvo, pos + len(alvo))
        if achados >= args.limite:
            print("... corte em %d achados" % args.limite)
            break
    if not achados:
        print("NAO LOCALIZADO: '%s' nao aparece na camada de texto do PDF." % args.termo)
        print("Atencao: se o PDF tem paginas escaneadas, o termo pode estar la e ser invisivel aqui.")


def cmd_imagens(args):
    """Extrai as imagens de paginas escaneadas pra que o modelo as LEIA como imagem.
    Cap deliberado: isto resolve o despacho digitalizado no meio do processo
    digital, nao substitui OCR de autos fisicos inteiros."""
    leitor = abrir(args.pdf)
    alvo = _faixa(args.paginas, len(leitor.pages))
    if len(alvo) > args.limite:
        print("RECUSADO: %d paginas pedidas, limite %d." % (len(alvo), args.limite))
        print("Extrair centenas de imagens nao resolve autos escaneados. Avise o advogado")
        print("que essa faixa precisa de OCR ou de leitura humana.")
        return 2
    os.makedirs(args.saida, exist_ok=True)
    n = 0
    for p in alvo:
        try:
            for j, img in enumerate(leitor.pages[p - 1].images):
                ext = os.path.splitext(img.name)[1] or ".png"
                destino = os.path.join(args.saida, "p%04d_%d%s" % (p, j, ext))
                with open(destino, "wb") as f:
                    f.write(img.data)
                print(destino)
                n += 1
        except Exception as e:  # filtro exotico numa pagina nao derruba as outras
            print("p.%d: NAO EXTRAIDA (%s)" % (p, str(e).splitlines()[0][:90]))
    if n == 0:
        print("Nenhuma imagem embutida nessas paginas.")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Mapa de PDF de processo (nao interpreta, so localiza)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    m = sub.add_parser("mapa", help="censo do PDF: documentos, paginas sem texto")
    m.add_argument("pdf")
    m.add_argument("--json", action="store_true")
    m.set_defaults(func=cmd_mapa)

    t = sub.add_parser("texto", help="texto de um intervalo de paginas")
    t.add_argument("pdf")
    t.add_argument("--paginas", required=True, help="ex: 1-12,40,55-60")
    t.set_defaults(func=cmd_texto)

    b = sub.add_parser("busca", help="acha um termo e devolve pagina + contexto")
    b.add_argument("pdf")
    b.add_argument("--termo", required=True)
    b.add_argument("--limite", type=int, default=60)
    b.set_defaults(func=cmd_busca)

    i = sub.add_parser("imagens", help="extrai imagens de paginas escaneadas")
    i.add_argument("pdf")
    i.add_argument("--paginas", required=True)
    i.add_argument("--saida", required=True, help="pasta temporaria, NUNCA dentro de repositorio")
    i.add_argument("--limite", type=int, default=10)
    i.set_defaults(func=cmd_imagens)

    args = ap.parse_args(argv)
    if not os.path.exists(args.pdf):
        print("ARQUIVO NAO ENCONTRADO: %s" % args.pdf)
        return 1
    try:
        return args.func(args) or 0
    except PdfIlegivel as e:
        print("NAO CONSEGUI LER: %s" % e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
