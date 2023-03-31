import pickle
import pandas as pd
import tft_utils
Ranks = tft_utils.Rank
Divisions = tft_utils.Division
Regions = tft_utils.Region
ranks_interests = [Ranks.diamond.value,
                   Ranks.platinum.value,
                   Ranks.gold.value,
                   Ranks.silver.value]

divisions_interests = [Divisions.one.value,
                       Divisions.two.value,
                       Divisions.three.value,
                       Divisions.four.value]

list_pd = []

for rank in ranks_interests:
    for division in divisions_interests:
        current_pick =  "Data/"+rank+"_"+division+".pkl"
        current_pd = pd.read_pickle(current_pick)
        list_pd.append(current_pd)
combined_pd = pd.concat(list_pd)
combined_pd.to_pickle("Data/player_match.pkl")
