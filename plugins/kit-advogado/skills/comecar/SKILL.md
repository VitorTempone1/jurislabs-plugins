---
name: comecar
description: Configura o JurisLabs OS pro jeito que este escritorio advoga. Faz uma entrevista curta (area de atuacao, tribunais, tipo de peca, tom, equipe) e grava o perfil de pratica num CLAUDE.md dentro da pasta do escritorio, junto com a arvore de pastas de casos. Todas as outras skills do kit leem esse perfil antes de trabalhar. Rode uma vez, logo depois de instalar o kit.
disable-model-invocation: true
---

# /kit-advogado:comecar

Primeira coisa a rodar depois de instalar o kit. Sai daqui com o OS sabendo em que area o
advogado atua, em que tribunal ele peticiona e como ele escreve.

**Nunca dispare sozinho.** Esta skill so roda quando o advogado digita `/kit-advogado:comecar`.

---

## Antes de perguntar qualquer coisa

### 1. Leia o que o instalador ja coletou

O dialogo de instalacao do plugin ja perguntou estes cinco dados. **Nao pergunte de novo.**

| Valor | De onde vem |
|---|---|
| Nome do escritorio | `${user_config.escritorio_nome}` |
| Nome do advogado | `${user_config.advogado_nome}` |
| Numero da OAB | `${user_config.oab_numero}` |
| UF da OAB | `${user_config.oab_uf}` |
| Pasta do escritorio | `${user_config.pasta_escritorio}` |

Se algum desses vier vazio ou vier como texto literal `${user_config...}` (sinal de que o
dialogo de instalacao nao rodou), **ai sim** pergunte, uma pergunta por vez, e avise ao final
que ele pode arrumar isso em `/plugin` sem refazer a entrevista.

### 2. Confira a pasta do escritorio

Na pasta de `${user_config.pasta_escritorio}`:

```bash
git rev-parse --is-inside-work-tree
```

- Respondeu **`fatal:` / erro** = perfeito, e o esperado. Siga.
- Respondeu **`true`** = a pasta esta dentro de um repositorio git. **Pare.** Explique em uma
  frase: "essa pasta esta dentro de um repositorio git, e dado de cliente nunca deve entrar em
  git. Escolha outra pasta, fora de qualquer projeto de codigo, tipo `Documentos/Escritorio`."
  Peca a pasta nova e refaca a checagem.

**Esta skill NUNCA roda `git init` na pasta do escritorio.** Sem repositorio, nao existe
`git push` acidental levando nome, CPF e processo de cliente pra fora da maquina.

### 3. Ja existe perfil?

Se `${user_config.pasta_escritorio}/CLAUDE.md` ja existir, leia e pergunte antes de mexer:
"ja tem um perfil configurado aqui. Quer **revisar** (eu pergunto tudo de novo e reescrevo) ou
**ajustar so um ponto**?" Nunca sobrescreva calado.

---

## A entrevista

**Uma pergunta por vez, com `AskUserQuestion`.** Espere a resposta antes da proxima. Nao
despeje as sete de uma vez, e nao resuma varias numa so.

**Nao configure `askUserQuestionTimeout`.** O advogado vai sair no meio pra atender o telefone,
pra assinar uma peca, pra falar com cliente. A pergunta tem que estar esperando quando ele voltar.

Regras de escrita das opcoes:

- No maximo 4 opcoes por pergunta. Toda pergunta aceita resposta escrita ("Outra"), entao diga
  no enunciado o que fazer se nenhuma servir.
- Cada opcao explica o **trade-off em linguagem de advogado**, nao de programador. Errado:
  "modo verboso". Certo: "eu escrevo mais longo e voce corta o que sobrar".
- Zero jargao de tecnologia. Se precisar de uma sigla, explique em meia linha.

### Pergunta 1 de 7 — Area de atuacao (parte 1)

Multipla escolha (`multiSelect`). **E a pergunta mais importante da entrevista:** e ela que
define qual regime de contagem de prazo o OS carrega. Contar prazo criminal em dia util, ou
prazo trabalhista pela regra do CPC, e o unico erro irreversivel do produto.

Enunciado: "Em que voce advoga hoje? Pode marcar mais de uma. Sao duas telas de areas, essa e a
primeira. Se a sua nao estiver em nenhuma das duas, escolha *Outra* e escreva."

