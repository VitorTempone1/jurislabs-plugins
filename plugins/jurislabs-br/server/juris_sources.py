#!/usr/bin/env python3
"""juris_sources.py - fontes juridicas oficiais BR para o MCP JurisLabs.

Tres fontes publicas e gratuitas, so com a stdlib (urllib + ElementTree):
- DJEN / Comunica (CNJ): publicacoes/intimacoes por OAB. Consulta PONTUAL
  (monitoramento diario automatico e do JurisTools SaaS, nao daqui).
- DataJud (CNJ): andamento processual por numero do processo (APIKey publica).
- LexML (Senado/CNJ): busca de legislacao (SRU, XML).

Todas essas fontes BLOQUEIAM acesso de IP de datacenter (desafio anti-bot /
403 / Cloudflare). Rodando na maquina do advogado (IP residencial) o bloqueio
e menor; em nuvem, aponte para um proxy via variavel de ambiente
(DJEN_BASE_URL / LEXML_SRU_URL). Quando detecta bloqueio, levanta
FonteBloqueada com mensagem acionavel, em vez de devolver lixo.

REGRA: e apoio. A palavra final e do advogado; conferir sempre no PJe/autos.
"""
from __future__ import annotations

import html as _html
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, timedelta

BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
RESSALVA = "Apoio, nao oficial. Conferir sempre no PJe/autos. A palavra final e do advogado."

# Chave publica do DataJud (publicada na wiki do CNJ). Sobreponivel por env.
_DATAJUD_KEY_PADRAO = "cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="


class FonteBloqueada(RuntimeError):
    """A fonte respondeu com desafio/bloqueio (IP de datacenter). Use proxy."""


class FonteErro(RuntimeError):
    """Erro de rede ou resposta inesperada."""


# --------------------------------------------------------------------------- #
# Camada HTTP (stdlib)
# --------------------------------------------------------------------------- #
def _parece_bloqueio(status: int, ctype: str, corpo: bytes) -> bool:
    """HTML no lugar de dados, ou status de bloqueio = desafio anti-bot."""
    if status in (403, 405, 429, 503):
        return True
    amostra = corpo[:200].lstrip().lower()
    if "text/html" in (ctype or "").lower():
        return True
    return amostra.startswith(b"<!doctype html") or amostra.startswith(b"<html")


def _get(url: str, params: dict | None = None, headers: dict | None = None,
         timeout: float = 30) -> bytes:
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": BROWSER_UA, **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            corpo = resp.read()
            ctype = resp.headers.get("Content-Type", "")
            status = resp.status
    except urllib.error.HTTPError as e:
        corpo, ctype, status = e.read(), e.headers.get("Content-Type", ""), e.code
    except urllib.error.URLError as e:
        raise FonteErro(f"erro de rede: {e.reason}") from e
    if _parece_bloqueio(status, ctype, corpo):
        raise FonteBloqueada(
            f"HTTP {status}: a fonte bloqueou o acesso (provavel IP de datacenter). "
            "Rode na maquina do advogado ou aponte para um proxy via env.")
    return corpo


