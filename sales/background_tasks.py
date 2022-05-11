#!/usr/bin/env python
import re
import pika
import sys

import requests
import json
class MessageSender:

    @classmethod
    def send(cls,queue,message):
        # send to rabbit cart_queue
        credentials = pika.PlainCredentials('guest', 'guest')
        parameters = pika.ConnectionParameters('192.168.49.2',
                                            30064,
                                            '/',
                                            credentials)
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()

        channel.queue_declare(queue=queue, durable=True)

        channel.basic_publish(
            exchange='',
            routing_key=queue,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            ))
        print(" [x] Sent %s %s" % (queue,message))
        connection.close()

        return "OK"

class SalesBackgroundTask:

    def processCart(self,cart):
        # send to rabbit cart_queue
        credentials = pika.PlainCredentials('guest', 'guest')
        parameters = pika.ConnectionParameters('192.168.49.2',
                                            30064,
                                            '/',
                                            credentials)
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()

        channel.queue_declare(queue='sales_cart_queue', durable=True)

        message = {"cart_id":str(cart['_id'])}
        channel.basic_publish(
            exchange='',
            routing_key='sales_cart_queue',
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            ))
        print(" [x] Sent %r" % message)
        connection.close()

        return "OK"

  
        
import time
import motor.motor_asyncio
from bson.objectid import ObjectId
MONGODB_URL = "mongodb://adminuser:password123@mongo-nodeport-svc.default.svc.cluster.local/?retryWrites=true&w=majority"  # prod
MONGODB_URL = "mongodb://adminuser:password123@192.168.49.2:32258/?retryWrites=true&w=majority"  # local
from background_tasks import SalesBackgroundTask
client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
db = client.sales
import asyncio
import pprint
async def set_order_as(condition,status):
    print("SET ORDER CONDITION=",condition,"AS STATUS=",status)
    r=await db["carts"].update_one(condition,{'$set':{"status":status}})
    print("modified_count",r.modified_count)
class MsgProcessor:

    def process(self,msg):
        msg = json.loads(msg)
        cart_id = msg["cart_id"]
        # request customer API
        # connect to mongo and read cart info
        req = requests.get("http://localhost:5678/customers")
        last_customer=(req.json()[-1])
        wallet_usd = last_customer["wallet_usd"]
        print("PREVIA WALLET",wallet_usd)
        req = requests.get("http://localhost:8000/sales/products")
        catalog_products=req.json()
        print("catalog_products",catalog_products)
        #asyncio.get_event_loop().run_until_complete(run())

        
        req = requests.get("http://localhost:8000/sales/checkout-status",params={"cart_id":cart_id})
        cart=req.json()
        products = cart["cart"]["products"]
        purchase=0
        order_failed=False
        # --- if  purchase > stock => NoStockError
        for product in products:
            product_info = requests.get("http://localhost:8000/sales/product",{"id":product["product_id"]}).json()
            stock=product_info["quantity"]
            if(product["quantity"] > stock):
                condition = {"customer_id": last_customer['_id'], "status": "pending"}
                order_failed=True
                print("Error no stock")
                loop = asyncio.get_event_loop()
                coroutine = set_order_as({"_id":ObjectId(cart_id)},"failed_by_stock")
                loop.run_until_complete(coroutine)
                loop.close()
                break

            purchase = purchase + product["price"]*product["quantity"]
        if(order_failed):
            MessageSender.send("failed_orders",{"cart_id":cart_id})
            return
        # with customer object and cart object
        # process rabbit cart_queue
        # --- if  purchase > wallet => NoMoneyError
        if(purchase>wallet_usd):
            condition = {"customer_id": last_customer['_id'], "status": "pending"}
            loop = asyncio.get_event_loop()
            coroutine = set_order_as({"_id":ObjectId(cart_id)},"failed_by_insufficient_funds")
            loop.run_until_complete(coroutine)
            loop.close()
            order_failed=True
            MessageSender.send("failed_orders",{"cart_id":cart_id})
            return
        # user_wallet = user_wallet - purchase
        wallet_new_value = last_customer["wallet_usd"]- purchase
        # actualizar la wallet del cliente!!
        req = requests.post("http://localhost:5678/customer/update-wallet",params={"wallet_usd":wallet_new_value,"customer_id":last_customer['_id']})
        _=req.json()
        condition = {"customer_id": last_customer['_id'], "status": "pending"}
        
        
        loop = asyncio.get_event_loop()
        coroutine = set_order_as({"_id":ObjectId(cart_id)},"success")
        loop.run_until_complete(coroutine)
        loop.close()
        MessageSender.send("success_orders",{"cart_id":cart_id})
        # if sucess=> create order and send to shipping microservice (using rabbitMQ)
        # if error => create fail order and send to customers microservice (using rabbitMQ)
        print("processed",msg)

class SalesBackgroundTaskWorker:

    @classmethod
    def worker(cls):
        credentials = pika.PlainCredentials('guest', 'guest')
        parameters = pika.ConnectionParameters('192.168.49.2',
                                            30064,
                                            '/',
                                            credentials)
        connection = pika.BlockingConnection(parameters)

        channel = connection.channel()

        channel.queue_declare(queue='sales_cart_queue', durable=True)
        msg_processor = MsgProcessor()
        def callback(ch, method, properties, body):
            data = body.decode()
            print(" [x] Received %r" % body.decode())
            msg_processor.process(data)
            
            print(" [x] Done")
            ch.basic_ack(delivery_tag=method.delivery_tag)
        channel.basic_qos(prefetch_count=1)

        channel.basic_consume(queue='sales_cart_queue', on_message_callback=callback)

        print(' [*] Waiting for messages. To exit press CTRL+C')
        channel.start_consuming()
if __name__=="__main__":

    SalesBackgroundTaskWorker.worker()