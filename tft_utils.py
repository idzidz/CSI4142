import re
import json
import requests
import time
import pickle
import pandas as pd
from enum import Enum
from apikey import apiheader

class Rank(Enum):
    '''
    These are the different ranks needed to 
    '''
    iron = "IRON"
    bronze = "BRONZE"
    silver = "SILVER"
    gold = "GOLD"
    platinum = "PLATINUM"
    diamond = "DIAMOND"
    

class Division(Enum):
    '''
    These are the four divisions in a league
    ex. Gold has four divisions 1 to 4
    '''
    one = "I"
    two = "II"
    three = "III"
    four = "IV"


    

class tft_requests(Enum):
    '''
    in order to access any data from the methods provided by riot for their data a specific url
    is needed per method. This url is also dependent on other factors given by the query made
    these url requests are organized in order to make adding arguments simple in the helper functions.
    Also riot limits the amount of requests you can make per minute so the _time values gives the amount of time
    the methods need to sleep inbetween requests
    '''
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
    '''
    All player,match queries have the general form of
    region.queryurl it is important to specify the region in the
    request so this enum gives you the letter combinations for any query you need to make
    '''
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
    '''
    an error exception made for finding traits that are not in the game
    '''
    def __init__(self,trait):
        super().__init__("trait "+trait+" doesnt exist")
def get_augment_list():
    with open('Data/augmetlist.pkl', 'rb') as f:
        augmentlist = pickle.load(f)
    return augmentlist
    
def get_puuid_from_summonerid(summonerid,region):
    '''
    given a summoner id( a type of account id, get the puuid(another type unique id that an account can have)
    '''
    puuid_request = tft_requests.summoner_info_summonerid_url.value
    #parse the url request with the region that the person is from
    puuid_request = re.sub("REGION",region,puuid_request)
    #parse the url request with the summoner id in it
    puuid_request = re.sub("SUMMONERID",summonerid,puuid_request)
    #make the request and add the apiheader which comes from the apikey
    info = json.loads(requests.get(puuid_request,headers = apiheader).text)
    time.sleep(tft_requests.app_max_requests.value)
    try:
        #get the puuid value from the data returned
        puuid = info['puuid']
    except:
        print(info)
    return puuid

def get_players_by_rank(rank,division,region,max_page_number=100000000):
    '''
    get all players in a rank and division from a particular region
    ex: get all gold 4 players in North america.

    Due to the fact that their are thousands of players that fit this, riot only returns pages at a time
    the number of pages are not set but a full page will only have 205 players so max_page_numbers will determine
    how many pages to go through and get the data

    general algo
    for each page until all pages are ran through or max_page_numbers is hit
        get all players names in this page
    put all players names collected
    for player names in players collected:
        get the player information via their name
    return all players
    '''
    #parse the request into a format that is necessary withought the pagenumber changed
    entries_request = tft_requests.entries_division_region_url.value
    entries_request = re.sub("REGION",region,entries_request)
    entries_request = re.sub("RANK",rank,entries_request) 
    entries_request = re.sub("DIVISION",division,entries_request)
    #a list of player names to be collected
    players = []
    
    page_counter = 1
    page_flag = True
    #iterate through all pages until max_page_number and make a request to get those players
    while(page_flag):
        print(page_counter)
        entries_request = re.sub("PAGENUMBER",str(page_counter),entries_request)
        #make a request to the page number that you are iterating through
        players_page_x = json.loads(requests.get(entries_request,headers = apiheader).text)
        time.sleep(tft_requests.app_max_requests.value)
        #if you have hit the max_page_number or the page you are looking at is empty(a sign that youve gone through all the relevant pages
        #set flag to false and stop iterating through
        if(page_counter>max_page_number or players_page_x == []):
            page_flag=False
        else:
            #add the content to the list of players collected
            players = players+players_page_x
        #go to the next page
        page_counter+=1
    
    puuid = []
    remaining_sleep_time = tft_requests.entries_division_region_time.value -(len(players)*tft_requests.summoner_info_summonerid_time.value)
    #wait a few seconds before making the next request dependent on the time taken for the last request
    if remaining_sleep_time >=0:
        time.sleep(remaining_sleep_time)
    player_counter = 0
    starttime = time.time()
    #iterate through all the players that were collected via the pages and get their full info
    for player in players:
        try:
            non_puuid = player
            non_puuid['puuid'] = get_puuid_from_summonerid(non_puuid['summonerId'],region)
            player_counter+=1
            puuid.append(non_puuid)
        except:
            #if an exception happens return the last player looked at
            endtime = time.time()
            totaltime = endtime-starttime
            return totaltime,player_counter
    #shape the player info into a pandas dataframe
    df = pd.DataFrame.from_dict(puuid)
    return df
    
