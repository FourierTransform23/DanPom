import pandas as pd

def calc_model_spread(df, tourney_gm):
    home_eff = df['AdjEM_Home'].astype(float)
    away_eff = df['AdjEM_Away'].astype(float)
    home_tempo = df['AdjTempo_Home'].astype(float)
    away_tempo = df['AdjTempo_Away'].astype(float)
    # Tournament games don't need the 3.5 coefficient
    if tourney_gm == True:
        model_odds = ((home_eff - away_eff) * (home_tempo + away_tempo) / 200)
    else:
        model_odds = ((home_eff - away_eff)*(home_tempo + away_tempo)/200)+3.5
    return model_odds


