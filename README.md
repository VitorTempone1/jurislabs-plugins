# Claude para advogados (marketplace JurisLabs)

Marketplace de plugins do Claude Code com skills que tiram a repeticao do dia do advogado. Curadoria da JurisLabs. Este e o destino do QR code da palestra "Claude para advogados".

## Como instalar (Claude Code)
Cole cada linha no Claude Code, uma de cada vez.
```
!curl -LsSf https://astral.sh/uv/install.sh | sh
/plugin marketplace add VitorTempone1/jurislabs-plugins
/plugin install juris-mcp-br@jurislabs
/plugin install juris-prazos@jurislabs
```
Depois e so pedir em portugues, ex.: "vê minhas intimações de hoje", "calcula o prazo dessa sentença".

> O `uv` e pre-requisito: o `juris-mcp-br` sobe o MCP com `uv run` e o `juris-prazos` usa `uv run` pra puxar os feriados (lib `holidays`) sozinho, sem mexer no Python do sistema.

## Plugins
| Plugin | O que faz | Status |
|---|---|---|
| **juris-prazos** | Calculadora de prazos processuais pelo CPC (dias uteis, termo inicial, recesso, feriados) | v0.1 pronto |

Roadmap do pacote completo (escrita, documentos, fontes juridicas BR, produtividade): ver `../CATALOGO.md`.

## Aviso
As skills sao APOIO ao trabalho do advogado. Nenhuma substitui a conferencia oficial (PJe/autos) nem a decisao juridica. A palavra final e sempre do advogado.

## Publicacao (pendente)
Pra virar destino do QR, este diretorio precisa virar um repo publico proprio (hoje mora no monorepo privado `ccos-ratos`). Decisao de infra em aberto: repo separado vs subarvore publica. Nao publicar sem alinhar.
