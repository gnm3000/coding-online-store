from fastapi import FastAPI
from typing import Optional
import os
import motor.motor_asyncio
app = FastAPI(root_path="/",docs_url='/api/docs')
#openapi_url='/api/openapi.json',docs_url='/api/docs',              redoc_url='/api/redoc'
#host="mongo-nodeport-svc"http://10.111.206.75:32000
from typing import Optional, List
#port="27017" #adminuser -p password123
minikubeip ="192.168.49.2"
MONGODB_URL="mongodb://adminuser:password123@mongo-nodeport-svc.default.svc.cluster.local/?retryWrites=true&w=majority" #prod
MONGODB_URL="mongodb://adminuser:password123@192.168.49.2:32258/?retryWrites=true&w=majority" # local

client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
db = client.customers
from pydantic import BaseModel, Field
from bson import ObjectId
class Customer(BaseModel):
    full_name: str
    wallet_usd: int



class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return str(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

class DetailPurchaseHistory(BaseModel):
    cart_id: str
    total_purchase: float = None
    from_wallet: float
    to_wallet: float

class CustomerModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    full_name: str = Field(...)
    wallet_usd: float = Field(...)
    purchase_history: List[DetailPurchaseHistory] = None
    

@app.get("/")
async def hello():
    return {"hello"}

@app.get("/customers",response_model=List[CustomerModel])
async def list_students():
    return await db["customers"].find({},{}).to_list(None)

@app.get("/customers/{customer_id}",response_model=CustomerModel)
async def list_students(customer_id):
    return await db["customers"].find_one({'_id':ObjectId(customer_id)},{})

from MongoDBConnector import MongoDBConnector, DBConnector

class Customer:
    def __init__(self,db_conn:DBConnector):
        self.db_conn = db_conn
    async def insert_one(self,data:dict):
        r=await self.db_conn.insert_one("customers",{"full_name": data["full_name"],"wallet_usd": data["wallet_usd"]})
        return r
    async def find_one(self,condition:dict):
        r=await self.db_conn.get_one("customers",condition)
        return r
    async def update_one(self,condition:dict,data):
        r=await self.db_conn.update_one("customers",condition,data)
        return r
    
    async def process_wallet(self,customer_id:str,purchase_usd:float,cart_id:str):
        customer_result = await self.find_one({'_id': ObjectId(customer_id)})
        wallet_usd = customer_result["wallet_usd"]
        wallet_new_value = wallet_usd - purchase_usd
        r= await self.update_one({'_id': ObjectId(customer_id)},data={'$set':{"wallet_usd":wallet_new_value},
                                    '$push':{"purchase_history":{"cart_id":cart_id, "total_purchase": purchase_usd,
                                                        "from_wallet":wallet_usd,"to_wallet":wallet_new_value}}}
                                )
        return r
    


@app.post("/customers")
async def new_customer(full_name: str, wallet_usd: int):
    customer = Customer(db_conn=MongoDBConnector(db_conn=db))
    r= customer.insert_one(data={"full_name": full_name,"wallet_usd": wallet_usd})
    return {"message": "customer inserted","id":str(r.inserted_id) }



@app.post("/customers/update-wallet")
async def update_wallet_customer(customer_id: str, purchase_usd: float,cart_id: str):
    customer = Customer(db_conn=MongoDBConnector(db_conn=db))
    r=await customer.process_wallet(customer_id=customer_id,purchase_usd=purchase_usd,cart_id=cart_id)

    return {"message": "customer wallet updated","id":str(r.modified_count) }




