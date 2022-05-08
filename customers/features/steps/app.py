from behave import *
import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from main import app
import json
import asyncio

@pytest.fixture
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()

@given('the petition of the customer for registration')
def step_impl(context):
    context.client = client = TestClient(app)
    
@when('we receive the full_name and amount USD for the wallet')
def step_impl(context):
    context.response = context.client.post("/customers",params={"full_name":"Martin Messi","wallet_usd":300})
    
    print(context.response)

@then('we get a confirmation insertion message')
def step_impl(context):
    assert context.response.status_code == 200
    assert context.response.json()["message"] == "customer inserted"


# implement pytest-bdd