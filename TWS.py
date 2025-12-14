from ibapi.client import *
from ibapi.wrapper import *
from ibapi.contract import Contract
from ibapi.tag_value import TagValue
import threading
import time
import pandas as pd
import numpy as np
from ibapi.utils import *


class TradeApp(EWrapper, EClient): 
    def __init__(self): 
        EClient.__init__(self, self)
    
    def nextValidId(self, orderId:int):
        self.orderId = orderId

    def nextId(self):
        self.orderId += 1
        return self.orderId

    def error(self, reqId, errorCode, errorString):
        print("Error. Id: ", reqId, " Code: ", errorCode, " Msg: ", errorString)        
    
    def securityDefinitionOptionParameter(self, reqId: int, exchange: str, underlyingConId: int,
                                          tradingClass: str, multiplier: str, expirations: SetOfString,
                                          strikes: SetOfFloat):
        
        print("SecurityDefinitionOptionParameter. ReqId:", reqId, "Exchange:", exchange,
              "Underlying conId:", underlyingConId, "Trading class:", tradingClass,
              "Multiplier:", multiplier, "Expirations:", expirations,
              "Strikes:", strikes)
    
    def securityDefinitionOptionParameterEnd(self, reqId):
        print("SecurityDefinitionOptionParameterEnd. ReqId:", reqId)
        self.disconnect()
   
def websocket_con():
    app.run()
    
app = TradeApp()      
app.connect("127.0.0.1", 7496, clientId=4)

time.sleep(1) 

con_thread = threading.Thread(target=websocket_con, daemon=True)
con_thread.start()

myContract = Contract()
myContract.symbol = "OKLO"
myContract.secType = "STK"
myContract.exchange = "SMART"
myContract.currency = "USD"


time.sleep(1)

app.req

