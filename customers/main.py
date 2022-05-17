from models import CustomerModel, Customer
from MongoDBConnector import MongoDBConnector
from fastapi import FastAPI
import os
import motor.motor_asyncio
from dotenv import load_dotenv
from typing import Optional, List
from bson import ObjectId

# DB
load_dotenv()
MONGODB_URL = os.getenv('MONGODB_URL')
client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
db = client.customers


app = FastAPI(root_path="/", docs_url='/customers/api/docs',openapi_url="/customers/openapi.json")


@app.get("/")
async def hello():
    return {"hello"}


@app.get("/customers", response_model=List[CustomerModel])
async def list_customers():
    return await db["customers"].find({}, {}).to_list(None)


@app.get("/customers/{customer_id}", response_model=CustomerModel)
async def get_customer(customer_id):
    return await db["customers"].find_one({'_id': ObjectId(customer_id)}, {})


@app.post("/customers")
async def new_customer(full_name: str, wallet_usd: float):
    customer = Customer(db_conn=MongoDBConnector(db_conn=db))
    r = await customer.insert_one(data={"full_name": full_name, "wallet_usd": wallet_usd})
    return {"message": "customer inserted", "customer_id": str(r)}


@app.post("/customers/update-wallet")
async def update_wallet_customer(customer_id: str, purchase_usd: float, cart_id: str):
    customer = Customer(db_conn=MongoDBConnector(db_conn=db))
    r = await customer.process_wallet(customer_id=customer_id, purchase_usd=purchase_usd, cart_id=cart_id)

    return {"message": "customer wallet updated", "id": str(r.modified_count)}
