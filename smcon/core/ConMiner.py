import json 
import os 
from smcon.core.specAutomata import *
from smcon.core.invariantslice import InvariantSlice
from smcon.core.Ktail import KTail 

MDL_ON = False
class ConMiner:
    def __init__(self, workdir, contractName) -> None:
        self.workdir = workdir 
        self.contractName = contractName
        self.ignores = []
        self.usefullName = False
        

    def enableFullName(self):
        self.usefullName  = True  

    def readInvariantFromJson(self, processed_invariant_file):
        invariant = json.load(open(processed_invariant_file, "r"))
        self.readInvariant(invariant)

    def readInvariant(self, invariant):
        predicates = []
        pre_invariants = {}
        post_invariants = {}
        for method in invariant:
            for variant in invariant[method]:
                # remove ori label 
                new_pre = []
                for item in variant["slice_pre"]:
                    m = re.match(r"ori\((.*)\)", item)
                    assert m is not None
                    m2 = re.match(r"(.*\])\.(\w+)", m.group(1))
                    if m2 is None:
                        m3 = re.search(r"(.*)\[(.*)\]", m.group(1))
                        arrayName =  m3.group(1)
                        indexName = m3.group(2)
                        m4 = re.match(r"(.*)\[(.*)\]", arrayName)
                        suffix = "_"
                        if m4 is not None:
                            arrayName = m4.group(1)
                        new_item =  item.replace("ori("+m.group(1)+")", arrayName+suffix)
                        new_pre.append(new_item)
                    else:
                        m3 = re.search(r"(.*)\[(.*)\]", m2.group(1))
                        arrayName =  m3.group(1)
                        indexName = m3.group(2)
                        field =  m2.group(2)
                        m4 =  re.match(r"(.*)\[(.*)\]", arrayName)
                        suffix = "_"
                        if m4 is not None:
                            arrayName = m4.group(1)
                        new_pre.append(item.replace("ori("+m.group(1)+")", arrayName+suffix+field))
                new_post = []
                for item in variant["slice_post"]:
                    m2 = re.match(r"(.*\])\.(.*)\s+.*", item)
                    if m2 is None:
                        m = re.match(r"(.*)\[(.*)\]\s+.*", item)
                        arrayName =  m.group(1)
                        indexName = m.group(2)
                        m4 = re.match(r"(.*)\[(.*)\]", arrayName)
                        suffix = "_"
                        if m4 is not None:
                            arrayName = m4.group(1)
                        new_item =  item.replace(arrayName+"["+indexName+"]", arrayName+suffix)
                        new_post.append(new_item)
                    else:
                        m3 = re.match(r"(.*)\[(.*)\]", m2.group(1))
                        arrayName =  m3.group(1)
                        indexName = m3.group(2)
                        field =  m2.group(2)
                        m4 =  re.match(r"(.*)\[(.*)\]", arrayName)
                        suffix = "_"
                        if m4 is not None:
                            arrayName = m4.group(1)
                        new_post.append(item.replace(m2.group(1)+"."+m2.group(2), arrayName+suffix+field))
                predicates += new_pre
                predicates += new_post
                # if len(new_pre) == 0:
                #     continue
                pre_invariants[method+"@"+"@".join(variant["parameterBinding"])] = new_pre
                post_invariants[method+"@"+"@".join(variant["parameterBinding"])] = new_post
        self.predicates = list(set(predicates))
        self.pre_invariants = pre_invariants
        self.post_invariants = post_invariants
        self.fieldPredMapping = getFieldPredicates(self.predicates)

        json.dump(self.pre_invariants, open(self.workdir+"-"+self.contractName+".pre_inv", "w"), indent=4)
        json.dump(self.post_invariants, open(self.workdir+"-"+self.contractName+".post_inv", "w"), indent=4)

    def readPreProcessedSliceInvariant(self, invariant):
        predicates = []
        pre_invariants = {}
        post_invariants = {}
        for method in invariant:
            for variant in invariant[method]:
                # remove ori label 
                new_pre = []
                # this is caused by the lack of detected invariant since no relevant methods have been called in the history
                if "slice_pre" not in variant:
                    continue 
                for item in variant["slice_pre"]:
                    m = re.match(r"^ori\((.*)\)", item)
                    assert m is not None
                    pure_item = m.group(1)
                    new_pre.append(item.replace(f"ori({pure_item})", pure_item).replace("$", "_"))
                   
                new_post = []
                for item in variant["slice_post"]:
                    new_post.append(item.replace("$", "_"))

                predicates += new_pre
                predicates += new_post
                pre_invariants[method+"@"+"@".join(variant["parameterBinding"])] = new_pre
                post_invariants[method+"@"+"@".join(variant["parameterBinding"])] = new_post
        self.predicates = list(set(predicates))
        self.pre_invariants = pre_invariants
        self.post_invariants = post_invariants
        self.fieldPredMapping = getFieldPredicates(self.predicates)

        json.dump(self.pre_invariants, open(self.workdir+"-"+self.contractName+".pre_inv", "w"), indent=4)
        json.dump(self.post_invariants, open(self.workdir+"-"+self.contractName+".post_inv", "w"), indent=4)


    def getFieldPredMapping(self):
        return self.fieldPredMapping

    def setInitialState(self, initialState):
        self.initialState =  initialState
        pass 

    def enableZeroIntialState(self):
        initialState =  list()
        for field in self.fieldPredMapping:
            initialState.append(f"{field} == 0")
        initialState =  translate2Z3exprFromPredSet(initialState)
        self.initialState = initialState
        return self.initialState
    
    def smcon(self):
        def Init():
            fsm = Automata()
            otherState = "False" 
            pre_invariants =  self.pre_invariants
            post_invariants = self.post_invariants
            for func in pre_invariants:
                sub_1_state = translate2Z3exprFromPredSet(pre_invariants[func])
                sub_2_state = translate2Z3exprFromPredSet(post_invariants[func])
                otherState = f"Or({otherState}, Or({sub_1_state}, {sub_2_state}))"
            otherState = f"And(Not({self.initialState}), {otherState})"
            fsm.addState(self.initialState)
            fsm.addState(otherState)
            fsm.addIntialState(self.initialState)
            return fsm 
            
        def Construct(fields,  pre_invariants, post_invariants, fieldPredMapping, fsm: Automata):
            fsm.addIntialState(self.initialState)
            fsm.generate(pre_invariants, post_invariants, fieldPredMapping, workdir=self.workdir)
            return fsm  
         
        def RmPath(fsm: Automata, traces: list, fields: list, pre_invariants, post_invariants):
            pi_n_1 = fsm.checkSpuriousPath()
            if pi_n_1 is None:
                return True, fsm 

            removeKind = fsm.splitAndRemove(pi_n_1, fields, pre_invariants, post_invariants)
            REMOVE_TRANSITION = 0
            while removeKind == REMOVE_TRANSITION:
                pi_n_1 = fsm.checkSpuriousPath()
                if pi_n_1 is None:
                    return True, fsm 
                removeKind = fsm.splitAndRemove(pi_n_1, fields, pre_invariants, post_invariants)
            
            return False, fsm

        def fair_shedule():
            timeout_count =  10
            traces = self.getTraces()
            fsm = Init()
            fsm.setEventTraces(traces=traces)
            old_states =  len(fsm.states)
            fields = list(self.fieldPredMapping.keys())

            fsm = Construct(fields, self.pre_invariants, self.post_invariants, self.fieldPredMapping, fsm)
            stable, fsm = RmPath(fsm, traces, fields, self.pre_invariants, self.post_invariants)
            
            print(old_states, "->",  len(fsm.states))
            while not stable and timeout_count > 0:
                old_states = len(fsm.states)
                Construct(fields, self.pre_invariants, self.post_invariants, self.fieldPredMapping, fsm)
                stable, fsm = RmPath(fsm, traces, fields, self.pre_invariants, self.post_invariants)
                timeout_count -= 1
                print(old_states, "->",  len(fsm.states))
            

            if not stable:
                Construct(fields, self.pre_invariants, self.post_invariants, self.fieldPredMapping, fsm)
            else:
                logging.info("No spurious path found")

            candidates = fsm.determinise(pre_invariants=self.pre_invariants, post_invariants=self.post_invariants)
        
            max_count = 3
            while len(candidates) > 0:
            # if len(candidates) > 0:
                for candidate in candidates:
                    if SMT_SAT(fieldorfileds=fields, preds=candidate):
                        fsm.addState(candidate)
                Construct(fields, self.pre_invariants, self.post_invariants, self.fieldPredMapping, fsm)
                max_count -= 1
                if max_count == 0:
                    break 
                candidates = fsm.determinise(pre_invariants=self.pre_invariants, post_invariants=self.post_invariants)

            if len(candidates) == 0:
                logging.warning("The final automata is a deterministic automata")
                # merge the leaf states
                if fsm.mergeLeafStates() is not None:
                    Construct(fields, self.pre_invariants, self.post_invariants, self.fieldPredMapping, fsm)
        
            return fsm 

        fsm = fair_shedule()
        return fsm 


    @property
    def fields(self):
        return list(self.fieldPredMapping.keys())
    
    def addTraces(self, trace_slice_file):
        self.traces = list()
        trace_slices = json.load(open(trace_slice_file, "r"))
        for trace_slice in trace_slices:
            trace = list()
            for index in range(len(trace_slice["event_trace"])):
                event = trace_slice["event_trace"][index]
                state = trace_slice["state_trace"][index]
                event_name = event["methodName"].split("(")[0]+"@"+"@".join([param["name"] for param  in event["parameters"]])
                state_predicates = []
                for item in state:  
                    field = item["name"]
                    value = item["value"]
                    new_field = field.replace("$", "_")
                    new_value = "\"\"" if value == "" else value if value is not None  else 0
                    state_predicates.append(f"{new_field} == {new_value}")
                if [event_name, state_predicates] in trace:
                    continue
                trace.append([event_name, state_predicates])
            self.traces.append(trace)

    def getTraces(self):
        return self.traces 

    def createBlueFringeMDL(self):
        method_traces =  [ [ method_post[0] for method_post in trace ]  for trace in self.traces]
        all_methods = set()
        [ all_methods.update(method_trace) for method_trace in method_traces ]
        with open(os.path.join(self.workdir, "method-traces.txt"), "w") as f:
                f.write("alphabet" + os.linesep)
                f.write(os.linesep.join(all_methods) + os.linesep)
                f.write("---------------------"+os.linesep)
                f.write("positive examples"+os.linesep)
                # for method_trace in method_traces:
                f.write(os.linesep.join([" ".join(method_trace) for method_trace in method_traces]))
        cmd  = f" cd {self.workdir}"
        cmd += f" && bash ./../../offlineLearn.sh ./"
        os.system(cmd)
        
    def Ktail(self, k: int):
        ktail = KTail()
        for trace in self.traces:
            trace = [item[0] for item in trace]
            ktail.add(trace)
        try:
            ktail.k_tails(k)
        except:
            traceback.print_exc()
            assert False
        ktail.visualize(k, self.workdir)


