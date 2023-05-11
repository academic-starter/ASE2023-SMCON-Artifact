import json 
import itertools
import re 
ori_state_invariant_pattern = re.compile(r"^ori(.*)[==|!=|>|<|>=|<=]\s*[0-9]+")
ori_state_invariant_strpattern = re.compile(r"^ori(.*)[==|!=]\s*\"\"+")
ori_state_invariant_subpattern = re.compile(r"^ori(.*)\sone of\s(.*)")
state_invariant_pattern = re.compile(r"(.*)[==|!=|>|<|>=|<=]\s*[0-9]+")
state_invariant_strpattern = re.compile(r"(.*)[==|!=]\s*\"\"+")
state_invariant_subpattern = re.compile(r"(.*)\sone of\s(.*)")
class InvariantSlice:
    def __init__(self, slice_configuration, invariant_file) -> None:
        self.slice_configuration = json.load(open(slice_configuration))
        self.full_invariants = json.load(open(invariant_file))
    
    # TODO: Implement this
    def get_invariant_slice(self):
        invariant_slice = {}
        for slice_config in self.slice_configuration:
            func = slice_config["function"]
            invariant_slice[func] = []
            abstractTypes = slice_config["abstract-types"]
            params = slice_config["params"]
            state = slice_config["state"]
            parameterBindingCandiates = dict()
            for index in range(len(params)):
                param = params[index]
                abstractType = abstractTypes[index]
                if abstractType not in parameterBindingCandiates:
                    parameterBindingCandiates[abstractType] = []
                parameterBindingCandiates[abstractType].append(param)
            parameterBindings = itertools.product(*parameterBindingCandiates.values())
            uniqueAbstractTypes = list(parameterBindingCandiates.keys())

            for parameterBinding in parameterBindings:
                newState =  []
                for substate in state:
                    for index in range(len(uniqueAbstractTypes)):
                        substate = re.subn(uniqueAbstractTypes[index], parameterBinding[index], substate)[0]
                    newState.append(substate)
                invariant_slice[func].append(dict(parameterBinding = parameterBinding, oldstate = state, newState = newState))
        
        for func_invariant in self.full_invariants:
            func = func_invariant["func"]
            executionType = func_invariant["executionType"]
            if func is None:
                continue
            if executionType != "TxType.NORMAL":
                continue 
            short_func = func.split("(")[0]
            if short_func not in invariant_slice:
                continue

            if func.find("@")!=-1:
                current_parameterBinding = func.split("@")[1:]
           
            for slice_invariant in invariant_slice[short_func]:
                # Two functions with same short name but different parameters
                if "slice_pre" in slice_invariant and len(slice_invariant["slice_pre"])>0:
                    continue
                parameterBinding = slice_invariant["parameterBinding"]

                if func.find("@")!=-1:
                    if set(parameterBinding) != set(current_parameterBinding):
                        continue
                    
                newState = slice_invariant["newState"]
                oldState = slice_invariant["oldstate"]
                newPreConditions = []
                newPostConditions = []
                newStatePreConditions = []
                newStatePostConditions = []

                equivalentParameterBinding = dict()

                def getPureName(name):
                    indice = [item for item in re.findall("\[([\w|\.|\*]*)\]", name)]
                    pure_statevar = name 
                    for index in indice:
                        pure_statevar = pure_statevar.replace("["+index+"]", "")
                    return pure_statevar, indice

                def createPrePostConditions():
                    for predicate in func_invariant["preconditions"]:
                        for substate in newState:
                            if substate.find("sum")!=-1:
                                core = re.match(r"sum\((.*)\)", substate).group(1)
                                if re.match("\[([\w|\.|\*]*)\])", core):
                                    # apply to unprocessed invariants
                                    purename, indice = getPureName(core)
                                    assert indice.index("*") != -1
                                    for index in indice:
                                        core = core.replace("["+index+"]", "\["+index.replace(".", "\.").replace("*", ".*")+"\]")

                                    if re.search(core, predicate):
                                        predicate = re.subn(core, purename + "_sum" + str(indice.index("*") + 1) + "[" + list(filter(lambda index: index!="*", indice))[0] + "]", predicate)[0]
                                        newPreConditions.append(predicate)
                                        if state_invariant_pattern.match(predicate) is not None or state_invariant_subpattern.match(predicate) is not None or state_invariant_strpattern.match(predicate) is not None:
                                            newStatePreConditions.append(predicate)
                                else:
                                    # apply to pre-processed sliced invariants
                                    newPreConditions.append(predicate)
                                    if ori_state_invariant_pattern.match(predicate) is not None or ori_state_invariant_subpattern.match(predicate) is not None or ori_state_invariant_strpattern.match(predicate) is not None:
                                            newStatePreConditions.append(predicate)
    
                            else:
                                if predicate.find(substate)!=-1:
                                    predicate = predicate.replace(substate, oldState[newState.index(substate)])
                                    newPreConditions.append(predicate)
                                    if state_invariant_pattern.match(predicate) is not None or state_invariant_subpattern.match(predicate) is not None or state_invariant_strpattern.match(predicate) is not None:
                                        newStatePreConditions.append(predicate)
                                else:
                                    newPreConditions.append(predicate)
                                    if ori_state_invariant_pattern.match(predicate) is not None or ori_state_invariant_subpattern.match(predicate) is not None or ori_state_invariant_strpattern.match(predicate) is not None:
                                            newStatePreConditions.append(predicate)

                        for index in range(len(parameterBinding)):
                            m = re.match(parameterBinding[index] + r"\s*==\s*(.*)", predicate)
                            if m is not None:
                                if parameterBinding[index] not in equivalentParameterBinding:
                                    equivalentParameterBinding[parameterBinding[index]] = list()
                                equivalentParameterBinding[parameterBinding[index]].append(m.group(1))
                            else:
                                m = re.match(r"(.*)s*==\s*"+ parameterBinding[index] , predicate)
                                if m is not None:
                                    print(parameterBinding[index], predicate)
                                    if parameterBinding[index] not in equivalentParameterBinding:
                                        equivalentParameterBinding[parameterBinding[index]] = list()
                                    m2 =  re.match("ori\((.*)\)", m.group(1)) 
                                    if m2 is not None:
                                        equivalentParameterBinding[parameterBinding[index]].append(m2.group(1))
                                    else:
                                        equivalentParameterBinding[parameterBinding[index]].append(m.group(1))

                    for predicate in func_invariant["postconditions"]:
                        for substate in newState:
                            if substate.find("sum")!=-1:
                                if re.match(r"sum\((.*)\)", substate):
                                    core = re.match(r"sum\((.*)\)", substate).group(1)
                                    purename, indice = getPureName(core)
                                    assert indice.index("*") != -1
                                    for index in indice:
                                        core = core.replace("["+index+"]", "\["+index.replace(".", "\.").replace("*", ".*")+"\]")
                                    if re.search(core, predicate):
                                        predicate = re.subn(core, purename + "_sum" + str(indice.index("*") + 1) + "[" + list(filter(lambda index: index!="*", indice))[0] + "]", predicate)[0]
                                        newPostConditions.append(predicate)
                                        if state_invariant_pattern.match(predicate) is not None or state_invariant_subpattern.match(predicate) is not None or state_invariant_strpattern.match(predicate) is not None:
                                            newStatePostConditions.append(predicate)
                                else:
                                    newPostConditions.append(predicate)
                                    if state_invariant_pattern.match(predicate) is not None or state_invariant_subpattern.match(predicate) is not None or state_invariant_strpattern.match(predicate) is not None:
                                            newStatePostConditions.append(predicate)
                            else:
                                if predicate.find(substate)!=-1:
                                    predicate = predicate.replace(substate, oldState[newState.index(substate)])
                                    if predicate.find("ori")!=-1:
                                        continue
                                    newPostConditions.append(predicate)
                                    if state_invariant_pattern.match(predicate) is not None or state_invariant_subpattern.match(predicate) is not None or state_invariant_strpattern.match(predicate) is not None:
                                        newStatePostConditions.append(predicate)
                                else:
                                    newPostConditions.append(predicate)
                                    if state_invariant_pattern.match(predicate) is not None or state_invariant_subpattern.match(predicate) is not None or state_invariant_strpattern.match(predicate) is not None:
                                            newStatePostConditions.append(predicate)
                
                createPrePostConditions()

                if len(newPreConditions) == 0 and len(newPostConditions) == 0:
                    # print("No slice for " + func) according to the given parameter binding 
                    # try equivalent parameter binding
                    # create new states
                    _newStates = []
                    for substate in newState:
                        for oldbind in equivalentParameterBinding:
                            if substate.find(oldbind) != -1:
                                for newbind in equivalentParameterBinding[oldbind]:
                                    _newStates.append(substate.replace(oldbind, newbind))
                                    # keep only one equivalent parameter binding
                                    break 
                    # slice_invariant["newState"] = _newStates
                    newState = _newStates
                    createPrePostConditions()

                slice_invariant["preconditions"] = list(set(newPreConditions))
                slice_invariant["postconditions"] = list(set(newPostConditions))
                slice_invariant["slice_pre"] = list(set(newStatePreConditions))
                slice_invariant["slice_post"] = list(set(newStatePostConditions))
        
        return invariant_slice

if __name__ == "__main__":
    invariant_slice = InvariantSlice("./result/0x7e0178e1720e8b3a52086a23187947f35b6f3fc4-GameChannel-config.json", "./result/0x7e0178e1720e8b3a52086a23187947f35b6f3fc4-GameChannel-trace.inv.json")
    json.dump(invariant_slice.get_invariant_slice(), open("test.json", "w"), indent=4) 