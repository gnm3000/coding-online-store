import asyncio
from copy import deepcopy
from bson import ObjectId
from pytest_bdd import scenarios, given, when, then, parsers, scenario


from fastapi.testclient import TestClient
import pytest
from unittest import mock

from models import FakeCatalogStore


@pytest.fixture
def context():
    return {}


@scenario('../features/main.feature', 'Decrease a product from stock')
def test_catalog_store():
    pass


@given("I'm a manager store who has products in the catalog", target_fixture='catalog')
def catalog(context):

    catalog = FakeCatalogStore(db=None)
    catalog.products_array.append({"_id":str(ObjectId()),"name":"t-shirt","quantity":100,"price":10,"delivery_date":1})
    context["initial_catalog"] = deepcopy(catalog)
    return catalog


@when("It's approved a customer's payment for 2 t-shirt")
def ddg_response_contents(catalog: FakeCatalogStore, context):
    product = catalog.products_array[0]
    r= catalog.decrease_quantity(product_id=str(product["_id"]),quantity=2)
    
    context["result"] = r


@then("I should get a decrease in my stock")
def response_add_cart(context):
    initial_qty = context["initial_catalog"].products_array[0]["quantity"]
    assert context["result"]["quantity"]<initial_qty
