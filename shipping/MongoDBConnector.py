
from datetime import datetime, timedelta
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
    def get_one(self,collection,_id:str):
        raise NotImplementedError
    def update_one(self,collection,condition,data:dict):
        raise NotImplementedError
    


class FakeMongoDBConnector(DBConnector):
    def __init__(self,db_conn):
        self.db_conn = db_conn
    def insert_one(self,collection,data):
        print("Data inserted",data)
        inserted_id=str(ObjectId())
        return inserted_id
        

    def get_one(self,collection,_id:str):
        print("get_one",id)
        if(collection=="orders"):
            return {"_id":_id,"delivery_date":(datetime.utcnow()+timedelta(days=5)).isoformat(),"status_history":[{"created_at":(datetime.utcnow()+timedelta(days=2)).isoformat()}]}

    def update_one(self,collection,condition,data):
        print("updated",collection)
        
class MongoDBConnector(DBConnector):
    def __init__(self,db_conn):
        self.db_conn = db_conn
    def insert_one(self,collection,data):
        r= self.db_conn[collection].insert_one(data)
        return r.inserted_id
    def get_one(self,collection,_id:str):
        return self.db_conn[collection].find_one({'_id': ObjectId(_id)})

    def update_one(self,collection,condition,data):
        return self.db_conn[collection].update_one(condition,data)