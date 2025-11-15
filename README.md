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

O script foi projetado para encontrar o arquivo de log automaticamente nos seguintes locais padrão:

- **Windows**: `C:\Program Files (x86)\Hearthstone\Logs`
- **macOS**: `~/Library/Preferences/Blizzard/Hearthstone/Logs`
- **Linux (via Wine)**: `~/.wine/drive_c/Program Files (x86)/Hearthstone/Logs`

Se o seu jogo estiver instalado em um local diferente, você precisará ajustar o caminho no script `deck_tracker.py`.

### 2. Base de Dados de Decks

O arquivo `meta_decks.json` contém a definição dos arquétipos. Cada deck é um objeto com:

- `archetype`: O nome do deck (ex: "Aggro Druid").
- `card_ids`: Uma lista de IDs de cartas (DBF IDs) que compõem o deck.

Você pode obter os DBF IDs de sites como [HearthstoneJSON](https://hearthstonejson.com/).

### 3. Instalar Dependências

Este script usa a biblioteca `hslog` para parsear os logs. Instale-a com:

```bash
pip install hslog tailer
```

## Como Usar

1. Certifique-se de que os logs do Hearthstone estão ativados (veja a seção de configuração).
2. Execute o script:

```bash
python deck_tracker.py
```

O script começará a monitorar o log. Assim que uma partida começar e seu oponente jogar cartas, ele tentará identificar o deck.