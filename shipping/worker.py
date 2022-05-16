
#!/usr/bin/env python



from dotenv import load_dotenv


load_dotenv()
MONGODB_URL = os.getenv('MONGODB_URL')

from datetime import datetime
from gc import collect

from bson.objectid import ObjectId
from MongoDBConnector import MongoDBConnector
from shipping_processor import ShippingProcessor,Cart,Notifier
import pymongo
client = pymongo.MongoClient(MONGODB_URL)
db = client["shipping"]
import requests
import pika, sys, os,time,json,random

def main():

    credentials = pika.PlainCredentials(os.getenv('RABBITMQ_USER'), os.getenv('RABBITMQ_PASS'))
    parameters = pika.ConnectionParameters(os.getenv('RABBITMQ_SERVER'),
                                       os.getenv('RABBITMQ_PORT'),
                                       '/',
                                       credentials)
    connection = pika.BlockingConnection(parameters)

    channel = connection.channel()

    channel.queue_declare(queue='success_orders', durable=True)
    channel.queue_declare(queue='ordered_orders', durable=True)
    channel.queue_declare(queue='sent_to_warehouse_orders', durable=True)
    channel.queue_declare(queue='packaged_orders', durable=True)
    channel.queue_declare(queue='carrier_picked_up_orders', durable=True)
    channel.queue_declare(queue='out_for_delivery_orders', durable=True)
    
    shipping_processor = ShippingProcessor(channel,notifier=Notifier(channel=channel),
                                                    db=MongoDBConnector(db_conn=client["shipping"]))
    def callback_success_orders(ch, method, properties, body):
        msg = json.loads(body.decode())
        # here we create the official order_entity
        shipping_processor.process_sucess_checkout(data=msg,
                                                    cart=Cart(cart_id=msg["cart_id"])
                                                    )
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    
    def callback_ordered_orders(ch, method, properties, body):
        msg = json.loads(body.decode())
        print(" [x] Received",msg)
        shipping_processor.process_ordered_orders(msg)
        # send to ordered.
        print(" [x] Done")
        ch.basic_ack(delivery_tag=method.delivery_tag)
    def callback_sent_to_warehouse_orders(ch, method, properties, body):
        msg = json.loads(body.decode())
        print(" [x] Received",msg)
        shipping_processor.process_warehouse_orders(msg)
        print(" [x] Done")
        ch.basic_ack(delivery_tag=method.delivery_tag)
    def callback_packaged_orders(ch, method, properties, body):
        msg = json.loads(body.decode())
        print(" [x] Received",msg)
        shipping_processor.process_packaged_orders(msg)
        print(" [x] Done")
        ch.basic_ack(delivery_tag=method.delivery_tag)
    def callback_carrier_picked_up_orders(ch, method, properties, body):
        msg = json.loads(body.decode())
        print(" [x] Received",msg)
        shipping_processor.process_carrier_picked_up_orders(msg)
        print(" [x] Done")
        ch.basic_ack(delivery_tag=method.delivery_tag)
    def callback_out_for_delivery_orders(ch, method, properties, body):
        msg = json.loads(body.decode())
        print(" [x] Received",msg)
        shipping_processor.process_out_for_delivery_orders(msg)
        print(" [x] Done")
        ch.basic_ack(delivery_tag=method.delivery_tag)
    
    #order_status = ["ordered","sent_to_warehouse", "packaged", "carrier_picked_up", "out_for_delivery", "delivered"]
    channel.basic_qos(prefetch_count=1)

    channel.basic_consume(queue='success_orders', on_message_callback=callback_success_orders)
    channel.basic_consume(queue='ordered_orders', on_message_callback=callback_ordered_orders)
    channel.basic_consume(queue='sent_to_warehouse_orders', on_message_callback=callback_sent_to_warehouse_orders)
    channel.basic_consume(queue='packaged_orders', on_message_callback=callback_packaged_orders)
    channel.basic_consume(queue='carrier_picked_up_orders', on_message_callback=callback_carrier_picked_up_orders)
    channel.basic_consume(queue='out_for_delivery_orders', on_message_callback=callback_out_for_delivery_orders)
    
    

    #shipping_processor.send_message()
    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)