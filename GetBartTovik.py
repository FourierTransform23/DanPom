from requests_html import HTMLSession
import pandas as pd
import re


def scrape_barttorvik_schedule(url: str) -> pd.DataFrame:
    """
    Scrapes the BartTorvik schedule page (JavaScript-rendered)
    and returns a cleaned pandas DataFrame with Away and Home
    team fields extracted from the Matchup column.
    """

    session = HTMLSession()
    try:
        response = session.get(url)
        response.html.render(timeout=30, sleep=2)

        table = response.html.find("table", first=True)
        if not table:
            raise RuntimeError("No table found on the page after JS rendering.")

        # Extract column headers
        headers = [th.text.strip() for th in table.find("tr th")]

        # Extract row data
        data = []
        for row in table.find("tr")[1:]:
            cells = [td.text.strip() for td in row.find("td")]

            if not cells:
                continue

            # Match row length to header length
            cells = cells[:len(headers)]
            data.append(dict(zip(headers, cells)))

        df = pd.DataFrame(data)

    finally:
        session.close()

    # Ensure Matchup column is usable
    df["Matchup"] = df["Matchup"].fillna("").replace(r"\s+", " ", regex=True)

    # Extract teams
    df["Away Team"] = df["Matchup"].apply(extract_away_team)
    df["Home Team"] = df["Matchup"].apply(extract_home_team)

    return df


def extract_away_team(matchup: str) -> str | None:
    """
    Extracts the away team name from a matchup like:
    '11 Kentucky at 7 Louisville ESPN'
    """

    if not isinstance(matchup, str):
        return None

    matchup = matchup.replace("\n", " ")

    # Rank + Team Name, before at/vs
    pattern = r"\d{1,3}\s*([A-Za-z .&'-]+?)\s+(?=at|vs)"
    match = re.search(pattern, matchup, flags=re.IGNORECASE)

    return match.group(1).strip() if match else None


def extract_home_team(matchup: str) -> str | None:
    """
    Extracts the home team name from a matchup like:
    '11 Kentucky at 7 Louisville ESPN'
    """

    if not isinstance(matchup, str):
        return None

    matchup = matchup.replace("\n", " ")

    # at/vs + Rank + Team Name
    pattern = r"(?:at|vs)\s+\d{1,3}\s*([A-Za-z .&'-]+)"
    match = re.search(pattern, matchup, flags=re.IGNORECASE)

    return match.group(1).strip() if match else None


if __name__ == "__main__":
    url = "https://www.barttorvik.com/schedule.php"
    df = scrape_barttorvik_schedule(url)
    print(df.head(5))
