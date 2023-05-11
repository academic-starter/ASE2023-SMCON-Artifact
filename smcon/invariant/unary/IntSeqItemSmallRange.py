from smcon.invariant.unary.IntSeqItemRange import IntSeqItemRange
from smcon.const import INVARIANT_STYLE
class IntSeqItemSmallRange(IntSeqItemRange):
    def __init__(self, varInfos) -> None:
        super().__init__(varInfos)
     
    def computeConfidence(self):
        return 1 < len(self.values) < 10
    
    @property
    def constVals(self):
        return self.values
    
    def __str__(self) -> str:
        if INVARIANT_STYLE == "DAIKON":
            desc = "elem of {0} is one of [{1}]".format(self.varInfos[0].name, ",".join(map(str, self.values)))
            return desc
        else:
            desc = "IntSeqItemSmallRange({0}, [{1}])".format(self.varInfos[0].name, ",".join(map(str, self.values)))
            return desc