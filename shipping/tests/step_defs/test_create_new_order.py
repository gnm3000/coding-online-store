
from pytest_bdd import scenarios, given, when,then, parsers,scenario

from fastapi.testclient import TestClient
import pytest
from unittest import mock
#scenarios('../features/main.feature')
from shipping_processor import ShippingProcessor,FakeCart,FakeNotifier
from MongoDBConnector import FakeMongoDBConnector
@pytest.fixture
def context():
    return {}

@scenario('../features/main.feature', 'Create a new order')
def test_order():
    pass
from bson.objectid import ObjectId
@pytest.fixture
def cart_id():
    return str(ObjectId())

@given("a new checkout payed arrived", target_fixture='shipping_processor')
def shipping_processor():
    # here a cart_id in success_state
    shipping_processor = ShippingProcessor(channel=None,notifier=FakeNotifier(channel=None),db=FakeMongoDBConnector(db_conn="xxx"))
    return shipping_processor

@when("a new order is created")
def order_status(shipping_processor: ShippingProcessor,context,cart_id):
    
    context["order"] = shipping_processor.process_sucess_checkout(data={"cart_id":cart_id},cart=FakeCart(cart_id=cart_id))
    
@then("I Should get the order in ordered status")
def response_add_cart(context):
    assert context["order"]["status"]=="ordered"
    