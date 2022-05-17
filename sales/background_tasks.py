#!/usr/bin/env python
import pprint
from dotenv import load_dotenv
import pymongo
from bson.objectid import ObjectId
import time
import re
import pika
import sys

import requests
import json
import os
load_dotenv()
MONGODB_URL = os.getenv('MONGODB_URL')

BASEURL_SALES_SERVICE = os.getenv('BASEURL_SALES_SERVICE','http://localhost:8000')
BASEURL_CUSTOMER_SERVICE = os.getenv('BASEURL_CUSTOMER_SERVICE','http://localhost:5678')

client = pymongo.MongoClient(MONGODB_URL)
db = client["sales"]
class MessageSender:

    @classmethod
    def send(cls, queue, message):
        # send to rabbit cart_queue
        credentials = pika.PlainCredentials(os.getenv('RABBITMQ_USER'), os.getenv('RABBITMQ_PASS'))
        parameters = pika.ConnectionParameters(os.getenv('RABBITMQ_SERVER'),
                                            int(os.getenv('RABBITMQ_PORT')),
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
        print(" [x] Sent %s %s" % (queue, message))
        connection.close()

        return "OK"


class SalesBackgroundTask:

    def processCart(self, cart_id: str):
        # send to rabbit cart_queue
        credentials = pika.PlainCredentials(os.getenv('RABBITMQ_USER'), os.getenv('RABBITMQ_PASS'))
        parameters = pika.ConnectionParameters(os.getenv('RABBITMQ_SERVER'),
                                            int(os.getenv('RABBITMQ_PORT')),
                                            '/',
                                            credentials)
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()

        channel.queue_declare(queue='sales_cart_queue', durable=True)

        message = {"cart_id": cart_id}
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




class MsgProcessor:

    def process(self, msg):
        msg = json.loads(msg)
        cart_id = msg["cart_id"]
        # request customer API
        # connect to mongo and read cart info

        req = requests.get(BASEURL_SALES_SERVICE+"/sales/products")
        catalog_products = req.json()
        print("catalog_products", catalog_products)
        # asyncio.get_event_loop().run_until_complete(run())

        req = requests.get(
            BASEURL_SALES_SERVICE+"/sales/checkout-status",
            params={
                "cart_id": cart_id})

        cart = req.json()
        products = cart["cart"]["products"]
        customer_id = cart["cart"]["customer_id"]
        req = requests.get(BASEURL_CUSTOMER_SERVICE+"/customers/%s" % customer_id)
        customer = req.json()
        wallet_usd = customer["wallet_usd"]
        print("WALLET USD", wallet_usd)

        purchase = 0
        order_failed = False
        # --- if  purchase > stock => NoStockError

        for product in products:
            product_info = requests.get(
                BASEURL_SALES_SERVICE+"/sales/product", {"id": product["product_id"]}).json()
            stock = product_info["quantity"]

            if(product["quantity"] > stock):
                condition = {
                    "customer_id": customer['_id'],
                    "status": "pending"}
                order_failed = True
                print("Error no stock")
                db["carts"].update_one({"_id": ObjectId(cart_id)}, {
                                       '$set': {"status": "failed_by_stock"}})

                break

            purchase = purchase + product["price"] * product["quantity"]
        if(order_failed):
            MessageSender.send("failed_orders", {"cart_id": cart_id})
            return
        # with customer object and cart object
        # process rabbit cart_queue
        # --- if  purchase > wallet => NoMoneyError
        if(purchase > wallet_usd):
            db["carts"].update_one({"_id": ObjectId(cart_id)}, {
                                   '$set': {"status": "failed_by_insufficient_funds"}})
            order_failed = True
            MessageSender.send("failed_orders", {"cart_id": cart_id})
            print("purchase", purchase)
            return
        # user_wallet = user_wallet - purchase
        #wallet_new_value = last_customer["wallet_usd"]- purchase
        # actualizar la wallet del cliente!!
        req = requests.post(BASEURL_CUSTOMER_SERVICE+"/customers/update-wallet", params={"cart_id": cart_id,
                                                                                     "purchase_usd": purchase,
                                                                                     "customer_id": customer['_id']})
        _ = req.json()
        db["carts"].update_one({"_id": ObjectId(cart_id)}, {
                               '$set': {"status": "success"}})
        MessageSender.send("success_orders", {"cart_id": cart_id})
        # if sucess=> create order and send to shipping microservice (using rabbitMQ)
        # if error => create fail order and send to customers microservice
        # (using rabbitMQ)
        print("processed", msg)


class SalesBackgroundTaskWorker:

    @classmethod
    def worker(cls):
        print(os.getenv('RABBITMQ_SERVER'),
                int(os.getenv('RABBITMQ_PORT')),
                os.getenv('RABBITMQ_USER'),
                os.getenv('RABBITMQ_PASS'))
        credentials = pika.PlainCredentials(os.getenv('RABBITMQ_USER'), os.getenv('RABBITMQ_PASS'))
        parameters = pika.ConnectionParameters(os.getenv('RABBITMQ_SERVER'),
                                       int(os.getenv('RABBITMQ_PORT')),
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

        channel.basic_consume(
            queue='sales_cart_queue',
            on_message_callback=callback)

        print(' [*] Waiting for messages. To exit press CTRL+C')
        channel.start_consuming()


if __name__ == "__main__":

    SalesBackgroundTaskWorker.worker()
