from bson import ObjectId
from pytest_bdd import scenarios, given, when,then, parsers,scenario

from main import app,Customer
from MongoDBConnector import FakeMongoDBConnector

from fastapi.testclient import TestClient
import pytest
from unittest import mock
import asyncio
#scenarios('../features/main.feature')
@pytest.fixture
def context():
    return {}

@scenario('../app.feature', 'the customer register to the store')
def test_customer():
    pass

@given("the petition of the customer for registration", target_fixture='customer')
def customer():
    customer = Customer(db_conn=FakeMongoDBConnector(db_conn=None))
    return customer


@when("we receive the full_name and amount USD for the wallet")
def ddg_response_contents(customer,context):
    result=asyncio.run(customer.insert_one(data={"full_name":"John Max","wallet_usd":111}))
    context["result"]= result
    

@then("I should get a confirmation insertion message")
def response_add_cart(context):
    assert len(context["result"]) == len(str(ObjectId()))
    



