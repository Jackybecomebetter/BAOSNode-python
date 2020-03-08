import json
import zmq
import threading
from threading import Lock
from concurrent.futures import ThreadPoolExecutor
import time

class ZMQRPCServer(object):
    m_instance = None
    m_mutex = Lock()

    def __init__(self):
        self.m_num = 0
        self.m_pool = None
        self.m_servers = None
        self.m_workers = None
        self.m_context = None
        self.m_callback = {"sub":None}
        pass

    # singleton
    @classmethod
    def getInstance(cls):
        if(cls.m_instance == None):
            cls.m_mutex.acquire()
            if(cls.m_instance == None):
                cls.m_instance = ZMQRPCServer()
            cls.m_mutex.release()
        return cls.m_instance

    def initServer(self,endpoint,threadCount):
        self.m_num = threadCount
        self.m_pool = ThreadPoolExecutor(max_workers=threadCount)
        print("ZMQ RPC Binding to ",endpoint)
        self.m_context = zmq.Context()
        self.m_workers = self.m_context.socket(zmq.DEALER)
        self.m_workers.bind("inproc://workers")

        self.m_servers = self.m_context.socket(zmq.ROUTER)
        self.m_servers.bind(endpoint)
    
    def registerCall(self,name,callback):
        self.m_callback[name] = callback    
        print("m_callback is ",self.m_callback)
    
    def send_str(self,socket,response):
        json_bytes = bytes(response, encoding = "utf8") #json to bytes
        socket.send(json_bytes)
    
    def DealRequest(self):
        context = ZMQRPCServer.get_instance().m_context
        socket = context.socket(zmq.REP)
        socket.connect("inproc://workers")  #connect proxy workers
        print("into deal request")
        while(1):
            try:
                request = socket.recv()
                print("recieve request is ",request)
                json_str = str(request, encoding = "utf-8")  
                json_dict = json.loads(json_str)
                if(json_dict.get("params") == None):
                    json_dict["params"] = None
                try:
                    if( "jsonrpc" in json_dict and "method" in json_dict and "id" in json_dict):
                        if( json_dict["jsonrpc"] != "2.0"):
                            raise Exception("Invalid Jsonrpc version, version must be 2.0")
                        # print("method is ",json_dict["method"])
                        print("m_num is ",self.m_num)
                        print("m_callback is ",self.m_callback) 
                        if( json_dict["method"] in self.m_callback.keys()):  # method found in register
                            callback = self.m_callback[json_dict["method"]]
                            response_result = callback(json_dict["id"],json_dict["params"])
                            self.send_str(socket,response_result)

                except Exception as e:
                    print("jsonrpc server excetion ",e)

            except zmq.error as e:
                print("zmq exception ({0}): {1}".format(e.errno, e.strerror))
                sys.exit()

    def run(self):
        for index in range(self.m_num):
            self.m_pool.submit(self.DealRequest)
        zmq.proxy(self.m_servers,self.m_workers)



    # thread1 = threading.Thread(target=zmq_get_instace)
    # thread2 = threading.Thread(target=zmq_get_instace)
    # thread3 = threading.Thread(target=zmq_get_instace)
    # thread4 = threading.Thread(target=zmq_get_instace)
    # thread5 = threading.Thread(target=zmq_get_instace)
    # thread1.start()
    # thread2.start()
    # thread3.start()
    # thread4.start()
    # thread5.start()
    # thread1.join()
    # thread2.join()
    # thread3.join()
    # thread4.join()
    # thread5.join()
