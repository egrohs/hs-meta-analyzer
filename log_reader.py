import re
import sys
from pathlib import Path
import time

# Regex para identificar uma carta sendo jogada da mão.
# Captura o nome da entidade, ID da carta e ID do jogador.
# Lida com "name=" e "entityName=".
CARD_PLAY_REGEX = re.compile(r"PowerTaskList.+ Entity=\[(?:entityName)=(.*) id=\d+ zone=PLAY.*cardId=(.*) player=(\d+)\] tag=JUST\_PLAYED")

# O oponente é sempre considerado o jogador com ID "2".

# Regex para encontrar os nomes dos jogadores (heróis) no início do jogo.
# Procura por entidades de herói que entram na zona de JOGO.
# Lida com "name=" e "entityName=".
PLAYER_NAME_REGEX = re.compile(r"\[(?:entityName|name)=(.*) id=\d+ zone=PLAY.*cardId=HERO_.*player=(\d+)\]")


def get_log_path():
    """
    Encontra e retorna o caminho para o arquivo Power.log.
    """
    # No Linux, para este projeto, vamos assumir que está no diretório atual.
    if sys.platform == "linux":
        return Path("./Power.log")
    
    # Caminhos para outros sistemas (não testado)
    if sys.platform == "win32":
        base_dir = Path("C:/Program Files (x86)/Hearthstone/Logs")
    elif sys.platform == "darwin":
        base_dir = Path.home() / "Library/Preferences/Blizzard/Hearthstone/Logs"
    else:
        print("Plataforma não suportada.")
        return None

    if not base_dir.exists():
        return None

    # Lógica para encontrar o diretório de log mais recente (simplificado)
    try:
        latest_log_dir = max([d for d in base_dir.iterdir() if d.is_dir()], key=lambda p: p.stat().st_mtime)
        log_file = latest_log_dir / "Power.log"
        return log_file if log_file.exists() else None
    except (ValueError, FileNotFoundError):
        return None


def follow(thefile):
    """'tail -f' em Python."""
    thefile.seek(0, 2)  # Vai para o final do arquivo
    while True:
        line = thefile.readline()
        if not line:
            time.sleep(0.1)
            continue
        yield line


def parse_log(log_path):
    """
    Analisa o arquivo de log do Hearthstone em tempo real, focando no oponente.
    """
    opponent_player_id = "1"  # Oponente é sempre o jogador 2
    opponent_name = None

    print(f"Monitorando o arquivo de log: {log_path}")
    print(f"Oponente é considerado o Jogador {opponent_player_id}.")
    print("-" * 20)

    with open(log_path, "r", encoding="utf-8") as f:
        
        def process_line(line):
            nonlocal opponent_name
            # Procura por nome de jogador caso ainda não tenha sido encontrado
            if not opponent_name:
                match = PLAYER_NAME_REGEX.search(line)
                if match:
                    player_name_match = match.group(1)
                    player_id_match = match.group(2)
                    if player_id_match == opponent_player_id:
                        opponent_name = player_name_match
                        print(f"Oponente encontrado: {opponent_name}")
                        print("-" * 20)

            # Procura por cartas jogadas pelo oponente
            match = CARD_PLAY_REGEX.search(line)
            if match:
                player_id_match = match.group(3)
                if player_id_match == opponent_player_id:
                    card_name = match.group(1)
                    card_id = match.group(2)
                    print(f"Oponente jogou: {card_name} (ID: {card_id})")

        # Processa o arquivo desde o início
        for line in f:
            process_line(line)

        # Agora, monitora em tempo real
        print("\nMonitorando novas cartas jogadas pelo oponente...")
        for line in follow(f):
            process_line(line)


def main():
    log_path = get_log_path()
    if not log_path or not log_path.exists():
        # Se não encontrar, cria um arquivo vazio para não dar erro.
        print("Power.log não encontrado. Criando um arquivo vazio.")
        print("Por favor, inicie uma partida no Hearthstone para popular o log.")
        log_path = Path("./Power.log")
        log_path.touch()

    try:
        parse_log(log_path)
    except KeyboardInterrupt:
        print("\nMonitoramento interrompido.")
    except Exception as e:
        print(f"\nOcorreu um erro: {e}")


if __name__ == "__main__":
    main()
