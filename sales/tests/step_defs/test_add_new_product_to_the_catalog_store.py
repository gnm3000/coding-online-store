import asyncio
from pytest_bdd import scenarios, given, when,then, parsers,scenario

from main import FakeCatalogStore

from fastapi.testclient import TestClient
import pytest
from unittest import mock
#scenarios('../features/main.feature')
@pytest.fixture
def context():
    return {}

@scenario('../features/main.feature', 'Add new product to the catalog store')
def test_catalog_store():
    pass

@given("I'm a manager and I want to setup the store", target_fixture='catalog')
def catalog():
    catalog=FakeCatalogStore(db=None)
    return catalog

@when("add a product to the catalog")
def ddg_response_contents(catalog:FakeCatalogStore,context):
    r=catalog.insert_one({"name": "Jeans","price": 40,"quantity": 100})
    context["result"] = r

@then("I should get the confirmation message of added product")
def response_add_cart(context):
    assert hasattr(context["result"],"inserted_id")
    
