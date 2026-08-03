# Claude para advogados (marketplace JurisLabs)

Marketplace de plugins do Claude Code com skills que tiram a repeticao do dia do advogado. Curadoria da JurisLabs. Este e o destino do QR code da palestra "Claude para advogados".

## Como instalar

**1) No Terminal do seu Mac**, cole esta linha e dê Enter. Ela confere e instala o que falta (`git`, `uv`), sem senha e sem mexer no Python do sistema:
```
curl -LsSf https://raw.githubusercontent.com/VitorTempone1/jurislabs-plugins/main/install.sh | bash
```

**2) Quando aparecer `✅ Tudo pronto`**, abra o Claude Code e cole cada linha, uma de cada vez:
```
/plugin marketplace add VitorTempone1/jurislabs-plugins
/plugin install jurislabs-br@jurislabs
/plugin install jurislabs-prazos@jurislabs
/plugin install kit-advogado@jurislabs
```

A ordem importa: o `kit-advogado` usa os dois de cima. Ao instalar o kit, o Claude vai te perguntar o nome do escritório, sua OAB e qual pasta do computador usar pra guardar os casos — responda e pronto.

Depois e so pedir em portugues, ex.: "vê minhas intimações de hoje", "calcula o prazo dessa sentença", "abre a pasta do cliente Fulano".

> O `uv` e pre-requisito: o `jurislabs-br` sobe o MCP com `uv run` e o `jurislabs-prazos` usa `uv run` pra puxar os feriados (lib `holidays`) sozinho, sem mexer no Python do sistema.

Travou em algum ponto? O passo a passo detalhado (com o caminho manual, sem script) esta logo abaixo.

## Instalação passo a passo

Isso resolve o que costuma travar num Mac "limpo": falta o `git`, falta o `uv`, ou o `uv` acabou de ser instalado mas o Claude Code (ou o Terminal) ainda não sabe onde ele está.

**Antes de tudo: abra o app Terminal** (Lupa no canto superior direito → digite "Terminal" → Enter). É uma tela preta/branca com texto — é nela que você vai colar os comandos desta seção, **não** no Claude Code.

### Caminho fácil: rodar o script

1. Cole esta linha no Terminal e dê Enter (não precisa baixar nada antes):
   ```
   curl -LsSf https://raw.githubusercontent.com/VitorTempone1/jurislabs-plugins/main/install.sh | bash
   ```
2. O script confere, um por um: Claude Code instalado, `git` instalado, `uv` instalado. Pra cada um que faltar, ele instala sozinho (sem `sudo`, sem pedir sua senha) ou te diz exatamente o que fazer — por exemplo, clicar em "Instalar" numa janela que abre sozinha, ou fechar e abrir o Terminal de novo.
4. Quando aparecer `✅ Tudo pronto.`, o script mostra os 4 comandos `/plugin`. Copie, abra o Claude Code e cole um de cada vez, na ordem em que aparecem.
5. **Como saber que deu certo:** depois de `/plugin install jurislabs-br@jurislabs`, peça pro Claude "vê minhas intimações da OAB 123456/SP". Se ele chamar a ferramenta `consultar_djen` (em vez de dizer que não tem essa capacidade), o MCP está no ar.

Se o script parar com `❌`, ele diz exatamente o comando pra rodar. Rode, feche e abra o Terminal de novo, e cole de novo o mesmo comando — pode rodar quantas vezes quiser, ele só faz o que ainda falta.

### Caminho manual (sem rodar script)

1. **Confirme que tem o Claude Code.** No Terminal, rode `claude --version`. Se der "command not found", instale primeiro em https://claude.com/download.
2. **Confirme que tem o `git`.** Rode `git --version`.
   - Se aparecer uma janela "As ferramentas de linha de comando não estão instaladas", clique em **Instalar** e espere (alguns minutos, precisa de internet). Depois rode `git --version` de novo até aparecer um número de versão.
