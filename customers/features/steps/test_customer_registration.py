from pytest_bdd import scenarios, given, when,then, parsers,scenario

from main import app
from fastapi.testclient import TestClient
import pytest
from unittest import mock
#scenarios('../features/main.feature')
@pytest.fixture
def context():
    return {}

@scenario('../app.feature', 'the customer register to the store')
def test_customer():
    pass

@given("the petition of the customer for registration", target_fixture='client_app')
def client_app():
    client_app = TestClient(app)
    return client_app

@when("we receive the full_name and amount USD for the wallet")
def ddg_response_contents(client_app,context):
    customer = mock.Mock()
    customer.inserted_id="xxx"
    with mock.patch("main.Customer.insert_one",return_value=customer):
        response= client_app.post("/customers",params={"full_name":"Martin Messi","wallet_usd":300})
        context["response"] = response

@then("I should get a confirmation insertion message")
def response_add_cart(context):
    assert context["response"].json()["message"]=="customer inserted"
    assert context["response"].status_code==200
    



