from pprint import pprint
from bson import ObjectId
from pydantic import BaseModel, Field
from typing import Optional, List
from fastapi import FastAPI
from typing import Optional
import os
import motor.motor_asyncio
app = FastAPI(root_path="/", docs_url='/api/docs')
# openapi_url='/api/openapi.json',docs_url='/api/docs',              redoc_url='/api/redoc'
# host="mongo-nodeport-svc"http://10.111.206.75:32000
# port="27017" #adminuser -p password123
minikubeip = "192.168.49.2"
MONGODB_URL = "mongodb://adminuser:password123@mongo-nodeport-svc.default.svc.cluster.local/?retryWrites=true&w=majority"  # prod
MONGODB_URL = "mongodb://adminuser:password123@192.168.49.2:32258/?retryWrites=true&w=majority"  # local

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

class OrderModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    cart_id: str = Field(...)
    customer_id: str = Field(...)
    delivery_date: str = Field(...)
    status: str = Field(...)
    products: List[ProductModel] = None
    #products: List[ProductModel] = Field(...)
    
    




@app.get("/")
async def hello():
    return {"hello"}


@app.get("/shipping/orders", response_model=List[OrderModel])
async def list_orders():
    """ list   """
    return await db["orders"].find().to_list(None)


@app.get("/shipping/return-products")
async def return_products():
    """ Saga Pattern  """
    # 1. Send a message to SALES: new return {product_id: xxx, quantity: 2} and sales edit product_catalog.quantity
    # 2. Send a message to customer: Edit order_id: xxx, add "product_id.quantity=-1", and edit customer.wallet_usd +price
    # 3. wait reply OK from sales and customer. ELSE get back, and this
    # return-products need to process again
    pass

async def insert_one(order_dict):
    order = await db["orders"].insert_one(order_dict)
    return order
from typing import Any, Dict, AnyStr, List, Union
JSONObject = Dict[AnyStr, Any]
JSONArray = List[Any]
JSONStructure = Union[JSONArray, JSONObject]
@app.post("/shipping/orders")
async def create_order(customer_id: str, cart_id: str, products: Union[JSONArray, JSONObject], delivery_date: str):
    """ Scenario: Create a new order """
    # save to DB, assign a processing time between 1 to 5 days, and set
    # order_status=Orderded
    #
    #products_example = [{"_id":"62796a564f406dec0c2dca6d","name":"t-shirt","price":21,"quantity":1}]
    order = await db["orders"].insert_one({"customer_id": customer_id, 
    "cart_id": cart_id,"delivery_date": delivery_date,
    "status": "ordered","products":products})

    # return Order saved with order_id

    # Order status: Ordered, Sent to warehouse, Packaged, Carrier picked up,
    # Out for delivery, Delivered
    pprint(order)
    return {"message": "order inserted", "id": str(order.inserted_id)}
