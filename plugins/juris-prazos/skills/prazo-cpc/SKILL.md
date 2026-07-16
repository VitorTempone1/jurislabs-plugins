---
name: prazo-cpc
description: Calcula prazo processual pelo CPC (dias uteis) a partir da data de disponibilizacao no DJE/DJEN. Use quando o advogado pedir "calcular prazo", "quando vence", "que dia cai o prazo", "prazo de X dias da publicacao/intimacao", ou passar uma data de disponibilizacao e um numero de dias. Aplica CPC art. 224 §§2-3 (termo inicial), art. 219 (dias uteis) e art. 220 (recesso), com feriados nacionais/estaduais.
---

# Calculadora de prazos processuais (CPC)

Calcula o vencimento de um prazo processual em dias uteis, a partir da data de disponibilizacao no Diario (DJE/DJEN).

## REGRA INEGOCIAVEL
O calculo e **apoio, nao verdade final**. NUNCA afirme o prazo como oficial e SEMPRE feche com a ressalva de conferir no PJe/autos. Feriado municipal da comarca e portaria pontual do tribunal podem nao estar na base. Se o advogado nao informar tribunal/UF, avise que os feriados estaduais/facultativos (Carnaval, Corpus Christi, etc.) nao entraram e que o calculo saiu conservador.

## Como usar
Rode o script `scripts/prazo_cpc.py`. Ele so precisa da stdlib; se a lib opcional `holidays` estiver instalada, entram os feriados nacionais/estaduais/facultativos (recomendado: `pip install holidays`).

```bash
python3 scripts/prazo_cpc.py --disp 2026-07-03 --dias 15 --tribunal TJMG --hoje 2026-07-15
```

Parametros:
- `--disp AAAA-MM-DD` (obrigatorio): data de disponibilizacao no Diario.
- `--dias N` (obrigatorio): prazo em dias uteis.
- `--tribunal TJXX` ou `--uf XX`: para carregar os feriados estaduais/facultativos certos. Sem isso, o calculo fica conservador.
- `--ja-publicado`: use quando a data informada JA e a data de publicacao (pula o art. 224 §2).
- `--hoje AAAA-MM-DD`: para mostrar quantos dias uteis faltam.
- `--json`: saida estruturada.

## O que ele aplica
- **CPC art. 224 §2:** considera-se publicado no 1o dia util seguinte a disponibilizacao.
- **CPC art. 224 §3:** o prazo comeca a correr no 1o dia util seguinte a publicacao.
- **CPC art. 219:** contam-se apenas os dias uteis.
- **CPC art. 220:** recesso de 20/12 a 20/01 (suspende).

## Como responder ao advogado
1. Rode o script com os dados que ele deu.
2. Mostre a cadeia: disponibilizacao -> publicacao (§2) -> inicio (§3) -> vencimento.
3. Destaque o **vencimento** e, se tiver `--hoje`, os dias uteis restantes.
4. Feche SEMPRE com a ressalva de conferencia no PJe. Se faltou tribunal/UF, peca pra confirmar e avise do calculo conservador.

## Exemplo
Disponibilizacao sexta 2026-07-03, prazo de 5 dias, TJMG:
publicacao seg 06/07 (§2), inicio ter 07/07 (§3), vencimento seg 2026-07-13 (art. 219).
