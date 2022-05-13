from bson import ObjectId
from pytest_bdd import scenarios, given, when,then, parsers,scenario

from main import app,Customer
from MongoDBConnector import FakeMongoDBConnector
from fastapi.testclient import TestClient
import pytest
import asyncio
from unittest import mock
#scenarios('../features/main.feature')
@pytest.fixture
def context():
    return {}

@scenario('../app.feature', 'the customer bought something and the business updated his wallet account')
def test_customer():
    pass

@given("An order is being processed by an amount in usd", target_fixture='customer')
def customer():
    customer = Customer(db_conn=FakeMongoDBConnector(db_conn=None))
    return customer

@when("we update the customer wallet")
def ddg_response_contents(customer: Customer,context):
    result=asyncio.run(customer.process_wallet(customer_id=str(ObjectId()),purchase_usd=100.1,cart_id=str(ObjectId())))
    context["result"]= result

@then("I should get his new balance")
def response_add_cart(context):
    print(context)
    assert context["result"].modified_count>0
    



