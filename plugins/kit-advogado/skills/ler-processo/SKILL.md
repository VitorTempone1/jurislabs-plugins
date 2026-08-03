---
name: ler-processo
description: Lê um PDF de processo judicial (autos completos, 50 a 800+ páginas) e devolve linha do tempo dos atos, partes e representantes, pedidos de cada lado, decisões proferidas, provas produzidas e pendentes, o que está parado agora e onde há prazo em curso — cada item com a página de onde saiu. Use quando o advogado disser "lê esse processo", "resume os autos", "acabei de receber o processo", "o que aconteceu nesse caso", "monta a linha do tempo", "peguei um caso no meio", "vou fazer sustentação e não li os autos", "cliente trocou de advogado e mandou o PDF", ou apontar um PDF grande de processo.
---

# Ler processo

O advogado aponta o PDF dos autos. Você devolve, em minutos, o que ele levaria horas lendo.

## REGRAS INEGOCIÁVEIS

Leia antes de tudo. Cada uma existe porque a violação destrói a confiança no primeiro uso.

1. **A saída é MINUTA.** Bloco fixo no topo com o que foi lido, o que **não** foi lido e o que ele precisa conferir. Nunca escreva "pronto para protocolar", "leitura completa" ou "processo integralmente analisado".
2. **Nenhum fato sem âncora.** Todo item da linha do tempo, todo pedido, toda decisão carrega a página (`p. 214`) e, quando houver, o id do documento (`Id. 105837629`). **Item sem âncora não entra na minuta** — vai para a seção "Não localizei".
3. **Não localizou? Escreva "não localizei".** Nunca preencha por plausibilidade. Processo tem sempre uma inicial, mas isso não autoriza você a descrever uma inicial que não leu. É o modo de falha que mata o produto.
4. **Prazo: apontar, nunca calcular.** Você diz "há intimação em p. X, datada de DD/MM — pode haver prazo correndo". Você **não** diz quando vence, não conta dia útil, não menciona recesso. Cálculo é da skill de prazos.
5. **Nada sai da máquina.** Zero busca na web, zero consulta a API, zero MCP com nome de parte, CPF ou número de processo. Nem para "confirmar a jurisprudência citada". Se o advogado pedir pesquisa, isso é outra skill, depois, e com o dado anonimizado.
6. **Escaneado é dito, não é escondido.** Página sem camada de texto entra na minuta como não lida, por faixa de páginas, com destaque. Resumo silencioso de 60% de um processo é pior que nenhum resumo.

## Passo 0 — perfil e arquivo

Leia o `CLAUDE.md` da pasta do escritório (área de atuação, tribunais, sistema). Se não existir, avise que `/kit-advogado:comecar` deixa a leitura mais afiada, e siga assim mesmo — não trave o advogado por causa de onboarding.

Confirme o caminho do PDF. Se ele apontar uma pasta com vários PDFs (autos vêm partidos em volumes), rode o mapa em cada um e trate como um processo só, guardando de qual arquivo veio cada página.

## Passo 1 — o mapa (isto é o que faz caber)

Um PDF de 800 páginas não cabe em contexto e não precisa caber. Primeiro rode o mapeador: ele mede o PDF na máquina, sem gastar contexto, e devolve um índice de ~100 linhas.

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/ler-processo/scripts/mapear_pdf.py" mapa "CAMINHO/autos.pdf"
```

No Windows sem Git instalado, o mesmo comando no PowerShell:

```powershell
uv run "$env:CLAUDE_PLUGIN_ROOT\skills\ler-processo\scripts\mapear_pdf.py" mapa "C:\caminho\autos.pdf"
```

Sai assim (814 páginas → 1 segundo, ~3 mil tokens):

```
PAGINAS: 814   DOCUMENTOS DETECTADOS: 120
SEM CAMADA DE TEXTO: 3 pagina(s) = 0%
  escaneadas (tem imagem, nao tem texto): p. 25-26, 85

