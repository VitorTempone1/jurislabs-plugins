#!/usr/bin/env python3
"""server.py - MCP JurisLabs: fontes juridicas oficiais BR para o Claude.

Expoe DJEN, DataJud e LexML como ferramentas MCP. Roda em stdio (local, custo
zero). A logica de rede fica em juris_sources.py (testavel sem o pacote mcp).

Instalar o runtime: pip install "mcp[cli]"
Rodar solto: python3 server.py
"""
from mcp.server.fastmcp import FastMCP

from juris_sources import (
    FonteBloqueada,
    FonteErro,
    buscar_legislacao as _buscar_legislacao,
    consultar_djen as _consultar_djen,
    consultar_processo as _consultar_processo,
)

mcp = FastMCP("juris-mcp-br")


def _seguro(fn, **kw) -> dict:
    try:
        return fn(**kw)
    except FonteBloqueada as e:
        return {"erro": "bloqueio", "detalhe": str(e),
                "dica": "Rode na maquina do advogado (IP residencial) ou configure um proxy."}
    except FonteErro as e:
        return {"erro": "falha", "detalhe": str(e)}


@mcp.tool()
def consultar_djen(oab: str, uf: str, dias: int = 7, tribunal: str = "",
                   numero_processo: str = "", incluir_teor: bool = False) -> dict:
    """Consulta PONTUAL de publicacoes/intimacoes de um advogado no DJEN (CNJ).

    Use quando o advogado pedir para ver publicacoes/intimacoes por OAB.
    NAO e monitoramento diario automatico (isso e do JurisTools SaaS).

    Devolve uma LISTA COMPACTA (data, tipo, processo, classe e um trecho curto).
    Para ler o texto integral de uma publicacao, chame de novo com
    numero_processo preenchido e incluir_teor=True.

    Args:
        oab: numero da OAB (so os digitos).
        uf: UF da OAB, ex.: MG, SP.
        dias: janela de dias para tras a partir de hoje (default 7).
        tribunal: opcional, filtra por sigla (ex.: TJMG).
        numero_processo: opcional, filtra por um processo (para ler o teor).
        incluir_teor: se True (com numero_processo), traz o texto integral.
    """
    return _seguro(_consultar_djen, oab=oab, uf=uf, dias=dias, tribunal=tribunal,
                   numero_processo=numero_processo, incluir_teor=incluir_teor)


@mcp.tool()
def consultar_processo(numero: str, tribunal: str) -> dict:
    """Consulta o andamento de um processo no DataJud (CNJ) pelo numero.

    Retorna classe, assuntos, orgao julgador, data de ajuizamento e os
    ultimos movimentos. So metadados publicos, nao o inteiro teor.

    Args:
        numero: numero do processo (com ou sem mascara).
        tribunal: sigla do tribunal, ex.: TJMG, TJSP, TRF1, STJ.
    """
    return _seguro(_consultar_processo, numero=numero, tribunal=tribunal)


@mcp.tool()
def buscar_legislacao(numero: str = "", ano: str = "", tipo: str = "lei",
                      esfera: str = "federal", urn: str = "") -> dict:
    """Resolve uma norma oficial (LexML/normas.leg.br) e devolve seus metadados.

    Retorna nome, apelidos (ex.: "Codigo de Defesa do Consumidor (CDC)"),
    ementa, data, link oficial e link do texto integral. Use quando o advogado
    citar uma lei/decreto por numero e ano, ou quiser confirmar a norma certa.

    Informe tipo + numero + ano (o mais comum), ou uma urn LexML completa.

    Args:
        numero: numero da norma, ex.: "8078".
        ano: ano da norma, ex.: "1990".
        tipo: "lei", "lei complementar", "decreto", "decreto-lei",
            "medida provisoria", "emenda constitucional", etc. (default "lei").
        esfera: "federal", "estadual", "municipal" (default "federal").
        urn: alternativa: urn LexML completa (ignora os campos acima).
    """
    return _seguro(_buscar_legislacao, numero=numero, ano=ano, tipo=tipo,
                   esfera=esfera, urn=urn)


if __name__ == "__main__":
    mcp.run()
