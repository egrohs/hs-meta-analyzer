import os
import sys
import json
import traceback
from pathlib import Path

import tailer
from hslog import LogParser
from hslog.export import EntityTreeExporter

# --- CONFIGURAÇÃO ---
HEARTHSTONE_LOGS_DIR_WINDOWS = "C:\\Program Files (x86)\\Hearthstone\\Logs"
HEARTHSTONE_LOGS_DIR_MACOS = Path.home() / "Library/Preferences/Blizzard/Hearthstone/Logs"
META_DECKS_DB_PATH = "meta_decks.json"
MINIMUM_MATCH_CONFIDENCE = 2 # Mínimo de cartas correspondentes para sugerir um arquétipo

class DeckTracker:
    """
    Analisa os logs do Hearthstone para identificar o arquétipo do oponente.
    """
    def __init__(self, log_path, decks_db_path):
        self.log_path = log_path
        self.parser = LogParser()
        self.opponent_played_cards = set()
        self.meta_decks = self._load_meta_decks(decks_db_path)
        self.game_id = 0 # Para rastrear o jogo atual
        self.last_known_archetype = "Desconhecido"

    def _load_meta_decks(self, filepath):
        """Carrega a definição de decks de um arquivo JSON."""
        try:
            with open(filepath, 'r', encoding="utf-8") as f:
                print(f"Base de dados de decks '{filepath}' carregada.")
                return json.load(f)
        except FileNotFoundError:
            print(f"ERRO: Arquivo de decks '{filepath}' não encontrado.")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"ERRO: Arquivo de decks '{filepath}' contém um JSON inválido.")
            sys.exit(1)

    def _determine_meta_deck(self):
        """Compara as cartas jogadas com os decks meta e retorna o mais provável."""
        best_match_archetype = "Desconhecido"
        highest_score = -1

        for deck in self.meta_decks:
            deck_cards = set(deck.get("card_ids", []))
            matches = self.opponent_played_cards.intersection(deck_cards)
            score = len(matches)

            if score > highest_score:
                highest_score = score
                best_match_archetype = deck.get("archetype", "Arquétipo Sem Nome")

        if highest_score > MINIMUM_MATCH_CONFIDENCE:
            if best_match_archetype != self.last_known_archetype:
                self.last_known_archetype = best_match_archetype
                print("\n" + "="*40)
                print(f"==> Deck do Oponente: {best_match_archetype}")
                print(f"    (Confiança baseada em {highest_score} cartas correspondentes)")
                print("="*40 + "\n")
        
        return best_match_archetype

    def _process_log_line(self, line):
        """Processa uma única linha do log."""
        self.parser.read_line(line)

        # Se não houver jogos no parser, não há nada a fazer.
        if not self.parser.games:
            return

        # Pega o jogo mais recente que o parser encontrou.
        current_game_tree = self.parser.games[-1]
        exporter = EntityTreeExporter(current_game_tree)
        game = exporter.export()

        # Se um novo jogo começou (e já temos um ID para ele), reinicia o estado.
        if hasattr(game, 'id') and game.id != self.game_id:
            print("\n--- Nova Partida Detectada ---")
            self.game_id = game.id
            self.opponent_played_cards.clear()
            self.last_known_archetype = "Desconhecido"

        opponent = next((p for p in getattr(game, 'players', []) if not p.is_main_player), None)
        if not opponent:
            return
        # Itera sobre as entidades que mudaram no último pacote de dados lido
        for entity in current_game_tree.games[-1].entities:
            is_card, is_played_by_opponent, is_in_play_zone, is_new_card = self._check_entity_conditions(entity, opponent.player_id)

            if is_card and is_played_by_opponent and is_in_play_zone and is_new_card:
                self.opponent_played_cards.add(entity.card_id)
                print(f"Oponente jogou: {entity.card_id}")
                self._determine_meta_deck()

    def run(self):
        """Inicia o monitoramento do arquivo de log."""
        print(f"Monitorando o arquivo de log: {self.log_path}")
        
        try:
            with open(self.log_path, "r", encoding="utf-8") as log_file:
                # 1. Processa todo o conteúdo que já existe no arquivo
                print("Analisando o histórico do log da sessão atual...")
                for line in log_file:
                    #print(f"Processando linha: {line.strip()}")
                    self._process_log_line(line)

                # 2. Agora, monitora novas linhas em tempo real de forma eficiente
                print("\nAnálise do histórico concluída. Monitorando em tempo real... (Ctrl+C para sair)")
                for line in tailer.follow(log_file):
                    self._process_log_line(line)
        except KeyboardInterrupt:
            print("\nMonitoramento interrompido pelo usuário.")
        except Exception as e:
            print("\nOcorreu um erro inesperado. Detalhes abaixo:")
            traceback.print_exc()

    def _check_entity_conditions(self, entity, opponent_id):
        """Verifica as condições de uma entidade para ser contada como 'jogada pelo oponente'."""
        is_card = entity.card_id is not None
        is_played_by_opponent = entity.controller == opponent_id
        # Garante que a carta foi para a zona de JOGO (não para a mão ou cemitério)
        is_in_play_zone = hasattr(entity, 'zone') and entity.zone == Zone.PLAY
        is_new_card = entity.card_id not in self.opponent_played_cards

def get_log_path():
    """
    Encontra e retorna o caminho para o arquivo Power.log mais recente,
    baseado no sistema operacional.
    """
    if sys.platform == "win32":
        base_dir = Path(HEARTHSTONE_LOGS_DIR_WINDOWS)
    elif sys.platform == "darwin": # macOS
        base_dir = HEARTHSTONE_LOGS_DIR_MACOS
    else:
        print("TODO Tratar o linux")
        print("Plataforma não suportada automaticamente. Por favor, edite o caminho do log no script.")
        return "./Power.log"
        # return None

    if not base_dir.exists():
        return None

    # Encontra a pasta de log mais recente dentro do diretório base
    try:
        latest_log_dir = max([d for d in base_dir.iterdir() if d.is_dir()], key=os.path.getmtime)
        log_file = latest_log_dir / "Power.log"
        return log_file
    except (ValueError, FileNotFoundError):
        # Pode acontecer se a pasta Logs estiver vazia ou não tiver subdiretórios
        return None

def main():
    """Função principal."""
    log_path = get_log_path()
    if not log_path or not os.path.exists(log_path):
        print("Arquivo Power.log não encontrado. Verifique se o caminho está correto e se os logs do Hearthstone estão ativados.")
        sys.exit(1)
    
    tracker = DeckTracker(log_path, META_DECKS_DB_PATH)
    tracker.run()

if __name__ == "__main__":
    main()
