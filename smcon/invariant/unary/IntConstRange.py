from smcon.invariant.unary.IntRange import IntRange
from smcon.const import INVARIANT_STYLE

class IntConstRange(IntRange):
    def __init__(self, varInfos) -> None:
        IntRange.__init__(self, varInfos)
     
    def _check(self, val):
        super()._check(val)
        return len(self.values) == 1
    
    @property
    def constVal(self):
        return list(self.values)[0]
    
    def __str__(self) -> str:
        if INVARIANT_STYLE == "VERISOL":
            if self.isPostCondition():
                desc = "VeriSol.Ensures({0}=={1})".format(self.varInfos[0].name, list(self.values)[0])
            else:
                desc = "VeriSol.Requires({0}=={1})".format(self.varInfos[0].name, list(self.values)[0])
            return desc 
        elif INVARIANT_STYLE == "DAIKON":
            desc = "{0} == {1}".format(self.varInfos[0].name, list(self.values)[0])
            return desc   
        else:
            desc = "IntEq({0}, {1})".format(self.varInfos[0].name, list(self.values)[0])
            return desc