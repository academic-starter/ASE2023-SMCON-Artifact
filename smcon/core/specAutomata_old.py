from hashlib import new
from itertools import combinations, permutations
import json
import traceback
from z3 import *
from itertools import product
from alive_progress import alive_bar
import re 
from visual_automata.fa.nfa import VisualNFA  

def getFieldPredicates(predset):
    fieldPredMapping = dict() 
    for pred in predset:
        if pred.find("==") != -1:
            if pred.split("==")[0].strip() not in fieldPredMapping:
                fieldPredMapping[pred.split("==")[0].strip()] = set()
            fieldPredMapping[pred.split("==")[0].strip()].add(pred)
        elif pred.find("!=") != -1:
            if pred.split("!=")[0].strip() not in fieldPredMapping:
                fieldPredMapping[pred.split("!=")[0].strip()] = set()
            fieldPredMapping[pred.split("!=")[0].strip()].add(pred)
        elif pred.find(">=") != -1:
            if pred.split(">=")[0].strip() not in fieldPredMapping:
                fieldPredMapping[pred.split(">=")[0].strip()] = set()
            fieldPredMapping[pred.split(">=")[0].strip()].add(pred)
        elif pred.find(">") != -1:
            if pred.split(">")[0].strip() not in fieldPredMapping:
                fieldPredMapping[pred.split(">")[0].strip()] = set()
            fieldPredMapping[pred.split(">")[0].strip()].add(pred)
        elif pred.find("<=") != -1:
            if pred.split("<=")[0].strip() not in fieldPredMapping:
                fieldPredMapping[pred.split("<=")[0].strip()] = set()
            fieldPredMapping[pred.split("<=")[0].strip()].add(pred)
        elif pred.find("<") != -1:
            if pred.split("<")[0].strip() not in fieldPredMapping:
                fieldPredMapping[pred.split("<")[0].strip()] = set()
            fieldPredMapping[pred.split("<")[0].strip()].add(pred)
        elif pred.find("one of") != -1:
            if pred.split("one of")[0].strip() not in fieldPredMapping:
                fieldPredMapping[pred.split("one of")[0].strip()] = set()
            fieldPredMapping[pred.split("one of")[0].strip()].add(pred)
        else:
            # print(pred)
            pass 
    return fieldPredMapping

def converStrtoNoEqual(itemstr):
    if itemstr == "\"\"":
        return "0"
    m2 =  re.compile("^(0x)*[0-9]+$").search(itemstr)
    if m2 is None:
        return "1"
    else:
        return itemstr

def translate2Z3expr(one_pred):
    if one_pred.find("one of") != -1:
        field = one_pred.split("one of")[0].strip()
        oneofranges = one_pred.split("[")[1].replace("\"","").split("]")[0].split(",")
        oneofranges = set([converStrtoNoEqual(value.strip()) for value in oneofranges])
        z3expr = "False"
        for val in oneofranges:
            z3expr = "Or("+z3expr + "," + f"{field} == {val}" + ")"  
        return z3expr 
    else:
        m = re.compile("^\w+\s+==\s+(.*)").search(one_pred)
        if m:
            itemstr =  m.groups()[0]
            newitemstr = converStrtoNoEqual(itemstr=itemstr)
            one_pred = one_pred.replace(itemstr, newitemstr)
        return one_pred

def translate2Z3exprFromPredSet(preds):
    z3expr = "True"
    for one_pred in preds:
        if isinstance(one_pred, str):
            z3expr = "And(" + z3expr + ","+ translate2Z3expr(one_pred)+")"
        elif isinstance(one_pred, list) or isinstance(one_pred, set) or isinstance(one_pred, tuple):
            z3expr = "And(" + z3expr + ","+ translate2Z3exprFromPredSet(one_pred)+")"
        else:
            assert False
    return z3expr

def SMT_Equilvlent(fieldorfileds, pred1, pred2):
    if isinstance(fieldorfileds, str):
        exec(f'{fieldorfileds} = Int("{fieldorfileds}")')
    elif isinstance(fieldorfileds, list) or isinstance(fieldorfileds, set) or isinstance(fieldorfileds, tuple):
        for field in fieldorfileds:
            exec(f'{field} = Int("{field}")')
    else:
        assert False

    exec(f's = Solver()')
    pred1 = translate2Z3expr(one_pred=pred1)
    pred2 = translate2Z3expr(one_pred=pred2)
    
    neg = f"({pred1})!=({pred2})"
    eval(f's.add({neg})')
    return eval(f"s.check()") == unsat 

