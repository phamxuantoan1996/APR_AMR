import minimalmodbus
import serial
import os
import sys
import stat

from flask import Flask, jsonify, request
from flask_cors import CORS

from threading import Thread
import json
import time

app = Flask(__name__)
CORS(app=app)

#GET 127.0.0.1:8002/input_regs?slave_id=1
@app.route('/input_regs',methods=['GET'])
def get_input_regs():
    try:
        slave_id = int(request.args.get("slave_id"))
        input_regs = []
        for server in mb_servers:
            if server.slave_id == slave_id:
                input_regs = server.input_regs
                break
        return jsonify({"input":input_regs}),200
    except Exception as e:
        return jsonify({"error set input regs":str(e)}),500



#POST 127.0.0.1:8002/hold_regs
# {
#     "slave_id":1,
#     "hold":[
#         {"address":1,"value":0}
#     ]
# }
@app.route('/hold_regs',methods=['POST'])
def set_hold_reg():
    try:
        content = request.json
        if 'hold' in content.keys() and "slave_id" in content.keys():
            hold_regs = content['hold']
            slave_id = int(content['slave_id'])
            if len(hold_regs) > 0:
                for server in mb_servers:
                    if server.slave_id == slave_id:
                        temp = server.hold_regs
                        for item in hold_regs:
                            keys = item.keys()
                            if 'address' in keys and 'value' in keys:
                                addr = int(item['address'])
                                val = int(item['value'])
                                if addr <= server.num_hold_reg and val >= 0:
                                    index = addr - server.start_hold_reg
                                    temp[index] = val
                        return jsonify({"ret_code":0}),201
        return jsonify({"ret_code":-1}),200
    except Exception as e:
        return jsonify({"error set hold regs":str(e)}),500

class Modbus_Function_Code:
    #input
    ReadInputRegs = 4
    ReadHoldRegs = 3
    #holding
    WriteHoldRegs = 16
    WriteHoldReg = 6

class ModbusServer:
    def __init__(self,modbus_port:str,modbus_baudrate:int,num_hold_reg:int,start_hold_reg:int,num_input_reg:int,start_input_reg:int,slave_id:int,time_poll:float,timeout_modbus:int):
        self.__modbus_port = modbus_port
        self.__modbus_baudrate = modbus_baudrate
        self.num_hold_reg = num_hold_reg
        self.start_hold_reg = start_hold_reg
        self.num_input_reg = num_input_reg
        self.start_input_reg = start_input_reg
        self.input_regs = []
        self.hold_regs = []
        self.slave_id = slave_id
        self.__time_poll = time_poll
        self.__timeout_modbus = timeout_modbus
        for i in range(0,num_hold_reg):
            self.hold_regs.append(0)
    
    def mb_init(self):
        try:
            self.client = minimalmodbus.Instrument(port=self.__modbus_port,slaveaddress=self.slave_id,mode=minimalmodbus.MODE_RTU)
            self.client.serial.baudrate = self.__modbus_baudrate
            self.client.serial.bytesize = 8
            self.client.serial.parity = serial.PARITY_NONE
            self.client.serial.timeout = self.__timeout_modbus
            self.client.serial.stopbits = 1
            return True
        except Exception as e:
            print(e)
            return False
        
    def read_input_regs(self) -> bool:
        try:
            value = self.client.read_registers(registeraddress=self.start_input_reg,number_of_registers=self.num_input_reg,functioncode=Modbus_Function_Code.ReadInputRegs)
            self.input_regs = value
            return True
        except Exception as e:
            print(str(e))
            self.input_regs = []
            return False
    
    def write_hold_regs(self) -> True:
        try:
            self.client.write_registers(registeraddress=self.start_hold_reg,values=self.hold_regs)
            return True
        except Exception as e:
            print(str(e))
            return False
        
def task_poll_mb_server_func():
    while True:
        for server in mb_servers:
            if server.num_hold_reg > 0:
                server.write_hold_regs()
            time.sleep(0.05)
            if server.num_input_reg > 0:
                server.read_input_regs()
            time.sleep(0.05)
        
if __name__ == '__main__':
    mb_servers = []

    driver_led = ModbusServer(modbus_port='/dev/ttyUSB0',modbus_baudrate=115200,num_hold_reg=1,start_hold_reg=0,num_input_reg=0,start_input_reg=0,slave_id=1,time_poll=200,timeout_modbus=5000)
    if driver_led.mb_init():
        mb_servers.append(driver_led)
    control_board = ModbusServer(modbus_port='/dev/ttyUSB0',modbus_baudrate=115200,num_hold_reg=10,start_hold_reg=0,num_input_reg=10,start_input_reg=0,slave_id=2,time_poll=200,timeout_modbus=5000)
    if control_board.mb_init():
        mb_servers.append(control_board)

    task_poll_mb_server = Thread(target=task_poll_mb_server_func,args=())
    task_poll_mb_server.start()

    app.run(host='0.0.0.0',port=8002,debug=False)

    