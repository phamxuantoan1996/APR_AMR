import requests
import time

class APR_Led_Color:
    Non = 0
    Red = 8
    Yellow = 10
    Green = 2

class APR_Transfer:
    Stop = 0
    Pick_From_Left = 1
    Put_To_Left = 2
    Pick_From_Right = 3
    Put_To_Right = 4

class APR_Stopper:
    Non = 0
    Close = 1
    Open = 2

class APR_Hold_Addr:
    Led = 0
    Lift = 1
    Transfer = 2

class AMR_Control_Board:

    def set_hold_reg(self,val:list) -> bool:
        url_post = "http://127.0.0.1:8000/hold_regs"
        hold_reg = {
            "hold":val
        }
        try:
            response = requests.post(url=url_post,json=hold_reg)
            if response.status_code == 201:
                return True
        except Exception as e:
            print(e)
        return False
    
    def get_input_reg(self) -> list:
        url_get = "http://127.0.0.1:8000/input_regs"
        try:
            response = requests.get(url=url_get)
            if response.status_code == 200:
                content = response.json()
                if 'input' in content.keys():
                    return content['input']
        except Exception as e:
            print(e)
        return []
    
    def SetLed(self,color:APR_Led_Color):
        values = [{"address" : APR_Hold_Addr.Led,"value" : color}] 
        self.set_hold_reg(val=values)
        print('--set_led--')

    def SetLift(self,lift:int) -> bool:
        values = [{"address" : APR_Hold_Addr.Lift,"value" : lift}] 
        print('--set_lift--')
        return self.set_hold_reg(val=values)

    def SetTransfer(self,dir:APR_Transfer) -> bool:
        values = [{"address" : APR_Hold_Addr.Transfer,"value" : dir}] 
        print('--set_convoyer--')
        return self.set_hold_reg(val=values)
    
    def Conv_Manual_CW(self) -> bool:
        values = [{"address" : APR_Hold_Addr.Transfer,"value" : 6}] 
        print('--set_convoyer--')
        return self.set_hold_reg(val=values)
    def Conv_Manual_CCW(self) -> bool:
        values = [{"address" : APR_Hold_Addr.Transfer,"value" : 7}] 
        print('--set_convoyer--')
        return self.set_hold_reg(val=values)
    def Conv_Manual_Stop(self) -> bool:
        values = [{"address" : APR_Hold_Addr.Transfer,"value" : 8}] 
        print('--set_convoyer--')
        return self.set_hold_reg(val=values)
    def Stopper_Manual_Up(self) -> bool:
        values = [{"address" : APR_Hold_Addr.Transfer,"value" : 9}] 
        print('--set_convoyer--')
        return self.set_hold_reg(val=values)
    def Stopper_Manual_Down(self) -> bool:
        values = [{"address" : APR_Hold_Addr.Transfer,"value" : 10}] 
        print('--set_convoyer--')
        return self.set_hold_reg(val=values)
    


if __name__ == '__main__':

    apr_board_control = AMR_Control_Board()
    # apr_board_control.SetLed(color=APR_Led_Color.Red)
    while True:
        apr_board_control.SetTransfer(APR_Transfer.Put_To_Left)
        time.sleep(8)
        apr_board_control.SetTransfer(APR_Transfer.Stop)
        time.sleep(1)
        apr_board_control.SetTransfer(APR_Transfer.Pick_From_Left)
        time.sleep(8)
        apr_board_control.SetTransfer(APR_Transfer.Stop)
        time.sleep(1)
    # apr_board_control.SetLift(100)
    # apr_board_control.Conv_Manual_CCW()