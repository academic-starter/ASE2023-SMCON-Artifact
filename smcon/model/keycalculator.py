
from functools import lru_cache
import web3 

def toInt(hexstr):
     return toUInt(hexstr)

@lru_cache
def toUInt(hexstr):
    if not isinstance(hexstr, int):
        if not isinstance(hexstr, str):
            hexstr = hexstr.hex()
        if hexstr.startswith("0x"):
                return int(hexstr, 16)
        else:
                return int(hexstr)      
    else:
        return hexstr 

@lru_cache
def getArrayBeginingSlot(varSlot):
    if isinstance(varSlot, str):
        assert varSlot.startswith("0x")
        varSlot = toInt(varSlot)
    return toInt(web3.Web3.solidity_keccak(["uint256"], [varSlot]))

@lru_cache
def getKeyisNonValueTypeSlotCalculation(key, baseSlot):
    assert isinstance(key, str)
    if key.startswith("0x"):
        hexKeyStr = key 
    else:
        hexKeyStr = web3.Web3.to_hex(key.encode())
    slotHexStr = hex(baseSlot).replace("0x","")
    slotHexStr = "".join(["0"]*(64-len(slotHexStr)))+slotHexStr
    hexStr = hexKeyStr + slotHexStr
    return web3.Web3.to_hex(web3.Web3.keccak(web3.Web3.to_bytes(hexstr=hexStr)))

@lru_cache
def getKeyisValueTypeSlotCalculation(key, baseSlot):
    slotHexStr = hex(baseSlot).replace("0x","")
    slotHexStr = "".join(["0"]*(64-len(slotHexStr)))+slotHexStr
    if isinstance(key, int):
        hexKeyStr = web3.Web3.to_hex(key).replace("0x","")
        hexKeyStr = "0x" + "".join(["0"]*(64-len(hexKeyStr)))+hexKeyStr
    elif isinstance(key, str):
        assert key.startswith("0x"), "{0} is not correct format with prefix 0x".format(key)
        if len(key) == 42:
            # mapping(address=>)
            hexKeyStr = key.replace("0x","")  
            hexKeyStr = "0x" + "".join(["0"]*(64-len(hexKeyStr)))+hexKeyStr 
        else:
            hexKeyStr =  key
            hexKeyStr =  hexKeyStr + "".join(["0"]*(66-len(hexKeyStr)))
    hexStr = hexKeyStr + slotHexStr
    try:
        return web3.Web3.to_hex(web3.Web3.keccak(web3.Web3.to_bytes(hexstr=hexStr)))
    except Exception as e:
        print(e)
        print("{0} is not supported!".format(hexStr))
        raise e 

if __name__ == "__main__":
    # baseSlot = 13
    # key = "https://ipfs.pixura.io/ipfs/QmP8o5x3YaVN6TCwUPuhSiQhapj5dP31CAigE2mzt3b3ZB"
    baseSlot = 3
    key = '0x860c4604fe1125ea43f81e613e7afb2aa49546aa'
    slot = getKeyisValueTypeSlotCalculation(key, baseSlot)
    print(slot)
    slot2 = getArrayBeginingSlot(toInt(slot))
    print(hex(slot2))
    # print(getKeyisNonValueTypeSlotCalculation(key, baseSlot))