def SMT_EquilvlentTwoPredicateSets(fieldorfileds, preds1, preds2):
    if isinstance(fieldorfileds, str):
        exec(f'{fieldorfileds} = Int("{fieldorfileds}")')
    elif isinstance(fieldorfileds, list) or isinstance(fieldorfileds, set) or isinstance(fieldorfileds, tuple):
        for field in fieldorfileds:
            exec(f'{field} = Int("{field}")')
    else:
        assert False
    exec(f's = Solver()')
    pred1 = translate2Z3exprFromPredSet(preds=preds1)
    pred2 = translate2Z3exprFromPredSet(preds=preds2)
    
    neg = f"({pred1})!=({pred2})"
    eval(f's.add({neg})')
    return eval(f"s.check()") == unsat 

def SMT_ImplyTwoPredicateSets(fieldorfileds, preds1, preds2):
    if isinstance(fieldorfileds, str):
        exec(f'{fieldorfileds} = Int("{fieldorfileds}")')
    elif isinstance(fieldorfileds, list) or isinstance(fieldorfileds, set) or isinstance(fieldorfileds, tuple):
        for field in fieldorfileds:
            exec(f'{field} = Int("{field}")')
    else:
        assert False
    exec(f's = Solver()')
    pred1 = translate2Z3exprFromPredSet(preds=preds1)
    pred2 = translate2Z3exprFromPredSet(preds=preds2)
    
    imply_property = f"And(({pred1}), Not({pred2}))"
    # print(imply_property)
    # eval(f's.add({pred1})')
    eval(f's.add({imply_property})')
    ret =  eval(f"s.check()") == unsat 
    eval(f"s.reset()")
    return ret 


def SMT_SAT_2(fieldorfileds, state, preds):
    if isinstance(fieldorfileds, str):
        exec(f'{fieldorfileds} = Int("{fieldorfileds}")')
    elif isinstance(fieldorfileds, list) or isinstance(fieldorfileds, set) or isinstance(fieldorfileds, tuple):
        for field in fieldorfileds:
            exec(f'{field} = Int("{field}")')
    else:
        assert False
    exec(f's = Solver()')
    for one_pred in preds:
        try:
            if isinstance(one_pred, str):
                one_pred = translate2Z3expr(one_pred=one_pred)
            elif isinstance(one_pred,list) or isinstance(one_pred, set) or isinstance(one_pred, tuple):
                one_pred = translate2Z3exprFromPredSet(preds=one_pred)
            else:
                assert False 
            eval(f's.add({one_pred})')
            eval(f's.add({state})')
        except Exception as e:
            print(one_pred)
            print(e)
            traceback.print_exc()
            assert False
    ret =  eval(f"s.check()") == sat 
    eval(f"s.reset()")
    return ret 

def SMT_SAT(fieldorfileds, preds):
    if isinstance(fieldorfileds, str):
        exec(f'{fieldorfileds} = Int("{fieldorfileds}")')
    elif isinstance(fieldorfileds, list) or isinstance(fieldorfileds, set) or isinstance(fieldorfileds, tuple):
        for field in fieldorfileds:
            exec(f'{field} = Int("{field}")')
    else:
        assert False
    exec(f's = Solver()')
    if isinstance(preds, str):
        eval(f's.add({preds})')
    elif isinstance(preds, (list, set, tuple)):
        for one_pred in preds:
            try:
                if isinstance(one_pred, str):
                    one_pred = translate2Z3expr(one_pred=one_pred)
                elif isinstance(one_pred,list) or isinstance(one_pred, set) or isinstance(one_pred, tuple):
                    one_pred = translate2Z3exprFromPredSet(preds=one_pred)
                else:
                    assert False 
                eval(f's.add({one_pred})')
            except Exception as e:
                print(one_pred)
                print(preds)
                raise e
    else:
        print(one_pred)
        print(preds)
        raise Exception("Unrecognized predicates")
    ret =  eval(f"s.check()") == sat 
    eval(f"s.reset()")
    return ret 

def removeAllEquilvlent(field, predicates):
    pred_combs = combinations(predicates, 2)
    for combs in pred_combs:
        pred1, pred2 = combs[0], combs[1]
        if SMT_EquilvlentTwoPredicateSets(fieldorfileds=field, preds1=[pred1], preds2=[pred2]):
                if len(pred1) > len(pred2):
                    predicates.discard(pred1)
                else:
                    predicates.discard(pred2)
    return predicates



