import re
from rapidfuzz import fuzz
import numpy as np


def parse_line_odds_fuzzy(odds_text, away_team, home_team):
    """
    Parses odds text and returns the odds as a signed float.

    Parameters:
      odds_text (str): A string in the format:
         "Line: ACRONYM -1.5\nO/U: 161.5"
      away_team (str): The away team's full name.
      home_team (str): The home team's full name.

    Returns:
      float: The parsed odds with a negative sign if it matches the away team,
             positive if it matches the home team.
    """
    # 1. Extract the text between "Line:" and "O/U"
    match = re.search(r"Line:\s*(.*?)\s*O/U", odds_text, re.DOTALL)
    if not match:
        print(f"{away_team} at {home_team}: No Odds found <{odds_text}>")
        return np.nan
    line_info = match.group(1).strip()  # e.g., "DART -1.5"

    # 2. Split the extracted text into the team acronym and the odds string
    parts = line_info.split()
    if len(parts) != 2:
        raise ValueError("Unexpected format for odds text; expected two parts")
    extracted_acronym, odds_value_str = parts[0], parts[1]

    try:
        odds_value = float(odds_value_str)
    except ValueError:
        raise ValueError("Odds value is not a valid float")

    # 3. Use fuzzy matching to compare the extracted acronym with the team names
    # Convert both sides to uppercase for a case-insensitive match
    away_score = fuzz.ratio(extracted_acronym.upper(), away_team.upper())
    home_score = fuzz.ratio(extracted_acronym.upper(), home_team.upper())

    # 4. Return negative odds if it's a better match for the away team, else positive
    if away_score >= home_score:
        return -abs(odds_value)
    else:
        return abs(odds_value)



