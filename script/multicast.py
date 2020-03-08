import socket
import signal
import pyuv
import json
from time import *

g_listenip = "0.0.0.0"
g_multicast_port = 30001

JsonType = 0
ProtoType = 1
topicType = 0
serviceType = 1

# json callback info
class JsnCallBack(object):
    def __init__(self):
        topicName = ""
        jsnSub = None     # std::function<void(const std::string & topic, const JsnCb &cb)> 
        jsnCb = None    # std::function<void (google::protobuf::Message *msg)> 

class MsgCallBack(object):
    def __init__(self):
        topicName = ""
        MsgCb = None      # std::function<void(const std::string & topic, const MsgCb &cb)>
        msgCb = None        

class ServiceCall(object):
    def __init__(self):
        serviceName = ""
        servCall = ""   # std::function<Json(const std::string & service, Json& params ,std::function<void(Json json)> &callback)>
        callback  = None  # std::function<void(Json json)>
        params = {}     # json params

class Multicast(object):

    # multicast init
    def __init__(self,multicast_addr,localip):
        # get local socket name
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8",80))
        self.__m_localip = sock.getsockname()[0]
        print("local ip ",self.__m_localip)

        # init recv_socket
        self.loop = pyuv.Loop.default_loop()
        self.__m_multicast_addr = multicast_addr
        self.__m_recv_socket = pyuv.UDP(self.loop)
        self.__m_recv_socket.bind((g_listenip,g_multicast_port),pyuv.UV_UDP_REUSEADDR)
        self.__m_recv_socket.set_membership(multicast_addr,pyuv.UV_JOIN_GROUP)
        self.__m_recv_socket.set_broadcast(True)
        self.__m_recv_socket.start_recv(self.handlerRecv)   # recieve handler

        # init send_socket
        self.__m_send_socket = pyuv.UDP(self.loop)
        self.__m_send_socket.bind((g_listenip,g_multicast_port),pyuv.UV_UDP_REUSEADDR)
        # self.__m_send_socket.set_membership(multicast_addr,pyuv.UV_JOIN_GROUP)

        # 
        self.__m_localEndpoint = ""
        self.__m_localrpcEndpoint = ""
        self.__m_jsnCbMap = {}
        self.__m_msgCbMap = {}
        self.__m_serviceCallMap = {}
        self.__m_topicMap = {}  # std::unordered_map<std::string, std::unordered_set<std::string>>
        self.__m_serviceMap = {} # std::unordered_map<std::string, std::unordered_set<std::string>>

        self.__m_signal_h = pyuv.Signal(self.loop)
        self.__m_signal_h.start(self.signal_handler, signal.SIGINT)
    
    def get_localip(self):
        return self.__m_localip

    # if ctrl + c signal , then close socket
    def signal_handler(self,handle, signum):
        self.__m_signal_h.close()
        self.__m_recv_socket.close()
        self.__m_send_socket.close()

    def __del__( self ):
        # deconstruct function
        pass
    
    def setLocalEndpoint(self,pubsubEndpoing,rpcEndpoint):
        self.__m_localEndpoint = pubsubEndpoing
        self.__m_localrpcEndpoint = rpcEndpoint
    
    def dealDelayCallBack(self,topicName):
        jsoncall = __m_jsnCbMap[topicName]
        if(jsoncall != None):
            jsncb = jsoncall.jsncb
            jsoncall.jsnSub(topicName,jsncb)   # call json sub
            del __m_jsnCbMap[topicName]
        
        # call msg sub for protobuf
    
    def dealServiceDelayCall(self,serviceName):
        service_call = self.__m_serviceCallMap[serviceName]
        if(service_call != None):
            params = service_call.params
            callback = service_call.callback
            service_call.servCall(serviceName,params,callback)
            del __m_serviceCallMap[serviceName]

    # update topic map or service map
    def updateMap(self,type,result):
        if(type == topicType):
            print("update topic map")
            endpoints = __m_topicMap[result["topic"]]   #topic may has sevel server endpoints
            endpoint = result["endpoint"]
            if(endpoints != None):  # find topic and related endpoints list
                if(endpoint in endpoints):   # alread has endpoint in list
                    return
                else:
                    __m_topicMap[result["topic"]].append(endpoint)
            else:   # not found then insert
                ends = []
                ends.append(endpoint)
                __m_topicMap[result["topic"]] = ends
        
        # service type
        elif(type == serviceType):   
            print("update service map")
            endpoints = __m_serviceMap[result["service"]]
            endpoint = result["endpoint"]
            if(endpoints != None):  # find topic and related endpoints list
                if(endpoint in endpoints):   # alread has endpoint in list
                    return
                else:
                    __m_serviceMap[result["service"]].append(endpoint)
            else:   # not found then insert
                ends = []
                ends.append(endpoint)
                __m_serviceMap[result["service"]] = ends

    def findLocalSupport(self,supportName,type):
        if(type == topicType):
            self.sendRspToPeer(self.__m_topicMap,supportName,self.__m_localEndpoint, "topic")
        elif(type == serviceType):
            self.sendRspToPeer(self.__m_serviceMap,supportName,self.__m_localrpcEndpoint, "service")

    # map : {service_name/topic_name,[endpoints]}
    def sendRspToPeer(self,map,supportName,endpoint,field):
        print("start to send response")
        map.setdefault(supportName,None)    # set default to prevent code collapse
        endpoints = map[supportName]
        if(endpoints != None):
            if endpoint in endpoints:
                json_dict = {
                    "method" : "response",
                    field : supportName,
                    "endpoint" : endpoint
                }
                json_str = json.dumps(json_dict)
                json_bytes = bytes(json_str, encoding = "utf8")
                self.__m_recv_socket.send((self.__m_multicast_addr,g_multicast_port),json_bytes)

    def multicastTopic(self,topicName,endpoint):
        json_dict = {
                    "method" : "commonMulti",
                    "topic" : topicName,
                    "endpoint" : endpoint
                }
        json_str = json.dumps(json_dict)
        json_bytes = bytes(json_str, encoding = "utf8")
        print("__m_multicast_addr is ",self.__m_multicast_addr)
        print("g_multicast_port is ",g_multicast_port)
        self.__m_send_socket.send((self.__m_multicast_addr,g_multicast_port),json_bytes)

    def sendRequest(self,supportName,filed):
        json_dict = {
                    "method" : "request",
                    filed : supportName,
                    "endpoint" : ""
                }
        print("send request")
        json_str = json.dumps(json_dict)
        json_bytes = bytes(json_str, encoding = "utf8")
        self.__m_send_socket.send((self.__m_multicast_addr,g_multicast_port),json_bytes)
    
    def multicastService(self,serviceName,endpoint):
        json_dict = {
                    "method" : "commonMulti",
                    "endpoint" : serviceName,
                    "endpoint" : endpoint
                }
        print("send service endpoint")
        json_str = json.dumps(json_dict)
        json_bytes = bytes(json_str, encoding = "utf8")
        self.__m_send_socket.send((self.__m_multicast_addr,g_multicast_port),json_bytes)
    
    # endpoints : endpoint list
    def findTopic(self,topicName,endpoints):
        res = True
        # print("finding topic name in local map: " ,topicName)
        topic_endpoints = self.__m_topicMap.get(topicName)
        if(topic_endpoints == None): #can not find topic
            print("can not find topic name in local map")
            res = False
            return res
        endpoints = topic_endpoints
        return res

    # endpoints : endpoint list
    def findService(self,serviceName,endpoints):
        res = True
        print("finding service name in local map: " ,serviceName)
        service_endpoints = self.__m_serviceMap[serviceName]
        if(service_endpoints == None): #can not find topic
            res = False
            return res
        endpoints = service_endpoints
        return res

    # std::unordered_map<std::string, JsnCallBack>
    #     struct JsnCallBack{
    #     std::string     topicName;
    #     std::function<void(const std::string & topic, const JsnCb &cb)> jsnSub;
    #     JsnCb           jsnCb;
    #     ~JsnCallBack(){}
    # };
    # JsnCallBack
    def pushTopic_JsonCallBack(self,JsnCallBack):
        self.__m_jsnCbMap[JsnCallBack.topicName] = JsnCallBack
    
    def pushServiceCallBack(self,serviceCall):
        self.__m_serviceCallMap[serviceCall.serviceName] = serviceCall
    
    def run(self):
        self.loop.run()     #run multicast service
        print("socket disconnect")
    
    def handlerRecv(self,handle, ip_port, flags, data, error):
        print("get into handler Recv")
        if(error is None):
            if(data is not None):
                json_str = str(data, encoding = "utf-8")  
                result = json.loads(json_str)
                print("recieve json is : ",result)

                if(result["endpoint"] is not None):
                    method = result["method"]
                    # if recieve topic msg
                    if(result["topic"] is not None):
                        if(method == "commonMulti"):
                            self.updateMap(topicType,result)
                            self.dealDelayCallBack(result["topic"])
                        elif(method == "request"):
                            self.findLocalSupport(result["topic"],topicType)
                        elif (method == "response"):
                            self.updateMap(topicType,result)
                            self.dealDelayCallBack(result["topic"])
                    # deal service msg
                    elif(result["service"] is not None):
                        if(method == "commonMulti"):
                            self.updateMap(serviceType,result)
                            self.dealServiceDelayCall(result["service"])
                        elif(method == "request"):
                            self.findLocalSupport(result["service"],serviceType)
                        elif(method == "response"):
                            self.updateMap(serviceType,result)
                            self.dealServiceDelayCall(result["service"])
        else:
            print("error is ",error)

def multicast_test(mult1):
    mult1.multicastService("add","192.168.1.3")
    mult1.multicastTopic("sub","192.34.2.2")
    mult1.sendRequest("topic_request","topic")
    mapset = {"topic_response" : ["192","168"]}
    mult1.sendRspToPeer(mapset,"topic_response","192","topic")

import threading

if __name__ == "__main__":
    mult1 = Multicast("239.255.0.1",10001)
    thread1 = threading.Thread(target=multicast_test,args=(mult1,),name="thread1")
    thread2 = threading.Thread(target=multicast_test,args=(mult1,),name="thread2")
    thread3 = threading.Thread(target=multicast_test,args=(mult1,),name="thread3")

    thread1.start()
    thread2.start()
    thread3.start()

    mult1.run()
    thread1.join()
    thread2.join()
    thread3.join()
    
