#!/usr/bin/env python

import logging
import subprocess
import sys
import pprint
import json
from .src import chifra
import os 
from alive_progress import alive_bar 
import math

def test():
    sys.argv = sys.argv[1:]
    obj = chifra().dispatch()
    pprint.pprint(obj)

def run():
    return chifra().dispatch()

def fetchBatchTransaction(tx_ids: list):
    global sys 
    cmds =  ["chifra",  "traces"]
    for tx_hash in tx_ids:
        cmds.append("{0}".format(tx_hash))
    cmds.extend(["-a"])
    sys.argv =  cmds 
    result = run()
    while result is None or "data" not in result or len(result["data"]) == 0:
        result = run()
        os.sleep(1)
    new_results = list()
    for tx_id in tx_ids:
        new_result = list()
        for tx in result["data"]:
            if tx["transactionIndex"] == int(tx_id.split(".")[1]) and tx["blockNumber"] == int(tx_id.split(".")[0]):
                new_result.append(tx)
        new_results.append(new_result)
    return new_results

def fetchTransaction(block, txid):
    global sys 
    sys.argv =  ["chifra", "traces", "{0}.{1}".format(block, txid), "-a"]
    result = run()
    while result is None or "data" not in result or len(result["data"]) == 0:
        result = run()
    return result["data"]

def fetchTransactionsForAccount(address, maxCount=2000, cached_record_number=0):
    global sys 
    transactions = list()
    p = subprocess.Popen(["chifra", "list", address, "--fmt", "json", "-c", str(cached_record_number+1), "-e", str(maxCount)], stdout=subprocess.PIPE)
    out, err = p.communicate()
    if err:
        logging.error(err)
        assert False
    result =  json.loads(out.decode())
    batch_size = 25
    result = list(result["data"])
    logging.warning("size of transactions to analyze:"+str(min(maxCount, len(result))))
    with alive_bar(math.ceil(min(maxCount, len(result))/batch_size)) as bar:
        for i in range(0, min(maxCount, len(result)), batch_size):
            tx_ids = list()
            for tx in result[i:i+batch_size]:
                tx_ids.append(str(tx["blockNumber"])+"."+str(tx["transactionIndex"]))
            transactions.extend(fetchBatchTransaction(tx_ids=tx_ids))
            bar()
    return transactions 

if __name__ == "__main__":
    TokenAddress = "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984"
    fetchTransactionsForAccount(address=TokenAddress, no=100)


    