PAGINAS      ID           TIPO                  TXT   DATAS NA PAGINA
1-8          200000001    PETICAO INICIAL       8/8   10/01/2024
27-38        200000006    CONTESTACAO           12/12 05/03/2024
45-70        200000009    LAUDO PERICIAL        26/26 30/08/2024
80-84        200000012    SENTENCA              5/5   14/03/2025
```

Como ele acha as fronteiras: o PJe carimba `Num. <id> - Pág. <n>` em toda página, e `Pág. 1` marca peça nova. Onde não há carimbo (eproc, e-SAJ, Projudi, PDF remontado), ele cai no título da peça no topo da página. Se um processo vier com tudo `?` na coluna TIPO, o agrupamento falhou: trate por faixa de páginas usando o modo `texto`, o resto da skill funciona igual.

**O mapa é índice, não é fonte.** A coluna DATAS traz datas *citadas na página*, que não são necessariamente a data do ato. Nada do mapa vira fato na minuta sem você ter lido a página.

## Passo 2 — triagem: o que ler e o que não ler

Aqui é onde 800 páginas viram 150. Classifique cada documento do mapa:

**Nível 1 — ler na íntegra.** É o que decide o caso:
inicial e emendas · contestação e reconvenção · réplica e impugnações · **toda** decisão, despacho, sentença e acórdão · ata/termo de audiência · embargos e recursos · contrarrazões · alegações finais e memoriais.

**Nível 2 — ler só a primeira página.** Basta para datar o ato e nomear o documento:
certidão · mandado · AR · citação e intimação · procuração e substabelecimento · petição avulsa curta · guia de custas.

**Nível 3 — não ler, só inventariar.** Prova documental bruta, que só interessa se alguém a invocou:
contrato · nota fiscal · extrato · comprovante · CTPS · prontuário · planilha · documentos pessoais.
Exceção: se um pedido ou uma decisão referenciar o anexo ("conforme doc. 5 de fls. 210"), aí ele sobe para o Nível 1.

**Perícia é caso à parte.** Laudo de 26 a 150 páginas: leia a primeira página, as 5 últimas (conclusão e resposta aos quesitos) e busque os termos:

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/ler-processo/scripts/mapear_pdf.py" busca "CAMINHO/autos.pdf" --termo "conclus"
uv run "${CLAUDE_PLUGIN_ROOT}/skills/ler-processo/scripts/mapear_pdf.py" busca "CAMINHO/autos.pdf" --termo "quesito"
```

O `busca` também é a forma barata de achar prova requerida e não apreciada: procure `protesta`, `requer a produção`, `prova testemunhal`, `depoimento pessoal`, `preclusão`, `designo audiência`.

## Passo 3 — leitura

Leia em ordem cronológica, com o modo `texto`, agrupando páginas para não fazer dezenas de chamadas:

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/ler-processo/scripts/mapear_pdf.py" texto "CAMINHO/autos.pdf" --paginas 1-8,27-38,43-44
```

Ele imprime `===== p. 214 =====` antes de cada página — **é daí que sai a âncora**. Página sem camada de texto vem marcada `<<< SEM CAMADA DE TEXTO - NAO LIDA`; se essa marca aparecer, a página vai para o bloco "não lido", nunca para a linha do tempo.

Ao ler, vá montando as sete listas da saída (partes, linha do tempo, pedidos, decisões, provas, situação atual, prazos apontados). Não guarde o texto integral: guarde o fato + a página.

### Quando delegar a subagentes

Some as páginas do Nível 1. Regra:

- **Até ~250 páginas: leia você mesmo, em série.** É o padrão. A linha do tempo depende de enxergar o processo inteiro de uma vez — é assim que você percebe que a prova deferida em p. 43 nunca foi produzida. Fatiar isso entre agentes é onde se perde essa percepção, que é justamente o que impressiona o advogado.
- **Acima de ~250 páginas de Nível 1, ou mais de 120 documentos:** delegue por blocos cronológicos contíguos de no máximo 40 documentos, um subagente por bloco. Dê a cada um: o caminho do PDF, a faixa de páginas, o comando `texto`, e o **esquema fixo de retorno** (linhas de `data | ato | quem | p. N | Id`). Proíba prosa. Depois monte a linha do tempo você mesmo e **descarte toda linha que voltar sem âncora** — subagente sem trava inventa.
- Bloco contíguo, nunca intercalado: quem lê a contestação precisa ter lido a inicial.

## Passo 4 — escaneado (a falha que não pode ser silenciosa)

PDF de processo antigo, autos digitalizados e despacho assinado à mão não têm camada de texto. O mapa já separou:

- **escaneadas** (tem imagem, não tem texto) → conteúdo desconhecido
- **em branco** (nem texto nem imagem) → provavelmente separador, mas ainda assim não lido
- **suspeitas** (pouco texto + imagem) → digitalização com carimbo por cima; pode haver conteúdo invisível

O que fazer, por tamanho:

| Situação | Conduta |
|---|---|
| Até 10 páginas cegas | Extraia as imagens e **leia como imagem**: `uv run "${CLAUDE_PLUGIN_ROOT}/skills/ler-processo/scripts/mapear_pdf.py" imagens "autos.pdf" --paginas 25-26,85 --saida <pasta temporária>` e abra os arquivos gerados. Resolve o caso comum do despacho digitalizado no meio do processo digital. |
| Mais de 10 páginas cegas | O script **recusa** de propósito. Diga ao advogado quais faixas ficaram cegas e que elas precisam de OCR ou de leitura humana. Não tente contornar. |
| Mais de 30% do PDF cego | Isso vai na **primeira linha** da resposta, antes de qualquer resumo: "li apenas X% dos autos". |
| Praticamente tudo cego | **Não entregue minuta.** Diga que o PDF é uma digitalização sem camada de texto e que qualquer resumo seria invenção. Ofereça reexportar os autos pelo sistema do tribunal (a exportação nativa costuma ter texto) ou passar por OCR. |

A pasta das imagens extraídas é temporária e **nunca** fica dentro de repositório git — ali tem PII.

## Passo 5 — a saída

Grave em `<pasta do PDF>/<nome-do-pdf>-leitura-AAAA-MM-DD.md` e mostre o resumo no chat. Se o arquivo já existir, crie um novo com sufixo de hora; **nunca sobrescreva** uma leitura anterior.

Estrutura obrigatória, nesta ordem:

```markdown
# MINUTA — leitura de processo
Não é peça. Não protocolar. Conferir nos autos antes de usar.

