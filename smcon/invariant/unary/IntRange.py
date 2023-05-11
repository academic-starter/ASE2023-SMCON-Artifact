from smcon.invariant.unary.Unary import VarInfo, List, Set
from smcon.invariant.unary.IntUnary import IntUnary 

class IntRange(IntUnary):
    values: Set  
    def __init__(self, varInfos) -> None:
        super().__init__(varInfos)
        self.values = set()     
    
    def _check(self, val):
        self.values.add(val)
        return True 

    def __str__(self) -> str:
        desc = "IntRange({0})".format(self.varInfos[0].name)
        return desc