import requests
from bs4 import BeautifulSoup
import pandas as pd


def scrape_espn_schedule(url):
    """
    Scrapes the ESPN men's college basketball schedule from the given URL and returns a DataFrame
    with columns: MATCHUP, TIME, TV, Tickets, Location, ODDS BY, Logo ESPN Bet.
    """
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    if response.status_code != 200:
        raise Exception(f"Failed to fetch page: {response.status_code}")

    soup = BeautifulSoup(response.text, 'html.parser')
    schedule_table = soup.find('table', {'class': 'Table'})

    if not schedule_table:
        raise Exception("No schedule table found on the page")

    games = []
    for row in schedule_table.find_all('tr')[1:]:  # Skip header row
        cols = row.find_all('td')
        if len(cols) < 6:
            continue  # Skip rows that don't have enough data

        away_tm = cols[0].text.strip()
        home_tm = cols[1].text.strip()
        time = cols[2].text.strip() if len(cols) > 2 else "N/A"
        tv = cols[3].text.strip() if len(cols) > 3 else "N/A"
        tickets = cols[4].text.strip() if len(cols) > 4 else "N/A"
        location = cols[5].text.strip() if len(cols) > 5 else "N/A"
        odds = cols[6].text.strip() if len(cols) > 6 else "N/A"

        games.append({
            "Away Team": away_tm,
            "Home Team": home_tm,
            "Time": time,
            "TV": tv,
            "Tickets": tickets,
            "Location": location,
            "Odds": odds,
            })

    return pd.DataFrame(games)

