import sys
import json
sys.path.append("../")
import signal
import json
from BaosNodeImpl import *

def CtrlC():
    print("exit")
    exit

if __name__ == "__main__":
    
    BaosNodeImpl.getInstance().init("239.255.0.1","10006", None)

    BaosNodeImpl.getInstance().publishTopic("print")

    signal.signal(signal.SIGINT,CtrlC)

    while(1):
        param = {}
        param["result"] = 123
        param = json.dumps(param)
        BaosNodeImpl.getInstance().publish_json("print",param)
        sleep(1)



