from smcon.invariant.Invariant import Invariant
from smcon.model.model import VarInfo
from typing import List, Set
import math 
from smcon.derivation.unary.Original import Original 

class Unary(Invariant):
    num_samples: List
    def __init__(self, varInfos) -> None:
        super().__init__(varInfos)
        self.num_samples = list()
    
    @classmethod 
    def valid_vars_length(cls, vars: List[VarInfo]):
        return len(vars) == 1
    
    def check(self, vals: List):
        assert len(vals) == 1
        self.verified = True
        val  = self.handleNone(vals[0])
        self.num_samples.append(val)
        return self._check(val)

    def handleNone(self, val):
        return val 
    
    def computeConfidence(self):
        # if self.varInfos[0].isDerived():
        #     return (1 - math.pow(0.5, len(self.num_samples))) * self.varInfos[0].derivation.computeConfidence()
        # else:
        #     return 1 - math.pow(0.5, len(self.num_samples))
        return 1 
    
    def _check(self, val):
        return False 
    
    def isPreCondition(self):
        return self.varInfos[0].isTxVar() or isinstance(self.varInfos[0].derivation, Original)
    
    def isPostCondition(self):
        return not self.isPreCondition()