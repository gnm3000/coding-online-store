from datetime import datetime
from pprint import pprint
from bson import ObjectId
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Optional, List
from fastapi import FastAPI
from typing import Optional
import os
import motor.motor_asyncio
app = FastAPI(root_path="/", docs_url='/api/docs')

load_dotenv()
MONGODB_URL = os.getenv('MONGODB_URL')
client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
db = client.shipping

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
class ProductModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str = Field(...)
    price: float = Field(...)
    quantity: int = Field(...)


class StatusHistory(BaseModel):
    status: str = Field(...)
    created_at: datetime = Field(...)
    

class OrderModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    cart_id: str = Field(...)
    customer_id: str = Field(...)
    #delivery_date: str = Field(...)
    status: str = Field(...)
    products: List[ProductModel] = None
    #products: List[ProductModel] = Field(...)
    status_history: List[StatusHistory] = None
    
@app.get("/")
async def hello():
    return {"hello"}

@app.get("/shipping/orders", response_model=List[OrderModel])
async def list_orders(cart_id=None):
    """ list shipping orders   """
    if(cart_id==None): return await db["orders"].find().to_list(None)
    return await db["orders"].find({"cart_id":cart_id}).to_list(None)

@app.get("/shipping/return-products")
async def return_products():
    """ Saga Pattern  """
    # 1. Send a message to SALES: new return {product_id: xxx, quantity: 2} and sales edit product_catalog.quantity
    # 2. Send a message to customer: Edit order_id: xxx, add "product_id.quantity=-1", and edit customer.wallet_usd +price
    # 3. wait reply OK from sales and customer. ELSE get back, and this
    # return-products need to process again
    pass

