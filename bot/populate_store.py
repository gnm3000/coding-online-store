

from dotenv import load_dotenv
import os

load_dotenv()
MONGODB_URL = os.getenv('MONGODB_URL')

import pymongo
client = pymongo.MongoClient(MONGODB_URL)
client.drop_database("customers")
client.drop_database("sales")
client.drop_database("shipping")

BASE_URL_SALES = os.getenv('BASE_URL_SALES',"http://localhost:8000")
BASE_URL_CUSTOMERS = os.getenv('BASE_URL_CUSTOMERS',"http://localhost:5678")
BASE_URL_SHIPPING = os.getenv('BASE_URL_SHIPPING',"http://localhost:5679")


    

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
    res=requests.post(BASE_URL_CUSTOMERS+"/customers",params=urlencode({"full_name":name,"wallet_usd":float(money)*4}))
    print(res.content)

response = requests.get(BASE_URL_CUSTOMERS+"/customers")
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
    
    res=requests.post(BASE_URL_SALES+"/sales/products",params=urlencode({"name":name,"price":price,"quantity":quantity,"delivery_date":delivery_date}))
    print(res.content)


response = requests.get(BASE_URL_SALES+"/sales/products")
products= response.json()
print("process finished")