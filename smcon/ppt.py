import logging
from smcon.model.model import VariableModel, TxType, FuncName, ContractName, VarInfo
from smcon.model.Tx import Transaction
from enum import Enum
from typing import Any, Dict, List, NewType 
from itertools import combinations, permutations


from smcon.derivation.Derivation import Derivation 
from smcon.derivation.unary.Original import Original 
from smcon.derivation.unary.StructMember import StructMember 
from smcon.derivation.binary.ArrayItem import ArrayItem 
from smcon.derivation.binary.MappingItem import MappingItem
from smcon.derivation.unary.MappingWildcard import MappingWildcard
from smcon.derivation.unary.ArrayWildcard import ArrayWildcard
from smcon.derivation.unary.IntSeqSum import IntSeqSum

from smcon.invariant import Invariant, IntEq, IntGe, IntGt, IntLe, IntLt, IntNotEq, AddressEq, AddressIsZero, AddressNotZero, BoolTrue, BoolFalse, StringNotNull, StringIsNull, IntIsZero, IntGtZero, AddressNotEq, IntConstRange, IntSmallRange, IntSeqConstSum, IntSeqItemSmallRange

from smcon.suppressor import Supressor

CompleteDerivations: List[Derivation] = [
   Original, IntSeqSum,  MappingWildcard, StructMember, ArrayItem, MappingItem
]

CompleteInvaraints: List[Invariant] = [
 IntEq, IntGe, IntGt, IntLe, IntLt, IntNotEq, AddressEq, AddressNotEq,
 AddressIsZero, AddressNotZero, 
 BoolTrue, BoolFalse,
 StringNotNull, StringIsNull, IntIsZero, IntGtZero, 
 IntConstRange, IntSmallRange, 
 IntSeqConstSum,
 IntSeqItemSmallRange
]
Variable = NewType("variable", VarInfo)

class PptType(Enum):
    CONTRACT = 0 # for contract-level invariants
    OBJECT =  1 # for object-level invaraints, e.g., invaraints about structure, mapping, and etc.
    ENTER = 2 # for function-elvel preconditions, the point entering function; only one enter point per function
    EXIT = 3 # for function-elvel post-conditions, the point leaving function; could be many exit points per function

class Ppt:
    vars: List[Variable]
    engine: Any
    def __init__(self, vars: List[Variable]) -> None:
        self.vars = vars 
    
    def register_engine(self, engine: Any):
        self.engine = engine
    
    def __str__(self) -> str:
        vars_desc = ", ".join([item.name for item in self.vars])
        return "[vars: {0}]".format(vars_desc)
    
