from mongDB import MongoDataBase
import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app=app)

def writeLogDB(msg:str):
    date_str = datetime.datetime.now().strftime("%d/%m/%Y")
    time_str = datetime.datetime.now().strftime("%H:%M:%S")

    content = {
        "date" : date_str,
        "time" : time_str,
        "message" : msg
    }
    db.MongoDB_insert(collection_name="Logfile",data=content)

def readLogDB(date:str) -> list:
    logs = db.MongoDB_find(collection_name="Logfile",query={"date":date})
    for i in range(0,len(logs)):
        logs[i].pop("_id")
    return logs

def deleteLogDB(date:str) -> int:
    num = db.MongoDB_detele(collection_name="Logfile",data={"date":date})
    return num

@app.route('/logs',methods = ['GET'])
def get_log():
    try:
        date = request.args.get("date")
        logs = readLogDB(date=date)
        return jsonify(logs),200
    except Exception as e:
        return jsonify({"error":str(e)}),500
@app.route('/logs',methods = ['DELETE'])
def delete_log():
    try:
        date = request.args.get("date")
        num = deleteLogDB(date=date)
        return jsonify({"result":num}),200
    except Exception as e:
        return jsonify({"error":str(e)}),500
    
if __name__ == '__main__':


    db = MongoDataBase(database_name="APR_DB",collections_name=["Logfile"])
    if db.MongoDB_Init():
        print('MongoDB init success')
    else:
        print('MongoDB init fail')


    app.run(host='0.0.0.0',port=8000,debug=False)
    
    

    
    

    