import zmq
import json
import threading

class ZMQRPCClient(object):
    def __init__(self):
        self.context = zmq.Context()
        #  Socket to talk to server
        print("Connecting to hello world server ...")
        self.socket = self.context.socket(zmq.REQ)
    
    def connect(self,endpoint):
        self.socket.connect(endpoint)
    
    def make_json_request(self,id,method,params = None):
        json_dict = {
		"jsonrpc" : "2.0",
		"method": method,
		"id": id
        }

        if(params != None):
            json_dict["params"] = params

        json_str = json.dumps(json_dict)
        # print("send data is ",json_str)
        json_bytes = bytes(json_str, encoding = "utf8")
        return json_bytes
    
    # string method , json params , return json
    def call(self, method, params =None):
        data = self.make_json_request(1,method,params)
        
        self.socket.send(data)

        reply = self.socket.recv()
        # change bytes to json and return
        json_str = str(reply, encoding = "utf-8")  
        result = json.loads(json_str)
        # print("recieve json is : ",result)

        return result
    
    def async_call(self,method,params,callback):
        if(callable(callback) != True):
            print("callback must be function")
            return -1
        
        new_thread = threading.Thread(target=self.async_call_proc,args=(method,params,callback))
        new_thread.start()
    
    def async_call_proc(self,method,params,callback):
        result = self.call(method,params)
        callback(result)
