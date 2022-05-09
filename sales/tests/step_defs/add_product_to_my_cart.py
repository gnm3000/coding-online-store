
from pytest_bdd import scenarios, given, when,then, parsers,scenario

from main import app
from fastapi.testclient import TestClient
import pytest

#scenarios('../features/main.feature')
@pytest.fixture
def context():
    return {}

@scenario('../features/main.feature', 'Add a product to my cart')
def test_cart():
    pass

@given("I'm a customer and I want to buy", target_fixture='client_app')
def client_app():
    client = TestClient(app)
    return client
    

@when("I add a product to my cart")
def ddg_response_contents(client_app,context):
    response = client_app.post("/sales/cart",params={"product_id": "62796a564f406dec0c2dca6d",
                                                     "customer_id": "6277135f64af6aad4682bed9",
                                                      "name": "t-shirt", "price":31,"quantity": 1})
    context["response"] = response
    
    #return response
    
@then("I should get the products list updated that already are in my cart")
def response_add_cart(context):
    #print(ddg_response_contents)
    assert context["response"].status_code==200
    pass
