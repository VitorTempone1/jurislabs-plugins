# Instalação do JurisLabs OS

Passo a passo do zero absoluto. Você não precisa saber programar, não precisa instalar Node,
não precisa saber o que é git. São 15 minutos.

Cada passo tem **uma única ação** e diz **o que você tem que ver na tela** pra saber que deu
certo. Se o que apareceu na sua tela for diferente do que está escrito aqui, pare e chame no
WhatsApp da mentoria. Não tente adivinhar.

---

## Antes de tudo: sua conta Claude precisa ser paga

**O plano gratuito do Claude não roda o Claude Code.** Não é limite de uso, não é "roda mais
devagar": simplesmente não abre.

O piso é o **Claude Pro (US$ 20/mês)**, e ele roda bem o kit inteiro. Max, Team e Enterprise
também servem. Se você tem plano maior, ótimo, mas não é requisito.

Confira em [claude.ai/settings/billing](https://claude.ai/settings/billing).

**O que você vai ver:** a palavra **Pro**, **Max**, **Team** ou **Enterprise** no seu plano
atual. Se aparecer **Free**, faça o upgrade antes de continuar. Nada abaixo funciona sem isso.

---

## Antes de tudo, parte 2: o que é o terminal

O terminal é uma janela preta (ou branca) onde você digita comandos em vez de clicar em botões.
É onde o Claude Code mora. Você vai usar ele umas 4 vezes na vida, só pra instalar. Depois
disso, é só conversa em português.

Não quer nem abrir o terminal? Pule direto pro **Plano B: o aplicativo Claude Code** no fim
deste documento. Ele faz tudo por menu, sem terminal nenhum, e serve pra Mac e pra Windows.

---

# Caminho Mac

## Passo 1. Abra o Terminal

Aperte **Command + barra de espaço**, digite `Terminal` e aperte **Enter**.

**O que você vai ver:** uma janela com fundo branco ou preto, com uma linha de texto terminada
por `$` ou `%` e o cursor piscando.

## Passo 2. Instale o Claude Code

Copie a linha abaixo inteira, cole no Terminal e aperte **Enter**.

```
curl -fsSL https://claude.ai/install.sh | bash
```

Vai demorar de 30 segundos a 2 minutos. Vai passar texto correndo na tela. Isso é normal.

**O que você vai ver:** o texto para de correr e o cursor volta a piscar numa linha nova.

## Passo 3. Feche e abra o Terminal de novo

Feche a janela (Command + Q) e abra de novo (Passo 1).

Esse passo parece bobo e não é: é ele que faz o computador enxergar o programa recém-instalado.
Pular esse passo é a causa mais comum de "não funcionou".

**O que você vai ver:** uma janela nova, limpa.

## Passo 4. Confirme que instalou

Digite e aperte **Enter**:

```
claude --version
```

**O que você vai ver:** um número de versão, tipo `2.1.211 (Claude Code)`.

**Se der errado:** apareceu `command not found: claude`. Reinicie o Mac e repita este passo.
Se continuar, vá pro **Plano B**.

## Passo 5. Crie a pasta do seu escritório

Ainda no Terminal, digite e aperte **Enter**:

```
mkdir -p ~/Documentos/Escritorio
```

Se o seu Mac estiver em inglês, troque `Documentos` por `Documents`.

**O que você vai ver:** nada. Nenhuma mensagem. No Terminal, silêncio quer dizer que deu certo.

**Importante:** essa pasta vai guardar dado de cliente. Escolha uma pasta **fora** de qualquer
projeto de programação ou pasta sincronizada com repositório de código. `Documentos` está ótimo.

## Passo 6. Entre na pasta e abra o Claude

Digite e aperte **Enter**:

```
cd ~/Documentos/Escritorio && claude
```

**O que você vai ver:** na primeira vez, ele abre o navegador pedindo pra você fazer login na
sua conta Claude. Faça o login, autorize, e volte pro Terminal.

Depois do login, você vai ver a tela do Claude Code com um campo de texto esperando você
escrever. **Você chegou.** Pule pra parte **Instalando o kit**, mais abaixo.

---

# Caminho Windows

Três avisos antes de começar, e os três são causa de travamento:

1. Use **PowerShell**, não o "Prompt de Comando" (CMD). São programas diferentes.
2. Use o PowerShell normal, **não** o que tem **(x86)** no nome.
3. Você **não** precisa ser administrador do computador.

## Passo 1. Abra o PowerShell certo

Clique no menu Iniciar e digite `PowerShell`.

Na lista que aparecer, clique em **"Windows PowerShell"**.

**NÃO** clique em "Windows PowerShell (x86)". **NÃO** clique em "Prompt de Comando".

**O que você vai ver:** uma janela azul-escura, e a última linha começando com `PS C:\Users\`
seguido do seu nome. **Se não tiver o `PS` no começo da linha, você abriu o programa errado.**
Feche e repita o passo.

## Passo 2. Instale o Claude Code

Copie a linha abaixo inteira, cole no PowerShell (clique com o botão direito dentro da janela
para colar) e aperte **Enter**.

```
irm https://claude.ai/install.ps1 | iex
```

**O que você vai ver:** texto correndo por 30 segundos a 2 minutos, e depois o cursor voltando
a piscar numa linha nova que começa com `PS C:\`.

## Passo 3. Feche e abra o PowerShell de novo

Feche a janela no X e abra de novo (Passo 1).

Sem isso, o Windows continua não enxergando o programa que acabou de ser instalado.

**O que você vai ver:** uma janela nova, limpa, começando com `PS C:\Users\`.

## Passo 4. Confirme que instalou

Digite e aperte **Enter**:

```
claude --version
```

**O que você vai ver:** um número de versão, tipo `2.1.211 (Claude Code)`.

Se não apareceu, vá pra tabela **Os 4 problemas do Windows**, logo abaixo.

## Passo 5. Crie a pasta do seu escritório

Digite e aperte **Enter**:

```
mkdir "$env:USERPROFILE\Documentos\Escritorio"
```

Se o seu Windows estiver em inglês, troque `Documentos` por `Documents`.

**O que você vai ver:** algumas linhas com o nome da pasta e a data. Isso é a confirmação.

**Se der errado:** apareceu `já existe um item com o mesmo nome`. Sem problema, a pasta já
existe. Siga pro próximo passo.

## Passo 6. Entre na pasta e abra o Claude

Digite as duas linhas abaixo, uma de cada vez, apertando **Enter** depois de cada uma:

```
cd "$env:USERPROFILE\Documentos\Escritorio"
```

```
claude
```

**O que você vai ver:** na primeira vez ele abre o navegador pedindo login na sua conta Claude.
Faça o login, autorize, e volte pro PowerShell.

Depois disso, a tela do Claude Code com um campo de texto esperando. **Você chegou.**

---

## Os 4 problemas do Windows

Praticamente todo travamento no Windows é um destes quatro. Ache o seu pelo texto que apareceu
na tela.

### Problema 1: você abriu o Prompt de Comando (CMD) em vez do PowerShell

**O que aparece na tela:**
`'irm' não é reconhecido como um comando interno ou externo`
(ou, em inglês, `'irm' is not recognized as an internal or external command`)

**Por que:** `irm` é um comando que só existe no PowerShell. Você está no CMD.

**Conserto:** feche a janela. Volte ao Passo 1 e clique em **"Windows PowerShell"**. A prova de
que você está no lugar certo é a linha começar com `PS C:\`.

### Problema 2: você colou um comando de CMD dentro do PowerShell

**O que aparece na tela:**
`O token '&&' não é um separador de instrução válido nesta versão`
(ou `The token '&&' is not a valid statement separator in this version`)

**Por que:** você colou uma linha escrita pro CMD numa janela de PowerShell.

**Conserto:** use exatamente a linha do Passo 2 deste documento, a que começa com `irm`. Não
use comando copiado de outro tutorial da internet.

### Problema 3: o Windows não acha o `claude` depois de instalar

**O que aparece na tela:**
`O termo 'claude' não é reconhecido como nome de cmdlet, função...`
(ou `The term 'claude' is not recognized as the name of a cmdlet`)

**Por que:** o programa foi instalado em `C:\Users\SeuNome\.local\bin`, mas a janela do
PowerShell que está aberta ainda não sabe disso.

**Conserto, na ordem:**
1. Feche o PowerShell e abra de novo. Tente `claude --version` outra vez. Resolve na maioria
   dos casos.
2. Não resolveu: **reinicie o computador** e tente de novo.
3. Ainda não: cole a linha abaixo no PowerShell e aperte Enter, e depois tente
   `claude --version` de novo:
   ```
   $env:Path += ";$env:USERPROFILE\.local\bin"
   ```
   Se funcionar **depois** dessa linha, o problema é só o Windows não estar guardando o
   caminho. Avise na mentoria que a gente resolve em 2 minutos, ou vá pro **Plano B**.

### Problema 4: você abriu a versão (x86) do PowerShell

**O que aparece na tela:** a instalação parece rodar mas termina com erro, ou o `claude` não
funciona depois. O título da janela é **"Windows PowerShell (x86)"**.

**Por que:** a (x86) é uma versão antiga de 32 bits, mantida por compatibilidade. O instalador
não funciona nela.

**Conserto:** feche essa janela. No menu Iniciar, clique em **"Windows PowerShell"**, o item
**sem** o `(x86)` no nome. Refaça a instalação a partir do Passo 2.

---

# Instalando o kit (Mac e Windows, igual)

Daqui pra frente é idêntico nos dois sistemas. Você está dentro do Claude Code, com o campo de
texto esperando.

## Passo 7. Adicione o marketplace da JurisLabs

Digite exatamente isto e aperte **Enter**:

```
/plugin marketplace add VitorTempone1/jurislabs-plugins
```

**O que você vai ver:** uma mensagem confirmando que o marketplace `jurislabs` foi adicionado,
com a lista de plugins disponíveis.

## Passo 8. Instale o kit

Digite e aperte **Enter**:

```
/plugin install kit-advogado@jurislabs
```

**O que você vai ver:** logo depois de instalar, aparece uma **tela de perguntas** pedindo o
nome do seu escritório, seu nome, número e UF da sua OAB, e a pasta do escritório.

Responda uma por uma. Na pasta do escritório, escreva o caminho completo da pasta que você
criou no Passo 5:

- Mac: `/Users/SEUNOME/Documentos/Escritorio`
- Windows: `C:\Users\SEUNOME\Documentos\Escritorio`

(troque `SEUNOME` pelo seu nome de usuário, que aparece na própria linha do terminal)

## Passo 9. Recarregue os plugins

Digite e aperte **Enter**:

```
/reload-plugins
```

**O que você vai ver:** uma confirmação de que os plugins foram recarregados. Isso é o que faz
as skills novas ficarem disponíveis sem você fechar tudo.

## Passo 10. LIGUE O AUTO-UPDATE (não pule este passo)

**Este é o passo mais importante depois da instalação.**

Marketplaces que não são da Anthropic vêm com atualização automática **desligada** por padrão.
Toda semana da mentoria a gente publica skill nova. Sem esse passo, **você não recebe
nenhuma** e nem fica sabendo.

1. Digite `/plugin` e aperte **Enter**.

   **O que você vai ver:** um menu com abas no topo, entre elas **Discover**, **Installed**,
   **Marketplaces** e **Errors**.

2. Use as setas do teclado para ir até a aba **Marketplaces** e aperte **Enter**.

   **O que você vai ver:** a lista de marketplaces, com **jurislabs** entre eles.

3. Selecione **jurislabs** e aperte **Enter**.

   **O que você vai ver:** as opções daquele marketplace.

4. Selecione **"Enable auto-update"** e aperte **Enter**.

   **O que você vai ver:** a opção vira **"Disable auto-update"**. Parece contraditório e não
   é: ela agora oferece *desligar*, porque já está **ligado**. É essa a confirmação de que deu
   certo.

5. Aperte **Esc** para sair do menu.

## Passo 11. Confirme que deu tudo certo

Digite e aperte **Enter**:

```
/kit-advogado:comecar
```

**O que você vai ver:** o kit começa a te fazer perguntas sobre a sua advocacia, uma de cada
vez: em que área você atua, em que tribunal peticiona, que peça você mais faz, como você
escreve. Responda com calma.

Pode sair no meio pra atender o telefone. A pergunta fica esperando, não tem cronômetro.

No fim, ele grava o perfil do seu escritório e te diz onde ficou. **A instalação acabou.**

**Se der errado:** o comando não foi reconhecido. Volte ao Passo 9 e rode `/reload-plugins`. Se
continuar, feche o Claude Code (digite `/exit`), abra de novo com `claude` e tente outra vez.

---

# Plano B: o aplicativo Claude Code

Se você travou no terminal, ou simplesmente não quer usar terminal, existe um **aplicativo com
janela e menus**, do jeito que qualquer outro programa funciona. Ele já vem com o Claude Code
embutido: não precisa instalar mais nada, nem Node, nem git.

## Passo B1. Baixe o aplicativo

- **Mac:** [baixar o .dmg](https://claude.ai/api/desktop/darwin/universal/dmg/latest/redirect)
- **Windows:** [baixar o instalador](https://claude.com/download)

**O que você vai ver:** o download começando no seu navegador.

## Passo B2. Instale

- **Mac:** abra o arquivo `.dmg` baixado e arraste o ícone do Claude para a pasta
  **Applications**.
- **Windows:** abra o arquivo `.exe` baixado e clique em **Avançar** até o fim.

**O que você vai ver:** o Claude aparecendo entre os seus programas.

## Passo B3. Abra e faça login

Abra o Claude e entre com a sua conta (a Pro, Max, Team ou Enterprise, lembra).

**O que você vai ver:** a tela principal do Claude.

## Passo B4. Vá para a aba Code

Na janela do aplicativo, clique na aba **Code**.

**O que você vai ver:** uma tela com um campo de texto, parecida com a do terminal, mas dentro
da janela do programa.

## Passo B5. Daqui pra frente é igual

Rode, dentro do campo de texto, os mesmos comandos dos **Passos 7 a 11** deste documento:

```
/plugin marketplace add VitorTempone1/jurislabs-plugins
/plugin install kit-advogado@jurislabs
/reload-plugins
/plugin
/kit-advogado:comecar
```

O menu de plugins (o `/plugin`) tem as mesmas abas **Discover**, **Installed**, **Marketplaces**
e **Errors**, e o **"Enable auto-update"** fica no mesmo lugar. O Passo 10 continua sendo
obrigatório.

---

# Resumo do que você tem que ter no fim

Marque cada um. Se algum estiver faltando, volte no passo correspondente.

- [ ] Plano **Pro** (ou maior) na conta Claude
- [ ] `claude --version` respondendo com um número de versão
- [ ] Uma pasta do escritório criada, fora de qualquer pasta de código
- [ ] Marketplace `jurislabs` adicionado
- [ ] Plugin `kit-advogado` instalado, com as perguntas de escritório e OAB já respondidas
- [ ] **Auto-update ligado** (a opção no menu mostra "Disable auto-update")
- [ ] `/kit-advogado:comecar` rodado até o fim, com o perfil gravado

---

# Duas coisas que valem pra sempre

**Nenhuma saída do sistema é peça pronta.** Tudo que sai daqui é minuta pra sua revisão. O
sistema não protocola, não assina e não peticiona. O último clique é sempre seu.

**A pasta do seu escritório fica só na sua máquina.** Ela não é sincronizada com a JurisLabs,
não é enviada pra lugar nenhum e, de propósito, não é um repositório de código. Nós nunca vemos
o dado do seu cliente. Você é o controlador desses dados, e o sistema é desenhado pra que
continue assim.
