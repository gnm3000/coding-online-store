import requests
from concurrent.futures import ThreadPoolExecutor,wait
import random
import time
# the customer see the catalog store
def customer_scenario(customer):
    req = requests.get("http://localhost:8000/sales/products")
    catalog=req.json()
    def get_random_products(quantity):
        random.shuffle(catalog)
        return catalog[:quantity]
        

    # the customer add a product to the cart

    for product in get_random_products(random.randint(1,3)):
        req = requests.post("http://localhost:8000/sales/cart",params={"product_id":product['_id'],
                                                                        "customer_id":customer['_id'],
                                                                        "name":product['name'],
                                                                        "price":product['price'],
                                                                        "quantity":random.randint(1,2),
                                                                        "delivery_date":product["delivery_date"]})

    cart=req.json()
    print("cart",cart)
    time.sleep(0.5)
    # the customer checkout and get the order in 
    req = requests.post("http://localhost:8000/sales/checkout",params={"customer_id":customer['_id']})
    checkout=req.json()
    print(checkout)
    
    while True:
        time.sleep(0.5)
        req = requests.get("http://localhost:8000/sales/checkout-status",params={"cart_id":cart['cart_id']})
        time.sleep(1)
        checkout_status=req.json()
        if("failed" in checkout_status["status"]):
            print("failed",checkout_status["status"])
            break
        if("success" in checkout_status["status"]):
            print("here ask to shipping by cart_id until this is delivered")
            req = requests.get("http://localhost:5679/shipping/orders",params={"cart_id":cart['cart_id']})
            print("Shipping_order")
            print(req.json())
            if(req.json()[0]["status"]=="delivered"):
                print("DELIVERED!!","end")
                break

if __name__ == "__main__":
    # here I get all the customers
    req = requests.get("http://localhost:5678/customers")
    customers = req.json()
    WORKERS = 10

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