def getCombinationsFromSameFieldPreds(field, fieldPredMapping):
    # global fieldPredMapping
    predicates = copy.deepcopy(fieldPredMapping[field])
    while True:
        if len(predicates)>=2:
            pred_combs = combinations(predicates, 2)
            Flag = True 
            for combs in pred_combs:
                pred1, pred2 = combs[0], combs[1]
                if SMT_ImplyTwoPredicateSets(fieldorfileds=field, preds1=[pred1], preds2=[pred2]):
                    predicates.discard(pred2)
                    expr1 = translate2Z3expr(pred1)
                    expr2 = translate2Z3expr(pred2)
                    predicates.add(f"And({expr2}, Not({expr1}))") 
                    Flag = False 
                    predicates = removeAllEquilvlent(field, predicates)
                    break  
                if SMT_ImplyTwoPredicateSets(fieldorfileds=field, preds1=[pred2], preds2=[pred1]):
                    predicates.discard(pred1)
                    expr1 = translate2Z3expr(pred1)
                    expr2 = translate2Z3expr(pred2)
                    predicates.add(f"And({expr1}, Not({expr2}))") 
                    Flag = False 
                    predicates = removeAllEquilvlent(field, predicates)
                    break
            if Flag:
                break 
        else:
            break 

    return predicates, []

def getPartitionsFromSameFieldPreds(field, fieldPredMapping):
    # global fieldPredMapping
    predicates = copy.deepcopy(fieldPredMapping[field])
    
    domainz3expr = "False"
    for pred in predicates:
        domainz3expr = "Or("+ domainz3expr + "," + translate2Z3expr(pred) + ")"

    partitions = []

    if len(predicates)>=2:
        pred_combs = combinations(predicates, 2)
        for combs in pred_combs:
            pred1, pred2 = combs[0], combs[1]
            z3expr1 = translate2Z3expr(pred1)
            z3expr2 = translate2Z3expr(pred2)
            if not SMT_SAT(fieldorfileds=field, preds=[pred1, pred2]) and  \
            SMT_Equilvlent(field, f"Or({z3expr1}, {z3expr2})", domainz3expr):
                # pred1 and pred2 is a partition of domain 
                partitions.append((pred1, pred2))
    else:
        pass  
    
    if len(partitions) == 0:
        partitions.append(tuple([domainz3expr]))

    return partitions

def getAllPartitionCombinations(fieldPredMapping):
    partitioncombinations = set()
    for field in fieldPredMapping.keys():
        partitions = getPartitionsFromSameFieldPreds(field, fieldPredMapping=fieldPredMapping)
        print(len(partitions), partitions)
        if len(partitioncombinations) == 0:
            partitioncombinations = partitions[0]
        else:
            partitioncombinations = set(product(partitioncombinations, partitions[0]))
    return partitioncombinations

def getCrossFieldCombinations(fieldPredMapping):
    cross_field_combinations = set()
    for field in fieldPredMapping.keys():
        feasible_candidates, unfeasible_candidates = getCombinationsFromSameFieldPreds(field, fieldPredMapping=fieldPredMapping)
        print(len(feasible_candidates), feasible_candidates)
        if len(cross_field_combinations) > 0:
            cross_field_combinations = set(product(cross_field_combinations, feasible_candidates))
        else:
            cross_field_combinations.update(feasible_candidates)
    return cross_field_combinations





