
from bson.objectid import ObjectId
from abc import ABC, abstractmethod
from unittest import mock

class DBConnector(ABC):
    @abstractmethod
    def __init__(self,db_conn) -> None:
        self.db_conn
    
    @abstractmethod
    def insert_one(self,collection,data:dict):
        raise NotImplementedError
    def get_one(self,collection,condition:dict):
        raise NotImplementedError
    def update_one(self,collection,condition,data:dict):
        raise NotImplementedError
    


class FakeMongoDBConnector(DBConnector):
    def __init__(self,db_conn):
        self.db_conn = db_conn
    async def insert_one(self,collection,data):
        print("Data inserted",data)
        inserted_id=str(ObjectId())
        return inserted_id
        

    async def get_one(self,collection,condition:dict):
        print("get_one",id)
        return {"wallet_usd":100}

    async def update_one(self,collection,condition,data):
        print("updated",collection)
        customer = mock.Mock()
        customer.modified_count=1
        return customer
class MongoDBConnector(DBConnector):
    def __init__(self,db_conn):
        self.db_conn = db_conn
    async def insert_one(self,collection,data):
        r= await self.db_conn[collection].insert_one(data)
        return r.inserted_id
    
    async def get_one(self,collection,condition:dict):
        return await self.db_conn[collection].find_one(condition)

    async def update_one(self,collection,condition,data):
        return await self.db_conn[collection].update_one(condition,data)