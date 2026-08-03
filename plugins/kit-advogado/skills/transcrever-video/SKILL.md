---
name: transcrever-video
description: Transcreve áudio e vídeo em texto, na própria máquina do advogado, sem mandar nada pra fora. Serve pra gravação de reunião com cliente, audiência gravada, áudio de WhatsApp, e vídeo de qualquer site (YouTube, Instagram, TikTok, X, Facebook, Vimeo e outros). Use quando ele disser "transcreve essa reunião", "transcreve esse áudio", "o que esse vídeo diz", ou mandar um arquivo de áudio/vídeo ou um link com intenção de transcrever.
allowed-tools: Bash, Read, Write
---

# Transcrever vídeo e áudio

Transcreve **na máquina do advogado**. Nada é enviado para serviço externo, o que
é exatamente o que permite transcrever reunião com cliente sem quebrar sigilo.

Funciona com duas origens:

- **arquivo local** — a gravação da reunião, o áudio de WhatsApp, o vídeo da
  audiência que ele baixou;
- **link** — YouTube, Instagram, TikTok, X, Facebook, Vimeo e mais de mil sites.

> **Se for link do YouTube, tente primeiro a skill `legendas-youtube`.** Quando o
> vídeo já tem legenda, ela resolve em segundos. Esta aqui só vale a pena quando
> não existe legenda, quando o arquivo é local, ou quando o assunto é sigiloso.

## Como rodar

Pré-requisito: o `uv` (https://docs.astral.sh/uv/). Ele baixa as dependências
sozinho na primeira vez, sem instalar nada no Python do sistema. Não precisa de
ffmpeg.

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/transcrever-video/scripts/transcrever_video.py" "<arquivo ou endereço>" --idioma pt --saida "<arquivo de saída>"
```

Opções:

- `--idioma pt` — passe sempre em gravação em português. Sem isso ele detecta, e
  detecção erra em áudio ruim ou com muito silêncio no começo.
- `--tempos` — cada trecho com `[M:SS]` na frente. **Use em audiência e
  depoimento**, onde a minutagem é o que permite citar.
- `--modelo small|medium|large-v3` — padrão `medium`. `small` é bem mais rápido e
  erra mais; `large-v3` é o mais preciso e pode levar bastante tempo numa
  gravação longa.
- `--saida ARQUIVO` — **use sempre.** Transcrição inteira despejada no chat
  queima o limite do plano à toa.

Antes de rodar, avise: **na primeira vez o modelo é baixado (cerca de 1,5 GB) e
demora alguns minutos.** Isso acontece uma vez só. Depois pergunte duas coisas,
uma por vez: precisa de marcação de tempo? o áudio é em português?

## Onde gravar

Reunião ou audiência de um caso vai dentro da pasta do caso:

```
${user_config.pasta_escritorio}/clientes/<slug>/reuniao/AAAA-MM-DD-<assunto>.transcricao.md
```

Depois de gravar a transcrição, **escreva também o `.resumo.md` ao lado**, com:
objetivo da conversa, principais conclusões, tópicos, próximos passos e itens de
ação. É o resumo que a skill `escritorio` vai ler nas próximas vezes; a
transcrição completa só é aberta para tirar dúvida pontual, buscando o trecho.
Essa disciplina é o que faz o kit caber no plano Claude Pro.

Fora de caso, grave em `${user_config.pasta_escritorio}/transcricoes/`.

## Regras

- **Nunca altere o conteúdo.** Palavra e sentido saem como estão. Consertar
  quebra de linha e formar parágrafos, sim; reescrever, não.
- **Transcrição automática erra.** Nome próprio, número de processo, valor e
  termo técnico saem errados com frequência. Todo trecho que virar prova, citação
  ou número em peça leva `⚠️ transcrição automática, conferir no áudio`. Nenhum
  valor e nenhum prazo entram em documento vindo daqui sem conferência no áudio.
- **Sigilo.** A gravação e a transcrição ficam na pasta do caso. Não anexe em
  e-mail, não publique, não mande pra serviço externo, não coloque em pasta
  sincronizada com terceiro.
- **Gravação de conversa e de audiência tem regra própria.** Se o advogado
  perguntar se pode usar aquilo como prova, essa é decisão jurídica dele: você
  transcreve, não opina sobre licitude da prova sem ele pedir análise.

## Se der errado

- **`uv: command not found`** — o `uv` não está instalado, ou o terminal foi
  aberto antes de instalar. Instale e **feche e reabra** o Claude Code.
- **Muito lento** — troque para `--modelo small` e rode de novo. Gravação de duas
  horas em `large-v3` num notebook comum pode levar horas.
- **Saiu em espanhol / saiu embaralhado** — faltou `--idioma pt`.
- **O download do link falha** — o site pode exigir login. Peça ao advogado para
  baixar o arquivo pelo próprio site e rode com o caminho do arquivo.

## Autoteste

```bash
uv run "${CLAUDE_PLUGIN_ROOT}/skills/transcrever-video/scripts/transcrever_video.py" --autoteste
```
