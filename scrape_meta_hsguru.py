import json
import requests
from bs4 import BeautifulSoup

HSGURU_META_URL = "https://www.hsguru.com/meta?format=1"
OUTPUT_FILE = "meta_data.json"

def scrape_meta_data():
    """
    Busca os dados do meta do site HSGuru e extrai o arquétipo, winrate, popularidade, etc.

    Returns:
        list: Uma lista de dicionários, onde cada dicionário representa um arquétipo.
              Retorna uma lista vazia se ocorrer um erro.
    """
    print(f"Buscando dados do meta em: {HSGURU_META_URL}")

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(HSGURU_META_URL, headers=headers, timeout=15)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"ERRO: Falha ao buscar a página. {e}")
        return []

    soup = BeautifulSoup(response.content, "html.parser")
    meta_data = []

    table = soup.find("table", class_="is-striped")
    if not table:
        print("AVISO: Tabela de meta não encontrada. O layout do site pode ter mudado.")
        return []

    tbody = table.find("tbody")
    if not tbody:
        print("AVISO: Corpo da tabela não encontrado.")
        return []

    rows = tbody.find_all("tr")
    print(f"Encontrados {len(rows)} arquétipos no meta.")

    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 6:
            continue

        archetype = cols[0].find("a").get_text(strip=True)
        winrate = cols[1].find("span", class_="basic-black-text").get_text(strip=True)
        popularity = cols[2].get_text(strip=True)
        turns = cols[3].get_text(strip=True)
        duration = cols[4].get_text(strip=True)
        climbing_speed = cols[5].get_text(strip=True)

        meta_data.append({
            "archetype": archetype,
            "winrate": float(winrate),
            "popularity": popularity,
            "turns": float(turns),
            "duration": float(duration),
            "climbing_speed": climbing_speed,
        })
        print(f"  - Arquétipo '{archetype}' processado.")

    return meta_data

def save_data_to_json(data, filepath):
    """Salva a lista de dados em um arquivo JSON."""
    if not data:
        print("Nenhum dado para salvar. O arquivo não será modificado.")
        return

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"\nBase de dados do meta foi salva com sucesso em '{filepath}'!")
    except IOError as e:
        print(f"ERRO: Falha ao salvar o arquivo JSON. {e}")

if __name__ == "__main__":
    data = scrape_meta_data()
    save_data_to_json(data, OUTPUT_FILE)
