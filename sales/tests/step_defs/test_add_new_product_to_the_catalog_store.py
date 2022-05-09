from pytest_bdd import scenarios, given, when,then, parsers,scenario

from main import app
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

@given("I'm a manager and I want to setup the store", target_fixture='client_app')
def client_app():
    client_app = TestClient(app)
    return client_app

@when("add a product to the catalog")
def ddg_response_contents(client_app,context):
    product = mock.Mock()
    product.inserted_id="xxx"
    with mock.patch("main.insert_one",return_value=product):
        response= client_app.post("/sales/products",params={"name": "Jeans","price": 40,"quantity": 100})
        context["response"] = response

@then("I should get the confirmation message of added product")
def response_add_cart(context):
    assert context["response"].json()["message"]=="product inserted"
    assert context["response"].status_code==200
    
