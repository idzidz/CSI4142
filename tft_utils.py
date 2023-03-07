import re
import json
import requests
import time
import pandas as pd
from enum import Enum
from apikey import apiheader

class Rank(Enum):
    iron = "IRON"
    bronze = "BRONZE"
    silver = "SILVER"
    gold = "GOLD"
    platinum = "PLATINUM"
    diamond = "DIAMOND"
    

class Division(Enum):
    one = "I"
    two = "II"
    three = "III"
    four = "IV"


class tft_requests(Enum):
    '''
    /tft/league/v1/entries/{tier}/{division}
    50 requests every 10 seconds
    '''
    entries_division_region_url = "https://REGION.api.riotgames.com/tft/league/v1/entries/RANK/DIVISION?page=PAGENUMBER"
    entries_division_region_time = 10/50
    '''
    /tft/league/v1/entries/by-summoner/{summonerId}
    60 requests every 1 minutes
    '''
    entries_by_summoner_id_url = "https://REGION.api.riotgames.com/tft/league/v1/entries/by-summoner/SUMMONERID"
    entries_by_summoner_id_time = 1 
    '''
    /tft/summoner/v1/summoners/{encryptedSummonerId}
    1600 requests every 1 minutes
    '''
    summoner_info_summonerid_url = "https://REGION.api.riotgames.com/tft/summoner/v1/summoners/SUMMONERID"
    summoner_info_summonerid_time = 60/1600
    '''
    /tft/league/v1/challenger
    30 requests every 10 seconds
    500 requests every 10 minutes
    '''
    challenger_from_region_url = "https://REGION.api.riotgames.com/tft/league/v1/challenger"
    challenger_from_region_time = (10*60)/500
    
    '''
    /tft/league/v1/grandmaster
    30 requests every 10 seconds
    500 requests every 10 minutes
    '''
    grandmaster_from_region_url = "https://REGION.api.riotgames.com/tft/league/v1/grandmaster"
    grandmaster_from_region_time = (10*60)/500
    
    '''
    /tft/league/v1/master
    30 requests every 10 seconds
    500 requests every 10 minutes
    '''
    master_from_region_url = "https://REGION.api.riotgames.com/tft/league/v1/master"
    master_from_region_time = (10*60)/500

    '''
    /tft/match/v1/matches/by-puuid/{puuid}/ids
    400 requests every 10 seconds
    '''
    match_history_by_puuid_url = "https://GREATERREGION.api.riotgames.com/tft/match/v1/matches/by-puuid/PLAYERPUUID/ids?start=0&count=NUM_MATCHES"
    match_history_by_puuid_time = 10/400
    
    '''
    /tft/match/v1/matches/{matchId}
    200 requests every 10 seconds
    '''
    match_by_matchid_url = "https://GREATERREGION.api.riotgames.com/tft/match/v1/matches/MATCHID"
    match_by_matchid_time = 10/200

    app_max_requests = 120/100
    
class Region(Enum):
    North_America = 'na1'
    Europe_Nordic_East = 'eun1'
    Brazil = 'br1'
    Europe_West = 'euw1'
    Japan = 'jp1'
    Republic_Korea = 'kr'
    Latin_America_North = 'la1'
    Latin_America_South = 'la2'
    Oceania = 'oc1'
    Turkey = 'tr1'
    Russia = 'ru'
    Philippines = 'ph2'
    Singapore_Malaysia_Indonesia = 'sg2'
    Thailand = 'th2'
    Taiwan_HongKong_Macao = 'tw2'
    Vietnam = 'vn2'
    regions_in_americas = ['na1','br1','la1','la2']
    regions_in_asia = ['kr','jp1']
    regions_in_europe = ['euw1','eun1','tr1','ru']
    regions_in_SEA = ['oc1','ph2','sg2','th2','tw2','vn2']
    regional_americas = 'americas'
    regional_asia = 'asia'
    regional_europe = 'europe' 
    regional_sea = 'sea'

class TraitNotFound(Exception):
    def __init__(self,trait):
        super().__init__("trait "+trait+" doesnt exist")

def get_puuid_from_summonerid(summonerid,region):
    puuid_request = tft_requests.summoner_info_summonerid_url.value
    puuid_request = re.sub("REGION",region,puuid_request)
    puuid_request = re.sub("SUMMONERID",summonerid,puuid_request)
    info = json.loads(requests.get(puuid_request,headers = apiheader).text)
    time.sleep(tft_requests.app_max_requests.value)
    try:
        puuid = info['puuid']
    except:
        print(info)
    return puuid