| Opcao | Como explicar |
|---|---|
| Trabalhista | Reclamatoria, audiencia na Justica do Trabalho, calculo de verbas |
| Civel e Consumidor | Cobranca, indenizacao, contrato, banco, plano de saude, aereo |
| Familia e Sucessoes | Divorcio, alimentos, guarda, inventario, partilha |
| Previdenciario | INSS, beneficio negado, revisao, recurso no CRPS |

### Pergunta 2 de 7 — Area de atuacao (parte 2)

Multipla escolha. Enunciado: "E alguma dessas tambem? Se nenhuma, escolha *Outra* e escreva
'nenhuma'."

| Opcao | Como explicar |
|---|---|
| Criminal | Defesa, inquerito, habeas corpus, execucao penal |
| Tributario | Auto de infracao, execucao fiscal, defesa administrativa |
| Empresarial e Societario | Contrato entre empresas, societario, recuperacao |
| Imobiliario | Despejo, locacao, usucapiao, compra e venda, condominio |

**Guarde tambem o regime**, que e o que o motor de prazo vai ler:

| Area marcada | Regime que o perfil registra |
|---|---|
| Civel, Consumidor, Familia, Sucessoes, Empresarial, Imobiliario | CPC (dias uteis) |
| Trabalhista | CLT (dias uteis, recesso proprio) |
| Criminal | CPP processual (dias corridos) e CP material (inclui o dia do comeco) |
| Previdenciario | CPC no judicial, administrativo em dias corridos no INSS/CRPS |
| Tributario | CPC no judicial, administrativo em dias corridos no fiscal |

Marcou mais de um regime: o perfil registra todos, e a regra fica sendo **perguntar o regime
caso a caso, nunca assumir**. Escreva isso no perfil com essas palavras.

### Pergunta 3 de 7 — Tribunais e sistema

Multipla escolha. Define feriado forense local (a maior fonte de erro real de prazo) e o
vocabulario das pecas. Enunciado: "Onde voce peticiona? Marque os sistemas que voce usa. Se usa
um que nao esta na lista, escolha *Outra* e escreva."

Ofereca em opcoes as combinacoes reais, cada uma explicada pelo que ela muda:

| Opcao | Como explicar |
|---|---|
| PJe | O da Justica do Trabalho e de boa parte da Justica Federal e estadual |
| eproc | Comum na Justica Federal do Sul e em alguns TJs |
| e-SAJ ou Projudi | Os sistemas estaduais (e-SAJ no TJSP e outros, Projudi em varios TJs) |
| JEF ou SEEU | Juizado Especial Federal e execucao penal |

Depois da resposta, pergunte **em texto normal** (nao gasta uma pergunta do wizard) em qual
tribunal e comarca ele atua mais, porque e o que define o feriado forense local. Uma linha:
"e em qual tribunal e comarca voce atua mais? (ex: TJMG, comarca de Belo Horizonte)".

### Pergunta 4 de 7 — Perfil de cliente

"Seus clientes sao mais pessoa fisica ou empresa?" Muda o tom da peca, o tipo de documento que
o OS vai pedir e o vocabulario da comunicacao com o cliente.

Opcoes: **Pessoa fisica** · **Empresa** · **Os dois, mais ou menos metade**.

### Pergunta 5 de 7 — Peca mais frequente

"Qual peca voce refaz mais vezes por mes?" E o que o kit vai otimizar primeiro. Ofereca 3 ou 4
opcoes coerentes com a area que ele marcou (peticao inicial · contestacao · recurso · manifestacao
e peticao simples), sempre com o *Outra* aberto.

### Pergunta 6 de 7 — Tom das minutas

"Como voce escreve?" Opcoes com o trade-off na cara:

| Opcao | Como explicar |
|---|---|
| Direto e curto | Peca enxuta, so o necessario. Le rapido, mas voce vai querer engordar a fundamentacao em caso grande |
| Fundamentado e tecnico | Mais doutrina e citacao. Peca mais robusta, mais longa pra revisar |
| Formal classico | Vocabulario tradicional, "Egregio", "Data venia". Combina com juiz mais formal |

### Pergunta 7 de 7 — Quem mais vai usar

"Alem de voce, mais alguem mexe no sistema?" Muda o nivel de trava: com equipe, o OS confirma
antes de qualquer coisa que altere prazo ou que gere peca final, e nunca conclui sozinho.

