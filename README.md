# Claude para advogados (marketplace JurisLabs)

Marketplace de plugins do Claude Code com skills que tiram a repeticao do dia do advogado. Curadoria da JurisLabs. Este e o destino do QR code da palestra "Claude para advogados".

## Como instalar (Claude Code)
Cole cada linha no Claude Code, uma de cada vez.
```
!curl -LsSf https://astral.sh/uv/install.sh | sh
/plugin marketplace add VitorTempone1/jurislabs-plugins
/plugin install jurislabs-br@jurislabs
/plugin install jurislabs-prazos@jurislabs
```
Depois e so pedir em portugues, ex.: "vê minhas intimações de hoje", "calcula o prazo dessa sentença".

> O `uv` e pre-requisito: o `jurislabs-br` sobe o MCP com `uv run` e o `jurislabs-prazos` usa `uv run` pra puxar os feriados (lib `holidays`) sozinho, sem mexer no Python do sistema.

## Plugins
| Plugin | O que faz | Status |
|---|---|---|
| **jurislabs-br** | MCP com fontes juridicas oficiais BR: DJEN (publicacoes por OAB), DataJud (andamento) e LexML (legislacao) | v0.1 pronto |
| **jurislabs-prazos** | Calculadora de prazos processuais pelo CPC (dias uteis, termo inicial, recesso, feriados) | v0.1 pronto |

Roadmap do pacote completo (escrita, documentos, fontes juridicas BR, produtividade): ver `../CATALOGO.md`.

## Aviso
As skills sao APOIO ao trabalho do advogado. Nenhuma substitui a conferencia oficial (PJe/autos) nem a decisao juridica. A palavra final e sempre do advogado.

## Publicacao
Publicado como repo publico proprio: `VitorTempone1/jurislabs-plugins` — destino do QR da palestra.
