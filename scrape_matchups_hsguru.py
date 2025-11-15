
import requests
from bs4 import BeautifulSoup
import json
import csv

def scrape_hsguru_matchups(url="https://www.hsguru.com/matchups"):
    """
    Scrapes Hearthstone deck matchup data from the given HSGuru URL.

    Args:
        url (str): The URL of the HSGuru matchups page.

    Returns:
        tuple: A tuple containing the matchup data as a dictionary and a list of deck names, or (None, None) if an error occurs.
    """
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for bad status codes
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {e}")
        return None, None

    soup = BeautifulSoup(response.content, 'html.parser')

    table = soup.find('table')
    if not table:
        print("No table found on the page.")
        return None, None

    headers = [th.text.strip() for th in table.find_all('th')]
    
    # The first header is empty, the rest are deck names
    deck_names = headers[1:]

    matchup_data = {}

    for row in table.find('tbody').find_all('tr'):
        cells = row.find_all('td')
        if not cells:
            continue

        row_deck_name = cells[0].text.strip()
        matchup_data[row_deck_name] = {}

        for i, cell in enumerate(cells[1:]):
            col_deck_name = deck_names[i]
            win_rate_str = cell.text.strip().replace('%', '')
            try:
                win_rate = float(win_rate_str)
                matchup_data[row_deck_name][col_deck_name] = win_rate
            except (ValueError, TypeError):
                matchup_data[row_deck_name][col_deck_name] = None

    return matchup_data, deck_names

if __name__ == "__main__":
    matchup_data, deck_names = scrape_hsguru_matchups()
    if matchup_data and deck_names:
        with open('hsguru_matchups.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow([''] + deck_names)
            
            # Write data rows
            for row_deck_name, matchups in matchup_data.items():
                row = [row_deck_name] + [matchups.get(col_deck_name, '') for col_deck_name in deck_names]
                writer.writerow(row)
        print("Matchup data saved to hsguru_matchups.csv")
