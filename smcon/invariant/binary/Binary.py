from smcon.invariant.Invariant import Invariant, VERISOL_USE
from smcon.model.model import VarInfo
from smcon.derivation.unary.Original import Original
from typing import List
import math 

class Binary(Invariant):
    num_samples: List
    def __init__(self, varInfos) -> None:
        super().__init__(varInfos)
        self.num_samples = list()
    
    @classmethod 
    def valid_vars_length(cls, vars: List[VarInfo]):
        return len(vars) == 2
    
    def check(self, vals: List[VarInfo]):
        assert len(vals) == 2
        self.verified = True
        vals = self.handleNone(vals)
        self.num_samples.append(vals)
        return self._check(vals[0], vals[1])
    
    def handleNone(self, vals: List):
        return vals 

    def computeConfidence(self):
        # coefficient = 1
        # for i in range(len(self.varInfos)):
        #     varInfo  = self.varInfos[i]
        #     if varInfo.isDerived():
        #         coefficient *= varInfo.derivation.computeConfidence()
        # return 1 * coefficient
        return 1 
        
    def _check(self, val_1, val_2):
        return False 
    
    def isPreCondition(self):
        return (isinstance(self.varInfos[0].derivation, Original) or self.varInfos[0].isTxVar()) and (isinstance(self.varInfos[1].derivation, Original)  or self.varInfos[1].isTxVar()) 
    
    def isPostCondition(self):
        return not self.isPreCondition()