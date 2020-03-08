import sys
sys.path.append("../")
from ZMQRPCClient import *
import zmq
import json
import time

def callback(result):
    if("result" in result):
        print("recieve json is : ",result["result"])

if __name__ == "__main__":
    client = ZMQRPCClient()

    client.connect("tcp://127.0.0.1:5555")

    while(1):
        # input params is dict type
        params_dict ={
            "sub1" : 3,
            "sub2" : 6
        }
        result = client.call("sub",params_dict)
        if("result" in result):
            print("result is ",result["result"])

        params_dict ={
            "sub1" : 60,
            "sub2" : 20
        }
        client.async_call("sub",params_dict,callback)
        time.sleep(1)

        result = client.call("get_data")
        if("result" in result):
            print("result is ",result["result"])
        # time.sleep(1)
