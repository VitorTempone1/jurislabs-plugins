# /// script
# requires-python = ">=3.9"
# dependencies = ["pypdf>=5.0"]
# ///
"""Verificacao do mapear_pdf. Sem framework, sem fixture externa.

Monta um PDF sintetico na mao (nenhum documento real, nenhum PII) e checa o
que quebra o produto se der errado:
  - pagina escaneada tem que ser DETECTADA, nunca lida como vazia em silencio
  - pagina que so tem carimbo do PJe conta como escaneada, nao como texto
  - fronteira de peca ("Pag. 1") tem que abrir documento novo

    uv run test_mapear_pdf.py
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mapear_pdf import (_faixa, agrupar, censo, compactar, detectar_tipo,
                        limpar_carimbos)


def pdf_sintetico(paginas):
    """paginas: lista de dicts {"linhas": [str], "imagem": bool}."""
    objs = {1: None, 2: None, 3: b"<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>"}
    prox, kids, img_num = 4, [], None
    for p in paginas:
        pnum, cnum = prox, prox + 1
        prox += 2
        rec = b"<</Font<</F1 3 0 R>>"
        if p.get("imagem"):
            if img_num is None:
                img_num, prox = prox, prox + 1
                objs[img_num] = (b"<</Type/XObject/Subtype/Image/Width 1/Height 1"
                                 b"/ColorSpace/DeviceGray/BitsPerComponent 8/Length 1>>\n"
                                 b"stream\n\x00\nendstream")
            rec += b"/XObject<</Im0 %d 0 R>>" % img_num
        rec += b">>"
        corpo = [b"BT /F1 11 Tf 1 0 0 1 60 %d Tm (%s) Tj ET" % (740 - 16 * i, l.encode("latin-1"))
                 for i, l in enumerate(p.get("linhas", []))]
        conteudo = b"\n".join(corpo)
        objs[cnum] = b"<</Length %d>>\nstream\n%s\nendstream" % (len(conteudo), conteudo)
        objs[pnum] = (b"<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Resources"
                      + rec + b"/Contents %d 0 R>>" % cnum)
        kids.append(pnum)
    objs[1] = b"<</Type/Catalog/Pages 2 0 R>>"
    objs[2] = b"<</Type/Pages/Count %d/Kids[%s]>>" % (
        len(kids), b" ".join(b"%d 0 R" % k for k in kids))

    out, offsets = b"%PDF-1.4\n", {}
    for n in sorted(objs):
        offsets[n] = len(out)
        out += b"%d 0 obj\n" % n + objs[n] + b"\nendobj\n"
    xref, ultimo = len(out), max(objs)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (ultimo + 1)
    for n in range(1, ultimo + 1):
        out += b"%010d 00000 n \n" % offsets.get(n, 0)
    out += b"trailer\n<</Size %d/Root 1 0 R>>\nstartxref\n%d\n%%%%EOF\n" % (ultimo + 1, xref)
    return out


PAGINAS = [
    # p1 - inicial, primeira pagina do documento 105837629
    {"linhas": ["PETICAO INICIAL", "Excelentissimo Senhor Doutor Juiz de Direito da 2a Vara",
                "Civel. FULANO DE TAL, ja qualificado, vem propor acao em face de",
                "BELTRANO LTDA, pelos fatos e fundamentos a seguir expostos.",
                "Num. 105837629 - Pag. 1"]},
    # p2 - continuacao do mesmo documento
    {"linhas": ["Dos pedidos. Requer a condenacao da re ao pagamento de danos",
                "morais, bem como a producao de prova pericial contabil, nos",
                "termos do artigo 369 do Codigo de Processo Civil. Da-se a causa",
                "o valor de R$ 50.000,00. Termos em que pede deferimento.",
                "Num. 105837629 - Pag. 2"]},
    # p3 - sentenca, documento 222
    {"linhas": ["SENTENCA", "Vistos etc. Trata-se de acao ordinaria. Julgo procedente em",
                "parte o pedido para condenar a re ao pagamento de R$ 10.000,00.",
                "Publique-se. Registre-se. Intimem-se. Data 14/03/2025.",
                "Num. 105837630 - Pag. 1"]},
    # p4 - escaneada: nenhum texto, so imagem
    {"linhas": [], "imagem": True},
    # p5 - a armadilha: carimbo do PJe da a ILUSAO de camada de texto
    {"linhas": ["Num. 105837631 - Pag. 1", "Assinado eletronicamente por FULANO DE TAL"],
     "imagem": True},
    # p6 - a armadilha inversa: pagina digital curtissima, mas LIDA.
    # Se ela for classificada como escaneada, a skill mente dizendo que nao leu.
    {"linhas": ["DESPACHO", "Cite-se. 22/01/2024.", "Num. 105837632 - Pag. 1"]},
]


def main():
    # --- funcoes puras -------------------------------------------------
    assert compactar([1, 2, 3, 7, 8, 20]) == "1-3, 7-8, 20"
    assert compactar([]) == ""
    assert compactar([5]) == "5"
    assert detectar_tipo("SENTENÇA\nVistos etc.") == "SENTENCA"
    assert detectar_tipo("Contestação\nVem apresentar") == "CONTESTACAO"
    assert detectar_tipo("bom dia") is None
    # o titulo da peca esta no topo: quem aparece primeiro vence
    assert detectar_tipo("APELACAO\nRequer a reforma da sentenca.") == "APELACAO"
    # no empate de posicao, vence o mais especifico
    assert detectar_tipo("PETICAO INICIAL\nExcelentissimo") == "PETICAO INICIAL"
    assert detectar_tipo("DECISAO INTERLOCUTORIA\nDefiro") == "DECISAO INTERLOCUTORIA"
    assert _faixa("1-3,5", 10) == [1, 2, 3, 5]
    assert _faixa("1-99", 4) == [1, 2, 3, 4]
    assert limpar_carimbos("Num. 111 - Pág. 3").strip() == ""

    # --- ponta a ponta, num PDF de verdade ------------------------------
    with tempfile.TemporaryDirectory() as d:
        caminho = os.path.join(d, "sintetico.pdf")
        with open(caminho, "wb") as f:
            f.write(pdf_sintetico(PAGINAS))
        pg = censo(caminho)

    assert len(pg) == 6, pg
    assert pg[0]["tipo"] == "PETICAO INICIAL", pg[0]
    assert pg[0]["doc_id"] == "105837629" and pg[0]["doc_pag"] == 1, pg[0]
    assert pg[1]["doc_pag"] == 2, pg[1]
    assert pg[2]["tipo"] == "SENTENCA", pg[2]
    assert pg[2]["datas"] == ["14/03/2025"], pg[2]

    # o que nao pode falhar em silencio:
    assert pg[3]["tem_texto"] is False and pg[3]["tem_imagem"] is True, pg[3]
    assert pg[4]["tem_texto"] is False, "pagina so com carimbo do PJe passou por lida: %r" % pg[4]
    assert pg[4]["tem_imagem"] is True, pg[4]
    assert pg[4]["doc_pag"] == 1, "o carimbo ainda tem que servir de fronteira: %r" % pg[4]
    assert pg[5]["tem_texto"] is True, "despacho curto virou 'nao lido': %r" % pg[5]
    assert pg[5]["suspeita"] is False, pg[5]

    docs = agrupar(pg)
    assert len(docs) == 4, docs
    assert (docs[0]["ini"], docs[0]["fim"], docs[0]["doc_id"]) == (1, 2, "105837629"), docs[0]
    assert (docs[1]["ini"], docs[1]["fim"], docs[1]["tipo"]) == (3, 4, "SENTENCA"), docs[1]
    # a pagina cega grudada na sentenca tem que aparecer no placar de texto
    assert (docs[1]["com_texto"], docs[1]["paginas"]) == (1, 2), docs[1]
    assert (docs[2]["ini"], docs[2]["com_texto"]) == (5, 0), docs[2]

    print("ok - %d paginas, %d documentos, escaneadas detectadas: p. %s"
          % (len(pg), len(docs),
             compactar([p["pagina"] for p in pg if not p["tem_texto"]])))


if __name__ == "__main__":
    main()
