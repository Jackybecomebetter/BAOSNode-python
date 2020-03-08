# from __future__ import print_function
# import signal
# import pyuv
# import json

# client = None

# def on_read(handle, ip_port, flags, data, error):
#     # print(data)

#     # decode json code 
#     str1=str(data, encoding = "utf-8")  
#     str1 = json.loads(str1)
#     print(str1['endpoint']," ",str1['method']," ",str1['service'])

# def signal_cb(handle, signum):
#     signal_h.close()
#     client.close()


# # init client
# print("PyUV version %s" % pyuv.__version__)
# loop = pyuv.Loop.default_loop()
# client = pyuv.UDP(loop)
# client.bind(("0.0.0.0",30001),pyuv.UV_UDP_REUSEADDR)
# client.set_membership("239.255.0.1",pyuv.UV_JOIN_GROUP)
# print("socket name : ",client.getsockname())

# client.set_broadcast(True)
# client.start_recv(on_read)

# data1 = {
#     'endpoint' : "tcp://192.168.31.138:10033",
#     "method":"commonMulti",
#     "service":"get"
# }
# json_str = json.dumps(data1)
# msg = bytes(json_str, encoding = "utf8")
# client.send(("239.255.0.1", 30001), msg)

# signal_h = pyuv.Signal(loop)
# signal_h.start(signal_cb, signal.SIGINT)

# 


# loop.run()
# print("Stopped!")

# class Base(object):
#     def __init__(self,data):
#         self.data = data
    
#     def print_data(self,data):
#         print("data is ",self.data)
#         print("data is ",data)

# a = Base(10)

# b = Base.print_data
# # b.print_data()
# b(a,20)