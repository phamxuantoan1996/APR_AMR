from flask import Flask, jsonify, request
from flask_cors import CORS

import json
from threading import Thread
import time

from mongDB import MongoDataBase
from control import ESA_API

from amr_control_board import AMR_Control_Board,APR_Transfer

import datetime

apr_status = {}

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
    
def writeLogDB(msg:str):
    date_str = datetime.datetime.now().strftime("%Y/%m/%d")
    time_str = datetime.datetime.now().strftime("%H:%M:%S")
    content = {
        "date" : date_str,
        "time" : time_str,
        "message" : msg
    }
    db.MongoDB_insert(collection_name="Logfile",data=content)

def writeMissionDB(line:int,type:int,time_start_str:str):
    date_str = datetime.datetime.now().strftime("%Y/%m/%d")
    time_end_str = datetime.datetime.now().strftime("%H:%M:%S")
    content = {
        "date" : date_str,
        "time_start" : time_start_str,
        "time_end" : time_end_str,
        "line" : line,
        "type" : type
    }
    
    db.MongoDB_insert(collection_name="Logfile",data=content)

@app.route('/navigation',methods = ['POST'])
def apr_navigation():
    try:
        content = request.json
        if 'id' in content.keys():
            Robot.navigation({"id":content['id']})
            return jsonify({"result":True}),201
        return jsonify({"result":False}),200
    except Exception as e:
        return jsonify({"error":str(e)}),500

# {"lift":500}
@app.route('/lift',methods = ['POST'])
def lift():
    try:
        content = request.json
        val = int(content["lift"])
        if val <= 900 and val >= 0:
            control_board.SetLift(lift=val)
            return jsonify({"result":True}),201
        return jsonify({"result":False}),400
    except Exception as e:
        return jsonify({"result":False,"error":str(e)}),500
    
# {"convoyer":"stop","cw","ccw"}
@app.route('/conveyor',methods = ['POST'])
def convoyer():
    try:
        content = request.json
        if content["conveyor"] == 'cw':
            control_board.Conv_Manual_CW()
            return jsonify({"result":True}),201
        elif content["conveyor"] == 'ccw':
            control_board.Conv_Manual_CCW()
            return jsonify({"result":True}),201
        elif content["conveyor"] == 'stop':
            control_board.Conv_Manual_Stop()
            return jsonify({"result":True}),201
        return jsonify({"result":False}),400
    except Exception as e:
        return jsonify({"result":False,"error":str(e)}),500

# {"stopper":"up","down"}
@app.route('/stopper',methods = ['POST'])
def stopper():
    try:
        content = request.json
        if content["stopper"] == "up":
            control_board.Stopper_Manual_Up()
            return jsonify({"result":True}),201
        elif content["stopper"] == "down":
            control_board.Stopper_Manual_Down()
            return jsonify({"result":True}),201
        return jsonify({"result":False}),400
    except Exception as e:
        return jsonify({"result":False,"error":str(e)}),500


def task_src_status_poll_func():
    global apr_status
    while True:
        Robot.status(Robot.keys)
        db.MongoDB_update(collection_name="APR_Status",query={"_id":1},data={"src_status":Robot.data_Status})
        time.sleep(0.2)
        apr_status = db.MongoDB_find(collection_name="APR_Status",query={"_id":1})[0]

