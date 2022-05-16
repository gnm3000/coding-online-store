import pika
from datetime import datetime
import json
from bson import ObjectId
import requests
import pymongo
from dotenv import load_dotenv
import os
load_dotenv()
MONGODB_URL = os.getenv('MONGODB_URL')
client = pymongo.MongoClient(MONGODB_URL)


class FailedOrdersProcessor:

    def process(self, msg):
        msg = json.loads(msg)
        cart_id = msg["cart_id"]
        print("cart_id", cart_id)
        # request get cart_id

        response = requests.get(
            "http://localhost:8000/sales/checkout-status",
            params={
                "cart_id": cart_id}).json()
        print(response)
        cart = response["cart"]

        order = {"customer_id": cart["customer_id"], "products": cart["products"], "cart_id": cart['_id'], "status": "failed",
                 "status_history": [], "created_at": datetime.utcnow().isoformat()}
        db = client["customers"]
        data = {'$push': {"failed_orders": order}}

        db["customers"].update_one(
            {'_id': ObjectId(cart["customer_id"])}, data)
        print("updated")
        pass


credentials = pika.PlainCredentials('guest', 'guest')
parameters = pika.ConnectionParameters('192.168.49.2',
                                       30064,
                                       '/',
                                       credentials)
connection = pika.BlockingConnection(parameters)

channel = connection.channel()

channel.queue_declare(queue='failed_orders', durable=True)
processor = FailedOrdersProcessor()


def callback(ch, method, properties, body):
    data = body.decode()
    print(" [x] Received %r" % body.decode())
    processor.process(data)

    print(" [x] Done")
    ch.basic_ack(delivery_tag=method.delivery_tag)


channel.basic_qos(prefetch_count=1)

channel.basic_consume(queue='failed_orders', on_message_callback=callback)

print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()
