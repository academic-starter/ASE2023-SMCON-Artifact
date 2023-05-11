from distutils.filelist import translate_pattern
import re
import glob 
import os 

Equidity_pairs = dict()
Constants = dict()
def parseEquidityInvariant(invariant: str):
    m = re.compile("^(.*)\s+(==)\s+orig\((.*)\)").search(invariant)
    if m is not None:
        result =  m.groups()
        if result[0] is not None and result[0] == result[2]:
            return {
                result[0]: result[2],
                result[2]: result[0]
            }
        else:
            return None 
    else:
        return None

def parseMsgSenderInvariant(invariant: str):
    m = re.compile("^(orig)*(.*)\s+(==|!=)\s+orig\((msg.sender)\)").search(invariant)
    if m is not None:
        ret  =  m.groups()
        if ret[1]!=ret[3]:
            return ret 
        else:
            return None
    else:
        return None

def revert_op(op: str):
    pre_op = op 
    if op == "==":
        post_op =  op 
    elif op == "!=":
        post_op =  op 
    elif op==">":
        post_op =  "<"
    elif op==">=":
        post_op =  "<="
    elif op == "<=":
        post_op =  ">="
    elif op == "<":
        post_op =  ">"
    else:
        assert False, op 
    assert not (pre_op == "<=" and post_op == ">")
    return post_op

def replace_constant_variables(invariant):
    global Constants
    p1 = re.compile("^(orig)*(.*)\s+(>=|>|==|!=|<|<=)\s+(orig)*(.*)")
    m = p1.search(invariant)
    if m:
        # exit(0)
        ret = m.groups() 
        orig_left, left, op, orig_right, right = ret
        constant_p  = re.compile("[0-9]+|true|false")
        if constant_p.search(left) is None and constant_p.search(right) is None:
                if orig_left == "orig" and f"{orig_left}{left}" in Constants:
                    constant = Constants[f"{orig_left}{left}"]
                    if orig_right == "orig":
                        invariant = orig_right + right +  " "+ revert_op(op) + " " + constant
                    else:
                        invariant = right +  " "+ revert_op(op) + " " + constant
                elif orig_left != "orig" and f"{left}" in Constants:
                    constant = Constants[f"{left}"]
                    if orig_right == "orig":
                        invariant = orig_right + right +  " "+ revert_op(op) + " " + constant
                    else:
                        invariant = right +  " "+ revert_op(op) + " " + constant
                elif orig_right == "orig" and f"{orig_right}{right}" in Constants:
                        constant = Constants[f"{orig_right}{right}"]
                        if orig_left == "orig":
                            invariant = orig_left + left +  " "+ op + " " + constant
                        else:
                            invariant = left +  " "+ op + " " + constant
                elif orig_right != "orig" and f"{right}" in Constants:
                        constant = Constants[f"{right}"]
                        if orig_left == "orig":
                            invariant = orig_left + left +  " "+ op + " " + constant
                        else:
                            invariant = left +  " "+ op + " " + constant
                else:
                    pass 
        # if pre_invariant.find("this.value")!=-1:
        #     print(pre_invariant, ret, invariant)
        return invariant
    else:
        return invariant

def parseAllConstants(invariants:list):
    global Constants 
    for invariant in invariants:
        if invariant.find("()")==-1:
            m = re.compile("^(orig)*(.*)\s+(==)\s+([0-9]+|true|false|\"0x0\")").search(invariant)
            if m is not None:
                # print(invariant)
                ret = m.groups() 
                if ret[0] == "orig" :
                    Constants[f"{ret[0]}{ret[1]}"] = ret[3]
                else:
                    Constants[f"{ret[1]}"] = ret[3]
    return

def parseStateInvariant(invariant: str):
    invariant_new = replace_constant_variables(invariant)
    if invariant_new != invariant:
        # print(invariant_new)
        invariant =  invariant_new
        # exit(0)
    m = re.compile("^(orig)*(.*)\s+(>=|>|==|!=|<=|<|one of)\s+([0-9]+|true|false|\"0x0\"|\{.*\})").search(invariant)
    if m is not None:
        return m.groups(), invariant
    else:
        return None, invariant