## O que eu li
- Arquivo: autos.pdf · 814 páginas · 120 documentos
- Na íntegra: p. 1-8, 27-44, 71-84 (peças decisórias e postulatórias)
- Só o cabeçalho: p. 9, 24, 85-90 (certidões, mandados, ARs)
- Não abri: p. 100-380 (anexos e prova documental — listados no inventário)

## O que eu NÃO li
- **Sem camada de texto (escaneadas): p. 25-26, 85.** Conteúdo desconhecido.
- Páginas com pouco texto e imagem (pode faltar conteúdo): p. 402
- [se nada faltou: "Todas as páginas tinham camada de texto."]

## O que você precisa conferir antes de usar
- [3 a 6 itens concretos: a data que aparece divergente, o pedido que ficou ambíguo,
   a decisão cujo dispositivo está na página escaneada, o prazo a calcular]

## Partes e representantes
| Polo | Parte | Advogado / OAB | Onde |

## Linha do tempo
| Data | Ato | Quem | Onde |
| 10/01/2024 | Distribuição da inicial | Autor | p. 1, Id. 200000001 |

## Pedidos
### Autor (p. 6-8)   ### Réu (p. 35-38)

## Decisões proferidas
| Data | Decisão | O que decidiu | Onde |

## Provas
- Produzidas: ...
- Requeridas e ainda pendentes: ...  ← o achado que mais vale
- Deferidas e não produzidas: ...

## Situação atual e próximo passo
[Onde o processo parou, o que se espera, quem tem que agir]

## Prazo em curso
[Apenas apontar: "intimação da sentença em p. 84, datada de 14/03/2025 — rode a
skill de prazos para calcular." NUNCA calcular aqui.]

## Não localizei
[Tudo que você procurou e não achou. Se está vazio, escreva "nada".]
```

Regras da saída:

- Divergência entre documentos (a inicial diz uma data, a certidão diz outra) **não se resolve escolhendo** — as duas entram, com as duas páginas, e a divergência sobe para "o que você precisa conferir".
- Valor em dinheiro sai como está escrito nos autos, com a página. Você não soma, não atualiza, não corrige.
- Jurisprudência citada dentro das peças é reproduzida como citação da parte, jamais como precedente verificado.
- No chat, entregue nesta ordem: uma linha de status (o que o processo é e onde parou) → o que não foi lido → linha do tempo → pendências → prazos apontados.

## O que esta skill NÃO faz

Não calcula prazo. Não protocola, não assina, não peticiona. Não pesquisa jurisprudência nem consulta tribunal. Não faz OCR. Não decide estratégia — para isso, depois de ler, o advogado chama a skill de análise de decisão ou os agentes jurídicos.

## Ferramenta

`scripts/mapear_pdf.py` — quatro modos: `mapa`, `texto`, `busca`, `imagens`. Roda por `uv run`, que baixa as dependências sozinho; funciona igual em Mac e Windows e não faz rede. Verificação: `uv run scripts/test_mapear_pdf.py` monta um PDF sintético e checa que página escaneada é detectada, que página com só carimbo do PJe não passa por lida, e que despacho curto não é confundido com página cega.
