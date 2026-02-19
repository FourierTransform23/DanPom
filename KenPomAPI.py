import requests
import time
from typing import Dict, Any, Optional
import os
import pandas as pd
import datetime
import config


class KenPomAPI:
    def __init__(self, api_key: str, base_url: str = "https://kenpom.com/api.php"):
        self.api_key = api_key
        self.base_url = base_url

    def _get(self, params: Dict[str, Any]) -> Any:
        """
        Internal helper for GET requests using Bearer token authentication.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

        resp = requests.get(self.base_url, headers=headers, params=params)
        resp.raise_for_status()
        return resp.json()

    def get_team_ratings(self, season: int = 2025) -> pd.DataFrame:
        """
        Get team ratings for a given season.
        Example endpoint: /api.php?endpoint=ratings&y=2025
        """
        params = {
            "endpoint": "ratings",
            "y": season
        }
        data = self._get(params)
        return pd.DataFrame(data)

    def get_game_results(self, season: int = 2025) -> pd.DataFrame:
        """
        Example placeholder if KenPom provides game results.
        Adjust endpoint and parameters if applicable.
        """
        params = {
            "endpoint": "game_results",
            "y": season
        }
        data = self._get(params)
        return pd.DataFrame(data)


# ---------- CACHE HANDLER ----------

CACHE_FILE = "pomeroy_ratings_cache.pkl"
CACHE_EXPIRATION_HOURS = 6  # adjust as needed


def get_cached_pomeroy_ratings():
    """Fetch and cache KenPom team ratings with 6-hour expiry."""
    if os.path.exists(CACHE_FILE):
        mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(CACHE_FILE))
        if datetime.datetime.now() - mod_time < datetime.timedelta(hours=CACHE_EXPIRATION_HOURS):
            print("Loading cached data...")
            return pd.read_pickle(CACHE_FILE)

    print("Fetching new data...")

    kp = KenPomAPI(config.KENPOM_API_KEY)

    try:
        ratings = kp.get_team_ratings(season=2026)
        print(f"Fetched {len(ratings)} team ratings.")
    except requests.HTTPError as e:
        print("HTTP error:", e)
        raise
    except Exception as e:
        print("Unexpected error:", e)
        raise

    ratings.to_pickle(CACHE_FILE)
    return ratings


# ---------- MAIN EXECUTION ----------

if __name__ == "__main__":
    df = get_cached_pomeroy_ratings()
    print(df.head(5))
