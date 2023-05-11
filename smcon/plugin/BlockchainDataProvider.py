import copy
from smcon.plugin.Provider import Provider
from smcon.plugin.SourcecodeProvider import SourcecodeProvider 
from smcon.plugin.StateDiffProvider import StateDiffProvider 
from smcon.plugin.TransactionProvider import TransactionProvider 
from typing import Dict, Any 
import logging
import os 
import json 
from alive_progress import alive_bar 

CONTRACT_ADDRESS = "contract_address"
class BlockchainDataProvider(Provider):
    def __init__(self, params: Dict, maxCount) -> None:
        super().__init__(params)
        self.maxCount = maxCount
    
    def _read(self, export_file):
        if os.path.exists(export_file):
            result = json.load(open(export_file))
            transactions = result["transactions"]
            contractName = result["contractName"]
            storageLayout =  result["storageLayout"]
            cached_record_number = result["cached_record_number"]
            if len(storageLayout) == 0:
                storageLayout = dict()
                scProvider =  SourcecodeProvider(self.params)
                try:
                    _, storageLayout, _ = scProvider.read()
                    result["storageLayout"] = storageLayout
                    json.dump(result, open(os.path.join(export_file), "w"))
                except:
                    logging.error("storage layout is empty")
                    exit(-1)
            
            abi = result["abi"]

            if len(result["transactions"]) >= self.maxCount:
                return contractName, storageLayout, abi, transactions[:self.maxCount]
            else:
                txProvider = TransactionProvider(self.params, self.maxCount - cached_record_number, cached_record_number)
                appended_transactions = txProvider.read()

                result["cached_record_number"] = cached_record_number + len(appended_transactions)

                logging.warning("fetching state diff for {0} transactions".format(len(appended_transactions)))
                with alive_bar(len(appended_transactions)) as bar:
                    for transaction in copy.copy(appended_transactions):
                        if len(transaction) != 0 and "transactionHash" in transaction[0]:
                            tx_hash = transaction[0]["transactionHash"]
                            params = dict(tx_hash=tx_hash)
                            sdProvider = StateDiffProvider(params=params)
                            stateDiff = sdProvider.read()
                            transaction[0]["stateDiff"] =  stateDiff
                        else:
                            appended_transactions.remove(transaction)
                        bar()
                transactions.extend(appended_transactions)
                result["transactions"] = transactions
                json.dump(result, open(os.path.join(export_file), "w"), indent=4)
                return contractName, storageLayout, abi, transactions
        else:
            scProvider =  SourcecodeProvider(self.params)
            storageLayoutFlag = True
         
            contractName, storageLayout, abi = scProvider.read()

            assert contractName is not None and storageLayout is not None and abi is not None 
            
            txProvider = TransactionProvider(self.params, self.maxCount)
            transactions = txProvider.read()
            cached_record_number = len(transactions)

            logging.warning("fetching state diff for {0} transactions".format(len(transactions)))
            with alive_bar(len(transactions)) as bar:
                for transaction in copy.copy(transactions):
                    if len(transaction) != 0 and "transactionHash" in transaction[0]:
                        tx_hash = transaction[0]["transactionHash"]
                        params = dict(tx_hash=tx_hash)
                        sdProvider = StateDiffProvider(params=params)
                        stateDiff = sdProvider.read()
                        transaction[0]["stateDiff"] =  stateDiff
                    else:
                        transactions.remove(transaction)
                    bar()
            if storageLayoutFlag:
                json.dump(dict(contractName = contractName, storageLayout = storageLayout, abi=abi, cached_record_number = cached_record_number, transactions = transactions),
                open(os.path.join(export_file), "w"), indent=4)        
            else:
                json.dump(dict(contractName = contractName, storageLayout = dict(), abi=abi, cached_record_number = cached_record_number,  transactions = transactions),
                open(os.path.join(export_file), "w"), indent=4)        

            return contractName, storageLayout, abi, transactions

    # @input, read a contract blockchain address
    # @output, produce a dictionary consisting of source code (including abi, storage layout), transactions, state changes 
    def read(self, export_dir = "./tmp/"):
        logging.debug(self.params[CONTRACT_ADDRESS])
        export_file = os.path.join(export_dir, self.params[CONTRACT_ADDRESS] +".json")

        return self._read(export_file=export_file)
    
        # if os.path.exists(os.path.join(export_dir, self.params[CONTRACT_ADDRESS] +".json")):
        #     result = json.load(open(os.path.join(export_dir, self.params[CONTRACT_ADDRESS] +".json")))        
        #     contractName = result["contractName"]
        #     storageLayout =  result["storageLayout"]
        #     if len(storageLayout) == 0:
        #         storageLayout = dict()
        #         scProvider =  SourcecodeProvider(self.params)
        #         try:
        #             _, storageLayout, _ = scProvider.read()
        #             result["storageLayout"] = storageLayout
        #             json.dump(result, open(os.path.join(export_dir, self.params[CONTRACT_ADDRESS] +".json"), "w"))
        #         except:
        #             logging.error("storage layout is empty")
        #             exit(-1)

        #     abi = result["abi"]
        #     transactions = result["transactions"]
        #     return contractName, storageLayout, abi, transactions
        # else:
        #     scProvider =  SourcecodeProvider(self.params)
        #     storageLayoutFlag = True
         
        #     contractName, storageLayout, abi = scProvider.read()

        #     assert contractName is not None and storageLayout is not None and abi is not None 
            
        #     txProvider = TransactionProvider(self.params, self.maxCount)
        #     transactions = txProvider.read()

        #     logging.warning("fetching state diff for {0} transactions".format(len(transactions)))
        #     with alive_bar(len(transactions)) as bar:
        #         for transaction in copy.copy(transactions):
        #             if len(transaction) != 0 and "transactionHash" in transaction[0]:
        #                 tx_hash = transaction[0]["transactionHash"]
        #                 params = dict(tx_hash=tx_hash)
        #                 sdProvider = StateDiffProvider(params=params)
        #                 stateDiff = sdProvider.read()
        #                 transaction[0]["stateDiff"] =  stateDiff
        #             else:
        #                 transactions.remove(transaction)
        #             bar()
        #     if storageLayoutFlag:
        #         json.dump(dict(contractName = contractName, storageLayout = storageLayout, abi=abi, transactions = transactions),
        #         open(os.path.join(export_dir, self.params[CONTRACT_ADDRESS] +".json"), "w"), indent=4)        
        #     else:
        #         json.dump(dict(contractName = contractName, storageLayout = dict(), abi=abi, transactions = transactions),
        #         open(os.path.join(export_dir, self.params[CONTRACT_ADDRESS] +".json"), "w"), indent=4)        

        #     return contractName, storageLayout, abi, transactions


if __name__ == "__main__":
    params = dict()
    params[CONTRACT_ADDRESS] = "0x1dac5649e2a0c943ffc4211d708f6ddde4742fd6"
    bdProvider = BlockchainDataProvider(params=params)
    bdProvider.read()
