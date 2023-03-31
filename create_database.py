from pymongo import MongoClient
import tft_utils
import pandas as pd
#this gets all the players from the ranks we want to observe as well as their
#latest game
playerdata = pd.read_pickle('Data/player_match.pkl')
#this queries and parses the match data then returns it in the form of a list
matchdata = tft_utils.get_matchdata_pd(playerdata)
#this creates the connection to the mongodb instance that is running in the local host
client = MongoClient()
#This creates the 'collection' or the noSql schema
matchdata_collection = client['TFT_Set8_matchdata']
#this inserts the data into the nosql schema
matchdata_collection.insert_many(matchdata)
#this line returns all the surrogate keys which are handled automatically
#via the mongodb interface
ids = posts.inserted_ids


