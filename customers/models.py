from pydantic import BaseModel, Field
from bson import ObjectId
from typing import Optional, List

from MongoDBConnector import MongoDBConnector, DBConnector
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
class ProductModel(BaseModel):
    product_id: str = Field(...)
    name: str = Field(...)
    price: float = Field(...)
    quantity: int = Field(...)
    delivery_date: int = Field(...)

class FailedOrder(BaseModel):
    customer_id: str
    products: List[ProductModel]
    cart_id: str
    status: str
    created_at: str

class CustomerModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    full_name: str = Field(...)
    wallet_usd: float = Field(...)
    purchase_history: List[DetailPurchaseHistory] = None
    failed_orders: List[FailedOrder] = None

class Customer:
    def __init__(self,db_conn:DBConnector):
        self.db_conn = db_conn
    async def insert_one(self,data:dict):
        r=await self.db_conn.insert_one("customers",{"full_name": data["full_name"],"wallet_usd": data["wallet_usd"]})
        return r
    async def find_one(self,condition:dict):
        r= await self.db_conn.get_one("customers",condition)
        return r
    async def update_one(self,condition:dict,data):
        r=await self.db_conn.update_one("customers",condition,data)
        return r
    
    async def process_wallet(self,customer_id:str,purchase_usd:float,cart_id:str):
        r =  (self.find_one({'_id': ObjectId(customer_id)}))
        customer_result= await r
        wallet_usd = customer_result["wallet_usd"]
        wallet_new_value = wallet_usd - purchase_usd
        r= await self.update_one({'_id': ObjectId(customer_id)},data={'$set':{"wallet_usd":wallet_new_value},
                                    '$push':{"purchase_history":{"cart_id":cart_id, "total_purchase": purchase_usd,
                                                        "from_wallet":wallet_usd,"to_wallet":wallet_new_value}}}
                                )
        return r
    
    