def main(workdir, address, contractName, invariant_file, slice_configuration_file, trace_slice_file):
    if not os.path.exists(os.path.join(workdir, address)):
        os.mkdir(os.path.join(workdir, address))

    slicer = InvariantSlice(slice_configuration=slice_configuration_file, invariant_file=invariant_file)
    invariant = slicer.get_invariant_slice()
    json.dump(invariant, open(os.path.join(workdir, address+"-"+contractName+"_" + "invariant-preprocessed.json"), "w"), indent=4)

    miner = ConMiner(workdir=workdir+"/"+address, contractName=contractName)
    miner.readPreProcessedSliceInvariant(invariant)
    miner.addTraces(trace_slice_file)

    miner.Ktail(0)
    miner.Ktail(1)
    miner.Ktail(2)
    # miner.createBlueFringeMDL()

    miner.enableZeroIntialState()
    fsm = miner.smcon()
    fsm.print(workdir=os.path.join(workdir, address))
    return True 

if __name__ == "__main__":
    workdir = sys.argv[1]
    address = sys.argv[2]
    contractName = sys.argv[3]
    invariant_file = sys.argv[4]
    slice_configuration_file = sys.argv[5]
    trace_slice_file = sys.argv[6]
    main(workdir, address, contractName, invariant_file, slice_configuration_file, trace_slice_file)