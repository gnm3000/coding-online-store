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
app = FastAPI(root_path="/", docs_url='/sales/api/docs')


load_dotenv()
MONGODB_URL = os.getenv('MONGODB_URL')
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
    delivery_date: int = Field(...)


class CartModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    customer_id: str = Field(...)
    status: str = Field(...)
    products: List[ProductModel]


@app.get("/")
async def hello():
    return {"hello"}


class AbstractCatalogStore(ABC):
    def __init__(self) -> None:
        super().__init__()

    def insert_one(self,data:dict):
        raise NotImplementedError


class CatalogStore(AbstractCatalogStore):
    def __init__(self, db):
        self.db = db

    async def _insert_one(self, dict_params):
        product = await db["products"].insert_one(dict_params)
        return product

    async def insert_one(self, data):
        return await self._insert_one(data)


class FakeCatalogStore(AbstractCatalogStore):
    def __init__(self, db):
        self.db = db

    def _insert_one(self, dict_params):
        p = Mock()
        p.inserted_id = str(ObjectId())
        return p

    def insert_one(self, data):
        return self._insert_one(data)


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


class AbstractCart(ABC):
    def __init__(self) -> None:
        super().__init__()

    def add(self, product_id: str, name: str, price: float,
            quantity: int, delivery_date: int):
        raise NotImplementedError


class MyShoppingCart(AbstractCart):
    def __init__(self, db, customer_id: str):
        self.customer_id = customer_id
        self.db = db

    async def add(self, product_id: str, name: str, price: float, quantity: int, delivery_date: int):
        condition = {"customer_id": self.customer_id, "status": "open"}
        product_line = {
            "product_id": product_id,
            "name": name,
            "price": price,
            "quantity": quantity, "delivery_date": delivery_date
        }
        cart = await self.db["carts"].find_one(condition)
        if(cart):
            await self.db["carts"].update_one(condition, {'$push': {'products': product_line}})
            return {"message": "the product was inserted to your cart",
                    "cart_id": str(cart['_id']),
                    "cart_products": cart["products"]
                    }
        else:
            cart = await self.db["carts"].insert_one({"customer_id": self.customer_id, "status": "open", "products": [product_line]})
            return {"message": "the product was inserted to your new cart",
                    "cart_id": str(cart.inserted_id),
                    "cart_products": [product_line]
                    }


class FakeShoppingCart(AbstractCart):
    def __init__(self, db, customer_id: str):
        self.customer_id = customer_id
        self.db = db
        self.empty = True

    def add(self, product_id: str, name: str, price: float,
            quantity: int, delivery_date: int):
        condition = {"customer_id": self.customer_id, "status": "open"}
        product_line = {
            "product_id": product_id,
            "name": name,
            "price": price,
            "quantity": quantity,
            "delivery_date": delivery_date
        }
        if(not self.empty):
            return {"message": "the product was inserted to your cart",
                    "cart_id": str(ObjectId()),
                    "cart_products": [product_line]
                    }
        else:
            self.empty = False
            return {"message": "the product was inserted to your new cart",
                    "cart_id": str(ObjectId()),
                    "cart_products": [product_line]
                    }


@app.post("/sales/cart")
async def add_product_to_cart(product_id: str, customer_id: str, name: str, price: float, quantity: int, delivery_date: int):
    """ Scenario: Add a product to my cart:
        add a product to my shopping cart and return the actual cart state"""
    # if no shopping cart open => create new
    # if shopping cart => append product
    my_shopping_Cart = MyShoppingCart(db=db, customer_id=customer_id)
    message_return = await my_shopping_Cart.add(product_id=product_id, name=name, price=price, quantity=quantity, delivery_date=delivery_date)
    return message_return


class CheckoutCartProcessor:
    def __init__(self, db):
        self.db = db

    async def getOpenCartByCustomerId(self, customer_id: str):
        condition = {"customer_id": customer_id, "status": "open"}
        return await self.db["carts"].find_one(condition)

    async def setCartPending(self, customer_id: str):
        condition = {"customer_id": customer_id, "status": "open"}
        return await self.db["carts"].update_one(condition, {'$set': {"status": "pending"}})

    def process_cart(self, cart_id, processor: SalesBackgroundTask):
        processor.processCart(cart_id=cart_id)


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