def task_chain_excution_func():
    while True:
        try:
            mode = apr_status["work_mode"]
            apr_task_chain = apr_status['task_chain']
            apr_task_chain_status = apr_status['task_chain_status']
            if len(apr_task_chain) > 0 and apr_task_chain_status == 0:
                time_start_str = datetime.datetime.now().strftime("%H:%M:%S")
                mission_success = True
                task_index = 0
                db.MongoDB_update(collection_name='APR_Status',query={'_id':1},data={'task_chain_status':2,"task_index":0})
                is_magazine = True
                for task in apr_task_chain:
                    if task['task_name'] == 'navigation_block':
                        print('APR move to ',task['target_point'])
                        writeLogDB("AMR di chuyen den diem : " + task["target_point"])
                        Robot.navigation({"id":task['target_point']})
                        while True:
                            if Robot.check_target(Robot.data_Status,target=task['target_point']):
                                task_index = task_index + 1
                                break 
                            print("signal cancel : ",apr_status["signal_cancel"])
                            if apr_status["signal_cancel"] == 1:
                                    mission_success = False
                                    break
                            time.sleep(1)  
                    if apr_status["signal_cancel"] == 1:
                        break
                    if task['task_name'] == 'navigation_non_block':
                        print('APR move to ',task['target_point'])
                        writeLogDB("AMR di chuyen den diem : " + task["target_point"])
                        Robot.navigation({"id":task['target_point']})
                        time.sleep(10)
                    if task['task_name'] == 'pick':
                        call_machine = db.MongoDB_find(collection_name="Call_Machine",query={"_id":task["line"]})[0]
                        if call_machine["floor2"] == 1 and not is_magazine:
                            print("AMR pick magazine")
                            writeLogDB("AMR lay magazine : " + "lift = " + str(task["level_lift"]))
                            # control lift
                            while not control_board.SetLift(task["level_lift"]):
                                time.sleep(1)
                            while True:
                                inputs = control_board.get_input_reg()
                                if len(inputs) > 0:
                                    if inputs[1] == task["level_lift"]:
                                        break
                                time.sleep(1)
                            # send cmd to loader rotate
                            id_line = task["line"]
                            if id_line in [1,2,3,4,5,6,7]:
                                db.MongoDB_update(collection_name="Call_Machine",query={"_id":task["line"]},data={"request_transfer":[0,1,0,0]})
                            # control convoyer
                            while not control_board.SetTransfer(APR_Transfer.Pick_From_Left):
                                time.sleep(1)
                            while True:
                                inputs = control_board.get_input_reg()
                                if len(inputs) > 0:
                                    if inputs[2] == APR_Transfer.Pick_From_Left:
                                        break
                                time.sleep(1)
                            time.sleep(2)
                            # send cmd to floor1 loader stop
                            while not control_board.SetTransfer(APR_Transfer.Stop):
                                break
                            id_line = task["line"]
                            if id_line in [1,2,3,4,5,6,7]:
                                db.MongoDB_update(collection_name="Call_Machine",query={"_id":task["line"]},data={"request_transfer":[0,0,0,0]})
                            # control lift
                            while not control_board.SetLift(100):
                                time.sleep(1)
                            while True:
                                inputs = control_board.get_input_reg()
                                if len(inputs) > 0:
                                    if inputs[1] == 100:
                                        break
                                time.sleep(1)
                            time.sleep(2)
                            # 
                            writeLogDB("AMR lay xong magazine")
                        else:
                            mission_success = False
                        task_index = task_index + 1
                    if task['task_name'] == 'put':
                        call_machine = db.MongoDB_find(collection_name="Call_Machine",query={"_id":task["line"]})[0]
                        # send cmd to loader rotate
                        id_line = task["line"]
                        if id_line in [1,2,3,4,5,6,7]:
                            if db.MongoDB_update(collection_name="Call_Machine",query={"_id":task["line"]},data={"request_transfer":[0,0,1,0]}):
                                print("convoyer rotate ok")
                        time.sleep(8)
                        call_machine = db.MongoDB_find(collection_name="Call_Machine",query={"_id":task["line"]})[0]
                        if call_machine["floor1"] == 1:
                            print('APR put magazine.')
                            writeLogDB("AMR tra magazine : " + "lift = " + str(task["level_lift"]))
                            # control lift
                            while not control_board.SetLift(task["level_lift"]):
                                time.sleep(1)
                            while True:
                                inputs = control_board.get_input_reg()
                                if len(inputs) > 0:
                                    if inputs[1] == task["level_lift"]:
                                        break
                                time.sleep(1)
                            time.sleep(1)
                            # control convoyer
                            while not control_board.SetTransfer(APR_Transfer.Put_To_Left):
                                time.sleep(1)
                            if id_line in [1,2,3,4,5,6,7]:
                                while True:
                                    call_machine = db.MongoDB_find(collection_name="Call_Machine",query={"_id":id_line})[0]
                                    if call_machine['floor1'] == 0:
                                        break
                                    time.sleep(1)

                            while not control_board.SetTransfer(APR_Transfer.Stop):
                                time.sleep(1)
                            while True:
                                inputs = control_board.get_input_reg()
                                if len(inputs) > 0:
                                    if inputs[2] == APR_Transfer.Stop:
                                        break
                                time.sleep(1)
                            time.sleep(2)
                            # send cmd to loader stop
                            id_line = task["line"]
                            if id_line in [1,2,3,4,5,6,7]:
                                db.MongoDB_update(collection_name="Call_Machine",query={"_id":task["line"]},data={"request_transfer":[0,0,0,0]})
                            # control lift
                            while not control_board.SetLift(100):
                                time.sleep(1)
                            while True:
                                inputs = control_board.get_input_reg()
                                if len(inputs) > 0:
                                    if inputs[1] == 100:
                                        break
                                time.sleep(1)
                            time.sleep(2)
                            is_magazine = False
                            writeLogDB("AMR tra xong magazine")
                        else:
                            # send cmd stop loader
                            id_line = task["line"]
                            if id_line in [1,2,3,4,5,6,7]:
                                if db.MongoDB_update(collection_name="Call_Machine",query={"_id":task["line"]},data={"request_transfer":[0,0,0,0]}):
                                    print("stop convoyer ok")
                            mission_success = False
                        task_index = task_index + 1
                    db.MongoDB_update(collection_name='APR_Status',query={'_id':1},data={"task_index":task_index})
                if mission_success:
                    writeMissionDB(line=apr_task_chain[0]["line"],type=1,time_start_str=time_start_str)
                else:
                    writeMissionDB(line=apr_task_chain[0]["line"],type=0,time_start_str=time_start_str)
                if apr_status["signal_cancel"] == 1:
                    # writeMissionDB(line=apr_task_chain[0]["line"],type=0)
                    if mode == "Auto":
                        db.MongoDB_detele(collection_name="APR_Missions",data={"_id":apr_status["mission_recv"]["_id"]})
                    db.MongoDB_update(collection_name='APR_Status',query={'_id':1},data={'task_chain_status':20,'mission_recv':{},"task_index":0,"task_chain":[],"work_mode":"Manual"})
                    Robot.cancel_navigation()
                else:
                    # writeMissionDB(line=apr_task_chain[0]["line"],type=1)
                    if mode == "Auto":
                        db.MongoDB_detele(collection_name="APR_Missions",data={"_id":apr_status["mission_recv"]["_id"]})
                    db.MongoDB_update(collection_name='APR_Status',query={'_id':1},data={'task_chain_status':10,'mission_recv':{},"task_index":None,"task_chain":[]})

                    
                db.MongoDB_update(collection_name="APR_Status",query={'_id':1},data={"signal_cancel":0})
            print('------------------------------')
            time.sleep(2)
        except Exception as e:
            print('task_execution_task fail : ',str(e))
            time.sleep(4)

