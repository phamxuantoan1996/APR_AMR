from flask import Flask, jsonify, request
from flask_cors import CORS

import json
from threading import Thread
import time

from mongDB import MongoDataBase
from control import ESA_API

app = Flask(__name__)
CORS(app=app)

def src_init() -> bool:
    check_init = True
    print('info:','connecting to src')
    if Robot.connect_status():
        print("info:","src status connected")
    else:
        check_init = False
        print("error:","src status connect error")
    if Robot.connect_navigation():
        print("info:","src naviagtion connected")
    else:
        check_init = False
        print("error:","src navigation connect error")
    if Robot.connect_other():
        print("info:","src other connected")
    else:
        check_init = False
        print("error:","src other connect error")
    if Robot.connect_control():
        print("info:","src control connected")
    else:
        check_init = False
        print("error:","src control connect error")
    if Robot.connect_config():
        print("info:","src config connected")
    else:
        check_init = False
        print("error:","src config connect error")
    time.sleep(2)
    if check_init:
        print('info:','src relocating')

        while True:
            try:
                Robot.status(Robot.keys)
                print(Robot.data_Status['reloc_status'])
                if Robot.data_Status['reloc_status'] == 0:#failed
                    print('a')
                    time.sleep(1)
                elif Robot.data_Status['reloc_status'] == 1:#successed
                    print('b')
                    break
                elif Robot.data_Status['reloc_status'] == 2:#relocating
                    print('c')
                    time.sleep(1)
                elif Robot.data_Status['reloc_status'] == 3:#complete
                    print('d')
                    Robot.confim_location()
                    time.sleep(2)
            except Exception as e:
                check_init = False
                print('error:','relocation error')
                break
    return check_init
    
@app.route('/status',methods = ['GET'])
def status():
    return jsonify(Robot.data_Status),200

def task_src_status_poll_func():
    while True:
        Robot.status(Robot.keys)
        db.MongoDB_update(collection_name="APR_Status",query={"_id":1},data={"src_status":Robot.data_Status})
        time.sleep(0.5)

def task_chain_excution_func():
    while True:
        status = db.MongoDB_find(collection_name="APR_Status",query={"_id":1})[0]
        apr_task_chain = status['task_chain']
        apr_task_chain_status = status['task_chain_status']
        if len(apr_task_chain) > 0 and apr_task_chain_status == 0:
            db.MongoDB_update(collection_name='APR_Status',query={'_id':1},data={'task_chain_status':2})
            for task in apr_task_chain:
                if task['task_name'] == 'navigation_block':
                    print('APR move to ',task['target_point'])
                    Robot.navigation({"id":task['target_point']})
                    while True:
                        if Robot.check_target(Robot.data_Status,target=task['target_point']):
                            break
                
                if task['task_name'] == 'navigation_non_block':
                    print('APR move to ',task['target_point'])
                    Robot.navigation({"id":task['target_point']})
                    time.sleep(2)

                if task['task_name'] == 'pick':
                    print('APR pick magazine.')
                    time.sleep(2)

                if task['task_name'] == 'put':
                    print('APR put magazine.')
                    time.sleep(2)
            
            db.MongoDB_update(collection_name='APR_Status',query={'_id':1},data={'task_chain_status':10})
        print('------------------------------')
        time.sleep(2)




if __name__ == '__main__':
    
    db = MongoDataBase(database_name="APR_DB",collections_name=["APR_Status","Call_Machine"])
    if db.MongoDB_Init():
        print('MongoDB init success')
    else:
        print('MongoDB init fail')

    Robot = ESA_API(host="192.168.192.5")
    src_init()

    task_src_status_poll = Thread(target=task_src_status_poll_func,args=())
    task_src_status_poll.start()
    

    task_chain_excution = Thread(target=task_chain_excution_func,args=())
    task_chain_excution.start()


    app.run(host='0.0.0.0',port=8001,debug=False)