def get_matches_from_playerid(puuid,greater_region,num_matches=1):
    '''
    get the list of matchids for the matches a player has played given a puuid from the player
    the default value gives you the latest match played
    ex:Ivan with puuid TXT played ten matches [n1,n2,n3] return [n1,n2,n3]
    '''
    #https://GREATERREGION.api.riotgames.com/tft/match/v1/matches/by-puuid/PLAYERPUUID/ids?start=0&count=NUM_MATCHES
    history_url = tft_requests.match_history_by_puuid_url.value
    #parse the request for the information given
    history_url = re.sub("PLAYERPUUID",puuid,history_url)
    history_url = re.sub("NUM_MATCHES",str(num_matches),history_url)
    history_url = re.sub("GREATERREGION",greater_region,history_url)
    #make the request that has been parsed
    history = json.loads(requests.get(history_url,headers = apiheader).text)
    #sleep in order to ensure another request isnt made that would violate the conditions of the api
    time.sleep(tft_requests.app_max_requests.value)
    return history

def get_match_data_from_matchid(greater_region,matchid,remaining_time = 0):
    '''
    get the match details and data given the region its from and the match id
    remaining_time is used if you know the functions run time inbetween calls to ensure
    the fastest time possible
    '''
    #https://GREATERREGION.api.riotgames.com/tft/match/v1/matches/MATCHID
    #parse the request with the information given by the function
    match_url = tft_requests.match_by_matchid_url.value
    match_url = re.sub("GREATERREGION",greater_region,match_url)
    match_url = re.sub("MATCHID",matchid,match_url)
    #make the request
    match = json.loads(requests.get(match_url,headers = apiheader).text)
    time.sleep(tft_requests.app_max_requests.value-remaining_time)
    return match

def get_greater_region(region):
    '''
    Some countries are grouped together in requests
    for example korea,japan are both in the ASIA greater region
    These list of countries per greater_region can be found in the Regions Enum
    '''
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
    Get all the most recent matches for all players within a region,rank and division
    this is utilized first due to the fact that riot forces you to query through players
    first before querying through matches
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
def find_correct_rarity(rarity_num):
        '''
        The database wrongly attributes some of the costs of units
        all units below 3 are one too low
        all units that are 5 costs are labeled as 6
        all units that are 4 costs are correctly labeled
        This just fixes it
        '''
        correct_rarity = rarity_num
        if correct_rarity<3:
            correct_rarity+=1
        elif correct_rarity==6:
            correct_rarity-=1
        return correct_rarity
def find_correct_style(style_num,traitname):
    '''
    given a trait style number give the style name
    for example if a trait has a style number 2 that means its a silver
    trait
    '''
    properstyle = "inactive"
    properstyle = "bronze" if style_num==1 else properstyle
    properstyle = "silver" if style_num==2 else properstyle
    properstyle = "gold" if style_num==3 else properstyle
    properstyle = "chromatic" if style_num==4 else properstyle
    properstyle = "threat" if traitname=='Set8_Threat' else properstyle
    return properstyle
def parse_single_unit_data(unit_list_item):
    '''
    this is a helper function that parses a unit from the riot tft database thats found in a single match
    into a useful format for storage
    '''
    items = unit_list_item['itemNames']
    firstitem = None
    seconditem = None
    thirditem = None
    #the default value for a unit with no items is None iterate through the list of items and
    #get the item that is there add change the item value
    if len(items)>0:
        firstitem = items[0]
        if len(items)>1:
            seconditem = items[1]
            if len(items)>2:
                thirditem = items[2]
    #get the name of the unit in the list
    name = unit_list_item['character_id']
    #get the rarity or cost
    rarity = find_correct_rarity(unit_list_item['rarity'])
    #get the tier of the unit
    tier = unit_list_item['tier']
    #format into a useful format for the database
    row = {name:[firstitem,seconditem,thirditem,rarity,tier]}
           
    return row


