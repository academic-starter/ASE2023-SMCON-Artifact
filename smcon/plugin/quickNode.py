import json 
import requests

def fetchVmTrace(tx_hash):
    url = 'https://falling-white-research.quiknode.pro/c5f95a47d726a2dd27e05f15061777155df4373f/'
    myobj = {"method":"trace_replayTransaction","params":[tx_hash,["vmTrace"]],"id":1,"jsonrpc":"2.0"}
    x = requests.post(url, json = myobj)
    data = json.loads(x.text)
    result = data["result"]
    vmTrace = result["vmTrace"]
    # output = result["output"]
    return vmTrace

def fetchStateDiff(tx_hash):
    url = 'https://falling-white-research.quiknode.pro/c5f95a47d726a2dd27e05f15061777155df4373f/'
    myobj = {"method":"trace_replayTransaction","params":[tx_hash,["stateDiff"]],"id":1,"jsonrpc":"2.0"}
    x = requests.post(url, json = myobj)
    data = json.loads(x.text)
    result = data["result"]
    stateDiff = result["stateDiff"]
    # output = result["output"]
    return stateDiff

if __name__ == "__main__":
    account = "Yearn Finance"
    tx_block = "17222636"
    tx_hash = "0x948b94e827664564401571632d0b2405c09776f1d2bbbdd16f8a068e80e161e1"
    stateDiff = fetchStateDiff(tx_hash=tx_hash)
    vmTrace = fetchVmTrace(tx_hash=tx_hash)
    json.dump(stateDiff, open("stateDiff.json", "w"))
    json.dump(vmTrace, open("vmTrace.json", "w"))