
from bson import ObjectId
from pytest_bdd import scenarios, given, when, then, parsers, scenario


import pytest

from models import AbstractCart, FakeShoppingCart

@pytest.fixture
def context():
    return {}


@scenario('../features/main.feature', 'Add a product to my cart')
def test_cart():
    pass


@given("I'm a customer and I want to buy", target_fixture='cart')
def cart():
    cart = FakeShoppingCart(db=None, customer_id=str(ObjectId()))
    return cart


@when("I add a product to my cart")
def ddg_response_contents(cart: AbstractCart, context):
    response = cart.add(product_id=str(ObjectId()),
                        name="t-shirt", price=31, quantity=1, delivery_date=1)

    context["response"] = response


@then("I should get the products list updated that already are in my cart")
def response_add_cart(context):
    assert len(context["response"]["cart_products"]) > 0
