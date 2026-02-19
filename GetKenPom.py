from kenpompy.utils import login
import kenpompy.summary, kenpompy.misc as kp
import os
import pandas as pd
import datetime

def get_kenpom_browser(email, password):
    return login(email, password)

def get_eff_stats(browser):
    # Get Efficiency Stats
    return kp.get_efficiency(browser)

def get_pomeroy_ratings(browser):
    # Get Main Pomeroy Stats
    return kp.get_pomeroy_ratings(browser)

CACHE_FILE = "pomeroy_ratings_cache.pkl"
CACHE_EXPIRATION_HOURS = 6 #Tourney
#CACHE_EXPIRATION_HOURS = 12  # adjust as needed

def get_cached_pomeroy_ratings(email, password):
    # Check if cache exists and is still fresh.
    if os.path.exists(CACHE_FILE):
        mod_time = datetime.datetime.fromtimestamp(os.path.getmtime(CACHE_FILE))
        if datetime.datetime.now() - mod_time < datetime.timedelta(hours=CACHE_EXPIRATION_HOURS):
            print("Loading cached data...")
            return pd.read_pickle(CACHE_FILE)

    # If cache doesn't exist or is expired, log in and fetch the data.
    print("Fetching new data...")
    browser = get_kenpom_browser(email, password)
    pomeroy_df = get_pomeroy_ratings(browser)

    # Save to cache.
    pomeroy_df.to_pickle(CACHE_FILE)
    return pomeroy_df

