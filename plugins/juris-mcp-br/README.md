# MCP JurisLabs (juris-mcp-br)

Traz tres fontes juridicas oficiais e gratuitas do Brasil para dentro do Claude, como um conector MCP. E o primeiro MCP juridico focado em BR (o ecossistema so tinha EUA/ES/LatAm).

## Ferramentas
| Ferramenta | O que faz | Fonte |
|---|---|---|
| `consultar_djen` | Publicacoes/intimacoes por OAB (consulta pontual) | DJEN/Comunica (CNJ) |
| `consultar_processo` | Andamento de um processo pelo numero | DataJud (CNJ) |
| `buscar_legislacao` | Metadados oficiais de uma lei/decreto (nome, apelido, ementa, link, texto integral) por numero+ano | normas.leg.br (LexML) |

Depois de instalado, e so pedir em linguagem natural: "vê as intimações da OAB 123456/MG dos últimos 7 dias", "qual o andamento do processo X no TJSP", "me confirma o Código de Defesa do Consumidor". O Claude monta a URN (tipo+numero+ano) e resolve na fonte oficial.

## Instalar
1. Pre-requisito: ter o `uv` (https://docs.astral.sh/uv/). O plugin sobe o MCP com
   `uv run --with mcp`, entao NAO precisa instalar o `mcp` na mao nem mexer no
   Python do sistema.
2. No Claude Code:
   ```
   /plugin marketplace add VitorTempone1/jurislabs-plugins
   /plugin install juris-mcp-br@jurislabs
   ```

## Limite conhecido (importante)
DJEN e DataJud podem **bloquear acesso de IP de datacenter** (desafio anti-bot). Rodando na **maquina do advogado (IP residencial)** o bloqueio e pequeno. A legislacao (normas.leg.br) NAO tem esse problema. Em nuvem, aponte para um proxy:
- `DJEN_BASE_URL` — base da API do DJEN (ex.: o proxy `juris-djen` da VPS).
- `DATAJUD_API_KEY` — sobrepoe a chave publica padrao do DataJud.
- `NORMAS_API_URL` — base da API do normas.leg.br (default ja funciona).

Quando detecta bloqueio, a ferramenta devolve `{"erro":"bloqueio", ...}` com dica, em vez de dado invalido.

## Fronteira com o JurisTools SaaS
`consultar_djen` e **pontual** (o advogado pergunta, responde). O **monitoramento diario automatico** de prazos, com alerta e e-mail, e do JurisTools SaaS. O MCP e a isca e a consulta ao vivo; o SaaS faz o trabalho pesado sozinho.

## Aviso
Tudo aqui e apoio. Metadados publicos, nao inteiro teor. Nenhuma resposta substitui a conferencia oficial no PJe/autos. A palavra final e do advogado.

## Status de validacao (15/07/2026, IP residencial real)
As 3 ferramentas validadas ao vivo (`server/test_live.py`):
- **DataJud: OK.** Puxa processo + movimentos; a APIKey publica padrao funciona.
- **DJEN: OK.** Puxou 100 publicacoes reais por OAB.
- **Legislacao: OK.** CDC, CPC e CPP resolvidos via normas.leg.br (URN por numero+ano), sem desafio anti-bot. (O SRU do LexML do Senado tem PoW; trocamos pelo resolvedor do normas.leg.br, que e a fonte oficial e nao bloqueia.)

Testes de parsing/normalizacao passam offline (`server/test_juris_sources.py`, 8 testes).
