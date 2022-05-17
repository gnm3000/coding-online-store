import requests
from concurrent.futures import ThreadPoolExecutor,wait
import random
import time
# the customer see the catalog store
import os
BASE_URL_SALES = os.getenv('BASE_URL_SALES',"http://localhost:8000")
BASE_URL_CUSTOMERS = os.getenv('BASE_URL_CUSTOMERS',"http://localhost:5678")
BASE_URL_SHIPPING = os.getenv('BASE_URL_SHIPPING',"http://localhost:5679")

    
def customer_scenario(customer):
    req = requests.get(BASE_URL_SALES+"/sales/products")
    catalog=req.json()
    def get_random_products(quantity):
        ''' mix the catalog and return n products'''
        random.shuffle(catalog)
        return catalog[:quantity]
        

    # the following is the customer add some products to the cart

    for product in get_random_products(random.randint(1,3)):
        req = requests.post(BASE_URL_SALES+"/sales/cart",params={"product_id":product['_id'],
                                                                        "customer_id":customer['_id'],
                                                                        "name":product['name'],
                                                                        "price":product['price'],
                                                                        "quantity":random.randint(1,2),
                                                                        "delivery_date":product["delivery_date"]})

    cart=req.json()
    print("cart",cart)
    time.sleep(0.5)
    # the customer checkout the cart
    req = requests.post(BASE_URL_SALES+"/sales/checkout",params={"customer_id":customer['_id']})
    checkout=req.json()
    print(checkout)
    
    while True:
        time.sleep(0.5)
        ''' i'm waiting for my checkout processing. Here the system check if there are stock products 
        and if I have enough money'''
        req = requests.get(BASE_URL_SALES+"/sales/checkout-status",params={"cart_id":cart['cart_id']})
        time.sleep(1)
        checkout_status=req.json()
        if("failed" in checkout_status["status"]):
            ''' I dont have money or the store dont have stock'''
            print("failed",checkout_status["status"])
            break
        if("success" in checkout_status["status"]):
            ''' now I ask for my specific order, What is the status? if it have been delivered '''
            req = requests.get(BASE_URL_SHIPPING+"/shipping/orders",params={"cart_id":cart['cart_id']})
            print("my shipping_order",req.json()[0]["status"])
            if(req.json()[0]["status"]=="delivered"):
                print("DELIVERED order!")
                break

if __name__ == "__main__":
    # here I get all the customers
    req = requests.get(BASE_URL_CUSTOMERS+"/customers")
    customers = req.json()
    WORKERS = 10
    if(True):
        for customer in customers:
            customer_scenario(customer)
        print("finished")
        exit()
    future_list = []
    with ThreadPoolExecutor(WORKERS) as executor:
        for customer in customers:
            future = executor.submit(customer_scenario, customer)
            future_list.append(future)

    wait(future_list)
    print("all task complete")
    time.sleep(1)

    for future in future_list:
        try:
            print(future.result())
            pass
        except Exception as e:
            print(e)



