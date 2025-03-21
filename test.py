from flask import Flask, jsonify, request
from flask_cors import CORS

import json
from threading import Thread
import time

app = Flask(__name__)
CORS(app=app)

@app.route('/task_chain',methods=['POST'])
def send_task_chain():
    try:
        content = request.json
        if len(APR_Status['task_chain']) == 0:
            APR_Status['task_chain'] = content['task_chain']
            return jsonify({"result":True}),201
        return jsonify({"result":False}),200
    except Exception as e:
        return jsonify({"error":str(e)}),500
    
@app.route('/status',methods = ['GET'])
def status():
    return jsonify(APR_Status),200

def task_chain_excution_func():
    while True:
        if len(APR_Status["task_chain"]):
            task_chain = APR_Status['task_chain']
            for task in task_chain:
                if task['task_name'] == 'navigation_block':
                    print('APR move to ',task['target_point'])
                    time.sleep(10)
                
                if task['task_name'] == 'navigation_non_block':
                    print('APR move to ',task['target_point'])
                    time.sleep(2)

                if task['task_name'] == 'pick':
                    print('APR pick magazine.')
                    time.sleep(2)

                if task['task_name'] == 'put':
                    print('APR put magazine.')
                    time.sleep(2)
            
            APR_Status['task_chain'] = []
        print('------------------------------')
        time.sleep(2)


if __name__ == '__main__':
    APR_Status = {
        "src_status":[],
        "task_chain":[],
        "cancel_signal":False,
        "pause_signal":False,
        "mission_status":0
    }
    

    task_chain_excution = Thread(target=task_chain_excution_func,args=())
    task_chain_excution.start()

    app.run(host='0.0.0.0',port=8001,debug=False)