class PptTopLevel(Ppt):
    contract: ContractName
    func: FuncName
    type: PptType
    executionType: TxType
    all_slices: List
    suppressor: Supressor
    def __init__(self, contract: ContractName, func: FuncName,  type: PptType, executionType: TxType, vars: List[Variable]) -> None:
        super().__init__(vars)
        self.contract = contract
        self.func =  func  
        self.type = type 
        self.executionType = executionType
        self.all_slices :List[PptSlice] =  list()

    def getVarType(self, varInfo: VarInfo):
        return self.engine.getVarType(self.func, varInfo)
    
    def checkTypeConsistent(self, varInfo1, varInfo2):
        return self.engine.checkTypeConsistent(self.func, varInfo1, varInfo2)

    def load(self, tx: Transaction):
        if not self.is_valid(tx):
            return 
        else:
            for slice in self.all_slices:
                vals = [ tx.getValue(_var) for _var in slice.vars]  
                slice.addValues(vals=vals)
    
    def loadSliceEvent(self, tx: Transaction, slice_states: List[Dict]):
        if not self.is_valid(tx):
            return 
        else:
            for myslice in self.all_slices:
                vals =  []
                for _var in myslice.vars:
                    if _var.name in [ item["name"] for item in slice_states]:
                        slice_state = list(filter(lambda item: item["name"] == _var.name, slice_states))[0]["value"]
                        vals.append(slice_state)
                    else:
                        vals.append(tx.getValue(_var)) 
                myslice.addValues(vals=vals)

    def is_valid(self, tx:Transaction):
        assert tx.contract ==  self.contract
        if self.type in [PptType.ENTER, PptType.EXIT]:
            # if tx.func == self.func:
            if self.func.find(tx.func)!=-1:
                if tx.tx_type == self.executionType:
                    return True 
            return False 
        else:
            return True 
    def addCustomizedVarInfos(self, varInfos: List[VarInfo]):
        self.vars.extend(varInfos)

    def create_derived_variables(self):
        logging.debug("create_derived_variables...")
        perm_1 = permutations(range(len(self.vars)), 1) 
        for item in perm_1:
            for derivation in [ArrayWildcard, MappingWildcard]:
                if derivation.valid_vars(vars=[self.vars[i] for i in item]):
                    instance = derivation.instantiate(vars=[self.vars[i] for i in item], ppt_slice=self)
                    derived_vars = instance.derive()
                    self.vars.extend(derived_vars)
        perm_1 = permutations(range(len(self.vars)), 1) 
        for item in perm_1:
            for derivation in [IntSeqSum]:
                if derivation.valid_vars(vars=[self.vars[i] for i in item]):
                    instance = derivation.instantiate(vars=[self.vars[i] for i in item], ppt_slice=self)
                    derived_vars = instance.derive()
                    self.vars.extend(derived_vars)
        perm_1 = permutations(range(len(self.vars)), 1)
        for item in perm_1:
            for derivation in [Original]:
                if derivation.valid_vars(vars=[self.vars[i] for i in item]):
                    instance = derivation.instantiate(vars=[self.vars[i] for i in item], ppt_slice=self)
                    derived_vars = instance.derive()
                    self.vars.extend(derived_vars)
        pass 
        # perm_2 = permutations(range(len(self.vars)), 2) 
        # for item in perm_2:
        #     for derivation in CompleteDerivations:
        #         if derivation.valid_vars(vars=[self.vars[i] for i in item]):
        #             instance = derivation.instantiate(vars=[self.vars[i] for i in item], ppt_slice=self)
        #             derived_vars = instance.derive()
        #             self.vars.extend(derived_vars)
        
        # perm_1 = permutations(range(len(self.vars)), 1) 
        # for item in perm_1:
        #     for derivation in CompleteDerivations:
        #         if derivation.valid_vars(vars=[self.vars[i] for i in item]):
        #             instance = derivation.instantiate(vars=[self.vars[i] for i in item], ppt_slice=self)
        #             derived_vars = instance.derive()
        #             self.vars.extend(derived_vars)
        
        # perm_1 = permutations(range(len(self.vars)), 1) 
        # for item in perm_1:
        #     for derivation in [Original]:
        #         if derivation.valid_vars(vars=[self.vars[i] for i in item]):
        #             instance = derivation.instantiate(vars=[self.vars[i] for i in item], ppt_slice=self)
        #             derived_vars = instance.derive()
        #             self.vars.extend(derived_vars)

    def createSlices(self):
        self.vars = list(set(self.vars))
        com_1 =  combinations(range(len(self.vars)), 1)
        for item in com_1:
            self.all_slices.append(self.get_or_instantiate_slice(vars=[self.vars[i] for i in item]))
        
        com_2 =  combinations(range(len(self.vars)), 2)
        for item in com_2:
            # if self.checkTypeConsistent(self.vars[item[0]], self.vars[item[1]]):
            self.all_slices.append(self.get_or_instantiate_slice(vars=[self.vars[i] for i in item]))
        
        # com_3 =  combinations(range(len(self.vars)), 3)
        # for item in com_3:
        #     if self.checkTypeConsistent(self.vars[item[0]], self.vars[item[1]]) \
        #         and self.checkTypeConsistent(self.vars[item[1]], self.vars[item[2]]):
        #         self.all_slices.append(self.get_or_instantiate_slice(vars=[self.vars[i] for i in item])) 

    def get_or_instantiate_slice(self, vars: List[Variable]):
        if 1==len(vars):
            return self.get_or_instantiate_slice1(vars)
        elif 2 == len(vars):
            return self.get_or_instantiate_slice2(vars)
        elif 3 ==  len(vars):
            return self.get_or_instantiate_slice3(vars)
        else:
            assert False, "The length {0} is not supported.".format(len(vars))

    def get_or_instantiate_slice1(self,vars):
        return PptSlice1(self, vars) 

    def get_or_instantiate_slice2(self, vars):
        return PptSlice2(self, vars)

    def get_or_instantiate_slice3(self, vars):
        return PptSlice3(self, vars)
    
    def getAllInvariants(self):
        results: List[Invariant] = list()
        for myslice in self.all_slices:
            myslice.finalize()
            results.extend(myslice.invs)
        return results 

    def compressInvaraints(self):
        results: List[Invariant] = list()
        for slice in self.all_slices:
            slice.finalize()
            slice.compressInvariants()
            results.extend(slice.invs)
        compressedResults: List[Invariant] = list()
        self.suppressor = Supressor(self.vars)
        for inv in results:
            if not self.suppressor.imply(compressedResults, inv):
                compressedResults.append(inv)
        return compressedResults

