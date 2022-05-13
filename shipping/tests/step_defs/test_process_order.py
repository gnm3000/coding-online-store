
from pytest_bdd import scenarios, given, when,then, parsers,scenario

from fastapi.testclient import TestClient
import pytest
from unittest import mock
#scenarios('../features/main.feature')
from shipping_processor import ShippingProcessor,FakeCart,FakeNotifier
from MongoDBConnector import FakeMongoDBConnector
from bson.objectid import ObjectId
@pytest.fixture
def context():
    return {}

@pytest.fixture
def shipping_processor():
    shipping_processor = ShippingProcessor(channel=None,notifier=FakeNotifier(channel=None),db=FakeMongoDBConnector(db_conn="xxx"))
    return shipping_processor

@pytest.fixture
def cart_id():
    return str(ObjectId())

@pytest.fixture
def order_id():
    return str(ObjectId())


@scenario('../features/main.feature', 'Process the created order')
def test_order():
    pass

@given("an order created in ordered status", target_fixture='ordered_status_order')
def order_created_ordered_status(shipping_processor,cart_id):
    # here a cart_id in success_state
    
    order= shipping_processor.process_sucess_checkout(data={"cart_id":cart_id},cart=FakeCart(cart_id=cart_id))
    assert order["status"] == "ordered"
    return order
@when("the order is completely processed")
def order_status(ordered_status_order,shipping_processor,context):
    order_id=ordered_status_order["order_id"]
    order = shipping_processor.process_ordered_orders(data={"order_id":order_id})
    assert order["status"] == "sent_to_warehouse"
    order = shipping_processor.process_warehouse_orders(data={"order_id":order_id})
    assert order["status"] == "packaged"
    order = shipping_processor.process_packaged_orders(data={"order_id":order_id})
    assert order["status"] == "carrier_picked_up"
    order = shipping_processor.process_carrier_picked_up_orders(data={"order_id":order_id})
    assert order["status"] == "out_for_delivery"
    order = shipping_processor.process_out_for_delivery_orders(data={"order_id":order_id})
    context["order"] = order
    
@then("I Should get the order in delivered status")
def response_add_cart(context):
    assert context["order"]["status"] == "delivered"
    