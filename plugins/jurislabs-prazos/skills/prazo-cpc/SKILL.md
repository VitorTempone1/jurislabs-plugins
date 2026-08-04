---
name: prazo-cpc
description: 'Calcula prazo processual em qualquer regime (CPC, CLT, CPP penal processual, CP penal material, JEC, administrativo federal, INSS/CRPS e fiscal federal), a partir da disponibilizacao no DJE/DJEN ou da ciencia. Use quando o advogado pedir "calcular prazo", "quando vence", "que dia cai o prazo", "prazo de X dias da publicacao/intimacao", "prescricao", "decadencia", ou passar uma data e um numero de dias. Aplica dias uteis x dias corridos por regime, o termo inicial (CPC art. 224 §§2-3), o recesso (20/12-06/01 sem expediente x 20/12-20/01 com prazo suspenso) e os feriados forenses da Lei 5.010/66 art. 62. SEM regime e sem saber se a data e disponibilizacao ou publicacao, a skill NAO calcula: ela pergunta.'
---

# Calculadora de prazos (multirregime)

O nome da skill continua `prazo-cpc` por compatibilidade, mas **o motor nao e so
CPC e nao tem regime padrao**. Chutar CPC num prazo penal erra por dias.

## REGRA INEGOCIAVEL
O calculo e **apoio, nao verdade final**. NUNCA afirme o prazo como oficial e
SEMPRE feche com a ressalva de conferir no PJe/autos. Feriado municipal da
comarca, portaria pontual do tribunal e indisponibilidade do sistema
(CPC art. 224 §1) podem nao estar na base.

## ANTES DE CALCULAR: as duas perguntas obrigatorias

O motor recusa calcular sem as duas. Nao adivinhe nenhuma delas, **pergunte** —
uma por vez, com as opcoes e o trade-off.

### 1. Qual o regime

```
A contagem muda por completo. Qual e o regime?

  [ Civel / CPC ]         dias UTEIS, para no recesso de 20/12 a 20/01
  [ Penal - processual ]  dias CORRIDOS, nao para em feriado (CPP art. 798)
  [ Outro regime ]        trabalhista, JEC, administrativo, prescricao penal

Nao tenho padrao. Chutar CPC num prazo penal atrasa o calculo em dias
e faz perder o prazo.
```

Se a resposta for penal, a proxima pergunta e obrigatoria:

```
Penal tem duas contagens OPOSTAS. Qual e o seu caso?

  [ Processual ]  recorrer, contestar, alegacoes finais - CPP art. 798,
                  EXCLUI o dia do comeco
  [ Material ]    prescricao, decadencia, queixa-crime - CP art. 10,
                  INCLUI o dia do comeco
```

### 2. A data e disponibilizacao ou publicacao

**Esta e a pergunta que a versao anterior desta skill nao fazia, e ela vale um
dia util de prazo, na direcao fatal.** Advogado fala "publicou dia 6", nao
"disponibilizou dia 6". O DJEN entrega **disponibilizacao**. Se voce passar uma
data de publicacao como se fosse disponibilizacao, o motor aplica o art. 224 §2
de novo e devolve o vencimento **um dia util mais tarde do que o real**.

```
A data 06/07/2026 e:

  [ Disponibilizacao ]  saiu no DJEN nesse dia (e o que o DJEN devolve)
  [ Publicacao ]        ja e a data de publicacao (o §2 ja foi aplicado)

Errar aqui vale um dia util de prazo.
```

Medido: "publicou seg 06/07/2026, 15 dias, TJMG" -> com `publicacao` vence
**27/07**; tratado como disponibilizacao vence **28/07**. Um dia TARDE.

Nos regimes que nao usam a cadeia do art. 224 (CPP, CP, administrativo), a data
e a **ciencia/intimacao** e o parametro `--natureza` nao e exigido.

## Como usar

`scripts/prazo_cpc.py`, so stdlib. Com a lib opcional `holidays` instalada
entram os feriados **civis** nacionais e estaduais (recomendado:
`pip install holidays`); sem ela o motor calcula e **avisa** que faltam.

