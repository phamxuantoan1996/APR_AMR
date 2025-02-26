#!/usr/bin/python
from flask import Flask, jsonify, request
from flask_cors import CORS

from threading import Thread
import json
import time

import minimalmodbus
import serial

app = Flask(__name__)
CORS(app=app)

@app.route('/input_regs',methods=['GET'])
def get_input_regs():
    return jsonify({"input":board.input_regs}),200

@app.route('/hold_regs',methods=['POST'])
def set_hold_reg():
    try:
        content = request.json
        keys = content.keys()
        if 'address' in keys and 'value' in keys:
            addr = int(content['address'])
            val = int(content['value'])
            if addr <= board.num_hold_reg and val > 0:
                index = addr - board.start_hold_reg
                temp = board.hold_regs
                temp[index] = val
                board.hold_regs = temp
                return jsonify({"ret_code":0}),201
        return jsonify({"ret_code":1}),200
    except Exception as e:
        return jsonify({"error":str(e)}),500

class Board_Control():
    def __init__(self,api_addr:str,api_port:int,modbus_port:str,modbus_baudrate:int,num_hold_reg:int,start_hold_reg:int,num_input_reg:int,start_input_reg:int):
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
    
    def Board_Control_Poll(self):
        while True:
            print('holding regs : ',self.__hold_regs)
            time.sleep(0.25)

    def Board_Control_Start(self):
        task_board_control_poll = Thread(target=self.Board_Control_Poll,args=())
        task_board_control_poll.start()
        app.run(host=self.__api_addr,port=self.__api_port,debug=False)

if __name__ == '__main__':
    board = Board_Control(api_addr='0.0.0.0',api_port=8000,modbus_port="/dev/ttyUSB0",modbus_baudrate=8000,num_hold_reg=50,start_hold_reg=0,num_input_reg=50,start_input_reg=0)
    board.Board_Control_Init()
    board.Board_Control_Start()

    