def parse_single_trait_data(trait_list):
    '''
    this will parse a single trait from a match into a useful for collection
    '''
    trait_tier = find_correct_style(trait_list['style'],trait_list['name'])
    row = {trait_list['name']:{
           "num_units":trait_list['num_units'],
           "trait_tier":trait_tier,
           "tier_total":trait_list['tier_total']}}
    
    return row
    

    
def parse_match_data(match_dict,rank="unknown",division="unknown",region="unknown",greater_region="unknown",matchid = "unknown"):
    '''
    this will parse a match that has been collected via a request. This will return a useful dictionary
    containing all the information given
    '''
    #gets the meta data of the match
    meta_part = match_dict['metadata']
    #this will contain all the participant data. This will also contain the player statistics for the match(units,traits,augments,gold won etc)
    participants = match_dict['info']['participants']
    #general information about the match(game length,type etc) that apply to all players
    non_participants = {key:value for key, value in match_dict['info'].items() if key!="participants"}
    #A list of information for each players
    total_participant_data = []
    #iterate through each player
    for participant in participants:
        #get the data about a participant(gold earned,game length etc) and parse it into a dict
        participant_data = {key:value for key, value in participant.items() if key not in ['augments','traits', 'units','companion']}
        #get the augment data and parse it into a dict
        augment_data = participant['augments']
        augment_dict = {augment:1 for augment in augment_data}
        #get the unit data and parse each individual unit
        unit_data = [parse_single_unit_data(unit) for unit in participant['units']]
        #iterate through the unit_data list and turn it into a dict for storage
        unit_dict = {}
        items_dict = {}
        for elem in unit_data:
            #if the unit is already been accounted for(as in you have a duplicate champ on your board) add another list to the
            #unit list
            unitkey = list(elem.keys())[0]
            if unitkey in list(unit_dict.keys()):
                unit_dict[unitkey]+=[elem[unitkey]]
            #if this unit is not in the 
            else:
                unit_dict[unitkey]=[elem[unitkey]]
            #give all the units that have this item this is useful for analytics on items
            #ex: Item1:[unit1,unit2,unit3]
            items = [[item,unitkey] for item in elem[unitkey][:3] if item !=None]
    
            for itempair in items:
                unitname=itempair[1]
                itemname = itempair[0]
                if itemname in list(items_dict.keys()):
                   items_dict[itemname] +=[unitname]
                else:
                    items_dict[itemname]=[unitname]
        #parse the trait data and create a dict out of it
        trait_data = [parse_single_trait_data(trait) for trait in participant['traits']]
        trait_dict = {key: value for trait in trait_data for key, value in trait.items()}
        #join all the seperate dictionaries (traits,units,participantdata,augmentdata)
        alldata_dictionary = [non_participants,participant_data,augment_dict,unit_dict,trait_dict,items_dict]
        participant_dict = {key:value for dictionary in alldata_dictionary for key,value in dictionary.items()}
        #add all the information given about the match before querying this match
        participant_dict['rank']=rank
        participant_dict['division'] = division
        participant_dict['region'] = region
        participant_dict['greater_region'] = greater_region
        participant_dict['matchid'] = matchid
        total_participant_data +=[participant_dict]
    return total_participant_data
  
def get_matchdata_pd(players_puuid):
    '''
    gets all the matches from a pandas dataframe passed that contains player infos and their most recent matches, gets the match data and pushes it
    into a mongodb database.

    This pandas dataframe has 
    '''
    match_data = []
    #for each player in each row
    for index,row in players_puuid.iterrows():
        #collect the individual data that is in the player database that we created
        matchid = row['match']
        region = row['region']
        greater_region =get_greater_region(region)
        region = {'region': region}
        rank = row['Rank']
        division = row['division']
        #get the data about the match we are analyzing
        matchData = get_match_data_from_matchid(greater_region,matchid)
        #parse the match data
        data = parse_match_data(matchData,rank,division,region,greater_region,matchid)
        
        match_data +=data
    return match_data


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
    
        
'''
Not used for phase 2
'''

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

    