def containRelevantSliceStatePredicate(criteria, result ):
    ret = True 
    try:
        for item in criteria:
            if result[1].find(item) == -1 or result[1].find("+") != -1 or result[1].find("*") != -1 or result[1].find("-") != -1:
                ret = False
                break
        if ret:
            return ret 
        ret = True
        for item in criteria:
            if result[-1].find(item) == -1 or result[1].find("+") != -1 or result[1].find("*") != -1 or result[1].find("-") != -1:
                ret = False
                break
        return ret 
    except Exception as e:
        print(result)
        raise e 

def containRelevantGlobalStatePredicate(criteria :list, result: list):
    ret = True 
    if result[1].find("this.")==-1 or any(map(lambda item: result[1].find(item)!=-1, criteria)) or (result[1].find("+") != -1 or result[1].find("*") != -1 or result[1].find("-") != -1):
        ret = False
    return ret 

def containRelevantStatePredicate(criteria, result):
    # return result[1].find("this.")!=-1 and ( containRelevantSliceStatePredicate(criteria, result) or containRelevantGlobalStatePredicate(criteria, result))
    return  result[1].find("this.")!=-1 and containRelevantSliceStatePredicate(criteria, result)

def containRelevantStatePredicateUsingExcludedCriteria(excludedcriteria, result):
    return containRelevantGlobalStatePredicate(criteria=excludedcriteria, result=result)

def validStateInvariant(invariant):
    # print(invariant, invariant.find("Value()")==-1)
    return invariant.find("elements")==-1 and invariant.find("balanceOf")==-1  and invariant.find("()")==-1  

def filterIrrelevantInvariant(invariant):
    return invariant.find("remainingCats") == -1 and invariant.find("remainingGenesisCats") == -1  and invariant.find("totalSupply") == -1  and invariant.find("rescueIndex") == -1  and invariant.find("searchSeed") == -1  and invariant.find("owner") == -1 and invariant.find("name") == -1  and invariant.find("symbol") == -1  and invariant.find("imageGenerationCodeMD5") == -1 and invariant.find("mode") == -1  and invariant.find("decimals") == -1 


def readInvariant(workdir, usefullName=False):
    global Equidity_pairs
    invariantsdict = dict()
    matches =  glob.glob(workdir+"/*.sol")
    assert len(matches) == 1, "contract file (.sol) not found"
    inv_file = matches[0].split(".sol")[0]+".inv"
    assert os.path.exists(inv_file), "inv file (.inv) not found"
    with open(inv_file,"r") as f:
        lines = f.readlines()
        index = 0
        while True:
            if lines[index].startswith("=="):
                index += 1
                break
            index += 1
        while True:
            if index >= len(lines):
                break 
            methodexit = lines[index].strip()
            if methodexit.find(":::EXIT1")!=-1:
                if not usefullName:
                    method = methodexit.split("(")[0].split(".")[1]
                else:
                    method = methodexit.split(":::")[0]
                Equidity_pairs[method] :dict =  dict()
                invariants = []
                while True:
                    if index >= len(lines):
                        break 
                    if lines[index].startswith("=="):
                        index += 1
                        break
                    else:
                        inv = lines[index].strip()
                        invariants.append(inv)
                        eq_var_inv =  parseEquidityInvariant(inv)
                        # print(inv, eq_var_inv)
                        if eq_var_inv is not None:
                            Equidity_pairs[method].update(eq_var_inv) 
                            # print(Equidity_pairs[method])
                    index += 1
                invariantsdict[method] = invariants
            else:
                while True:
                    if index >= len(lines):
                        break 
                    if lines[index].startswith("=="):
                        index += 1
                        break
                    index += 1
    return invariantsdict     


