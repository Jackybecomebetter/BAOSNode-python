import sys
import json
sys.path.append("../")

from ZMQRPCServer import *

def sub(id, params):

    if("sub1" in params.keys() and "sub2" in params.keys()):
        sub1 = int(params["sub1"])
        sub2 = int(params["sub2"])
        result = sub1 - sub2

        json_dict = {
            "jsonrpc" : "2.0",
		    "id" : id,
            "result" : result
	    }
        json_str = json.dumps(json_dict)
        return json_str

def get_data(id, params = None):

    json_dict = {
        "jsonrpc" : "2.0",
        "id" : id,
        "result" : "helloworld"
    }
    json_str = json.dumps(json_dict)
    return json_str

if __name__ == "__main__":
    
    endpoint = "tcp://*:5555"

    ZMQRPCServer.get_instance().initServer(endpoint,4)

    ZMQRPCServer.get_instance().registerCall("sub",sub)

    ZMQRPCServer.get_instance().registerCall("get_data",get_data)

    ZMQRPCServer.get_instance().run()