# test typedef
class baosimpl(object):
    def print_data(params):
        print("params is ",params)

class function_call(object):
    def __init__(self):
        self.call = None
        self.params = ""

# test typedef
# func1_call = function_call()
# func1_call.call = baosimpl.print_data
# func1_call.params = "data1"
# func2_call = function_call()
# func2_call.call = baosimpl.print_data
# func2_call.params = "data2"
# func_map = {}
# func_map["data1"] = func1_call
# func_map["data2"] = func2_call
# func_map["data1"].call(func_map["data1"].params)
# func_map["data2"].call(func_map["data2"].params)

# test list inside dict
# map = {"",[]}

# test list in func
def test_list(service):
    service.append("192.168.1.1")

ser = []
print("ser is ",ser)
test_list(ser)
print("ser is ",ser[0])
if "192.168.1.1" in ser:
    print("true")

