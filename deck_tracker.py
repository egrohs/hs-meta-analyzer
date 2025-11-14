import os
import sys
import json
import time
from pathlib import Path

import tailer
from hearthstone.enums import GameTag, Zone
from hearthstone.hslog import LogParser
from hearthstone.hslog.export import EntityTreeExporter

# --- CONFIGURAÇÃO ---
HEARTHSTONE_LOG_PATH_WINDOWS = "C:\\Program Files (x86)\\Hearthstone\\Logs\\Power.log"
HEARTHSTONE_LOG_PATH_MACOS = Path.home() / "Library/Preferences/Blizzard/Hearthstone/Logs/Power.log"
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
        
        # Garante que temos um jogo completo para analisar
        if not self.parser.games or not self.parser.games[-1].game:
            return

        exporter = EntityTreeExporter(self.parser.games[-1])
        game = exporter.export()

        opponent = next((p for p in game.players if not p.is_main_player), None)
        if not opponent:
            return

        for entity in game.entities:
            is_card = entity.card_id is not None
            is_played_by_opponent = entity.controller == opponent.player_id
            is_in_play_zone = entity.zone == Zone.PLAY
            is_new_card = entity.card_id not in self.opponent_played_cards

            if is_card and is_played_by_opponent and is_in_play_zone and is_new_card:
                self.opponent_played_cards.add(entity.card_id)
                print(f"Oponente jogou: {entity.card_id}")
                self._determine_meta_deck()

    def run(self):
        """Inicia o monitoramento do arquivo de log."""
        print(f"Monitorando o arquivo de log: {self.log_path}")
        
        try:
            with open(self.log_path, "r", encoding="utf-8") as log_file:
                # Pula para o final do arquivo para não processar jogos antigos
                log_file.seek(0, 2)
                
                for line in tailer.follow(log_file):
                    self._process_log_line(line)
        except KeyboardInterrupt:
            print("\nMonitoramento interrompido pelo usuário.")
        except Exception as e:
            print(f"\nOcorreu um erro: {e}")

def get_log_path():
    """Retorna o caminho do log do Hearthstone com base no SO."""
    if sys.platform == "win32":
        return HEARTHSTONE_LOG_PATH_WINDOWS
    elif sys.platform == "darwin": # macOS
        return HEARTHSTONE_LOG_PATH_MACOS
    else:
        # Para Linux, o caminho pode variar. O usuário pode precisar especificar.
        print("Plataforma não suportada automaticamente. Por favor, edite o caminho do log no script.")
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
