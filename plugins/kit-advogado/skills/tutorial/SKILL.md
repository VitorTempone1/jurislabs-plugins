---
name: tutorial
description: >
  Escreve um passo a passo pro advogado executar à mão, quando alguma coisa não sai por
  API (painel de terceiro, login do tribunal, botão que só existe na interface). Sai como
  checklist em Markdown, escrito pra leigo: uma ação por passo, nome exato do botão, link
  direto e o que a pessoa tem que VER pra saber que deu certo. Use quando ele disser
  "faz um tutorial", "passo a passo", "me ensina", "como eu faço", "explica como se fosse
  pra leigo", ou quando você concluir uma investigação e o conserto depender de painel.
---

# tutorial — passo a passo pra executar à mão

Serve pro que **não sai automatizado**: painel de terceiro, botão atrás de login,
sistema de tribunal, coisa que exige o olho humano.

## Antes de escrever

1. **Tente fazer sozinho primeiro.** Se der pra resolver sem ele, resolva e não
   escreva tutorial nenhum. Tutorial é o plano B, não o reflexo.
2. **Não invente caminho de menu.** Se não tem certeza do nome do botão, busque a
   documentação oficial (WebSearch/WebFetch) e cite o link. Se mesmo assim ficar
   incerto, escreva o que sabe, marque o passo como incerto e dê o plano B
   ("se não achar, o suporte responde em X").
3. **Separe o que já é fato do que é hipótese.** Se o conserto depende de um
   diagnóstico, o tutorial começa pelo diagnóstico, não pelo conserto.

## Como escrever cada passo

- **Uma ação por passo.** "Clique em X" e "cole o número" são dois passos, não um.
- **Nome exato do botão, entre aspas**, do jeito que aparece na tela. Nada de
  "vá nas configurações".
- **Link direto** sempre que existir (a URL já com o identificador certo, não a
  home do serviço).
- **O que você vai ver:** toda ação termina dizendo o resultado esperado. É assim
  que ele sabe que acertou sem precisar perguntar.
- **Se der errado:** nos passos que costumam falhar, uma linha do erro provável e
  a saída.
- **Zero jargão não explicado.** A primeira vez que uma sigla aparece, explique em
  meia linha.
- **Avise o que é irreversível** antes do passo, não depois. Se algo vai ser
  apagado, mande copiar pra um arquivo antes.
- **Um assunto por vez.** Se são dois problemas, são duas partes, e a segunda só
  começa depois da primeira ter sido conferida. Mexer nos dois junto impede saber
  qual resolveu.

## Como termina

Todo tutorial acaba com **"como saber se deu certo"** — de preferência uma
checagem que *você* consegue fazer depois. Diga explicitamente: "me avisa quando
terminar que eu reconfiro".

Se o efeito demora (fila do tribunal, propagação, publicação no diário), diga
quanto tempo esperar antes de conferir. Sem isso ele confere cedo, vê o estado
velho e acha que falhou.

## Formato

Arquivo Markdown com caixinhas `- [ ]`, gravado em
`${user_config.pasta_escritorio}/tutoriais/AAAA-MM-DD-<tema>.md`. Caixinha porque
tutorial longo se faz em duas sentadas e ele precisa saber onde parou.

Estrutura: título → uma frase dizendo o que vamos resolver → bloco "em três
linhas" → uma seção por parte → os passos como `- [ ]` (o item é a ação, a linha
abaixo é o detalhe e o que vai ver) → seção final "como saber se deu certo".

No chat, junto: **resumo de 5 linhas**, não o tutorial inteiro repetido.
