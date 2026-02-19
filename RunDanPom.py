import pandas as pd
from GetESPNSchedule import scrape_espn_schedule
from KenPomAPI import get_cached_pomeroy_ratings
from ParseOdds import parse_line_odds_fuzzy
from CalcModelSpread import calc_model_spread
from GetBartTovik import scrape_barttorvik_schedule, extract_away_team
from GetActionNetworkClean import get_action_network_sharp_report
import re
import numpy as np
from datetime import datetime
import config


def clean_team_name(team_name):
    """Removes leading numbers, spaces, and special characters (@) from the team name."""
    return re.sub(r"^[0-9\s@]+", "", team_name)

# Get today's date in YYYYMMDD format
today = datetime.now()
date_str = today.strftime("%Y%m%d")

print(f"=== DanPom Report for {date_str} ===\n")

# Load the override mapping file
override_file = "Ken Pom ESPN Mapping.csv"
override_df = pd.read_csv(override_file)
override_dict = dict(zip(override_df['ESPN'], override_df['KenPom']))

# Scrape ESPN schedule with today's date
print("Fetching ESPN schedule...")
url = f"https://www.espn.com/mens-college-basketball/schedule/_/date/{date_str}"
espn_df = scrape_espn_schedule(url)

# Apply cleaning function to both columns
espn_df["Away Team"] = espn_df["Away Team"].apply(clean_team_name)
espn_df["Home Team"] = espn_df["Home Team"].apply(clean_team_name)

# Replace team names in ESPN DataFrame
espn_df['Away Team'] = espn_df['Away Team'].replace(override_dict)
espn_df['Home Team'] = espn_df['Home Team'].replace(override_dict)

# Get KenPom efficiency stats
print("Fetching KenPom ratings...")
kenpom_df = get_cached_pomeroy_ratings()

# Get Bart Torvik schedule
print("Fetching Bart Torvik data...")
url_tovik = "https://www.barttorvik.com/schedule.php"
df_tovik = scrape_barttorvik_schedule(url_tovik)

# Create a new column 'Away Team' using the extract_away_team function
if 'Matchup' in df_tovik.columns:
    df_tovik['Away Team'] = df_tovik['Matchup'].apply(extract_away_team)
else:
    raise Exception("The 'Matchup' column was not found in the BartTovik scraped data.")

if 'Time' in df_tovik.columns:
    df_tovik.drop(columns=['Time'], inplace=True)

if 'T-Rank Line' in df_tovik.columns:
    df_tovik.rename(columns={'T-Rank Line': 'Bart Tovik'}, inplace=True)

# Get Action Network sharp money data with error handling
print("Fetching Action Network sharp money data...")
action_df = None
try:
    action_df = get_action_network_sharp_report(
        config.ACTION_NETWORK_EMAIL,
        config.ACTION_NETWORK_PASSWORD,
        date_str
    )
    if action_df is not None:
        print(f"✓ Got sharp money data for {len(action_df)} games")
        # Save Action Network data to separate file
        action_output = rf"/home/dconde/Documents/DanPom/ActionNetwork_{date_str}.csv"
        action_df.to_csv(action_output, index=False)
        print(f"✓ Saved Action Network data to: {action_output}")
    else:
        print("⚠ Action Network data unavailable")
except Exception as e:
    print(f"⚠ Error fetching Action Network data: {e}")
    print("  Continuing without sharp money data...")

# Merge ESPN schedule with KenPom stats
merged_df = espn_df.merge(kenpom_df, left_on=['Away Team'], right_on=['TeamName'], how='left')
merged_df = merged_df.merge(kenpom_df, left_on=['Home Team'], right_on=['TeamName'], how='left', suffixes=('_Away', '_Home'))
merged_df = merged_df.merge(df_tovik, how='left', on='Away Team', suffixes=('_KenPom', '_BartTovik'))

# Handle edge case when Ken Pom Home Team name doesn't match Bart Tovik
if 'Home Team_KenPom' in merged_df.columns:
    merged_df.rename(columns={'Home Team_KenPom':'Home Team'}, inplace=True)

# Parse odds
merged_df['Spread'] = merged_df.apply(
    lambda row: parse_line_odds_fuzzy(row['Odds'], row['Away Team'], row['Home Team']),
    axis=1
)

print(merged_df[['Away Team', 'Home Team', 'Odds', 'Spread']].head())

# Calculate model spread
merged_df['Model_Spread'] = calc_model_spread(merged_df, config.TOURNEY_GM)
merged_df = merged_df.dropna(subset=['Model_Spread'])
merged_df['Model_Spread'] = pd.to_numeric(merged_df['Model_Spread'], errors='coerce')
merged_df['Spread'] = pd.to_numeric(merged_df['Spread'], errors='coerce')
merged_df['AdjEM_Home'] = pd.to_numeric(merged_df['AdjEM_Home'], errors='coerce')
merged_df['AdjEM_Away'] = pd.to_numeric(merged_df['AdjEM_Away'], errors='coerce')

# CROSSOVER - identify games where one team is above average and one is below
merged_df['Crossover'] = np.where(
    ((merged_df['AdjEM_Home'] < 0) & (merged_df['AdjEM_Away'] > 0)) |
    ((merged_df['AdjEM_Home'] > 0) & (merged_df['AdjEM_Away'] < 0)),
    "YES",
    "NO"
)

# Create a new column "Abs. Diff" as the absolute difference between Model_Spread and Spread
merged_df['Abs. Diff'] = abs(merged_df['Model_Spread'] - merged_df['Spread'])

# Sort the DataFrame highest to lowest based on "Abs. Diff"
merged_df = merged_df.sort_values(by='Abs. Diff', ascending=False)

# Filter the DataFrame using the condition:
# (Model_Spread > Spread and AdjEM_Home > 0) OR (Model_Spread < Spread and AdjEM_Away > 0)
mask = (
    ((merged_df['Model_Spread'] > merged_df['Spread']) & (merged_df['AdjEM_Home'] > 0)) |
    ((merged_df['Model_Spread'] < merged_df['Spread']) & (merged_df['AdjEM_Away'] > 0))
)

filtered_df = merged_df[mask].copy()

# Select columns for output
filter_cols = ['Away Team', 'Home Team', 'Time', 'TV', 'Odds', 'AdjEM_Away', 'AdjEM_Home', 'Model_Spread', 'Spread',
                 'Crossover', 'Abs. Diff', 'Bart Tovik', 'AdjOE_Away', 'AdjOE_Home', 'AdjDE_Away', 'AdjDE_Home']

result = filtered_df[filter_cols]

print("\n=== FILTERED RESULTS (Games with Model Edge) ===")
print(result)

# Save to CSV
output_file = rf"/home/dconde/Documents/DanPom/DanPom_{date_str}.csv"
output_file_all = rf"/home/dconde/Documents/DanPom/DanPom_all_{date_str}.csv"

result.to_csv(output_file, index=False)
merged_df[filter_cols].to_csv(output_file_all, index=False)

print(f"\n✓ Saved filtered results to: {output_file}")
print(f"✓ Saved all games to: {output_file_all}")
print(f"\nTotal games analyzed: {len(merged_df)}")
print(f"Games with model edge: {len(result)}")