def task_control_led_sound_func():
    led_cur = 0
    while True:
        # control_led
        try:
            
            if Robot.data_Status['emergency']:
                if led_cur != 9:
                    led_cur = 9
                    control_board.SetLed(9)
            elif Robot.data_Status['blocked']:
                if led_cur != 8:
                    led_cur = 8
                    control_board.SetLed(8)
            elif apr_status["task_chain"] == []:
                if led_cur != 10:
                    led_cur = 10
                    control_board.SetLed(10)
            elif apr_status["task_chain"] != []:
                if led_cur != 2:
                    led_cur = 2
                    control_board.SetLed(2)
            sensor = control_board.get_input_reg()[10:20]
            db.MongoDB_update(collection_name="APR_Status",query={"_id":1},data={"sensors":sensor})
            
        except Exception as e:
            print("task control led : ",str(e))
        time.sleep(1)
        # control_sound


        time.sleep(1)

if __name__ == '__main__':
    
    db = MongoDataBase(database_name="APR_DB",collections_name=["APR_Status","Call_Machine","APR_Missions","Logfile"])
    if db.MongoDB_Init():
        print('MongoDB init success')
    else:
        print('MongoDB init fail')
    db.MongoDB_update(collection_name="APR_Status",query={"_id":1},data={"task_chain_status":0,"task_chain":[],"mission_recv":{},"task_index":None,"signal_cancel":0})
    Robot = ESA_API(host="192.168.192.5")
    src_init()

    control_board = AMR_Control_Board()
    while not control_board.SetLift(100):
        time.sleep(1)
    while True:
        inputs = control_board.get_input_reg()
        if len(inputs) > 0:
            if inputs[1] == 100:
                break
        time.sleep(1)
    
    writeLogDB("AMR Initial Successed")

    task_src_status_poll = Thread(target=task_src_status_poll_func,args=())
    task_src_status_poll.start()
    
    task_chain_excution = Thread(target=task_chain_excution_func,args=())
    task_chain_excution.start()

    task_control_led_sound = Thread(target=task_control_led_sound_func,args=())
    task_control_led_sound.start()

    app.run(host='0.0.0.0',port=8001,debug=False)