3. **Instale o `uv`** (o programa que sobe o MCP sozinho, sem mexer no Python do seu Mac). Rode:
   ```
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
   Vai aparecer um texto dizendo onde ele foi instalado (geralmente `~/.local/bin`).
4. **Feche o Terminal e abra um novo** (importante: sem isso o comando `uv` some para os próximos programas, inclusive o Claude Code). Confirme rodando `uv --version` — tem que mostrar um número, não erro.
5. **Se o Claude Code já estava aberto**, feche e abra ele de novo também, pelo mesmo motivo do passo anterior.
6. **Agora sim**, no Claude Code, cole um de cada vez, nesta ordem:
   ```
   /plugin marketplace add VitorTempone1/jurislabs-plugins
   /plugin install jurislabs-br@jurislabs
   /plugin install jurislabs-prazos@jurislabs
   /plugin install kit-advogado@jurislabs
   ```
7. **Confirme que funcionou** pedindo em português: "vê minhas intimações da OAB 123456/SP dos últimos 7 dias". Se o Claude responder com dados (ou com erro de bloqueio de IP, que é outro assunto — ver aviso no README do `jurislabs-br`), o MCP subiu certo.

## Plugins
| Plugin | O que faz | Status |
|---|---|---|
| **jurislabs-br** | MCP com fontes juridicas oficiais BR: DJEN (publicacoes por OAB), DataJud (andamento) e LexML (legislacao) | v0.1 pronto |
| **jurislabs-prazos** | Calculadora de prazos processuais pelo CPC (dias uteis, termo inicial, recesso, feriados) | v0.1 pronto |
| **kit-advogado** | O kit do escritorio: pasta por cliente, briefing do caso sempre atualizado e tres advogados de IA (pesquisa, parte contraria, estrategia) | v0.1 pronto |

## O kit-advogado

E o plugin que transforma o Claude no assistente do seu escritorio. Depois de instalado, voce fala em portugues normal e ele faz:

- **Organiza seus casos.** "Abre a pasta do cliente Fulano" cria a estrutura da pasta e mantem um `briefing.md` do caso com o historico datado, pra voce nunca mais reconstruir o que ja aconteceu.
- **Le processo grande.** "Le esse PDF do processo" pega um PDF de centenas de paginas e devolve linha do tempo, partes, pedidos, decisoes e o que esta pendente.
- **Poe tres advogados de IA no seu caso.** Um pesquisa jurisprudencia e tese a favor, outro ataca tudo como se fosse a parte contraria, e o terceiro le a briga entre os dois e monta a estrategia.

Ele pergunta o que precisa saber na hora de instalar (nome do escritorio, sua OAB, qual pasta usar) e depois na primeira conversa (sua area, seus tribunais, seu tom).

**Seus dados ficam no seu computador.** O kit grava os casos na pasta que voce escolher, na sua maquina. A JurisLabs nao ve nada disso. Escolha uma pasta que **nao** esteja dentro de um repositorio do GitHub nem numa pasta compartilhada.

Instalacao passo a passo, com Mac e Windows separados e os erros comuns de cada um: [`plugins/kit-advogado/INSTALACAO.md`](plugins/kit-advogado/INSTALACAO.md).

> Depois de instalar, **ligue o auto-update dos plugins**. Marketplace de terceiro vem com auto-update desligado, e sem isso voce nao recebe as skills novas. O passo esta no `INSTALACAO.md`.

Roadmap do pacote completo (escrita, documentos, fontes juridicas BR, produtividade): ver `../CATALOGO.md`.

## Aviso
As skills sao APOIO ao trabalho do advogado. Nenhuma substitui a conferencia oficial (PJe/autos) nem a decisao juridica. A palavra final e sempre do advogado.

## Publicacao
Publicado como repo publico proprio: `VitorTempone1/jurislabs-plugins` — destino do QR da palestra.
