from bson import ObjectId
from pydantic import BaseModel, Field
from typing import Optional, List
from fastapi import FastAPI
from typing import Optional
import os
import motor.motor_asyncio
from bson.objectid import ObjectId
app = FastAPI(root_path="/", docs_url='/api/docs')
# openapi_url='/api/openapi.json',docs_url='/api/docs',              redoc_url='/api/redoc'
# host="mongo-nodeport-svc"http://10.111.206.75:32000
# port="27017" #adminuser -p password123
minikubeip = "192.168.49.2"
MONGODB_URL = "mongodb://adminuser:password123@mongo-nodeport-svc.default.svc.cluster.local/?retryWrites=true&w=majority"  # prod
MONGODB_URL = "mongodb://adminuser:password123@192.168.49.2:32258/?retryWrites=true&w=majority"  # local
from background_tasks import SalesBackgroundTask
client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
db = client.sales


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


@app.get("/sales/products", response_model=List[ProductModel])
async def list_products_catalog():
    """ list the catalog store products  """
    return await db["products"].find({}, {}).to_list(None)

@app.get("/sales/product", response_model=ProductModel)
async def get_a_product(id:str):
    """ Get one product from catalog store  """
    return await db["products"].find_one({"_id": ObjectId(id) })

async def insert_one(dict_params):
    product= await db["products"].insert_one(dict_params)
    return product
@app.post("/sales/products")
async def new_product_catalog(name: str, price: float, quantity: int):
    """ Scenario: Add new product to the catalog store """

    product = insert_one({"name": name, "price": price, "quantity": quantity})
    return {"message": "product inserted", "id": str(product.inserted_id)}

@app.post("/sales/cart")
async def add_product_to_cart(product_id: str, customer_id: str, name: str, price: float, quantity: int):
    """ Scenario: Add a product to my cart:
        add a product to my shopping cart and return the actual cart state"""
    # if no shopping cart open => create new
    # if shopping cart => append product

    condition = {"customer_id": customer_id, "status": "open"}
    product_line = {
        "product_id": product_id,
        "name": name,
        "price": price,
        "quantity": quantity}
    cart = await db["carts"].find_one(condition)
    if(cart):
        db["carts"].update_one(condition,{'$push': {'products': product_line}})
        return {"message": "the product was inserted to your cart",
                "cart_id": str(cart['_id']),
                "cart_products": cart["products"]
                }
    else:
        cart = await db["carts"].insert_one({"customer_id": customer_id, "status": "open","products": [product_line]})
        return {"message": "the product was inserted to your new cart",
                "cart_id": str(cart.inserted_id),
                "cart_products": [product_line]
                }
    


@app.post("/sales/checkout")
async def checkout_cart(customer_id: str):
    """ Scenario: The customer want to checkout and pay the order from the cart """
    # get the cart -> product list
    condition = {"customer_id": customer_id, "status": "open"}
    cart = await db["carts"].find_one(condition)
    if(cart==None):
        return {"message": "No cart was found"}
    cart["status"] = "pending"
    # save the cart as processing=pending
    await db["carts"].update_one(condition,{'$set':{"status":"pending"}})
    
    processor = SalesBackgroundTask()
    processor.processCart(cart)
    
    return {"message":"Your cart is in processing state","cart_id":str(cart['_id']),"status":"pending"}
    raise NotImplementedError


@app.get("/sales/checkout-status")
async def checkout_cart(cart_id: str):
    """ Scenario: The customer asks for the checkout status """
    cart = await db["carts"].find_one({"_id": ObjectId(cart_id) })
    cart["_id"] = str(cart["_id"])
    if(cart["status"]=="pending"): return {"message":"Your cart is still in processing state. Please wait","status":"pending","cart":cart}
    
    if(cart["status"]=="success"): return {"message":"Your cart has been processed succesfully","status":"success","cart":cart}
    
    if(cart["status"]=="failed_by_insufficient_funds"): 
        return {"message":"Your cart has not been processed due insufficient funds.", "status":"failed_by_insufficient_funds","cart":cart}
    if(cart["status"]=="failed_by_stock"): 
        return {"message":"Your cart has not been processed due insufficient stock.", "status":"failed_by_stock","cart":cart}
    
    
    return {"message": "Error", "status":cart["status"],"cart":cart}
    
    
    raise NotImplementedError
