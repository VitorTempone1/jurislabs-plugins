#!/usr/bin/env bash
# install.sh — prepara o Mac (ou Linux) para instalar os plugins JurisLabs no Claude Code.
# Rode ISSO no Terminal, ANTES de colar os comandos /plugin no Claude Code:
#
#   bash install.sh
#
# Idempotente: pode rodar quantas vezes quiser, só faz o que ainda falta.

set -uo pipefail

ok()   { printf "✅ %s\n" "$1"; }
falta() { printf "❌ %s\n" "$1"; }
info() { printf "   %s\n" "$1"; }

erro_final() {
  echo
  falta "$1"
  echo
  echo "Corrija o passo acima e cole de novo o mesmo comando de instalação"
  exit 1
}

echo "== Verificando pré-requisitos do MCP JurisLabs =="
echo

# 1) Claude Code precisa existir — é ele quem instala os plugins.
if command -v claude >/dev/null 2>&1; then
  ok "Claude Code encontrado ($(command -v claude))."
else
  erro_final "Não achei o Claude Code instalado. Instale primeiro em https://claude.com/download e depois cole de novo o mesmo comando de instalação."
fi

# 2) git — o Claude Code usa git por baixo dos panos para baixar o marketplace
#    (comando "/plugin marketplace add").
if command -v git >/dev/null 2>&1; then
  ok "git encontrado ($(command -v git))."
else
  if [[ "$(uname -s)" == "Darwin" ]]; then
    falta "git não encontrado. No Mac ele vem com as \"Ferramentas de Linha de Comando\"."
    info "Vou abrir a instalação agora. Uma janela vai aparecer — clique em \"Instalar\" e espere terminar"
    info "(alguns minutos). Depois cole de novo o mesmo comando de instalação"
    xcode-select --install 2>/dev/null || true
    exit 1
  else
    erro_final "git não encontrado. Instale com o gerenciador de pacotes da sua distribuição (ex.: sudo apt install git) e rode de novo."
  fi
fi

# 3) uv — é quem sobe o MCP e baixa suas dependências sozinho, sem mexer no
#    Python do sistema. Sem sudo, instala só para o usuário atual.
UV_BIN=""
if command -v uv >/dev/null 2>&1; then
  UV_BIN="$(command -v uv)"
  ok "uv encontrado ($UV_BIN)."
else
  falta "uv não encontrado. Instalando agora (sem sudo, só para o seu usuário)..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  echo

  # o instalador põe o uv em ~/.local/bin (ou ~/.cargo/bin em versões antigas);
  # procura nos dois antes de desistir, sem depender do usuário reabrir o terminal.
  for candidato in "$HOME/.local/bin/uv" "$HOME/.cargo/bin/uv"; do
    if [[ -x "$candidato" ]]; then
      UV_BIN="$candidato"
      break
    fi
  done

  if [[ -z "$UV_BIN" ]]; then
    erro_final "O instalador do uv rodou mas não achei o programa depois. Feche e abra o Terminal de novo e cole de novo o mesmo comando de instalação"
  fi
  ok "uv instalado ($UV_BIN)."
fi

# 4) PATH — o Claude Code (se já estiver aberto) só enxerga o uv se ele
#    estiver no PATH do processo dele. Se acabamos de instalar, o Claude Code
#    aberto AGORA ainda não sabe disso.
if ! command -v uv >/dev/null 2>&1; then
  echo
  falta "uv foi instalado, mas este terminal ainda não está enxergando ele no PATH."
  info "Fresh install: feche este Terminal, abra um novo e cole de novo o mesmo comando de instalação"
  info "(Se o Claude Code já estava aberto, feche e abra ele de novo também.)"
  exit 1
fi

echo
ok "Tudo pronto. Agora abra (ou reabra) o Claude Code e cole, uma linha de cada vez:"
echo
echo "  /plugin marketplace add VitorTempone1/jurislabs-plugins"
echo "  /plugin install jurislabs-br@jurislabs"
echo "  /plugin install jurislabs-prazos@jurislabs"
echo "  /plugin install kit-advogado@jurislabs"
echo
info "A última linha (kit-advogado) é o kit do escritório: pasta de cada cliente,"
info "briefing do caso e os três advogados de IA. Ela precisa das duas de cima,"
info "então cole na ordem. Ao instalar, o Claude vai perguntar o nome do seu"
info "escritório, sua OAB e qual pasta usar — responda e pronto."
echo
