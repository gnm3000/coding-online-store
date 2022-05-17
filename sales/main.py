from abc import ABC, abstractmethod

from dotenv import load_dotenv
from background_tasks import SalesBackgroundTask
from unittest.mock import Mock
from bson import ObjectId
from pydantic import BaseModel, Field
from typing import Optional, List
from fastapi import FastAPI
from typing import Optional
import os
import motor.motor_asyncio
from bson.objectid import ObjectId

from models import CartModel, CatalogStore, CheckoutCartProcessor, MyShoppingCart, ProductModel
app = FastAPI(root_path="/", docs_url='/sales/api/docs',openapi_url="/sales/openapi.json")

load_dotenv()
MONGODB_URL = os.getenv('MONGODB_URL')
client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
db = client.sales




@app.get("/")
async def hello():
    return {"hello"}



@app.get("/sales/products", response_model=List[ProductModel])
async def list_products_catalog():
    """ list the catalog store products  """
    return await db["products"].find({}, {}).to_list(None)


@app.get("/sales/product", response_model=ProductModel)
async def get_a_product(id: str):
    """ Get one product from catalog store  """
    return await db["products"].find_one({"_id": ObjectId(id)})


@app.post("/sales/products")
async def new_product_catalog(name: str, price: float, quantity: int, delivery_date: int):
    """ Scenario: Add new product to the catalog store """
    catalog = CatalogStore(db=db)
    product = await catalog.insert_one({"name": name, "price": price, "quantity": quantity, "delivery_date": delivery_date})
    return {"message": "product inserted", "id": str(product.inserted_id)}


@app.post("/sales/cart")
async def add_product_to_cart(product_id: str, customer_id: str, name: str, price: float, quantity: int, delivery_date: int):
    """ Scenario: Add a product to my cart:
        add a product to my shopping cart and return the actual cart state"""
    # if no shopping cart open => create new
    # if shopping cart => append product
    my_shopping_Cart = MyShoppingCart(db=db, customer_id=customer_id)
    message_return = await my_shopping_Cart.add(product_id=product_id, name=name, price=price, quantity=quantity, delivery_date=delivery_date)
    return message_return



@app.post("/sales/checkout")
async def checkout_cart(customer_id: str):
    """ Scenario: The customer want to checkout and pay the order from the cart """
    # get the cart -> product list
    ch = CheckoutCartProcessor(db)
    cart = await ch.getOpenCartByCustomerId(customer_id=customer_id)

    if(cart is None):
        return {"message": "No cart was found"}
    cart_id = cart['_id']
    await ch.setCartPending(customer_id=customer_id)
    ch.process_cart(cart_id=str(cart_id), processor=SalesBackgroundTask())
    return {"message": "Your cart is in processing state",
            "cart_id": str(cart_id), "status": "pending"}


@app.get("/sales/checkout-status")
async def checkout_cart(cart_id: str):
    """ Scenario: The customer asks for the checkout status """
    cart = await db["carts"].find_one({"_id": ObjectId(cart_id)})
    if(cart is None):
        return {"message": "cart not found"}
    cart["_id"] = str(cart["_id"])
    if(cart["status"] == "pending"):
        return {"message": "Your cart is still in processing state. Please wait",
                "status": "pending", "cart": cart}

    if(cart["status"] == "success"):
        return {"message": "Your cart has been processed succesfully",
                "status": "success", "cart": cart}

    if(cart["status"] == "failed_by_insufficient_funds"):
        return {"message": "Your cart has not been processed due insufficient funds.",
                "status": "failed_by_insufficient_funds", "cart": cart}
    if(cart["status"] == "failed_by_stock"):
        return {"message": "Your cart has not been processed due insufficient stock.",
                "status": "failed_by_stock", "cart": cart}

    return {"message": "Error", "status": cart["status"], "cart": cart}


@app.get("/sales/checkout/list", response_model=List[CartModel])
async def list_checkout():
    """ Scenario: The customer asks for the checkout status """
    return await db["carts"].find({}).to_list(None)
