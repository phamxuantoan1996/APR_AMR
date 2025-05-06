import pymongo
import datetime
class MongoDataBase:
    def __init__(self,database_name:str,collections_name:list) -> None:
        self.clientMongo = pymongo.MongoClient('mongodb://localhost:27017/')
        self.collectionsDB = {}
        self.database_name = database_name
        self.collections_name = collections_name

    def MongoDB_Init(self) -> bool:
        try:
            self.clientMongo.admin.command("ping")

            self.database = self.clientMongo[self.database_name]

            for name in self.collections_name:
                self.collectionsDB[name] = self.database[name]
            return True
        except Exception as e:
            print("MongoDB error : " + str(e))
        return False
    
    def MongoDB_insert(self,collection_name:str,data:dict) -> bool:
        try:
            self.collectionsDB[collection_name].insert_one(data)
            return True
        except Exception as e:
            print("MongoDB error : " + str(e))
            return False

    def MongoDB_detele(self,collection_name:str,data:dict) -> int:
        try:
            res = self.collectionsDB[collection_name].delete_many(data)
            return res.deleted_count
        except Exception as e:
            print("MongoDB error : " + str(e))
            return -1
        
    def MongoDB_find(self,collection_name:str,query:dict) -> list:
        try:
            return list(self.collectionsDB[collection_name].find(query))
        except Exception as e:
            print("MongoDB error : " + str(e))
            return []
    
    def MongoDB_update(self,collection_name:str,query:dict,data:dict) -> bool:
        update = { "$set": data}
        try:
            self.collectionsDB[collection_name].update_one(query,update)
            return True
        except Exception as e:
            print("MongoDB error : " + str(e))
            return False
        
# def writeLogDB(msg:str):
#     date_str = datetime.datetime.now().strftime("%d/%m/%Y")
#     time_str = datetime.datetime.now().strftime("%H:%M:%S")

#     content = {
#         "date" : date_str,
#         "time" : time_str,
#         "message" : msg
#     }
#     apr_db.MongoDB_insert(collection_name="Logfile",data=content)

# def readLogDB(date:str) -> list:
#     logs = apr_db.MongoDB_find(collection_name="Logfile",query={"date":date})
#     for i in range(0,len(logs)):
#         logs[i].pop("_id")
#     return logs

# if __name__ == '__main__':
#     apr_db = MongoDataBase(database_name="APR_DB",collections_name=["Logfile"])
#     apr_db.MongoDB_Init()
#     print(readLogDB(date="06/04/2025"))
