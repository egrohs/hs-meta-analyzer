import json
import requests
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

# --- CONFIGURAÇÃO ---
HSGURU_META_URL = "https://www.hsguru.com/decks?format=1" #"https://www.hsguru.com/meta?format=1" # format=1 é o modo Wild
OUTPUT_FILE = "meta_decks2.json"
HSGURU_META_URL = "https://www.hsguru.com/decks?format=1" # format=1 é o modo Padrão (Standard)
OUTPUT_FILE = "meta_decks.json"

# Configurações do Selenium
SCROLL_PAUSE_TIME = 2  # Tempo de espera para o conteúdo carregar após cada rolagem
SCROLL_ATTEMPTS = 10   # Quantas vezes o script tentará rolar para baixo

def scrape_meta_decks():
    """
    Busca os decks do meta do site HSGuru e extrai o arquétipo e os IDs das cartas.

    Returns:
        list: Uma lista de dicionários, onde cada dicionário representa um deck.
              Retorna uma lista vazia se ocorrer um erro.
    """
    print(f"Buscando dados de decks do meta em: {HSGURU_META_URL}")

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(HSGURU_META_URL, headers=headers, timeout=15)
        response.raise_for_status()  # Lança um erro para respostas HTTP 4xx/5xx
    except requests.exceptions.RequestException as e:
        print(f"ERRO: Falha ao buscar a página. {e}")
        return []

    soup = BeautifulSoup(response.content, "html.parser")
    meta_decks = []

    # Encontra todos os containers de deck na página
    # O seletor foi atualizado para corresponder à nova estrutura do site (Dez/2023)
    deck_containers = soup.select("div[id^='deck_stats-']")

    if not deck_containers:
        print("AVISO: Nenhum container de deck encontrado na página. O layout do site pode ter mudado.")
        return []

    print(f"Encontrados {len(deck_containers)} decks no meta.")
    
    for container in deck_containers:
        # Extrai o nome do arquétipo
        archetype_element = container.select_one("h2.deck-title a")
        if not archetype_element:
            continue # Pula se não encontrar o nome do arquétipo

        archetype = archetype_element.get_text(strip=True)
        
        # Extrai os IDs das cartas (dbfId)
        # O seletor agora busca por 'phx-value-card_id' e exclui cartas de sideboard
        card_elements = container.select("div[phx-value-card_id]:not([phx-value-sideboard])")
        card_ids = [card.get("phx-value-card_id") for card in card_elements]

        if archetype and card_ids:
            meta_decks.append({
                "archetype": archetype,
                "card_ids": card_ids
            })
            print(f"  - Deck '{archetype}' processado com {len(card_ids)} cartas.")

    return meta_decks

def save_decks_to_json(decks, filepath):
    """Salva a lista de decks em um arquivo JSON."""
    if not decks:
        print("Nenhum deck para salvar. O arquivo não será modificado.")
        return

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(decks, f, indent=4, ensure_ascii=False)
        print(f"\nBase de dados de decks foi salva com sucesso em '{filepath}'!")
    except IOError as e:
        print(f"ERRO: Falha ao salvar o arquivo JSON. {e}")

if __name__ == "__main__":
    decks_data = scrape_meta_decks()
    save_decks_to_json(decks_data, OUTPUT_FILE)