| Opcao | Como explicar |
|---|---|
| So eu | Menos confirmacao no meio do caminho |
| Eu e estagiario | O OS pede confirmacao antes de mexer em prazo e sempre marca a peca como minuta pra sua revisao |
| Eu e secretaria ou equipe | Trava alta: nada de prazo muda sem voce confirmar, e toda peca sai marcada pra revisao |

---

## O que escrever no disco

Duas coisas: o perfil e a arvore de pastas. Confirme antes de escrever, mostrando um resumo de
5 linhas do que entendeu e onde vai gravar.

### 1. A arvore

Dentro de `${user_config.pasta_escritorio}`:

```
CLAUDE.md                     <- o perfil
clientes/
  _modelo/                    <- copie essa pasta pra cada cliente novo
    briefing.md
    documentos/
    pecas/
modelos/                      <- as pecas-modelo dele
```

Nada de `git init`. Nada de arquivo escondido. Nada alem disso: pasta a mais que ninguem usa so
atrapalha quem e leigo.

Em `clientes/_modelo/briefing.md`, um esqueleto curto: cliente, contra quem, o que aconteceu,
o que ele quer, numero do processo, prazos, proximo passo.

### 2. O perfil (`CLAUDE.md`)

Texto puro. Escreva com a cara de um documento do escritorio, nao de arquivo de configuracao.
Ele e editavel a mao: diga isso na primeira linha depois do titulo.

Estrutura:

```markdown
# Perfil de pratica — <escritorio_nome>

Este arquivo e o que o JurisLabs OS le antes de trabalhar. E texto normal:
se algo aqui mudar, abra e edite. Rode /kit-advogado:comecar de novo se quiser refazer tudo.

## O escritorio
Advogado: <advogado_nome> — OAB/<oab_uf> <oab_numero>
Clientes: <pessoa fisica / empresa / os dois>
Equipe: <so ele / estagiario / secretaria ou equipe>

## Areas e regime de prazo
<lista das areas marcadas>
Regime de contagem: <regimes correspondentes>
<se for mais de um regime:>
REGRA: com mais de um regime na casa, o OS NUNCA assume o regime pelo tipo do caso.
Pergunta qual e antes de calcular qualquer prazo.

## Onde ele peticiona
Sistemas: <PJe / eproc / e-SAJ / Projudi / JEF / SEEU>
Tribunal e comarca principal: <o que ele respondeu>
Feriado forense local: conferir sempre na portaria do tribunal. E a maior fonte de erro de prazo.

## Como escrever
Tom: <tom escolhido>
Peca mais frequente: <peca>

## Travas que valem sempre aqui
1. Toda saida juridica e MINUTA. O OS nao protocola, nao assina, nao peticiona.
   O ultimo clique e sempre do advogado.
2. Prazo calculado pelo OS e apoio. Confira no sistema do tribunal antes de confiar.
3. Citacao sem numero do julgado e URL do inteiro teor nao entra em peca.
4. Precedente: recente e de pe. Nunca julgado antigo havendo mais novo em sentido contrario.
5. Nada de prazo muda em lote sem conferencia item a item.
<se tem equipe:>
6. Equipe usa o sistema: qualquer alteracao de prazo passa por confirmacao antes.

## Sobre esta pasta
Esta pasta guarda dado de cliente e por isso NAO e um repositorio git, de proposito:
sem git, nao tem como um comando levar por engano nome, CPF ou processo de cliente pra fora
da sua maquina. Nao rode `git init` aqui.
```

---

## Como termina

Fale em portugues de gente, cinco linhas no maximo:

1. Onde ficou o perfil (caminho completo) e que ele pode abrir e editar quando quiser.
2. As areas e o regime de prazo que ficaram gravados.
3. Que a pasta nao e repositorio git, e que isso e proposital.
4. Uma sugestao concreta do que fazer agora, tirada da area dele. Exemplo pra trabalhista:
   "me manda o PDF de um processo seu e eu te devolvo a linha do tempo".
5. Que `/kit-advogado:comecar` pode ser rodado de novo a qualquer momento, sem perder nada.

Nao liste os arquivos criados um por um. Nao mostre JSON. Nao mostre comando pra ele copiar,
a nao ser que ele peca.
