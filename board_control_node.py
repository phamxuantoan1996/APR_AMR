#!/usr/bin/python
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

@app.route('/input_regs',methods=['GET'])
def get_input_regs():
    return jsonify({"input":board.input_regs}),200
    
@app.route('/hold_regs',methods=['POST'])
def set_hold_reg():
    try:
        content = request.json
        if 'hold' in content.keys():
            hold_regs = content['hold']
            if len(hold_regs) > 0:
                temp = board.hold_regs
                for item in hold_regs:
                    keys = item.keys()
                    if 'address' in keys and 'value' in keys:
                        addr = int(item['address'])
                        val = int(item['value'])
                        if addr <= board.num_hold_reg and val >= 0:
                            index = addr - board.start_hold_reg
                            temp[index] = val
                        else:
                            return jsonify({"ret_code":1}),200
                    else:
                        return jsonify({"ret_code":1}),200
                board.hold_regs = temp
        return jsonify({"ret_code":0}),201
    except Exception as e:
        return jsonify({"error":str(e)}),500
    
class Modbus_Function_Code:
    #input
    ReadInputRegs = 4
    ReadHoldRegs = 3
    
    #holding
    WriteHoldRegs = 16
    WriteHoldReg = 6

class Board_Control():
    def __init__(self,api_addr:str,api_port:int,modbus_port:str,modbus_baudrate:int,num_hold_reg:int,start_hold_reg:int,num_input_reg:int,start_input_reg:int,slave_id:int,time_poll:float,timeout_modbus:int):
        self.__api_addr = api_addr
        self.__api_port = api_port
        self.__modbus_port = modbus_port
        self.__modbus_baudrate = modbus_baudrate
        self.__num_hold_reg = num_hold_reg
        self.__start_hold_reg = start_hold_reg
        self.__num_input_reg = num_input_reg
        self.__start_input_reg = start_input_reg
        self.__input_regs = []
        self.__hold_regs = []
        self.__slave_id = slave_id
        self.__time_poll = time_poll
        self.__timeout_modbus = timeout_modbus

    def ConnectToBoard(self):
        try:
            # os.chmod(self.__modbus_port,stat.S_IRWXU)
            self.client = minimalmodbus.Instrument(port=self.__modbus_port,slaveaddress=self.__slave_id,mode=minimalmodbus.MODE_RTU)
            self.client.serial.baudrate = self.__modbus_baudrate
            self.client.serial.bytesize = 8
            self.client.serial.parity = serial.PARITY_NONE
            self.client.serial.timeout = self.__timeout_modbus
            self.client.serial.stopbits = 1
            return True
        except Exception as e:
            print(e)
            return False

    @property
    def start_hold_reg(self) -> list:
        return self.__start_hold_reg
    
    @property
    def num_hold_reg(self) -> list:
        return self.__num_hold_reg
    
    @property
    def input_regs(self) -> list:
        return self.__input_regs
    
    @property
    def hold_regs(self) -> list:
        return self.__hold_regs
    @hold_regs.setter
    def hold_regs(self,val:list):
        self.__hold_regs = val

    def Board_Control_Init(self):
        for i in range(0,self.__num_hold_reg):
            self.__hold_regs.append(0)
        for i in range(0,self.__num_input_reg):
            self.__input_regs.append(0)

    def read_input_regs(self,address:int,count:int) -> list:
        try:
            value = self.client.read_registers(registeraddress=address,number_of_registers=count,functioncode=Modbus_Function_Code.ReadInputRegs)
            return value
        except Exception as e:
            print(str(e))
            return []
    
    def write_hold_regs(self,address:int,value:list) -> bool:
        try:
            self.client.write_registers(registeraddress=address,values=value)
            return True
        except Exception as e:
            print(str(e))
            return False
    
    def Board_Control_Poll(self):
        while True:
            # self.__input_regs = self.read_input_regs(address=self.__start_input_reg,count=self.__num_input_reg)
            print('input regs : ',self.__input_regs)
            print('hold : ',self.__hold_regs)
            if self.write_hold_regs(address=self.__start_hold_reg,value=self.__hold_regs) and (len(self.__input_regs) > 0):
                # self._modbus_error = False
                pass
            else:
                # self._modbus_error = True
                pass
            self.__input_regs = self.read_input_regs(address=0,count=10)
            time.sleep(self.__time_poll)

    def Board_Control_Start(self):
        task_board_control_poll = Thread(target=self.Board_Control_Poll,args=())
        task_board_control_poll.start()
        app.run(host=self.__api_addr,port=self.__api_port,debug=False)

if __name__ == '__main__':
    board = Board_Control(api_addr='0.0.0.0',api_port=8000,modbus_port="/dev/ttyUSB0",modbus_baudrate=115200,num_hold_reg=10,start_hold_reg=0,num_input_reg=10,start_input_reg=0,slave_id=1,time_poll=0.25,timeout_modbus=10)
    if board.ConnectToBoard():
        print('connect to board control success')
    else:
        print('connect to board control error')
    board.Board_Control_Init()
    board.Board_Control_Start()

    