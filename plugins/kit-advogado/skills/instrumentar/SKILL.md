---
name: instrumentar
description: Regra e método pra problema PERSISTENTE. Quando uma tentativa de conserto já falhou 2+ vezes no mesmo problema, PARE de adivinhar e instrumente pra ver o comportamento real antes de mexer de novo. Use quando o advogado disser "de novo não funcionou", "já tentamos várias coisas", "continua o mesmo erro", "isso tá persistente", ou quando você mesmo perceber que está na 2ª+ tentativa do mesmo sintoma.
---

# Instrumentar antes de consertar (problema persistente)

**A regra:** falharam **2 tentativas** no mesmo problema? Pare de adivinhar.
Instrumente, observe o comportamento REAL, e só então conserte.

Vale pra qualquer coisa que "não funciona": um script que não roda, uma
integração que não traz o dado, um arquivo que some, um relatório que vem vazio,
um comando que dá certo numa máquina e não na outra.

## Por que

Adivinhar em problema persistente vira um ciclo tóxico: "conserto confiante →
ainda quebrado → outro conserto confiante → ainda quebrado". Cada tentativa
parece certa e falha. Isso queima tempo, dinheiro e confiança. Instrumentar
quebra o ciclo: você **vê** onde quebra, e o conserto costuma ser de uma linha.

Sinal claro de que você está adivinhando: trocar a ABORDAGEM inteira sem saber
ONDE exatamente o fluxo quebra.

## O método (7 passos)

1. **Formule a pergunta que decide.** Não "por que não funciona", e sim uma
   pergunta binária: *o arquivo chega? o valor está preenchido? na ordem certa?
   com que conteúdo?* A instrumentação existe pra responder ISSO.
2. **Escolha o instrumento** (cardápio abaixo).
3. **Instrumente de forma VISÍVEL e TEMPORÁRIA.** Marque tudo com
   `DEBUG TEMPORÁRIO`. Prefira imprimir na tela a esconder num log que ninguém
   abre.
4. **Reproduza.** Você reproduz, ou o advogado reproduz e manda o print. Coisa
   que depende de janela do sistema, login ou tempo de resposta muitas vezes só
   reproduz na mão de quem está na frente da máquina.
5. **Leia a evidência e ache a causa RAIZ.** Compare sempre **um caso que FALHA
   com um que FUNCIONA** — a diferença é o problema.
6. **Conserte na raiz** (a menor mudança no lugar certo). Se o conserto for numa
   função que várias coisas chamam, conserte lá, não em cada chamador.
7. **REMOVA toda a instrumentação** e valide com o advogado.

## Cardápio de instrumentos

| Sintoma | Instrumento |
|---|---|
| "Não acontece nada" quando clico / rodo | Imprimir cada etapa com **hora em milissegundos**: começou, recebeu, terminou |
| Valor "some" / vem vazio | Imprimir o valor **antes e depois** de cada transformação, não só no fim |
| "Funciona 1 em N vezes" | Hora em milissegundos + a **ordem** dos eventos. Intermitência é quase sempre corrida entre duas coisas |
| "Funciona nesta máquina e não naquela" | Isole a variável: versão do arquivo, sistema, variável de ambiente, permissão de pasta |
| "Funciona no navegador A e não no B" | Testar o mesmo endereço nos dois; navegador de privacidade bloqueia coisa em silêncio |
| Integração / site que não responde | Registrar o pedido, a resposta e o código de status; testar o endereço isolado |
| Arquivo/pasta que "não existe" mas existe | Imprimir o caminho **exatamente** como foi montado, com aspas, e comparar caractere a caractere. Acento e espaço no nome quebram de formas invisíveis |

## Regras de ouro

- **Instrumentação é visível e temporária.** Marque `DEBUG TEMPORÁRIO`, e no
  passo 7 remova TUDO (confira procurando pela marca).
- **Compare falha × sucesso.** A causa mora na diferença.
- **Não troque a abordagem às cegas.** Primeiro descubra ONDE quebra; só então
  decida o que mudar.
- **Erro engolido vira vazio, e vazio parece dado.** Se um passo falha em
  silêncio e o resultado sai vazio, ninguém percebe que quebrou: parece só que
  "não tinha nada". Todo erro tem que aparecer.
- **Hora em milissegundos** revela corridas que a hora em segundos esconde.

## O caso que originou a regra

- **Sintoma:** num formulário, anexar documento por **clique** não funcionava
  (só arrastando o arquivo).
- **O que deu errado:** 4 tentativas trocando a ABORDAGEM inteira do anexo. Todas
  pareciam certas, todas falharam. Dias perdidos.
- **A virada:** um painel na própria tela registrando cada evento. Ele mostrou que
  o arquivo **chegava** em toda tentativa, e mesmo assim nada aparecia. Ou seja: o
  problema não era o clique nem o navegador, era o que acontecia **depois** de o
  arquivo chegar.
- **Causa raiz:** o código limpava o campo antes de terminar de copiar o arquivo
  pra memória. Arrastar funcionava porque não limpava o campo.
- **Conserto:** uma linha.
- **Lição:** era pra ter instrumentado na 3ª tentativa, não na 10ª.
