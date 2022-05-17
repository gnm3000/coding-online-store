from email import header
from locust import SequentialTaskSet, HttpUser, constant, task,between
import json
import random,time
from urllib.parse import urlencode
import csv
import os
from locust import events
import requests
BASE_URL_SALES = os.getenv('BASE_URL_SALES',"http://localhost:8000")
BASE_URL_CUSTOMERS = os.getenv('BASE_URL_CUSTOMERS',"http://localhost:5678")
BASE_URL_SHIPPING = os.getenv('BASE_URL_SHIPPING',"http://localhost:5679")


response = requests.get(BASE_URL_CUSTOMERS+"/customers")
USERS = response.json()
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    print("A new test is starting")
    

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    print("A new test is ending")

class MySeqTask(SequentialTaskSet):
    customer={'_id': '627719815625cb5486f30791', 'full_name': 'Martin Messi', 'wallet_usd': 300.0, 'purchase_history': None}
    
    product1={'_id': '627977ed61c9f2b4a0c6bf20', 'name': 'Shirt White', 'price': 10.0, 'quantity': 100}
    
    

    def on_start(self):
        self.check_checkout=""
        self.shipping_status=""
        if(len(USERS)>0):
            self.customer = USERS.pop()
        else:
            self.stop()
        
    
    @task
    def define_products(self):
        
        response = self.client.get(BASE_URL_SALES+"/sales/products")
        catalog = response.json()
        random.shuffle(catalog)
        self.random_products = catalog[:random.randint(1,5)]
        
        
    @task
    def add_to_cart(self):
        products = self.random_products
        for product in products:
            payload = {"product_id":product['_id'],"customer_id":self.customer['_id'],"name":product["name"],"price":product["price"],
                                "quantity":random.randint(1,3),"delivery_date":product["delivery_date"]}
            response = self.client.post(BASE_URL_SALES+"/sales/cart?",params=urlencode(payload))
    @task
    def checkout_cart(self):
        response = self.client.post(BASE_URL_SALES+"/sales/checkout",params=urlencode({"customer_id":self.customer['_id']}))
        if(response.json()["message"]=="No cart was found"):
            self.stop()
        self.checkout = response.json()
        
    @task
    def checkout_status(self):
        while True:
            response = self.client.get(BASE_URL_SALES+"/sales/checkout-status",params=urlencode({"cart_id":self.checkout['cart_id']}))
            time.sleep(1)
            checkout_status=response.json()
            if(checkout_status["status"]!="pending"):
                break
        self.check_checkout = checkout_status["status"]
        
        if(checkout_status["status"]=="success"):
            count=0
            while True:
                req = self.client.get(BASE_URL_SHIPPING+"/shipping/orders",params={"cart_id":self.checkout['cart_id']})
                self.shipping_status=req.json()[0]["status"]
                if(self.shipping_status=="delivered"):
                    break
                count=count+1
                if(count>30):
                    break
                time.sleep(1)

    @task
    def stop(self):
        print("finish",self.check_checkout,self.shipping_status)
        self.user.environment.reached_end = True
        self.user.environment.runner.quit()


class MyLoadTest(HttpUser):
    host = "http://itdoesnt-matter.xyz"
    tasks = [MySeqTask]
    wait_time = between(0.5, 1)