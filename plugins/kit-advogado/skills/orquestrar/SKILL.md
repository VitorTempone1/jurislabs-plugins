---
name: orquestrar
description: >
  Método pra tarefa de VOLUME (vários casos, vários documentos, pesquisar + revisar) sem
  estourar o limite do plano. Use SEMPRE que o trabalho pedir mais de um agente, ou quando
  você pensar "vou abrir um agente pra isso". Rege quem chama quem e o que NÃO delegar.
  Dispara também quando o advogado disser "tá lento", "gasta menos", "delega", "usa os
  agentes", "atingi o limite", ou reclamar de retrabalho.
---

# Orquestrar sem estourar o limite

O gasto quase nunca vem do trabalho em si. Vem da forma de organizar: um agente
relendo o que outro já leu, transcrição inteira aberta quando o resumo bastava,
e pedido de setenta linhas produzindo resposta gorda na mesma medida.

Isso importa de verdade aqui: no plano Claude Pro existe um teto por janela de
tempo. Quem organiza mal atinge o teto no meio de um prazo.

## O time do kit

| Agente | Faz |
|---|---|
| `pesquisa-juridica` | jurisprudência, legislação, teses a favor |
| `parte-contraria` | ataca tudo que nós montamos |
| `head-juridico` | lê a briga dos dois e decide a estratégia |

A ordem é sempre **pesquisa → contrária → head**. Pular etapa estraga o head, e
refazer custa mais do que fazer certo na primeira.

## Antes de delegar, três perguntas

1. **Resolve em umas 3 ações?** Faça direto. Abrir um agente tem custo fixo de
   arranque; abaixo disso você é mais rápido e mais barato fazendo na hora.
2. **As frentes são mesmo separadas?** Fatiar por arquivo quando o problema é um
   só compartilhado = pagar N vezes pelo mesmo achado. Só divida quando as partes
   forem independentes de verdade.
3. **Já existe um agente com esse contexto aberto?** Continue ele em vez de abrir
   outro. O novo paga a leitura toda de novo.

## O pedido

Cinco linhas, não setenta. O que ele precisa ter:

- **O alvo**: a pasta do caso, o arquivo, o endereço. Sem isso o agente sai
  varrendo o computador, e varredura é o que mais custa.
- **Uma entrega**, não cinco. Cinco tarefas num pedido só viram meia hora em
  série; separadas, saem em paralelo no tempo da mais lenta.
- **Critério de pronto objetivo**: "a tabela de prazos preenchida e conferida",
  "as três teses com fonte recuperada". Sem isso vem ida e volta.
- **O que não é dele**: diga o que outro agente está tocando agora, pra não
  escreverem no mesmo arquivo.

## Regras duras

- **Resumo primeiro, documento inteiro só se precisar.** Transcrição de reunião,
  PDF de 400 páginas e processo inteiro se leem pelo trecho, buscando, não do
  começo ao fim. É a maior economia disponível, de longe.
- **Quem constrói não confere.** Uma passada de conferência só, no fim. Conferir
  duas vezes é desperdício puro.
- **Ler o documento antes de sair pesquisando na internet.** Resolve a maior
  parte por uma fração do custo. Busca externa é pra CONFIRMAR, não pra descobrir
  o que o próprio arquivo já dizia.
- **Nenhum agente apaga nada.** Nem documento, nem checkpoint, nem saída de outro
  agente. Corrigiu? Novo checkpoint explicando.
- **Nenhum agente protocola, assina ou envia.** Deixa a minuta pronta e avisa. O
  último clique é sempre do advogado.
- **Você confere no fim.** Reler a saída e conferir a fonte de uma citação é mais
  barato que abrir um agente revisor, e pega quase tudo.

## Depois

Se o trabalho gerou uma decisão que um agente futuro estragaria sem saber (uma
tese abandonada de propósito, um pedido que saiu por escolha do cliente), escreva
como checkpoint no `briefing.md`. Uma linha ali economiza uma sessão inteira
depois.
