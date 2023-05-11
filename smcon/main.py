import argparse
import logging
import json 
import os 
from smcon.model.Replayer import TransactionReplayer
from smcon.engine import smcon
from smcon.ppt import PptTopLevel
from smcon.trace.traceslice import TraceSlice, Trace, covertTx2Event, default
from smcon.const import RESULT_DIR 

def main(address, configuration=None, maxCount=500):
    txreplayer = TransactionReplayer(contract_address=address, maxCount=maxCount)
    invcon = smcon(address, txreplayer.contractName, txreplayer.getDeclModel(), txreplayer.getABISpec())
    invcon.initializePpts()
    tx = txreplayer.readPerTx()
    if configuration is None:
        while (not txreplayer.done()) and maxCount>0:
            firstOrMultiple, tx = txreplayer.readPerTx()
            logging.warning(tx.tx_hash  + (str(tx.func) if tx.func is not None else ""))
            logging.debug((str(tx.func[0]) if tx.func is not None and len(tx.func)>0 else "") + json.dumps(tx.envs) if tx.envs is not None else None)
            if not firstOrMultiple:
                invcon.process_data(tx)
            maxCount -= 1
    else:
        slice_configuration = json.load(open(configuration))
        trace = Trace()
        slicer = TraceSlice(trace=trace)
        slicer.setSliceCriteriaByInterestedParams(interested_params=slice_configuration)
        while (not txreplayer.done()) and maxCount>0:
            firstOrMultiple, tx = txreplayer.readPerTx()
            # txreplayer.toStateJson(txreplayer.contractName+"-"+str(maxCount)+".json")
            logging.warning(tx.tx_hash + (str(tx.func) if tx.func is not None else ""))
            logging.debug((str(tx.func[0]) if tx.func is not None and len(tx.func)>0 else "") + json.dumps(tx.envs) if tx.envs is not None else None)
            if not firstOrMultiple:
                invcon.process_data(tx)
                if not tx.hasRevert():
                    newSubEvents = slicer.onlineSlice(covertTx2Event(tx))
                    for newSubEvent in newSubEvents:
                        event, pre_slice_states, post_slice_states = newSubEvent
                        ppt :PptTopLevel = invcon.dynamicCreateOrGetSlicePPT(funcName=event.methodName, key_parameters=event.parameters, slice_states=post_slice_states)
                        ppt.loadSliceEvent(tx=tx, slice_states= pre_slice_states + post_slice_states)
            maxCount -= 1
        json.dump(slicer.to_list(), open(os.path.join(RESULT_DIR, address + "-" + txreplayer.contractName + "-" + "trace_slices.json"), "w"), indent=4)
    invcon.generate_invariants()
    invcon.generate_trace_slice_invariants()
    txreplayer.toStateJson(os.path.join(RESULT_DIR, address + "-" +txreplayer.contractName+".json"))

GameChannel_Address = "0x7e0178e1720e8b3a52086a23187947f35b6f3fc4"
Token_Address = "0x1dac5649e2a0c943ffc4211d708f6ddde4742fd6"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=\
                                     'SMCon: Automata Specification Mining for Smart Contracts with Trace Slicing and Predicate Abstraction!')
    parser.add_argument('--address', type=str, required=False, default=GameChannel_Address, 
                        help='address of Ethereum smart contract,\
                              default (0x7e0178e1720e8b3a52086a23187947f35b6f3fc4-GameChannel)')
    
    parser.add_argument('--configuration', type=str, required=False, default=None, 
                        help='configuration of slice criteria (xxx-config.json)')
    parser.add_argument('--maxCount', type=int, required=False, default=500, 
                        help='the number of transactions used,\
                              (default, 500)')
    args = parser.parse_args()
    main(args.address, args.configuration, args.maxCount)