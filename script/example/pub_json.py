import sys
import json
sys.path.append("../")

import json
from BaosNodeImpl import *

if __name__ == "__main__":
    
    BaosNodeImpl.getInstance().init("239.255.0.1","10006", None)

    BaosNodeImpl.getInstance().publishTopic("print")

    while(1):
        param = {}
        param["result"] = 123
        param = json.dumps(param)
        BaosNodeImpl.getInstance().publish_json("print",param)
        sleep(1)