class PptSlice(Ppt):
    arity: int 
    parent: PptTopLevel
    invs: List[Invariant] 
    suppressor: Supressor
    def __init__(self, parent: PptTopLevel, vars: List[Variable]) -> None:
        super().__init__(vars)
        self.parent = parent
        self.invs = list()
        self.suppressor = Supressor(self.vars)
    
    def instantiate_invariants(self):
        self._instantiate_given_invaraints(CompleteInvaraints)

    def _instantiate_given_invaraints(self, invariants: List[Invariant]):
        for proto_inv in invariants:
            if proto_inv.valid_vars(self.vars):
                self.invs.append(proto_inv.instantiate(self.vars))
    
    def addValues(self, vals: List):
        false_invs = list()
        size = len(self.invs)
        for inv in self.invs:
            if not inv.check(vals):
                false_invs.append(inv)
        for inv in false_invs:
            self.invs.remove(inv)
        assert size == len(self.invs) + len(false_invs)
    
    def finalize(self):
        results =  []
        for inv in self.invs:
            inv.finalize()
            if not inv.falsify and inv.verified:
                results.append(inv)
        self.invs =  results

    def compressInvariants(self):
        if len(self.invs) == 0:
            return
        # IntGt -> IntGe 
        # IntGt -> IntNotEq
        # IntEq -> IntGe
        # IntEq -> IntLe 
        # IntLt -> IntLe
        # IntLt -> IntNotEq
        single_result = self.invs[0]
        for inv in self.invs[1:]:
            if not self.suppressor.imply([single_result], inv):
                single_result = inv  

        self.invs =  [single_result]

        # ImplyRules = dict()
        # ImplyRules["IntGt"] =  {"IntGe", "IntNotEq"}
        # ImplyRules["IntEq"] =  {"IntGe", "IntLe"}
        # ImplyRules["IntLt"] =  {"IntLe", "IntNotEq"}
        # for inv_rule in ImplyRules:
        #     for inv in self.invs:
        #         if self.getInvariantName(inv) == inv_rule:
        #             for _inv in self.invs:
        #                 if self.getInvariantName(_inv) in ImplyRules[inv_rule]:
        #                     _inv.setUseless()
        
        # useless_invs = list()
        # for inv in self.invs:
        #     if inv.useless:
        #         useless_invs.append(inv)
        
        # for inv in useless_invs:
        #     self.invs.remove(inv)
        
    
    @classmethod
    def getInvariantName(cls, inv: Invariant):
        if isinstance(inv, IntGt):
            return "IntGt"
        elif isinstance(inv, IntGe):
            return "IntGe"
        elif isinstance(inv, IntEq):
            return "IntEq"
        elif isinstance(inv, IntNotEq):
            return "IntNotEq"
        elif isinstance(inv, IntLe):
            return "IntLe"
        elif isinstance(inv, IntLt):
            return "IntLt"
        else:
            return "others"
        
    
class PptSlice1(PptSlice):
    def __init__(self, parent: PptTopLevel, vars: List[Variable]) -> None:
        PptSlice.__init__(self, parent, vars)
        assert 1 == len(self.vars)
        self.arity = 1
    
    
class PptSlice2(PptSlice):
    def __init__(self, parent: PptTopLevel, vars: List[Variable]) -> None:
        PptSlice.__init__(self, parent, vars)
        assert 2 == len(self.vars)
        self.arity = 2

class PptSlice3(PptSlice):
    def __init__(self, parent: PptTopLevel, vars: List[Variable]) -> None:
        PptSlice.__init__(self, parent, vars)
        assert 3 == len(self.vars)
        self.arity = 3