```bash
python3 scripts/prazo_cpc.py --regime cpc --natureza disponibilizacao \
  --data 2026-07-03 --dias 15 --tribunal TJMG --hoje 2026-07-15
```

| Parametro | Para que |
|---|---|
| `--regime` | **obrigatorio, sem padrao.** Ver a tabela de regimes abaixo |
| `--data AAAA-MM-DD` | obrigatorio: disponibilizacao, publicacao ou ciencia |
| `--natureza` | `disponibilizacao` \| `publicacao` \| `ciencia`. Obrigatorio em CPC/CLT/JEC |
| `--dias N` | obrigatorio: tamanho do prazo |
| `--unidade` | `uteis` \| `corridos` — sobrepoe a unidade do regime. Necessario no PAF (arts. 15 e 33 = 20 dias **uteis** num regime que e corrido por regra). Recusado no CPP e no CP |
| `--tribunal TJXX` / `--uf XX` | carrega feriado estadual e o calendario do tribunal |
| `--feriados CAMINHO` | arquivo ou pasta com `<TRIBUNAL>.json` (default: `feriados/`) |
| `--feriado-extra AAAA-MM-DD` | feriado a mais (repetivel): portaria, feriado local |
| `--excluir AAAA-MM-DD` | data que a lib marca mas que **tem expediente** (repetivel) |
| `--sem-suspensao MOTIVO` | desliga o recesso. CPP art. 798-A: reu preso vinculado a prisao, Maria da Penha, medida urgente |
| `--litisconsortes` + `--autos` | CPC art. 229. `--autos` e obrigatorio junto: o **§2º nao dobra em autos eletronicos** |
| `--folga N` | dias uteis do `PROTOCOLAR ATE` (default 2) |
| `--hoje AAAA-MM-DD` | mostra os dias restantes |
| `--json` | saida estruturada |

## Os regimes

| `--regime` | Unidade | Dia do comeco | Suspensao | Base |
|---|---|---|---|---|
| `cpc` | uteis | exclui | 20/12–20/01 | art. 219; 220; 224 §§1-3 |
| `clt` | uteis | exclui | 20/12–20/01 | art. 775 (Lei 13.467/2017); 775-A |
| `jec` | uteis | exclui | 20/12–20/01 | Lei 9.099/95 art. 12-A |
| `cpp-processual` | **corridos** | exclui | 20/12–20/01, **com excecoes** | CPP art. 798, §1, §3; 798-A |
| `cp-material` | **corridos** | **INCLUI** | **nao suspende** | CP art. 10 |
| `adm-federal` | corridos | exclui | nao ha | Lei 9.784/99 art. 66 |
| `adm-previdenciario` | corridos | exclui | nao ha | Dec. 3.048/99 art. 305 §1º (30 dias) |
| `adm-fiscal-federal` | **misto** | exclui | **20/12–20/01** | Dec. 70.235/72 na redacao da **LC 227/2026** |

Pontos que erram na mao e o motor ja trata:

- **CPP art. 798** — dias corridos. A contagem em dias uteis do CPC art. 219
  **nao se aplica** ao processo penal. O motor recusa `--unidade uteis` aqui.
- **CP art. 10** — prazo material **inclui** o dia do comeco, nao suspende e nao
  prorroga. E a regra **oposta** a processual. Na mesma data e no mesmo prazo,
  CP e CPP dao resultados diferentes — e isso e correto.
- **CPP art. 798-A** — o recesso **nao** suspende: I reu preso, nos processos
  vinculados a essa prisao; II Lei 11.340/2006 (Maria da Penha); III medidas
  urgentes, por despacho fundamentado. Use `--sem-suspensao MOTIVO`.
- **CPC art. 229 §2º** — litisconsortes com procuradores diferentes **nao** tem
  prazo em dobro em **autos eletronicos**. Como hoje quase tudo e
  PJe/eproc/e-SAJ/Projudi, o dobro e a excecao. O motor nao dobra sem `--autos`.
- **PAF federal (LC 227/2026)** — o fiscal federal **passou a ter recesso**
  (art. 5º-A) e virou regime **misto**: corridos por regra (art. 5º, I), mas
  impugnacao (art. 15), recurso ao CARF (art. 33) e o prazo residual (art. 5º-B)
  sao em **dias uteis**. Nesses, passe `--unidade uteis`. O direito
  intertemporal de prazo em curso em 14/01/2026 esta em aberto na LC.
