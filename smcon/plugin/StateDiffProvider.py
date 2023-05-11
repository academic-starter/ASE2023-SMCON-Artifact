from typing import Any
from .Provider import Provider
import logging
from .quickNode import fetchStateDiff 

TX_HASH="tx_hash"
class StateDiffProvider(Provider):
    def __init__(self, params) -> None:
        super().__init__(params=params)

    # @input, read a transaction hashes
    # @output, produce a set of state diffs for one or maybe more contract address 
    def read(self) -> Any:
        logging.debug(self.params[TX_HASH])
        result = fetchStateDiff(self.params[TX_HASH])
        return result 

if __name__ == "__main__":
    params = dict()
    params[TX_HASH] = "0x4fc330598e1abc9e09dd1e00836d0d2d46b25d3cbce6cc60137dc14897ef65dd"
    sdProvider = StateDiffProvider(params=params)
    sdProvider.read()