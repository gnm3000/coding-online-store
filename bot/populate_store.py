

from dotenv import load_dotenv
import os

load_dotenv()
MONGODB_URL = os.getenv('MONGODB_URL')

import pymongo
client = pymongo.MongoClient(MONGODB_URL)
client.drop_database("customers")
client.drop_database("sales")
client.drop_database("shipping")
import csv,requests
from urllib.parse import urlencode
customers = csv.reader(open("data/customers.csv"))
first=True
for row in customers:
    if(first==True):
        first=False
        continue
    money = row[1]
    name=row[0]
    print(money)
    print(float(money))
    res=requests.post("http://localhost:5678/customers",params=urlencode({"full_name":name,"wallet_usd":float(money)*4}))
    print(res.content)

response = requests.get("http://localhost:5678/customers")
users= response.json()
##
products = csv.reader(open("data/products.csv"))
first=True
for row in products:
    if(first==True):
        first=False
        continue
    #name,price,quantity,delivery_date
    name,price,quantity,delivery_date = row[0],row[1],row[2],row[3]
    
    res=requests.post("http://localhost:8000/sales/products",params=urlencode({"name":name,"price":price,"quantity":quantity,"delivery_date":delivery_date}))
    print(res.content)


response = requests.get("http://localhost:8000/sales/products")
products= response.json()