def _post_json(url: str, payload: dict, headers: dict | None = None,
               timeout: float = 30) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, method="POST",
        headers={"User-Agent": BROWSER_UA, "Content-Type": "application/json",
                 **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            corpo, ctype, status = resp.read(), resp.headers.get("Content-Type", ""), resp.status
    except urllib.error.HTTPError as e:
        corpo, ctype, status = e.read(), e.headers.get("Content-Type", ""), e.code
    except urllib.error.URLError as e:
        raise FonteErro(f"erro de rede: {e.reason}") from e
    if _parece_bloqueio(status, ctype, corpo):
        raise FonteBloqueada(f"HTTP {status}: DataJud bloqueou o acesso. Confira a APIKey/rede.")
    try:
        return json.loads(corpo)
    except json.JSONDecodeError as e:
        raise FonteErro(f"resposta nao-JSON: {e}") from e


# --------------------------------------------------------------------------- #
# Legislacao - normas.leg.br (LexML) por URN. Nao tem desafio anti-bot.
# --------------------------------------------------------------------------- #
NORMAS_API = os.environ.get("NORMAS_API_URL", "https://normas.leg.br/api/public")

# tipo humano -> componente de tipo na URN LexML
_TIPO_URN = {
    "lei": "lei",
    "lei complementar": "lei.complementar",
    "decreto": "decreto",
    "decreto-lei": "decreto.lei",
    "decreto lei": "decreto.lei",
    "medida provisoria": "medida.provisoria",
    "emenda constitucional": "emenda.constitucional",
    "constituicao": "constituicao",
    "resolucao": "resolucao",
    "portaria": "portaria",
    "sumula": "sumula",
}


def _montar_urn(numero: str, ano: str, tipo: str = "lei", esfera: str = "federal") -> str:
    """Monta a URN LexML. Aceita ano-so (o resolvedor nao exige a data exata)."""
    t = tipo.strip().lower()
    t = _TIPO_URN.get(t, t.replace(" ", ".").replace("-", "."))
    return f"urn:lex:br:{esfera.strip().lower()}:{t}:{ano.strip()};{_so_digitos(numero)}"


def _parse_norma(d: dict, urn: str) -> dict:
    if not isinstance(d, dict) or d.get("status") == 404 or not d.get("name"):
        return {"encontrado": False, "urn": urn,
                "detalhe": "Norma nao encontrada. Confira tipo/numero/ano ou passe a urn.",
                "ressalva": RESSALVA}
    enc = d.get("encoding") or []
    texto = enc[0].get("contentUrl") if enc and isinstance(enc[0], dict) else None
    return {
        "encontrado": True,
        "nome": d.get("name"),
        "apelidos": d.get("alternateName") or [],
        "ementa": d.get("abstract") or d.get("headline"),
        "data": d.get("legislationDate"),
        "publicacao": d.get("datePublished"),
        "keywords": d.get("keywords") or [],
        "urn": d.get("legislationIdentifier") or urn,
        "link": f"https://normas.leg.br/?urn={urn}",
        "textoIntegral": texto,
        "ressalva": RESSALVA,
    }


def buscar_legislacao(numero: str = "", ano: str = "", tipo: str = "lei",
                      esfera: str = "federal", urn: str = "",
                      timeout: float = 30) -> dict:
    """Resolve uma norma pelo numero/ano (ou urn) e devolve metadados oficiais."""
    if not urn:
        if not (numero and ano):
            raise FonteErro("informe numero+ano (e tipo), ou uma urn LexML completa")
        urn = _montar_urn(numero, ano, tipo, esfera)
    corpo = _get(f"{NORMAS_API}/metadados/gerais", params={"urn": urn}, timeout=timeout)
    try:
        dados = json.loads(corpo)
    except json.JSONDecodeError as e:
        raise FonteErro(f"resposta nao-JSON: {e}") from e
    return _parse_norma(dados, urn)


# --------------------------------------------------------------------------- #
# DataJud (andamento processual) - Elasticsearch DSL
# --------------------------------------------------------------------------- #
def _alias_datajud(tribunal: str) -> str:
    t = tribunal.strip().lower()
    t = re.sub(r"^api_publica_", "", t)
    if not re.fullmatch(r"[a-z0-9]+", t):
        raise FonteErro(f"tribunal invalido: {tribunal!r} (ex.: TJMG, TJSP, TRF1, STJ)")
    return t


def _so_digitos(s: str) -> str:
    return re.sub(r"\D", "", s or "")


def _parse_datajud(resp: dict) -> list[dict]:
    hits = (resp.get("hits") or {}).get("hits") or []
    out = []
    for h in hits:
        src = h.get("_source") or {}
        movs = sorted(
            ({"data": m.get("dataHora"), "movimento": m.get("nome")}
             for m in (src.get("movimentos") or [])),
            key=lambda m: m.get("data") or "", reverse=True)
        out.append({
            "numeroProcesso": src.get("numeroProcesso"),
            "tribunal": src.get("tribunal"),
            "grau": src.get("grau"),
            "classe": (src.get("classe") or {}).get("nome"),
            "assuntos": [a.get("nome") for a in (src.get("assuntos") or [])],
            "orgaoJulgador": (src.get("orgaoJulgador") or {}).get("nome"),
            "dataAjuizamento": src.get("dataAjuizamento"),
            "ultimosMovimentos": movs[:15],
        })
    return out


def consultar_processo(numero: str, tribunal: str, timeout: float = 30) -> dict:
    """Consulta andamento de um processo no DataJud pelo numero (20 digitos)."""
    alias = _alias_datajud(tribunal)
    url = f"https://api-publica.datajud.cnj.jus.br/api_publica_{alias}/_search"
    key = os.environ.get("DATAJUD_API_KEY", _DATAJUD_KEY_PADRAO)
    payload = {"size": 5, "query": {"match": {"numeroProcesso": _so_digitos(numero)}}}
    resp = _post_json(url, payload, headers={"Authorization": f"APIKey {key}"}, timeout=timeout)
    processos = _parse_datajud(resp)
    return {"numero": numero, "tribunal": alias.upper(), "total": len(processos),
            "processos": processos, "ressalva": RESSALVA}


# --------------------------------------------------------------------------- #
# DJEN / Comunica (publicacoes por OAB) - consulta PONTUAL
# --------------------------------------------------------------------------- #
DJEN_BASE = os.environ.get("DJEN_BASE_URL", "https://comunicaapi.pje.jus.br/api/v1")


def _texto_limpo(t: str) -> str:
    """Tira HTML/estilo do teor e normaliza espacos (para o trecho e o teor)."""
    t = re.sub(r"(?is)<(style|script)[^>]*>.*?</\1>", " ", t or "")
    t = re.sub(r"<[^>]+>", " ", t)
    t = _html.unescape(t)
    return re.sub(r"\s+", " ", t).strip()


def _normalizar_djen(item: dict, incluir_teor: bool = False) -> dict:
    # Por padrao devolve so um TRECHO curto. O teor inteiro de 100 publicacoes
    # estoura o limite de resposta; use incluir_teor num processo filtrado.
    texto = _texto_limpo(item.get("texto") or "")
    rec = {
        "numeroProcesso": item.get("numeroprocessocommascara") or item.get("numero_processo"),
        "dataDisponibilizacao": item.get("data_disponibilizacao"),
        "siglaTribunal": item.get("siglaTribunal"),
        "tipoDocumento": item.get("tipoDocumento"),
        "classe": item.get("nomeClasse"),
        "trecho": texto[:120],
    }
    if incluir_teor:  # visao detalhada: link + texto integral
        rec["link"] = item.get("link")
        rec["teor"] = texto[:4000]
    return rec


def consultar_djen(oab: str, uf: str, dias: int = 7, tribunal: str = "",
                   numero_processo: str = "", incluir_teor: bool = False,
                   hoje: date | None = None, timeout: float = 30) -> dict:
    """Consulta PONTUAL de publicacoes/intimacoes por OAB no DJEN.

    Compacta por padrao (so um trecho de cada). Para o texto integral, filtre
    por numero_processo e passe incluir_teor=True.
    """
    hoje = hoje or date.today()
    inicio = hoje - timedelta(days=max(1, dias) - 1)
    params = {
        "numeroOab": _so_digitos(oab),
        "ufOab": uf.strip().upper(),
        "dataDisponibilizacaoInicio": inicio.isoformat(),
        "dataDisponibilizacaoFim": hoje.isoformat(),
        "itensPorPagina": 100,
        "pagina": 1,
    }
    if tribunal:
        params["siglaTribunal"] = tribunal.strip().upper()
    if numero_processo:
        params["numeroProcesso"] = _so_digitos(numero_processo)
    corpo = _get(f"{DJEN_BASE}/comunicacao", params=params,
                 headers={"Accept": "application/json",
                          "Referer": "https://comunica.pje.jus.br/"}, timeout=timeout)
    try:
        dados = json.loads(corpo)
    except json.JSONDecodeError as e:
        raise FonteBloqueada(f"resposta nao-JSON (provavel bloqueio): {e}") from e
    itens = dados.get("items") or []
    # so traz o teor inteiro quando o resultado ja esta filtrado (poucos itens)
    teor = incluir_teor and (bool(numero_processo) or len(itens) <= 5)
    pubs = [_normalizar_djen(i, incluir_teor=teor) for i in itens]
    aviso = "Consulta pontual. O monitoramento diario automatico e do JurisTools."
    if len(itens) >= 100:
        aviso += " Teto de 100 por pagina atingido: pode haver mais (reduza o periodo ou filtre por tribunal/processo)."
    return {
        "oab": f"{params['numeroOab']}/{params['ufOab']}",
        "periodo": {"inicio": inicio.isoformat(), "fim": hoje.isoformat()},
        "total": len(pubs),
        "publicacoes": pubs,
        "aviso": aviso,
        "ressalva": RESSALVA,
    }