- **CRPS** — so o 30 dias do Dec. 3.048/99 art. 305 §1º e regra. Prazo de
  **rito** vem do Regimento Interno (Portaria MPS 125/2026, ja alterada duas
  vezes em 2026) e muda por portaria: conferir, nao esta aqui.

## Feriados: o que entra e o que voce precisa dar

O motor separa **tres** calendarios que a versao anterior fundia num so:

1. **Ha expediente forense?** decide a publicacao (§2) e o termo inicial (§3).
   Fecha em **20/12 a 06/01** (Res. CNJ 244/2016 art. 1º).
2. **O prazo corre?** decide a contagem. Suspenso em **20/12 a 20/01**. De
   **07 a 20/01 o tribunal esta ABERTO e publicando** e mesmo assim o prazo nao
   corre (Res. CNJ 244/2016 art. 3º, par. unico). Sao duas janelas, nao uma.
3. **O dia conta no regime?** dias uteis x dias corridos.

Camadas de feriado:

| Camada | Conteudo | Onde |
|---|---|---|
| 1-2 | civil nacional e estadual | lib `holidays`, categoria `public` **apenas** |
| 3 | forense nacional: Semana Santa (quarta ao domingo), Carnaval **segunda e terca**, 11/08, 1º e 2/11, 8/12 | Lei 5.010/66 art. 62, embutido no motor |
| 4 | portaria do tribunal: Quarta de Cinzas, Corpus Christi, emendas, Dia do Servidor transferido, aniversario da comarca | `feriados/<TRIBUNAL>.json` |
| 5 | exclusoes: data que a lib marca mas que **tem expediente** | mesmo JSON, chave `exclusoes` |
| 6 | feriado municipal da comarca | **nao automatizavel** — vira ressalva |

**Ponto facultativo civil nao e feriado forense.** Quarta de Cinzas, Corpus
Christi, Dia do Servidor e vesperas **sairam** do calendario automatico: a
Lei 5.010/66 art. 62, III lista *"os dias de segunda e terca-feira de Carnaval"*
e para ai. Cinzas depende de portaria. Consequencia pratica: **sem o JSON do
tribunal o vencimento pode sair mais CEDO que o real**, e o motor avisa isso em
voz alta. Quando existir o JSON, o motor cita a portaria na saida.

Hoje o repositorio tem `feriados/TJMG.json` (Portaria Conjunta 1764/PR/2026).
Para outro tribunal: copie o formato, cite a portaria em `_fonte`, preencha
`vigencia` com o ano. Calendario de ano vencido faz o motor **avisar** em vez de
usar calado. Correcao pontual sem criar JSON: `--feriado-extra` e `--excluir`.

## Como responder ao advogado

1. Confirme **regime** e **natureza da data** antes de rodar. Sem as duas, nao rode.
2. Rode o script.
3. Mostre a **conta inteira**, nunca so a data final. A linha `CONTA:` da saida
   ja vem pronta:
   `disponibilizado em X -> publicado em Y (CPC art. 224 §2º) -> inicio em Z (§3º)
   -> N dias uteis no regime R, excluidos os feriados A e B -> vence em W`
4. Destaque `VENCE EM` **e** `PROTOCOLAR ATE` (D-2 uteis). A agenda marca o
   PROTOCOLAR ATE, nunca o vencimento.
5. Repasse todo `AVISO` que aparecer. Aviso engolido e o modo de falha da casa:
   erro engolido vira vazio, e vazio parece dado.
6. Feche SEMPRE com a ressalva de conferencia no PJe.
7. Cruze com o calculo manual antes de dar por certo. Nunca altere status de
   prazo em lote sem conferencia item a item.

## Autoteste

```bash
python3 scripts/test_prazo_cpc.py
```

A suite **exige** a lib `holidays` e morre sem ela — de proposito. Teste de
prazo que passa sem calendario nao e teste de prazo: era exatamente o que a
suite anterior fazia, e por isso os quatro defeitos de calendario passavam
verdes por ela.
