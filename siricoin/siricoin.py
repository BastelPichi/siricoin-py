import json, requests, re
from web3 import Web3
from eth_account.messages import encode_defunct


class siriCoin:
    def __init__(self, node="https://node-1.siricoin.tech:5006"):
        self.node = node
        self.w3node = node + "/web3"
        self.w3 = Web3(Web3.HTTPProvider(self.w3node))

    def _check(self):
        if not self.w3.isConnected():
            self.w3 = Web3(Web3.HTTPProvider(self.w3node)) #if not connected to node, perform a reconnect
            if not self.w3.isConnected():
                raise ConnectionError
            else:
                return
        else:
            return

    def sign_transaction(self, private_key, transaction):
        message = encode_defunct(text=transaction["data"])
        transaction["hash"] = self.w3.soliditySha3(["string"], [transaction["data"]]).hex()
        _signature = self.w3.eth.account.sign_message(message, private_key=private_key).signature.hex()
        signer = self.w3.eth.account.recover_message(message, signature=_signature)
        sender = self.w3.toChecksumAddress(json.loads(transaction["data"])["from"])
        if (signer == sender):
            transaction["sig"] = _signature
        return transaction

    def get_last_transaction(self, address):
        """Get last transaction of a user."""
        self._check()
        r = requests.get(f"{self.node}/accounts/accountInfo/{address}")
        return r.json()["result"]["transactions"][len(r.json()["result"]["transactions"]) - 1]


    def get_epoch(self):
        """"Get current block."""
        self._check()
        r = requests.get(f"{self.node}/chain/getlastblock").json()["result"]["miningData"]["proof"]
        return r


    def is_address(self, address):
        """Checks if the address is valid."""
        self._check()
        return self.w3.isAddress(address)
    
    def is_txid(self, txid):
        """Checks if a transaction hash/ID is valid."""
        self._check()
        return bool(re.search("^[0-9a-fA-F]{64}$$", txid.replace("0x", "")))
    
    def set_BIO(self, privkey, bio):
        try:
            self._check()
            
            addr=self.w3.eth.account.from_key(privkey).address
            tx = {"data": json.dumps({"from": self.w3.toChecksumAddress(addr), "to": self.w3.toChecksumAddress(addr), "tokens": 0, "parent": self.get_last_transaction(addr), "epoch": self.get_epoch(), "type": 0, "bio": str(bio)})}
            signature = self.sign_transaction(privkey, tx)
            r = requests.get(f"{self.node}/send/rawtransaction/?tx={json.dumps(signature).encode().hex()}")
            if r.json()["success"] == True:
                return True
            else:
                return False
        except Exception as e:
            print(e)
            return False


    def transaction(self, privkey, fromaddr, to, amount):
        """Build a transaction and send it to the node. Returns ``False`` or the txid."""
        try:
            fromaddr = self.w3.toChecksumAddress(fromaddr)
            to = self.w3.toChecksumAddress(to)
            data = {"from": fromaddr, "to": to, "tokens": amount, "parent": self.get_last_transaction(fromaddr), "epoch": self.get_epoch(), "type": 0}
            strdata = json.dumps(data)
            tx = {"data": strdata}
            signature = self.sign_transaction(privkey, tx)
            a = json.dumps(signature)
            b = a.encode().hex()
            r = requests.get(f"{self.node}/send/rawtransaction/?tx={b}")
            if r.json()["success"] == True:
                return r.json()["result"][0]
            else:
                return False
        except Exception as e:
            print(e)
            return False


    def balance(self, address):
        """Get balance of a user."""
        return requests.get(f"{self.node}/accounts/accountBalance/{address}").json()["result"]["balance"]
