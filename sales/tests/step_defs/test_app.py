
from pytest_bdd import scenarios, given, when,then, parsers



scenarios('../features/main.feature')

@given("the a product to add to my cart", target_fixture='product_example')
def product_example():
    return {"product_id": "xxx", "name": "t-shirt", "price":30,"quantity": 1}

@when("add a product to the cart")
def ddg_response_contents(product_example):
    #api call with product example
    pass

@then("get the products list updated that already are in my cart")
def response_add_cart():
    assert 1==2
