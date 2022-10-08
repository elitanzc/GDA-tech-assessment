import pymongo
from pymongo import MongoClient
import pandas as pd
import json
from pandas import read_excel
from pandas.api.types import CategoricalDtype


########## Saving json file from link ##########

from urllib.request import urlopen

url = "https://raw.githubusercontent.com/Papagoat/brain-assessment/main/restaurant_data.json"
with urlopen(url) as source:
    out = source.read()

data = json.loads(out)

with open("restaurant_data.json", "w") as file:
    merged = []
    for i in range(len(data)):
        # combine all results shown
        merged.extend(data[i]["restaurants"])
    json.dump(merged, file)


########## Connect to Mongodb and create database ##########
    
mongodb = MongoClient('localhost', 27017)
mongodb.drop_database('Restaurants')
db = mongodb.Restaurants


########## Load data files & save as them collections of the database ##########

restaurant_data = json.load(open("restaurant_data.json"))
# create and populate collection
res = db.restaurants
res.insert_many(restaurant_data)

country_code = read_excel("Country-Code.xlsx")
country_code = country_code.to_dict(orient='records')
# create and populate collection
ccode = db.countrycode
ccode.insert_many(country_code)


########## 1. Generate restaurants.csv ##########

def get_Country_from_CountryCode(country_id, collection):
    out = collection.find_one({"Country Code":country_id}, {"_id":0, "Country":country_id})
    if not out:
        return "NA"
    else:
        return out["Country"]

out = res.aggregate([ 
    {"$group": {
        "_id": "$restaurant.R.res_id", "Restaurant Name": {"$first":"$restaurant.name"}, 
        "Country": {"$first":"$restaurant.location.country_id"}, 
        "City": {"$first":"$restaurant.location.city"}, 
        "User Rating Votes": {"$first":"$restaurant.user_rating.votes"}, 
        "User Aggregate Rating": {"$first":"$restaurant.user_rating.aggregate_rating"}, 
        "Cuisines": {"$first":"$restaurant.cuisines" }
    }}
])
df1 = pd.DataFrame(list(out)).sort_values(by="_id", ignore_index=True)
df1.rename(columns={"_id":"Restaurant Id"}, inplace=True)
# map country_id to country
df1["Country"] = df1["Country"].apply(lambda country_id: get_Country_from_CountryCode(country_id, ccode))
# change dtype of User Aggregate Rating to float
df1["User Aggregate Rating"] = pd.to_numeric(df1["User Aggregate Rating"])
# save as csv locally
df1.to_csv("restaurants.csv")


########## 2. Generate restaurant_events.csv ##########

column_names = ["Event Id", "Restaurant Id", "Restaurant Name",
                "Photo URL", "Event Title", "Event Start Date", "Event End Date"]
events_dict = dict(zip(column_names, [[] for i in range(len(column_names))]))
# filter restaurants with events that happened in April 2019
out = res.find({
    "$and":[
        {"restaurant.zomato_events.event.start_date":{"$lt":'2019-05'}}, 
        {"restaurant.zomato_events.event.end_date":{"$gte":'2019-04'}}
    ]
}, {"_id":0, "restaurant.R.res_id":1, "restaurant.name":1, "restaurant.zomato_events.event.event_id":1, 
"restaurant.zomato_events.event.photos":1, "restaurant.zomato_events.event.title":1, 
"restaurant.zomato_events.event.start_date":1, "restaurant.zomato_events.event.end_date":1})

for doc in out:
    # doc is one restaurant
    doc = doc["restaurant"]
    # restaurant.zomato_events contains a list of events
    for event in doc["zomato_events"]:
        event = event["event"]
        if event["start_date"] >= '2019-05' or event["end_date"] < '2019-04':
            continue
        events_dict["Event Id"].append(event["event_id"])
        events_dict["Event Title"].append(event["title"])
        events_dict["Restaurant Id"].append(doc["R"]["res_id"])
        events_dict["Restaurant Name"].append(doc["name"])
        # take the url of the first photo if any
        photo_urls = [p["photo"]["url"] for p in event["photos"]]
        if not photo_urls:
            events_dict["Photo URL"].append("NA")
        else:
            events_dict["Photo URL"].append(photo_urls[0])
        events_dict["Event Start Date"].append(event["start_date"])
        events_dict["Event End Date"].append(event["end_date"])
df2 = pd.DataFrame(events_dict).sort_values(by="Event Id", ignore_index=True)
# save as csv locally
df2.to_csv("restaurant_events.csv")


########## 3. Get threshold ##########

ratings = ["Excellent", "Very Good", "Good", "Average", "Poor"]

out = res.aggregate([
    {"$match": {
        "restaurant.user_rating.rating_text": {"$in":ratings}
    }},
    {"$group":{
        "_id": "$restaurant.user_rating.rating_text",
        "min_rating": {"$min": "$restaurant.user_rating.aggregate_rating"},
        "max_rating": {"$max": "$restaurant.user_rating.aggregate_rating"}
    }}
])
df3 = pd.DataFrame(list(out))
df3.rename(columns={"_id":"Rating"}, inplace=True)
df3["Rating"] = df3["Rating"].astype(CategoricalDtype(categories=ratings, ordered=True))
df3.sort_values(by="Rating", ignore_index=True, inplace=True)
print(df3)
print()
print("Thresholds:")
print("4.5 <= Excellent <= 5.0")
print("4.0 <= Very Good < 4.5")
print("3.5 <= Good < 4.0")
print("2.5 <= Average < 3.5")
print("0.0 <= Poor < 2.5")




    