def simplifyDaikonInvaraint(invariant):
    # return invariant.split("].get")[1].replace("(", "").replace(")", "")
    if invariant.find("].")!=-1:
        return invariant.replace("orig(msg.sender)", "msg_sender").split("].")[1].replace("(", "").replace(")", "").replace("true", "1").replace("false", "0").replace("\"0x0\"", "0")
    elif invariant.find("this.")!=-1:
        return invariant.replace("orig(msg.sender)", "msg_sender").split(".")[1].replace("(", "").replace(")", "").strip().replace("true", "1").replace("false", "0").replace("\"0x0\"", "0")
    elif invariant.find("]")==-1:
         return invariant.replace("orig(msg.sender)", "msg_sender").replace("\"0x0\"", "0")
    else:
        assert False, invariant



invaraintsdict = None 

def getStatePredicatesAndMsgsenderPredicatesFromFunctionInvaraints(workdir, usefullName=False):
    global invaraintsdict
    invaraintsdict = readInvariant(workdir, usefullName=usefullName)    
    global Constants
    global Equidity_pairs
    # print(invaraintsdict)
    relevantPreInvariantsdict = dict()
    relevantPostInvariantsdict = dict() 
    relevantPreMsgsenderInvariantsdict = dict()
    relevantPostMsgsenderInvariantsdict = dict() 
    all_predicates = set()
    for method in invaraintsdict.keys():
            Constants.clear()
            invariants = invaraintsdict[method]
            relevantPreInvariants = list()
            relevantPostInvariants = list()
            relevantPreMsgSenderInvariants = list()
            relevantPostMsgSenderInvariants = list()
            # print(len(invariants))
            parseAllConstants(invariants=invariants)
            # if method.startswith("enterBidForPunk"):
            #     print(Constants)
            for invariant in invariants:
                      
                    result, invariant = parseStateInvariant(invariant)
                    if result is not None:
                        if validStateInvariant(invariant) and containRelevantGlobalStatePredicate([], result):
                            all_predicates.add(simplifyDaikonInvaraint(invariant))
                            if result[0] is not None:
                                if  result[0]=="orig":
                                    if invariant not in relevantPreInvariants:
                                        relevantPreInvariants.append(simplifyDaikonInvaraint(invariant))
                                else: 
                                    assert False
                            else:
                                    if result[1] in Equidity_pairs[method]:
                                      
                                        if invariant not in relevantPreInvariants:
                                            relevantPreInvariants.append(simplifyDaikonInvaraint(invariant))
                                            relevantPostInvariants.append(simplifyDaikonInvaraint(invariant))
                                    else:
                                        if invariant not in relevantPostInvariants:
                                            relevantPostInvariants.append(simplifyDaikonInvaraint(invariant))
                    result = parseMsgSenderInvariant(invariant)
                    if result is not None:
                            if result[0] is not None:
                                if  result[0]=="orig":
                                    if invariant not in relevantPreMsgSenderInvariants:
                                        relevantPreMsgSenderInvariants.append(simplifyDaikonInvaraint(invariant))
                                else: 
                                    assert False
                            else:
                                    if result[1] in Equidity_pairs[method]:
                                        if invariant not in relevantPreMsgSenderInvariants:
                                            relevantPreMsgSenderInvariants.append(simplifyDaikonInvaraint(invariant))
                                            relevantPostMsgSenderInvariants.append(simplifyDaikonInvaraint(invariant))
                                    else:
                                        if invariant not in relevantPostMsgSenderInvariants:
                                            relevantPostMsgSenderInvariants.append(simplifyDaikonInvaraint(invariant))
            
            relevantPreInvariants = list(filter(lambda item: filterIrrelevantInvariant(item) , relevantPreInvariants))
            relevantPostInvariants = list(filter(lambda item: filterIrrelevantInvariant(item) , relevantPostInvariants))
            # print(relevantPostInvariants, set(relevantPostInvariants))

            relevantPreInvariantsdict["*"+method] = list(set(relevantPreInvariants))
            relevantPostInvariantsdict["*"+method] = list(set(relevantPostInvariants))

            relevantPreMsgsenderInvariantsdict["*"+method] = relevantPreMsgSenderInvariants
            relevantPostMsgsenderInvariantsdict["*"+method] = relevantPostMsgSenderInvariants
               
    
    return all_predicates, relevantPreInvariantsdict, relevantPostInvariantsdict, relevantPreMsgsenderInvariantsdict, relevantPostMsgsenderInvariantsdict   

