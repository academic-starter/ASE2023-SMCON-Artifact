from hashlib import new
from itertools import combinations, permutations
import json
import traceback
from z3 import *
from itertools import product
from alive_progress import alive_bar
import re 
from visual_automata.fa.nfa import VisualNFA  
from multiprocessing import Pool
import logging
    
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
            assert False, f"predicates format error {pred}"
            pass 
    return fieldPredMapping

def converStrtoNoEqual(itemstr):
    if itemstr == "\"\"":
        return "0"
    if isinstance(itemstr, str) and itemstr.startswith("0x") and int(itemstr[2:], base=16) == 0:
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
            try:
                exec(f'{field} = Int("{field}")')
            except:
                print(f'{field} = Int("{field}")')
                raise Exception("Unrecognized predicates")
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


def parrellel_checking(method, post_invariants, fields, targetState):
    posts = set(post_invariants[method])
    posts.add(targetState)
    return SMT_SAT(fieldorfileds=fields, preds = posts)




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

class Automata:
    printCount = 0
    def __init__(self) -> None:
        self.reset()
    
    def reset(self):
        self.dummpyStates = set()
        self.states = list()
        self.labels = set()
        self.transitions =  dict()
        self.enable_states = set()
        
        self.statespre = dict()
        self.statespost = dict()

        self.recorded_all_state_traces = []

    def addState(self, state):
        if state not in self.states:
            self.states.append(state)

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
        self.addState(state)
        self.initialState = state 
        self.enable_states.add(self.initialState)

    def promoteTransitionMaybeToRequireByTrace(self, fields, trace, currentState, statetraces = None):
        self.enable_states.add(currentState)
        states = self.states
        if statetraces is None:
            statetraces = []
            statetraces.append(states.index(self.initialState))
        if len(trace) == 0:
            self.recorded_all_state_traces.append(statetraces)
            return True
        
        method, posts = trace[0] 
        if currentState in self.transitions:
                if method not in self.transitions[currentState]:
                    raise Exception(f"method {method} is not in the transitions of state {currentState}, invalid trace")
                for require_item in self.transitions[currentState][method]:
                    nextState = require_item[0]
                    requireFlag =  require_item[1]

                    preds = set(posts)
                    for pred in copy.copy(preds):
                        if pred.split(" ")[0].strip() not in fields:
                            preds.remove(pred)
                            trace[0][1].remove(pred) 

                    if isinstance(nextState, str):
                        preds.add(nextState)
                    elif isinstance(nextState, list) or isinstance(nextState, set) or isinstance(nextState, tuple):
                        preds.update(nextState)
                    else:
                        assert False

                    # check if the the variable of predicate is in the fields
                    # if not, then the predicate is not related to the fields
                    
                    statetraces.append(method)
                    statetraces.append(str(states.index(nextState)))
                    require_item[1] = True 
                    self.promoteTransitionMaybeToRequireByTrace(fields, trace[1:], nextState, statetraces=copy.deepcopy(statetraces))
        return True          

    def setEventTraces(self, traces):
        self.event_traces = traces 

    def determinise(self, pre_invariants, post_invariants):
        isDeterminstic = True
        for from_state in self.transitions:
            for label in self.transitions[from_state]:
                pre_condition =  pre_invariants[label]
                post_condition = post_invariants[label]
                items = self.transitions[from_state][label]
                if len(items) > 1:
                    # non-deterministic behaviour 
                    # determinise it
                    q = translate2Z3exprFromPredSet(post_condition)
                    sub_state = "False"
                    for item in items:
                        if item[0] == self.initialState:
                            continue
                        sub_state = f"Or({sub_state}, {item[0]})"
                    new_q =  f"And({q}, {sub_state})"
                    self.addState(new_q)

                    for item in items:
                        if item[0] == self.initialState:
                            continue 
                        self.states.remove(item[0])
                        item[0] = f"And({item[0]},Not({new_q}))"
                        self.addState(item[0])
                    isDeterminstic = False
                    return isDeterminstic 
        return isDeterminstic

    def generate(self, pre_invariants, post_invariants, fieldPredMapping):
        def myf():
            fields = list(fieldPredMapping.keys())
            toProcess = list()
            isProcessed = list() 
            all_state_candidates = self.states 
            candidates_size = len(all_state_candidates)
            toProcess.append(self.initialState)

            self.transitions = dict()

            while len(toProcess) > 0:
                currentState = toProcess.pop()
                isProcessed.append(currentState)
                with alive_bar(len(list(pre_invariants.keys())), force_tty=True) as bar:
                    for method in pre_invariants.keys():
                        pre_condition = pre_invariants[method]
                        assert isinstance(pre_condition, list) or isinstance(pre_condition, set) or isinstance(pre_condition, tuple)

                        pres = set(pre_condition)
                        pres.add(currentState)

                        if SMT_SAT(fieldorfileds=fields, preds=pres):
                            try:
                                with Pool() as p:
                                    sat_results = p.starmap(parrellel_checking, zip([method]*candidates_size, [post_invariants]*candidates_size, [fields]*candidates_size, all_state_candidates))
                                    for i in range(len(sat_results)):
                                        if sat_results[i] == True:
                                            nextState = all_state_candidates[i]
                                            if nextState not in isProcessed and nextState not in toProcess:
                                                toProcess.append(nextState)
                                            self.addTransition(currentState, method, nextState) 
                                            assert nextState in self.states
                            except Exception as e:
                                traceback.print_exc()
                                raise e       
                        bar()
        myf() 
        max_count = 5 
        while max_count > 0: 
            if not self.determinise(pre_invariants=pre_invariants, post_invariants=post_invariants):
                max_count -= 1
                myf()
            else:
                break 

        return self 

    def visitFSM(self, fields):
        print("enable transitions of FSM")
        self.recorded_all_state_traces = []
        # reset all transitions to be not visited
        for fromState in self.transitions:
            for label in self.transitions[fromState]:
                for item in self.transitions[fromState][label]:
                    item[1] = False
        for trace in self.event_traces:
            try:
                self.promoteTransitionMaybeToRequireByTrace(fields, trace[0:], self.initialState)
            except Exception as e:
                logging.error(e)
                logging.error(f"trace {trace} is not valid")
        return self 
    
    def checkSpuriousPath(self):
        def checkLoop(state_trace, q_n, t_n_1):
            q_n_index = self.states.index(q_n)
            count = 0 
            for i in range(len(state_trace)):
                if state_trace[i] == q_n_index and state_trace[i+1] == t_n_1:
                    count += 1
            if count > 1:
                return True
            return False
        
        for state_trace in self.recorded_all_state_traces:
            q_n = self.states[int(state_trace[-1])]
            if q_n not in self.transitions:
                continue
            for t_n_1 in self.transitions[q_n]:
                for item in self.transitions[q_n][t_n_1]:
                    q_n_1 = item[0]
                    requireFlag = item[1]
                    if requireFlag == False:
                        return q_n, t_n_1
                    else:
                        if checkLoop(state_trace, q_n_1, t_n_1):
                            continue
                        else:
                            return q_n, t_n_1
        return None, None

    def splitAndRemove(self, q_n, t_n_1, fields,  pre_invariants, post_invariants):
        g_m_invs = pre_invariants[t_n_1]
        u_m_invs = post_invariants[t_n_1]

        g_m = translate2Z3exprFromPredSet(g_m_invs)
        hat_q_1 = f"And({q_n}, {g_m})"
        hat_q_2 = f"And({q_n}, Not({g_m}))" 

        requireFlag =  all([ not item[1] for item in self.transitions[q_n][t_n_1]]) 
        if requireFlag == True:
            # t_n_1 is an unreachable transition
            self.transitions[q_n].pop(t_n_1, None) 

        elif SMT_SAT(fieldorfileds=fields, preds=hat_q_1) and SMT_SAT(fieldorfileds=fields, preds=hat_q_2):
            self.states.remove(q_n)
            self.addState(hat_q_1)
            self.addState(hat_q_2)
            del self.transitions[q_n]
            new_transitions = copy.deepcopy(self.transitions)
            for from_state in self.transitions:
                for method in self.transitions[from_state]:
                    for item in self.transitions[from_state][method]:
                        if item[0] == q_n:
                            new_transitions[from_state][method].remove(item)
                    if len(new_transitions[from_state][method]) == 0:
                        new_transitions[from_state].pop(method, None)
                if new_transitions[from_state] == {}:
                    new_transitions.pop(from_state, None)
            self.transitions =  new_transitions
        
        else:
            # pick any pi_n
            for state_trace in self.recorded_all_state_traces:
                for i in range(len(state_trace)):
                    if state_trace[i] == q_n:
                        assert i > 1 
                        event = self.event_traces[int(i/2)-1]
                        method, posts = event
                        Pred = translate2Z3exprFromPredSet(posts)
                        OnePred = f"And({q_n}, {Pred})"
                        OtherPred =  f"And({q_n}, Not({Pred}))"
                        self.states.remove(q_n)
                        self.addState(OnePred)
                        self.addState(OtherPred)
                        del self.transitions[q_n]
                        new_transitions = copy.deepcopy(self.transitions)
                        for from_state in self.transitions:
                            for method in self.transitions[from_state]:
                                for item in self.transitions[from_state][method]:
                                    if item[0] == q_n:
                                        new_transitions[from_state][method].remove(item)
                                if len(new_transitions[from_state][method]) == 0:
                                    new_transitions[from_state].pop(method, None)
                            if new_transitions[from_state] == {}:
                                new_transitions.pop(from_state, None)
                        self.transitions =  new_transitions
        return self 
        


    def clearAllMaybeTransition(self):
        remove_num = 0
        new_transitions = copy.deepcopy(self.transitions)
        for from_state in self.transitions:
            for method in self.transitions[from_state]:
                for item in self.transitions[from_state][method]:
                    if item[1] == False:
                        remove_num += 1
                        new_transitions[from_state][method].remove(item)
                if len(new_transitions[from_state][method]) == 0:
                    new_transitions[from_state].pop(method, None)
            if len(new_transitions[from_state]) == 0:
                new_transitions.pop(from_state, None)
        self.transitions = new_transitions
        hitStates =  set()
        for from_state in self.transitions:
            for method in self.transitions[from_state]:
                for item in self.transitions[from_state][method]:
                    hitStates.add(item[0])
                    hitStates.add(from_state)
        # assert len(hitStates) == len(self.states)
        discarded_states =  list(set(self.states) - set(hitStates))
        print(f"remove transitions: {remove_num}")
        print(f"remove states: {len(discarded_states)}")
        return discarded_states

    def addTransition(self, from_state, label, to_state, require=False):
        assert from_state in self.states
        assert to_state  in self.states
        self.labels.add(label)

        if from_state not in self.transitions:
            self.transitions[from_state] = dict()
        
        if label not in self.transitions[from_state]:
            self.transitions[from_state][label] = list()
        
        if any([ item[0] == to_state for item in self.transitions[from_state][label] ]) == False:
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
        assert len(self.states) > 1 
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