def get_players_by_rank(rank,division,region,max_page_number=100000000):    
    entries_request = tft_requests.entries_division_region_url.value
    entries_request = re.sub("REGION",region,entries_request)
    entries_request = re.sub("RANK",rank,entries_request) 
    entries_request = re.sub("DIVISION",division,entries_request)
    players = []
    page_counter = 1
    page_flag = True
    while(page_flag):
        print(page_counter)
        entries_request = re.sub("PAGENUMBER",str(page_counter),entries_request)
        players_page_x = json.loads(requests.get(entries_request,headers = apiheader).text)
        time.sleep(tft_requests.app_max_requests.value)
        if(page_counter>max_page_number or players_page_x == []):
            page_flag=False
        else:
            players = players+players_page_x
        page_counter+=1
    
    puuid = []
    remaining_sleep_time = tft_requests.entries_division_region_time.value -(len(players)*tft_requests.summoner_info_summonerid_time.value)
    print(remaining_sleep_time)
    print(len(players))
    if remaining_sleep_time >=0:
        time.sleep(remaining_sleep_time)
    player_counter = 0
    starttime = time.time()
    for player in players:
        try:
            non_puuid = player
            non_puuid['puuid'] = get_puuid_from_summonerid(non_puuid['summonerId'],region)
            player_counter+=1
            puuid.append(non_puuid)
        except:
            endtime = time.time()
            totaltime = endtime-starttime
            return totaltime,player_counter
    df = pd.DataFrame.from_dict(puuid)
    return df
    
def get_matches_from_playerid(puuid,greater_region,num_matches=1):
    #https://GREATERREGION.api.riotgames.com/tft/match/v1/matches/by-puuid/PLAYERPUUID/ids?start=0&count=NUM_MATCHES
    history_url = tft_requests.match_history_by_puuid_url.value
    history_url = re.sub("PLAYERPUUID",puuid,history_url)
    history_url = re.sub("NUM_MATCHES",str(num_matches),history_url)
    history_url = re.sub("GREATERREGION",greater_region,history_url)
    history = json.loads(requests.get(history_url,headers = apiheader).text)
    time.sleep(tft_requests.app_max_requests.value)
    return history

def get_match_data_from_matchid(greater_region,matchid,remaining_time = 0):
    #https://GREATERREGION.api.riotgames.com/tft/match/v1/matches/MATCHID
    match_url = tft_requests.match_by_matchid_url.value
    match_url = re.sub("GREATERREGION",greater_region,match_url)
    match_url = re.sub("MATCHID",matchid,match_url)
    match = json.loads(requests.get(match_url,headers = apiheader).text)
    time.sleep(tft_requests.app_max_requests.value-remaining_time)
    return match

def get_greater_region(region):
    mat = ""
    if region in Region.regions_in_americas.value:
        mat = Region.regional_americas.value
    elif region in Region.regions_in_asia.value:
        mat=Region.regional_asia.value
            
    elif region in Region.regions_in_europe:
        mat=gRegion.regional_europe.value

    elif region in Region.regions_in_SEA:
        mat=Region.regional_sea.value
    return mat

def get_rank_division_matches(region,rank,division,num_matches=1):
    '''
    '''
    players = get_players_by_rank(rank,division,region,1)
    players = pd.DataFrame.from_dict(players)
    players['region'] = region
    greater_region = get_greater_region(region)
    players['Rank'] = rank
    players['division'] = division
    puuids = players['puuid']
    matches = []
    for puuid in puuids:
        mat = get_matches_from_playerid(puuid,greater_region)[0]
        matches.append(mat)
        
    players['match'] = matches
    return players

def get_matchdata_pd(players_puuid):
    
    for index,row in players_puuid.iterrows():
        matchid = row['match']
        region = row['region']
        greater_region = get_greater_region(region)
        matchData = get_match_data_from_matchid(greater_region,matchid)
    

def create_tft_dictionaries():
    '''
    returns 3 dictionaries from the json files for the information on tft champions, traits and items
    '''
    with open("./Data/tftchampions.json") as tftc:
        tftchampionslist = json.loads(tftc.read())
    tftchampions = {}
    for champion in tftchampionslist:
        champname = champion['character_id']
        tftchampions[champname] = champion
    with open("./Data/tftitems.json") as tfti:
        tftitemslist = json.loads(tfti.read())
    tftitems = {}
    for item in tftitemslist:
        itemname = item['nameId']
        tftitems[itemname] = item
    with open("./Data/tfttraits.json") as tftt:
        tfttraitslist = json.loads(tftt.read())
    tfttraits = {}
    for trait in tfttraitslist:
        traitname = trait['trait_id']
        tfttraits[traitname] = trait
    return tftchampions,tftitems,tfttraits
