
import os
from dotenv import load_dotenv
import pika,json,requests
from datetime import datetime
from MongoDBConnector import MongoDBConnector,DBConnector

from abc import ABC, abstractmethod
from datetime import timedelta
import time
import random
from bson.objectid import ObjectId

load_dotenv()
MONGODB_URL = os.getenv('MONGODB_URL')

BASEURL_SALES_SERVICE = os.getenv('BASEURL_SALES_SERVICE','http://localhost:8000')
BASEURL_CUSTOMER_SERVICE = os.getenv('BASEURL_CUSTOMER_SERVICE','http://localhost:5678')
class AbstractNotifier(ABC):
    @abstractmethod
    def __init__(self,channel):
        raise NotImplementedError
    
    def send_to_queue(self,queue,data_json:dict):
        raise NotImplementedError


class Notifier(AbstractNotifier):
    def __init__(self,channel):
        self.channel = channel
    
    def send_to_queue(self,queue,data_json):
        self.channel.basic_publish(
                    exchange='',
                    routing_key=queue,
                    body=json.dumps(data_json),
                    properties=pika.BasicProperties(
                        delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
                    ))
class FakeNotifier(AbstractNotifier):
    def __init__(self,channel):
        self.channel = channel
    
    def send_to_queue(self,queue,data_json):
        print("Fake Notify ",queue,data_json)


class AbstractCart(ABC):
    @abstractmethod
    def __init__(self,cart_id:str) -> None:
        super().__init__()
    
    @abstractmethod
    def requestCart(self):
        raise NotImplementedError
    
class FakeCart(AbstractCart):
    def __init__(self,cart_id:str):
        self.cart_id = cart_id
        
    def requestCart(self):
        
        return {"products":[{"id":"xxx","name":"T-Shirt","price":200,"quantity":1,"delivery_date":2}],"_id":"xxxx","customer_id":"yyy"}
class Cart(AbstractCart):
    def __init__(self,cart_id:str):
        self.cart_id = cart_id
        
    def requestCart(self):
        req = requests.get(BASEURL_SALES_SERVICE+"/sales/checkout-status",params={"cart_id":self.cart_id})
        return req.json()["cart"]

