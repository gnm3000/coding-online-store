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
db = client.sales
from pydantic import BaseModel, Field
from bson import ObjectId




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

    

@app.get("/")
async def hello():
    return {"hello"}

@app.get("/sales/products",response_model=List[ProductModel])
async def list_products_catalog():
    """ list the catalog store products  """
    return await db["products"].find({},{}).to_list(None)
    

@app.post("/sales/products")
async def new_product_catalog(name: str, price: float,quantity: int):
    """ Scenario: Add new product to the catalog store """
    
    product=await db["products"].insert_one({"name": name,"price": price, "quantity": quantity})
    return {"message": "product inserted","id":str(product.inserted_id) }

@app.post("/sales/cart")
async def add_product_to_cart(product_id: str, name: str, price: float,quantity: int):
    """ Scenario: Add a product to my cart: 
        add a product to my shopping cart and return the actual cart state"""
    # if no shopping cart open => create new
    # if shopping cart => append product
    raise NotImplementedError

@app.post("/sales/checkout")
async def checkout_cart(name: str, price: float,quantity: int):
    """ Scenario: The customer want to checkout and pay the order from the cart """
    # get the cart -> product list
    # save the cart as processing=pending
    # send to background_task
    # --- if  purchase > wallet => NoMoneyError
    # --- if  purchase > stock => NoStockError
    # user_wallet = user_wallet - purchase
    # if sucess=> create order and send to shipping microservice
    # if error => create fail order and send to customers microservice
    raise NotImplementedError

@app.get("/sales/checkout-status")
async def checkout_cart(cart_id: str):
    """ Scenario: The customer asks for the checkout status """
    raise NotImplementedError