AllStatetraces = []
class Automata:
    printCount = 0
    def __init__(self) -> None:
        self.reset()
    
    def reset(self):
        self.dummpyStates = set()
        self.states = set()
        self.labels = set()
        self.transitions =  dict()
        self.enable_states = set()
        
        self.statespre = dict()
        self.statespost = dict()

    def addState(self, state):
        self.states.add(state) 

    def removeLabel(self, label):
        self.labels.discard(label)
        for from_state in self.transitions:
            if label in list(self.transitions[from_state].keys()): 
                self.transitions[from_state].pop(label, None)

    def removeTransition(self, from_state, label, to_state):
        self.transitions[from_state][label].discard(to_state)
        if len(self.transitions[from_state][label]) == 0:
            self.transitions[from_state].pop(label, None)

    def addLabel(self, label):
        self.labels.add(label)

    def addIntialState(self, state):
        self.states.add(state)
        self.initialState = state 
        self.enable_states.add(self.initialState)
        self.states = list(self.states)

    def promoteTransitionMaybeToRequireByTrace(self, fields, trace, currentState, statetraces = None):
        global AllStatetraces
        self.enable_states.add(currentState)
        states = self.states
        if statetraces is None:
            statetraces = []
            statetraces.append(states.index(self.initialState))
        if len(trace) == 0:
            AllStatetraces.append(statetraces)
            return True
        method, posts = trace[0]
        # statetraces.append(states.index(currentState))
        if currentState in self.transitions:
            if  method in self.transitions[currentState]:
                for require_item in self.transitions[currentState][method]:
                    nextState = require_item[0]
                    preds = set(posts)

                    if isinstance(nextState, str):
                        preds.add(nextState)
                    elif isinstance(nextState, list) or isinstance(nextState, set) or isinstance(nextState, tuple):
                        preds.update(nextState)
                    else:
                        assert False

                    if SMT_SAT(fieldorfileds=fields, preds = preds):
                        statetraces.append(method)
                        statetraces.append(str(states.index(nextState)))
                        if self.promoteTransitionMaybeToRequireByTrace(fields, trace[1:], nextState, statetraces=copy.deepcopy(statetraces)):
                            require_item[1] = True 
                            return True 
                    else:
                        continue
            else:
                return False
        else:
            print(trace)
            print("not found method:")
            print(method)
            print(os.linesep)
            assert False
            # return False
        return True
    
    def clearAllMaybeTransition(self, optimaticFlag = True ):
        remove_num  = 0
        for from_state in self.transitions:
            emptyset = set()
            for method in self.transitions[from_state]:
                nextstates = self.transitions[from_state][method] 
                newnextstates = [ nextstate for nextstate in nextstates if nextstate[1] == True ]
                remove_num += len(nextstates) -  len(newnextstates)
                if len(newnextstates) == 0:
                    emptyset.add(method)
                else:
                    self.transitions[from_state][method] = newnextstates
            if optimaticFlag:
                if from_state not in self.enable_states:
                    for method in emptyset:
                        self.transitions[from_state].pop(method, None )
            else:
                for method in emptyset:
                    self.transitions[from_state].pop(method, None )
        print(f"remove transitions: {remove_num}")

    def addTransition(self, from_state, label, to_state, require=False):
        assert from_state in self.states
        assert to_state  in self.states
        # assert label in self.labels
        self.labels.add(label)

        if from_state not in self.transitions:
            self.transitions[from_state] = dict()
        
        if label not in self.transitions[from_state]:
            self.transitions[from_state][label] = list()
        
        self.transitions[from_state][label].append([to_state, require])

        if to_state not in self.statespre:
            self.statespre[to_state] = set()
        if to_state != from_state:
            self.statespre[to_state].add(label)
        
        if from_state not in self.statespost:
            self.statespost[from_state] = set()
        self.statespost[from_state].add(label)

    def print(self, workdir):
        self.visualize(workdir)
        Automata.printCount += 1

    def visualize(self, workdir):
          
        # assert len(self.states) > 1 
        states = set()
        labels = set()
        string_transitions = dict()
        for from_state in self.transitions:
            if self.states.index(from_state) not in string_transitions:
                string_transitions[str(self.states.index(from_state))] =  dict() 
            for label in self.transitions[from_state]:
                for to_state in self.transitions[from_state][label]:
                    states.add(str(self.states.index(from_state)))
                    states.add(str(self.states.index(to_state[0])))
                    req_label = str(label)+str("-T" if to_state[1] else "-F")
                    # req_label = str(label)
                    labels.add(req_label)
                    if req_label not in string_transitions[str(self.states.index(from_state))]:
                        string_transitions[str(self.states.index(from_state))][req_label] = set() 
                    string_transitions[str(self.states.index(from_state))][req_label].add(str(self.states.index(to_state[0])))
        for from_state in string_transitions:
            for label in string_transitions[from_state]:
                string_transitions[from_state][label] = list(string_transitions[from_state][label])

        initialState = str(self.states.index(self.initialState))
        nfa = VisualNFA(
            states= states,
            input_symbols= labels,
            transitions= string_transitions,
            initial_state = initialState,
            final_states = set(),
        )
        
        nfa.show_diagram(filename = f"{workdir}/FSM-{Automata.printCount}.dot", view=False, format_type="pdf")

        # total_transitions_length =  sum([ len(string_transitions[key][method]) \
        #     for key in string_transitions.keys()  for method in string_transitions[key]])
        # total_states_length = len(states)
        result = {
            # "total_transitions_length":total_transitions_length,
            # "total_states_length": total_states_length,
            "states": self.states,
            "statemachine":string_transitions,
            "initialState":initialState
        }
        json.dump(result, open(f"{workdir}/FSM-{Automata.printCount}.json", "w"))


