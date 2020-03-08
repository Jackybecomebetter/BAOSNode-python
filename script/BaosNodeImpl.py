import json
import zmq
import threading
from threading import Lock
from concurrent.futures import ThreadPoolExecutor
import time
from multicast import *
from ZMQRPCServer import *

# socket info
class socketInfo(object):
    def __init__(self,socket,flag):
        self.socket = socket
        self.flag = flag

# auto auto lock class 
# input a lock and start lock when init
# When out of scope, the destructor is called to release the lock
class AutoLock:
    def __init__(self,lock):
        self._lock = lock
        self._lock.acquire()
        print("lock")

    def __del__(self):
        print('unlock')
        self._lock.release()

class BaosNodeImpl(object):
    m_instance = None
    m_poolSize = 8

    def __init__(self):
        self.m_mutex = []
        self.m_index = 0
        for i in range(BaosNodeImpl.m_poolSize):
            self.m_mutex.append(Lock())
        self.m_connManager = None
        self.m_pool = None
        self.m_servers = None
        self.m_workers = None
        self.m_context = None
        self.m_callback = {"sub":None}
        self.m_jsonHandlers = {}    #{string,[jscb]}
        self.m_msgQueue = [i for i in range(BaosNodeImpl.m_poolSize)]    # message queue to save recieve
        self.m_connection = {}
        self.m_connectionDealWay = {}   # {string,[int]}
        self.m_connectionJson = {}  # {string,socket}

        self.m_localIP = None
        self.m_localPort = None

        self.m_poller = zmq.Poller() 
        self.m_socketInsVec = [] # [{flag,socket}]

        pass
    
    def init(self, multiIP, localPort, point = None):
        self.m_connManager = Multicast(multiIP,self.m_localIP)
        self.m_localIP = self.m_connManager.get_localip()
        self.m_localPort = localPort

        # pub&sub init
        self.m_topicEndpoint = "tcp://" + self.m_localIP + ":" + self.m_localPort
        print("ZMQ PUB Binding to ",self.m_topicEndpoint)
        self.m_context = zmq.Context()
        self.m_pub = self.m_context.socket(zmq.PUB)
        self.m_pub.bind(self.m_topicEndpoint)

        # zmq rpc server init
        self.m_serviceEndpoint =  "tcp://" + self.m_localIP + ":"  + str(int(self.m_localPort) + 1)
        ZMQRPCServer.getInstance().initServer(self.m_serviceEndpoint, BaosNodeImpl.m_poolSize)

        self.m_rpcConnection = {}

        # multicast run and basnodeimpl's dealpoller run
        self.m_connManager.setLocalEndpoint(self.m_topicEndpoint, self.m_serviceEndpoint)
        self.m_pool = ThreadPoolExecutor(max_workers=BaosNodeImpl.m_poolSize)   # init thread pool size
        self.m_pool.submit(Multicast.run, args=(self.m_connManager))
        self.m_pool.submit(self.dealpoller)

        # websocket init

    @classmethod
    def getInstance(cls):
        if(cls.m_instance == None):
            lock = Lock()
            lock.acquire()
            if(cls.m_instance == None):
                cls.m_instance = BaosNodeImpl()
            lock.release()
        return cls.m_instance
    
    # create protobuf message
    def createMessage(self,type_name):
        pass

    def runService(self):
        self.m_pool.submit(ZMQRPCServer.run,ZMQRPCServer.getInstance())
    
    # jsonrpcpp::request_callback f
    def registerService(self,serviceName, f):
        # multicast service
        self.m_connManager.multicastService(serviceName,"tcp://" + self.m_localIP + ":" +  str(int(m_localPort) + 1) )
        # register call
        ZMQRPCServer.getInstance().registerCall(serviceName, f)

    def callService(self,serviceName, params , callback):
        endpoints = []
        result = {}

        # if can not find service ,then update 
        if(self.m_connManager.findService(serviceName,endpoints) == None):
            servicecall = ServiceCall()
            servicecall.params = params
            servicecall.callback = callback
            servicecall.servCall = self.callService
            servicecall.serviceName = serviceName
            self.m_connManager.pushServiceCallBack(servicecall)
            self.m_connManager.sendRequest(serviceName, "service")
            return result
        
        # find serve and it's process it's related endpoints
        for endpoint in endpoints:
            print("service endpoint is ",endpoint)
            # if alread found rpc connection in m_rpcConnection
            if(endpoint in self.m_rpcConnection.keys()):
                if(callback == None):
                    result = m_rpcConnection[endpoint].call(serviceName, params)
                else:
                    m_rpcConnection[endpoint].async_call(serviceName,params,callback)
            # if not found rpc connection in m_rpcConnection ,then create connection and save it
            else:
                m_rpcConnection[endpoint] = ZMQRPCClient()
                m_rpcConnection[endpoint].connect(endpoint)
                if(callback == None):
                    result = m_rpcConnection[endpoint].call(serviceName, params)
                else:
                    m_rpcConnection[endpoint].async_call(serviceName,params,callback)
        
        
    def publishTopic(self,topic):
        self.m_connManager.multicastTopic(topic, self.m_topicEndpoint)
    
    def publish_json(self,topic,json_str):
        sendstr = topic + '-' + json_str
        json_bytes = bytes(json_str, encoding = "utf8")
        self.m_pub.send(json_bytes)

        # Publish the data to each client that connects to the node via Websocket and subscribes to the topic
        pass
        
    def dealRecv(self, msg, flag , index):
        auto_lock = AutoLock(self.m_mutex[self.m_index % BaosNodeImpl.m_poolSize])

        buf = str(msg, encoding = "utf8")
        content = buf.split("-")[1]
        topic = buf.split("-")[0]

        if( flag == ProtoType):
            pass
        elif(flag == JsonType):
            param = json.dumps(content)
            handlers = self.m_jsonHandlers[topic]   # handlers list for spectific topic
            for handler in handlers:
                handler(param)

    # def newSubThread(self,socket, flag):
    #     while(1):
    #         try:
    #             self.m_msgQueue[self.m_index % BaosNodeImpl.m_poolSize] = socket.recv()
    #         except zmq.error as e:
    #             print(e)
    #             continue
    #         self.m_pool.submit(self.dealRecv,args = (self.m_msgQueue[self.m_index % BaosNodeImpl.m_poolSize],flag,self.m_index))
    #         self.m_index = self.m_index + 1
    #         if(self.m_index == BaosNodeImpl.m_poolSize):
    #             self.m_index = 0

    # add alread created and connect socket to list and add socket to zmq poller monitor
    def addSocket(self,socket, flag):
        self.m_poller.register(socket, zmq.POLLIN)
        self.m_socketInsVec.append(socketInfo(socket,flag))

    # zmq poller monitor socket and deal with socket recv
    def dealpoller(self):
        while(1):
            socks = self.m_poller.poll()    # socks [(socket,flag)]  
            # process poller monitor sockets
            for i in range(len(sock)):
                if(socks[i][1] == zmq.POLLIN):  #socket flag == zmq.POLLIN
                    try:
                        auto_lock = AutoLock(self.m_mutex[self.m_index % BaosNodeImpl.m_poolSize])
                        self.m_msgQueue[self.m_index % BaosNodeImpl.m_poolSize] = self.m_socketInsVec[i].socket.recv()
                    
                    except zmq.error as e:
                        print(e)
                        continue
                    self.m_pool.submit(self.dealRecv,args = (self.m_msgQueue[self.m_index % BaosNodeImpl.m_poolSize],
                                        self.m_socketInsVec[i].flag,self.m_index))
                    self.m_index = self.m_index + 1
                    if(self.m_index == BaosNodeImpl.m_poolSize):
                        self.m_index = 0
    
    # create new subcribe socket and add it into connection
    # use addSocket to put socket into poller monitor
    # insert endpoint into connectiondealway which use to check if endpoint is connect or not
    def initNewSub(self,endpoint, topic, flag):
        self.m_connection[endpoint] = self.m_context.socket(zmq.SUB)
        self.m_connection[endpoint].connect(endpoint)
        self.m_connection[endpoint].setsockopt(zmq.SUBSCRIBE,topic, len(topic))
        
        self.addSocket(self.m_connection[endpoint],flag)

        if(topic not in self.m_connectionDealWay.keys()):
            vec = [0 for i in range(10)]
            self.m_connectionDealWay[endpoint] = vec
    
    def subscribeTopic_Json(self, topic, jsncb):
        endpoints = []
        endpoint = ""

        if( self.m_connManager.findTopic(topic, endpoints) == None ):
            print("can not find topic")
            jsnCB = JsnCallBack()
            jsnCB.jsnCb = jsncb     # user json callback function
            jsnCB.jsnSub = self.subscribeTopic_Json         # baosnodeimpl.subscribeTopic_Json callback function
            jsnCB.topicName = topic

            self.m_connManager.pushTopic_JsonCallBack(jsnCB)
            self.m_connManager.sendRequest(topic,"topic")
            return
        
        self.m_jsonHandlers[topic] = jsncb
        for endpoint in endpoints:
            if(endpoint not in self.m_connectionJson.keys()):
                self.initNewSub(endpoint, topic, JsonType)
            else:
                self.m_connectionJson[endpoint].setsockopt(zmq.SUBSCRIBE, topic, len(topic))
                if(self.m_connectionDealWay[endpoint][JsonType] == 0):
                    self.addSocket(self.m_connectionJson[endpoint], JsonType)
                    self.m_connectionDealWay[endpoint][JsonType] = 1
    
    def unSubscribeTopic(self,topic):
        endpoints = []

        self.m_connManager.findTopic(topic,endpoints)

        # clear json data type connection and handlers
        for endpoint in endpoints:
            if( endpoint in self.m_connectionJson.keys() ):
                # cancel subscribe
                for i in range(len(self.m_jsonHandlers[topic])):
                    self.m_connectionJson[endpoint].setsockopt(zmq.UNSUBSCRIBE,topic,len(topic))
                del self.m_jsonHandlers[topic]
                print("unsubscribe ",topic)
        
        # clear protobuf data type connection and handlers


