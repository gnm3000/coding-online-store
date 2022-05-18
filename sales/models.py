
from abc import ABC
from typing import List
from unittest.mock import Mock
from bson import ObjectId
from pydantic import BaseModel, Field

from abc import ABC, abstractmethod

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

class AbstractCatalogStore(ABC):

    @abstractmethod
    def __init__(self) -> None:
        super().__init__()
    @abstractmethod
    def insert_one(self,data:dict):
        raise NotImplementedError
    @abstractmethod
    def decrease_quantity(self,product_id:str,quantity:int):
        raise NotImplementedError


class CatalogStore(AbstractCatalogStore):
    def __init__(self, db):
        self.db = db

    async def _insert_one(self, dict_params):
        product = await self.db["products"].insert_one(dict_params)
        return product

    async def insert_one(self, data):
        return await self._insert_one(data)
    async def decrease_quantity(self, product_id:str,quantity:int):
        product = await self.db["products"].update_one({'_id':ObjectId(product_id)},{"$inc": {"quantity": -quantity}})
        return product


    


class FakeCatalogStore(AbstractCatalogStore):
    def __init__(self, db):
        self.db = db
        self.products_array = []
    def _insert_one(self, dict_params):
        p = Mock()
        p.inserted_id = str(ObjectId())
        self.products_array.append(p)
        return p

    def insert_one(self, data):
        return self._insert_one(data)

    def decrease_quantity(self, product_id:str,quantity:int):
        for idx, product in enumerate(self.products_array):
            if(product_id==product["_id"]):
                self.products_array[idx]["quantity"] = self.products_array[idx]["quantity"] -1
                return self.products_array[idx]

        



class AbstractCart(ABC):

    @abstractmethod
    def __init__(self) -> None:
        super().__init__()


    @abstractmethod
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