from multiprocessing import Pool
    
def parrellel_checking(method, post_invariants, fields, targetState):
    posts = set(post_invariants[method])
    posts.add(targetState)
    return SMT_SAT(fieldorfileds=fields, preds = posts)

def GenerateInvariantMTS(all_pred_combiantions, pre_invariants, post_invariants, initState, fieldPredMapping):
    fields = list(fieldPredMapping.keys())
    FSM = Automata()  
    toProcess = list()
    isProcessed = list() 
    for combination in all_pred_combiantions:
        FSM.addState(combination)
    FSM.addIntialState(initState)
    toProcess.append(initState)
    while len(toProcess) > 0:
        currentState = toProcess.pop()
        isProcessed.append(currentState)
        with alive_bar(len(list(pre_invariants.keys())), force_tty=True) as bar:
            for method in pre_invariants.keys():
                    assert isinstance(pre_invariants[method], list) or isinstance(pre_invariants[method], set) or isinstance(pre_invariants[method], tuple)
                    pres = set(pre_invariants[method])
                    pres.add(currentState)
                    if SMT_SAT(fieldorfileds=fields, preds=pres):
                        try:
                            with Pool() as p:
                                listStates = list(FSM.states)
                                sat_results = p.starmap(parrellel_checking, zip([method]*len(listStates), [post_invariants]*len(listStates), [fields]*len(listStates), listStates))
                                for i in range(len(sat_results)):
                                    if sat_results[i] == True:
                                        if listStates[i] not in isProcessed and listStates[i] not in toProcess:
                                            toProcess.append(listStates[i])
                                        FSM.addTransition(currentState, method, listStates[i]) 
                        except Exception as e:
                            traceback.print_exc()
                            raise e 
                            
                    bar()
    FSM.states = list(set(isProcessed))
    return FSM

def filterPredicates(fields, posts):
    new_posts = set()
    for field in fields:
        for post in posts:
            if post.find(field)!=-1:
                new_posts.add(post)
    return new_posts

def SplitState2RemovePath(sourceState, pre_method_post_invariant, post_method_pre_invariant):
    pred1 = translate2Z3exprFromPredSet(pre_method_post_invariant)
    pred2 = translate2Z3exprFromPredSet(post_method_pre_invariant)
    # state1 = f"And({sourceState}, And(Not({pred2}), Not({pred1})))"
    # state2 = f"And({sourceState}, And(And({pred2}), Not({pred1})))"
    # state3 = f"And({sourceState}, And(Not({pred2}), And({pred1})))"
    state1 = f"And({sourceState}, Not({pred2}))"
    state2 = f"And({sourceState}, {pred2})"
    return state1, state2

def parallel_check_methodAB(state, fieldorfileds, methodAB, pre_invariants, post_invariants):
    return SMT_SAT_2(fieldorfileds=fieldorfileds, state=state, preds=set(post_invariants[methodAB[0]]).union(pre_invariants[methodAB[1]]))  

def refineFSMState(fsm: Automata, fields, pre_invariants :dict, post_invariants: dict):
    print("refineFSMState")
    all_states = set(copy.deepcopy(fsm.states))
    for state in all_states:
        if state not in fsm.transitions:
            continue
        if state in fsm.statespre and state in fsm.statespost:
                with Pool() as pool:
                    methodABs = list(product(set(fsm.statespre[state]), set(fsm.statespost[state])))
                    results: list = pool.starmap(parallel_check_methodAB, zip( [state]*len(methodABs), [fields]*len(methodABs), methodABs, [pre_invariants]*len(methodABs), [post_invariants]*len(methodABs))) 
                    no = results.count(False)
                    if no != 0:
                        index = results.index(False)
                        methodA, methodB = methodABs[index][0], methodABs[index][1]
                        print(methodA, methodB)
                        state1, state2 = SplitState2RemovePath(state, pre_method_post_invariant=post_invariants[methodA], post_method_pre_invariant=pre_invariants[methodB])
                        all_states.remove(state)
                        if state1 is not None:
                            all_states.add(state1)
                        if state2 is not None:
                            all_states.add(state2)
                        break 
               
    return all_states


