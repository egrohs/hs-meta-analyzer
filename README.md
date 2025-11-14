# HS Meta Analyzer

Um simples script em Python para analisar os logs do jogo Hearthstone em tempo real, identificar as cartas jogadas pelo oponente e sugerir o arquétipo (meta deck) mais provável.

## Funcionalidades

- Monitora o arquivo `Power.log` do Hearthstone.
- Extrai as cartas jogadas pelo oponente durante uma partida.
- Compara as cartas com uma base de dados de decks (`meta_decks.json`).
- Exibe no console o arquétipo mais provável do oponente.

## Configuração

### 1. Habilitar Logs do Hearthstone

Para que o script funcione, o Hearthstone precisa gerar um arquivo de log detalhado.

- Vá para a pasta de instalação do Hearthstone.
- Crie um arquivo chamado `log.config` (se não existir).
- Adicione o seguinte conteúdo ao arquivo:

[Power]
LogLevel=1
FilePrinting=true
ConsolePrinting=false
ScreenPrinting=false
Verbose=true

Após fazer isso, o jogo começará a registrar todos os eventos detalhados da partida no arquivo Power.log.

Localização do Arquivo de Log
O arquivo Power.log será gerado no seguinte local:

Windows: C:\Program Files (x86)\Hearthstone\Logs\Power.log
macOS: ~/Library/Preferences/Blizzard/Hearthstone/Logs/Power.log