
from pytest_bdd import scenarios, given, when,then, parsers,scenario

from main import app
from fastapi.testclient import TestClient
import pytest
from unittest import mock
#scenarios('../features/main.feature')
@pytest.fixture
def context():
    return {}

@scenario('../features/main.feature', 'Create a new order')
def test_order():
    pass

@given("a new order payed arrived", target_fixture='client_app')
def client_app():
    client = TestClient(app)
    return client
    

@when("my order was received")
def ddg_response_contents(client_app,context):
    order_object = mock.Mock()
    order_object.inserted_id = "xxx"
    with mock.patch("main.insert_one",return_value=order_object):
        response = client_app.post("/shipping/orders",params={"cart_id": "62796a564f406dec0c2dca6d",
                                                        "customer_id": "6277135f64af6aad4682bed9",
                                                        "products":[{"name": "t-shirt", "price":31,"quantity": 1}],
                                                        "delivery_date":"2022-05-12"
                                                        })
    context["response"] = response
    
    #return response
    
@then("I Should get the order in ordered status, saved and get a confirmation message ready to be processed")
def response_add_cart(context):
    #print(ddg_response_contents)
    assert context["response"].status_code==200
    assert context["response"].json()["message"]=="order inserted"
    
    pass
