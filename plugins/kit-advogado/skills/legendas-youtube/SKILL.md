---
name: legendas-youtube
description: Pega a legenda de um vídeo do YouTube e devolve o texto limpo, sem baixar o vídeo. É o caminho rápido quando o vídeo já tem legenda. Use quando o advogado colar um link do YouTube pedindo "transcreve", "o que esse vídeo diz", "me resume essa aula/audiência/live", "pega a legenda", "manda a transcrição".
allowed-tools: Bash, Read, Write
---

# Legendas do YouTube

Baixa **só a legenda** (não o vídeo), converte para texto corrido e devolve.
Não precisa de ffmpeg e não usa transcrição por IA: é o caminho barato e rápido.

Só funciona no YouTube e só quando o vídeo **tem** legenda (própria ou
automática). Se não tiver, ou se o link for de outro site, use a skill
`transcrever-video`, que transcreve o áudio na máquina do advogado.

## Como rodar

Pré-requisito: o `uv` instalado (https://docs.astral.sh/uv/). Ele baixa a
dependência sozinho na primeira vez, sem instalar nada no Python do sistema.

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/legendas-youtube/scripts/legendas_youtube.py" "<endereço do vídeo>"
```

Opções:

- `--tempos` — cada trecho vem com `[M:SS]` na frente. Use quando o advogado
  precisa citar minutagem (audiência gravada, depoimento).
- `--idiomas pt,pt-BR,en` — ordem de preferência. O padrão já é esse.
- `--saida ARQUIVO` — grava em arquivo em vez de despejar no chat. **Use sempre
  que a transcrição for longa**: o texto inteiro no chat consome o limite do
  plano à toa.

Antes de rodar, pergunte **uma coisa só**: quer com marcação de tempo ou texto
corrido?

## Onde gravar

Se o vídeo tem a ver com um caso, grave dentro da pasta do caso:

```
${user_config.pasta_escritorio}/clientes/<slug>/reuniao/AAAA-MM-DD-<assunto>.transcricao.md
```

Fora disso, grave em `${user_config.pasta_escritorio}/transcricoes/`.

## Regras

- **Nunca altere o conteúdo.** Palavra e sentido saem como estão. Você pode
  juntar as linhas em parágrafos coerentes e consertar quebra no meio da frase;
  não pode reescrever, resumir dentro do arquivo nem "melhorar".
- Depois de gravar, entregue no chat **o resumo**, não a transcrição inteira.
- Legenda automática erra nome próprio, número e termo técnico. Ao usar qualquer
  trecho como prova ou citação, marque `⚠️ legenda automática, conferir no áudio`.
- Se o vídeo tem conteúdo de cliente, ele é sigiloso igual: fica na pasta do
  caso, não vai pra lugar nenhum.

## Se der errado

- **"não tem legenda nos idiomas pedidos"** — tente `--idiomas en` ou
  `--idiomas pt-BR`; se ainda assim não houver, o vídeo não tem legenda: passe
  para `transcrever-video`.
- **Erro de idade ou região** — o vídeo exige login. Não contorne: peça ao
  advogado o link de outro lugar ou o arquivo.
- **`uv: command not found`** — o `uv` não está instalado ou o terminal foi
  aberto antes da instalação. Instale e **feche e reabra** o Claude Code.

## Autoteste

Para conferir que o conversor de legenda continua correto depois de qualquer
mudança:

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/legendas-youtube/scripts/legendas_youtube.py" --autoteste
```
