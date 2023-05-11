from smcon.invariant.unary.Unary import Unary, VarInfo, List
from smcon.const import INVARIANT_STYLE

class AddressIsZero(Unary):
    def __init__(self, varInfos) -> None:
        Unary.__init__(self, varInfos)
    
    @classmethod 
    def valid_vars_type(cls, vars: List[VarInfo]):
        return vars[0].type == "address" or vars[0].type == "address_payable"
    
    def _check(self, val):
        return int.from_bytes(bytes.fromhex(val[2:]),"little") == 0
    
    def handleNone(self, val):
        val = val if val is not None else "0x"+"".join(["0"]*40)
        return super().handleNone(val)
    
    def __str__(self) -> str:
        # logging.warn(self.varInfos)
        if INVARIANT_STYLE == "VERISOL":
            if self.isPostCondition():
                desc = "VeriSol.Ensures({0}==address(0))".format(self.varInfos[0].name)
            else:
                desc = "VeriSol.Requires({0}==address(0))".format(self.varInfos[0].name)
            return desc  
        elif INVARIANT_STYLE == "DAIKON":
            desc = "{0} == 0".format(self.varInfos[0].name)
            return desc  
        else:
            varName = self.varInfos[0].name
            desc = "AddressIsZero({0})".format(varName)
            return desc