def get_trait_from_traitstem(traitstem,traitdict):
    '''
    will return the full proper trait name from stems
    ex: underground will return TFT8_
    '''
    for trait in traitdict.keys():
        if "set8".lower() in trait.lower():
            if traitstem.lower() in trait.lower():
                return trait
            elif traitstem.lower() == 'InterPolaris'.lower():
                return('Set8_SpaceCorps')
    raise(TraitNotFound(traitstem))
    
        
    

def get_traits_from_unit(unitname,championdict,itemdict,traitdict):
    '''
    '''
    unit_trait = [trait['id'] for trait in championdict[unitname]['traits']]
    return unit_trait

def get_traits_from_items(itemlist,itemdict):
    '''
    '''
    traits_from_items = []
    for item in itemlist:
        if item != None:
            item_trait_benefit = re.sub("Item|TFT8_Augment_|TFT8_Item_|TFT_Item","",item)
            if re.match("Emblem\d?",item_trait_benefit)!=None:
                item_trait_benefit = re.sub("Emblem\d?","",item_trait_benefit)
                traits_from_items.append(item_trait_benefit)
    return traits_from_items
def get_traits_from_augments(augments,traitdict):
    augment_traits = []
    for augment in augments:
        is_augmentstem = re.match("TFT8_Augment_\D*Trait",augment)
       
        if is_augmentstem!=None:
            
            traitstem = re.sub("TFT8_Augment_|Trait\d?","",augment)
            trait = get_trait_from_traitstem(traitstem,traitdict)
            augment_traits.append(trait)
    return augment_traits
def calculate_comp_traits(unitlist,itemlist,augmentlist,championdict,itemdict,fulltraitdict):
    '''
    '''
    traitdict = {}
    unitlist = list(dict.fromkeys(unitlist))
    for unit in unitlist:
        unit_traits = get_traits_from_unit(unit,championdict,itemdict,fulltraitdict)
        for trait in unit_traits:
            if trait in traitdict.keys():
                traitdict[trait] +=1
            else:
                traitdict[trait] = 1
    
    itemtraitstems = get_traits_from_items(itemlist,itemdict)
   
    itemtraits = []
    for itemstem in itemtraitstems:
       
        propertraits = get_trait_from_traitstem(itemstem,fulltraitdict)
        
        itemtraits.append(propertraits)
   
    for trait in itemtraits:
        if trait in traitdict.keys():
            traitdict[trait]+=1
        else:
            traitdict[trait] = 1
    augment_traits = get_traits_from_augments(augmentlist,fulltraitdict)
    for augment in augment_traits:
        if augment in fulltraitdict.keys():
            try:
                traitdict[augment]+=1
            except:
                TraitNotFound(augment)
        else:
            traitdict[augment]=1
    
    return traitdict
def calculate_trait_tier(numunits,trait,traitdict):
    '''
    '''
    trait_data = traitdict[trait]
    conditions = trait_data['conditional_trait_sets']
    for tier in conditions:
        if 'max_units' in tier.keys():
            min_units = tier['min_units']
            max_units = tier['max_units']
            tiercolor = tier['style_name']
            if numunits>= min_units and numunits<=tier['max_units']:
                return([min_units,tiercolor])
        else:
            min_units = tier['min_units']
            tiercolor = tier['style_name']
            if numunits>= min_units:
                return([min_units,tiercolor])
    return([0,"Grey"])

def get_img_for_champ(champname):
    url = "https://raw.communitydragon.org/latest/game/assets/characters/"+champname.lower()+"/hud/"+champname.lower()+".tft_set8.png"
    champ_img =img(src = url)
    return champ_img
def get_img_for_item(itemname):
    c,i,t = create_tft_dictionaries()
    
    if re.match("Emblem\d?",itemname)!=None:
        item = re.sub("TFT8_Item_.+EmblemItem",itemname)
        url = "https://raw.communitydragon.org/latest/game/assets/maps/particles/tft/item_icons/traits/spatula/set8/"
    else:
        url = "https://raw.communitydragon.org/latest/game/assets/maps/particles/tft/"+itemname.lower()+".png"
    item_img = img(src=url)
    return item_img
def get_img_for_trait(traitname):
    pass
def get_img_for_augment(augmentname):
    pass

    
