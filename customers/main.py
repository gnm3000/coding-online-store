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

class CustomerModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    full_name: str = Field(...)
    wallet_usd: int = Field(...)
    

@app.get("/")
async def hello():
    return {"hello"}

@app.get("/customers",response_model=List[CustomerModel])
async def list_students():
    return await db["customers"].find({},{}).to_list(None)
    

@app.post("/customers")
async def new_customer(full_name: str, wallet_usd: int):
    
    customer=await db["customers"].insert_one({"full_name": full_name,"wallet_usd": wallet_usd})
    return {"message": "customer inserted","id":str(customer.inserted_id) }