class ShippingProcessor:

    def __init__(self,channel,notifier:AbstractNotifier,db: DBConnector):
        self.channel = channel
        self.notifier = notifier
        self.db = db
    def calculate_dates(self,start:str,end:str) -> datetime:
        start_datetime = datetime.fromisoformat(start)
        end_datetime = datetime.fromisoformat(end)
        minutes_diff=int((end_datetime-start_datetime).total_seconds()/60)
        print("minutes_diff",minutes_diff)
        minutes= random.randint(60,(int(minutes_diff*0.3)))
        # in each stage we can take since 1 hour to the 30% the time of delivery date 
        return (start_datetime+timedelta(minutes=minutes))
    
    def process_sucess_checkout(self,data:dict,cart: AbstractCart):
        print("Shipping processor process_sucess_checkout wait 10ms")
        cart = cart.requestCart()
        
        max_delivery_date_days=max([p["delivery_date"] for p in cart["products"]])
        today= datetime.utcnow()    
        delivery_date = today+timedelta(days=max_delivery_date_days)
        status={"status": "ordered","created_at":datetime.utcnow().isoformat()}
        order = {"customer_id":cart["customer_id"], "products": cart["products"], "cart_id":cart['_id'],"status":"ordered",
                    "status_history":[status],"delivery_date":delivery_date.isoformat()}
        # 1. create order
        order_inserted_id=self.db.insert_one("orders",order)
        #2. notificar a customer queue="order_notifications" {order_id: xxx, change_from:checkout, to: ordered, status: ordered, date: 22:11:03}
        
        self.notifier.send_to_queue(queue="notification_orders",data_json={"order_id":str(order_inserted_id),"customer_id":cart["customer_id"],"status":status})
        self.notifier.send_to_queue(queue="ordered_orders",data_json={"order_id":str(order_inserted_id)})
        
        # time processing orders: 1 to 5 days
        # get delivery_date from cart
        time.sleep(random.randint(10,50)/1000)
        return {"order_id":str(order_inserted_id),"status":status["status"]}
    def process_ordered_orders(self,data:dict):
        print("Shipping processor process_ordered_orders wait 10ms")
        
        order=self.db.get_one(collection="orders",_id=data["order_id"])
        max_date_str=order["delivery_date"]
        last_date_str=order["status_history"][-1]["created_at"]
        new_date = self.calculate_dates(last_date_str,max_date_str)
        
        status={"status": "sent_to_warehouse","created_at":new_date.isoformat()}
        self.db.update_one(collection="orders",condition={"_id":ObjectId(data["order_id"])},
                                    data={'$set':{'status':status["status"]},'$push': {'status_history': status}})
        #db["orders"].update_one({"_id":ObjectId(data["order_id"])},{'$set':{'status':status["status"]},'$push': {'status_history': status}})
        time.sleep(random.randint(10,50)/1000)
        self.notifier.send_to_queue(queue="sent_to_warehouse_orders",data_json={"order_id":data["order_id"]})
        return {"order_id":str(data["order_id"]),"status":status["status"]}
    def process_warehouse_orders(self,data:dict):
        print("Shipping processor  process_warehouse_orders wait 10ms")
        
        order=self.db.get_one(collection="orders",_id=data["order_id"])
        max_date_str=order["delivery_date"]
        last_date_str=order["status_history"][-1]["created_at"]
        new_date = self.calculate_dates(last_date_str,max_date_str)
        #order=db["orders"].find_one({'_id': ObjectId(data["order_id"])})
        status={"status": "packaged","created_at":new_date.isoformat()}
        #db["orders"].update_one({"_id":ObjectId(data["order_id"])},{'$set':{'status':status["status"]},'$push': {'status_history': status}})
        self.db.update_one(collection="orders",condition={"_id":ObjectId(data["order_id"])},
                                    data={'$set':{'status':status["status"]},'$push': {'status_history': status}})
        time.sleep(random.randint(10,50)/1000)
        self.notifier.send_to_queue(queue="packaged_orders",data_json={"order_id":data["order_id"]})
        return {"order_id":str(data["order_id"]),"status":status["status"]}
    def process_packaged_orders(self,data:dict):
        print("Shipping processor process_packaged_orders wait 10ms")
        #order=db["orders"].find_one({'_id': ObjectId(data["order_id"])})

        order=self.db.get_one(collection="orders",_id=data["order_id"])
        max_date_str=order["delivery_date"]
        last_date_str=order["status_history"][-1]["created_at"]
        new_date = self.calculate_dates(last_date_str,max_date_str)
        status={"status": "carrier_picked_up","created_at":new_date.isoformat()}
        #db["orders"].update_one({"_id":ObjectId(data["order_id"])},{'$set':{'status':status["status"]},'$push': {'status_history': status}})
        self.db.update_one(collection="orders",condition={"_id":ObjectId(data["order_id"])},
                                    data={'$set':{'status':status["status"]},'$push': {'status_history': status}})
        time.sleep(random.randint(10,50)/1000)
        self.notifier.send_to_queue(queue="carrier_picked_up_orders",data_json={"order_id":data["order_id"]})
        return {"order_id":str(data["order_id"]),"status":status["status"]}
    def process_carrier_picked_up_orders(self,data:dict):
        print("Shipping processor process_carrier_picked_up_orders wait 10ms")
        #order=db["orders"].find_one({'_id': ObjectId(data["order_id"])})

        order=self.db.get_one(collection="orders",_id=data["order_id"])
        max_date_str=order["delivery_date"]
        last_date_str=order["status_history"][-1]["created_at"]
        new_date = self.calculate_dates(last_date_str,max_date_str)
        status={"status": "out_for_delivery","created_at":str(new_date.isoformat())}
        
        self.db.update_one(collection="orders",condition={"_id":ObjectId(data["order_id"])},
                                    data={'$set':{'status':status["status"]},'$push': {'status_history': status}})

        time.sleep(random.randint(10,50)/1000)
        self.notifier.send_to_queue(queue="out_for_delivery_orders",data_json={"order_id":data["order_id"]})

        return {"order_id":str(data["order_id"]),"status":status["status"]}
    def process_out_for_delivery_orders(self,data:dict):
        print("Shipping processor wait 10ms")
        #order=db["orders"].find_one({'_id': ObjectId(data["order_id"])})

        order=self.db.get_one(collection="orders",_id=data["order_id"])
        max_date_str=order["delivery_date"]
        status={"status": "delivered","created_at":max_date_str}
        self.db.update_one(collection="orders",condition={"_id":ObjectId(data["order_id"])},
                                    data={'$set':{'status':status["status"]},'$push': {'status_history': status}})
        time.sleep(random.randint(10,50)/1000)
        print("SET delivered. FINISHED")
        return {"order_id":str(data["order_id"]),"status":status["status"]}