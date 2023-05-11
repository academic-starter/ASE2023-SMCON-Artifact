from smcon.invariant.unary.Unary import VarInfo, List, Set
from smcon.invariant.unary.IntSeqUnary import IntSeqUnary 

class IntSeqItemRange(IntSeqUnary):
    values: Set  
    def __init__(self, varInfos) -> None:
        super().__init__(varInfos)
        self.values = set()     
    
    def _check(self, val):
        self.values.update(val)
        return True 

    def __str__(self) -> str:
        # FIXME: 
        desc = "IntSeqItemRange({0})".format(self.varInfos[0].name)
        return desc