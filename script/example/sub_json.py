import sys
sys.path.append("../")
from BaosNodeImpl import *
import json
import time
import os
import signal

def CtrlC():
    print("exit")
    exit()


def print(result):
    if("result" in result):
        print("recieve json is : ",result["result"])

if __name__ == "__main__" :
    BaosNodeImpl.getInstance().init("239.255.0.1","10009", None)
    BaosNodeImpl.getInstance().subscribeTopic_Json("print", print)

    signal.signal(signal.SIGINT, CtrlC)

    input()

