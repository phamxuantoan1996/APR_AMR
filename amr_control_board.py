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

if __name__ == '__main__':

    apr_board_control = AMR_Control_Board()
    # apr_board_control.SetLed(color=APR_Led_Color.Red)
    # apr_board_control.SetTransfer(APR_Transfer.Stop)
    apr_board_control.SetLift(400)