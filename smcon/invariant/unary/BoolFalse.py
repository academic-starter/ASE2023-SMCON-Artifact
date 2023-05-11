from smcon.invariant.unary.Unary import VarInfo, List, Set
from smcon.invariant.unary.BoolUnary import BoolUnary
from smcon.const import INVARIANT_STYLE

class BoolFalse(BoolUnary):
    def __init__(self, varInfos) -> None:
        super().__init__(varInfos)
    
    
    def _check(self, val):
        if val is None:
            val = False
        return val == False
    
    def __str__(self) -> str:
        if INVARIANT_STYLE == "VERISOL":
            if self.isPostCondition():
                desc = "VeriSol.Ensures({0}==false)".format(self.varInfos[0].name)
            else:
                desc = "VeriSol.Requires({0}==false)".format(self.varInfos[0].name)
            return desc    
        elif INVARIANT_STYLE == "DAIKON":
            desc = "{0} == false".format(self.varInfos[0].name)
            return desc
        else:
            desc = "BoolFalse({0})".format(self.varInfos[0].name)
            return desc
    
