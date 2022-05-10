MONGODB_URL = "mongodb://adminuser:password123@mongo-nodeport-svc.default.svc.cluster.local/?retryWrites=true&w=majority"  # prod
MONGODB_URL = "mongodb://adminuser:password123@192.168.49.2:32258/?retryWrites=true&w=majority"  # local

from types import coroutine
import motor.motor_asyncio
client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URL)
db = client.shipping


"""

async def process_orders():
    
    # BACKGROUND PROCESS: this process need to scale
    result = db["orders"].find()
    response = await result.to_list(None)
    print(result)
    # 1. set max processing_date by delivery_date
    # 2. change each status with 10ms and 50ms in between until status=Delivered
    # 3. Notify to customer: (order_id, status_from, status_to, datetime)
    pass
import asyncio
if __name__ == "__main__":
    asyncio.create_task(process_orders())
"""
import random
import asyncio

async def get_data(status):
    return await db["orders"].find({"status":status}).to_list(None)

async def check_orders(status):
    order_status = ["ordered","sent_to_warehouse", "packaged", "carrier_picked_up", "out_for_delivery", "delivered"]
    while True:
        orders = await get_data(status)
        print("orders %s" % status,orders)
        # 1. for each order 
        await asyncio.sleep(random.randint(1,3))

def loop_in_thread(loop):
    asyncio.set_event_loop(loop)
    order_status = ["ordered","sent_to_warehouse", "packaged", "carrier_picked_up", "out_for_delivery", "delivered"]
    coroutines = [check_orders(status) for status in order_status]
    loop.run_until_complete(asyncio.gather(*coroutines))
    
    

loop = asyncio.get_event_loop()
import threading

t = threading.Thread(target=loop_in_thread, args=(loop,))
t.start()