def SplitState2TwoToRemovePath(sourceState, methodA_post_invariant, methodB_post_invariant):
    pred1 = translate2Z3exprFromPredSet(methodA_post_invariant)
    pred2 = translate2Z3exprFromPredSet(methodB_post_invariant)
    state1 = f"And({sourceState}, And(Not({pred2}), Not({pred1})))"
    state2 = f"And({sourceState}, And({pred2}, Not({pred1})))"
    state3 = f"And({sourceState}, And(Not({pred2}), And({pred1})))"
    state4 = f"And({sourceState}, And({pred2}, {pred1}))"
    return state1, state2, state3, state4

def checkSpuriousPath(fsm: Automata, fields, pre_invariants, post_invariants):
    global AllStatetraces
    print("checkSpuriousPath")
    all_states = set(copy.deepcopy(fsm.states))
    def findSuffixStrSet(index_method):
        prefixs = set()
        for traces in AllStatetraces:
            if " ".join(map(str, traces)).find(" ".join(map(str, index_method)))!=-1:
                prefixs.add(" ".join(map(str, traces)).split(" ".join(map(str, index_method)))[-1])
        return prefixs 
    for state in fsm.states:
        # if state in fsm.statespre and state in fsm.statespost:
            # the state node is not a leaf node. 
            # the state has incoming and outcoming transitions.
            index = fsm.states.index(state)
            incomingmethods = list(set([ method for from_state in fsm.transitions for method in fsm.transitions[from_state] if state in [item[0] for item in fsm.transitions[from_state][method]] ]))
            # print(incomingmethods)
            for com in combinations(zip(incomingmethods, len(incomingmethods)*[index]), 2):
                index_methodA, index_methodB = com 
                prefixs_A = findSuffixStrSet(index_methodA)
                prefixs_B = findSuffixStrSet(index_methodB)
                if prefixs_A !=  prefixs_B:
                    print(index_methodA, index_methodB)
                    # there is a spurious path at `state`
                    # split `state` into four states to break the tie
                    methodA_post_invariant = post_invariants[index_methodA[0]]
                    methodB_post_invariant = post_invariants[index_methodB[0]]
                    state1, state2, state3, state4 = SplitState2TwoToRemovePath(sourceState = state, methodA_post_invariant=methodA_post_invariant, methodB_post_invariant=methodB_post_invariant) 
                    
                    # if SMT_Equilvlent(fieldorfileds=fields, pred1=state, pred2=state4):
                    if False:
                        # fsm.dummpyStates.add(("dummy", copy.deepcopy(state)))
                        # dummyState = f"And(True, {copy.deepcopy(state)})"
                        # fsm.dummpyStates.add(dummyState)
                        # transition_to_replace = list(set([ method for from_state in fsm.transitions for method in fsm.transitions[from_state] if state in [item[0] for item in fsm.transitions[from_state][method]] ]))
                        continue 
                    else:
                        all_states.discard(state)
                        if SMT_SAT(fieldorfileds=fields, preds=state1):
                            all_states.add(state1)
                        else:
                            print("fail")
                        if SMT_SAT(fieldorfileds=fields, preds=state2):
                            all_states.add(state2)
                        else:
                            print("fail")
                        if SMT_SAT(fieldorfileds=fields, preds=state3):
                            all_states.add(state3)
                        else:
                            print("fail")
                        if SMT_SAT(fieldorfileds=fields, preds=state4):
                            all_states.add(state4)
                        else:
                            print("fail")
                    
                        break 
                    # return all_states
    return all_states

def visitFSM(fsm: Automata, traces, fields):
    global AllStatetraces
    print("checkSpuriousTransition")
    for trace in traces:
        try:
            fsm.promoteTransitionMaybeToRequireByTrace(fields, trace[0:], fsm.initialState)
        except:
            traceback.print_exc()
            print(trace)
            assert False
            # print(traces[0])
            exit(0)
    # allstraces = set([ tuple(statetraces) for statetraces in AllStatetraces])
    # for statetrace in allstraces:
    #     print(statetrace)
    fsm.clearAllMaybeTransition(optimaticFlag=False)
    return fsm 