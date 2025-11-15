import os
import sys
import json
import traceback
from pathlib import Path

import tailer
from hslog import LogParser
from hslog.export import EntityTreeExporter
from hearthstone import cardxml
from hslog.packets import TagChange, CreateGame, FullEntity
from hearthstone.entities import Game

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
        self.db, self.dbf_id_to_name = self._load_card_database()
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

    def _load_card_database(self):
        """Carrega o banco de dados de cartas e cria um mapa de dbfId para nome."""
        db, _ = cardxml.load_dbf()
        mapping = {}
        for card_data in db.values():
            if hasattr(card_data, 'dbf_id') and hasattr(card_data, 'name'):
                mapping[str(card_data.dbf_id)] = card_data.name
        return db, mapping

    def _determine_meta_deck(self):
        """Compara as cartas jogadas com os decks meta e retorna o mais provável."""
        best_match_archetype = "Desconhecido"
        highest_score = -1
        best_matching_cards = set()

        for deck in self.meta_decks:
            deck_cards = set(deck.get("card_ids", []))
            matches = self.opponent_played_cards.intersection(deck_cards)
            score = len(matches)

            if score > highest_score:
                highest_score = score
                best_match_archetype = deck.get("archetype", "Arquétipo Sem Nome")
                best_matching_cards = matches

        if highest_score > MINIMUM_MATCH_CONFIDENCE:
            if best_match_archetype != self.last_known_archetype:
                self.last_known_archetype = best_match_archetype
                print("\n" + "="*40)
                print(f"==> Deck do Oponente: {best_match_archetype}")
                print(f"    (Confiança baseada em {highest_score} cartas correspondentes):")
                
                # Imprime os nomes das cartas que deram match
                for card_dbf_id in sorted(list(best_matching_cards)):
                    card_name = self.dbf_id_to_name.get(card_dbf_id, f"ID:{card_dbf_id}")
                    print(f"      - {card_name}")

                print("="*40 + "\n")
        
        return best_match_archetype

    def _process_log_line(self, line):
        """Processa uma única linha do log."""
        self.parser.read_line(line)

        if not self.parser.games:
            return

        current_game_tree = self.parser.games[-1]

        # Encontra o pacote CreateGame para obter a entidade do jogo de forma robusta.
        # Isso é necessário para contornar as falhas de atributo em diferentes versões do hslog.
        game_entity = None
        for packet in current_game_tree:
            if isinstance(packet, CreateGame):
                for sub_packet in packet.packets:
                    if isinstance(sub_packet, FullEntity):
                        if sub_packet.tags.get(Game.Tag.GAME_ENTITY) == 1:
                            game_entity = sub_packet
                            break
                if game_entity:
                    break
        
        if not game_entity:
            return # Pacote CreateGame ainda não foi encontrado

        current_game_id = game_entity.id
        if current_game_id != self.game_id:
            print("\n--- Nova Partida Detectada ---")
            self.game_id = current_game_id
            self.opponent_played_cards.clear()
            self.last_known_archetype = "Desconhecido"

        exporter = EntityTreeExporter(current_game_tree)
        game = exporter.export()

        if not game:
            return

        opponent = next((p for p in game.players if not p.is_main_player), None)
        if not opponent:
            return

        for packet in self.parser.flush():
            if isinstance(packet, TagChange) and packet.tag == Game.Tag.ZONE and packet.value == Game.Zone.PLAY:
                entity = current_game_tree.find_entity(packet.entity)
                if not entity or not entity.card_id:
                    continue
                if entity.controller == opponent.player_id:
                    card_data = self.db.get(entity.card_id)
                    dbf_id = str(getattr(card_data, 'dbf_id', None))

                    if dbf_id and dbf_id not in self.opponent_played_cards:
                        self.opponent_played_cards.add(dbf_id)
                        print(f"Oponente jogou: {getattr(card_data, 'name', entity.card_id)} (ID: {dbf_id})")
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

def get_log_path():
    """
    Encontra e retorna o caminho para o arquivo Power.log mais recente,
    baseado no sistema operacional.
    """
    if sys.platform == "win32":
        base_dir = Path(HEARTHSTONE_LOGS_DIR_WINDOWS)
    elif sys.platform == "darwin": # macOS
        base_dir = HEARTHSTONE_LOGS_DIR_MACOS
    elif sys.platform == "linux":
        return "./Power.log"
    else:
        print("Plataforma não suportada automaticamente. Por favor, edite o caminho do log no script.")
        return None

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
