from bitcointx.core import CMutableTransaction, CTransaction, CBitcoinTransaction, CBitcoinMutableTransaction
from bitcointx.core import b2x
from bitcointx.rpc import RPCCaller
from bitcointx import select_chain_params
import pprint
import pickle
import binascii

hexlify = binascii.hexlify
unhexlify = binascii.unhexlify

# # Connect to bitcoind through RPC
select_chain_params("bitcoin/testnet")

connection = RPCCaller(allow_default_conf=True)

def store(tx, file_name, connection):
    with open(file_name, 'wb') as f:
        pickle.dump(hexlify(tx.serialize()), f)

    decoded_tx = connection._call('decoderawtransaction', b2x(tx.serialize()))
    print(f"Transaction {decoded_tx['txid']} was saved to file {file_name}. \n")
    pprint.pprint(decoded_tx)


def load(file_name, decoded=False):
    with open(file_name, 'rb') as f:
        tx = pickle.load(f)
    tx = CTransaction.deserialize(unhexlify(tx))

    decoded_tx = connection._call('decoderawtransaction', b2x(tx.serialize()))
    print(f"Transaction {decoded_tx['txid']} was loaded from file {file_name}. \n")
    pprint.pprint(decoded_tx)

    if decoded:
        return decoded_tx
    else:
        return tx


def broadcast(tx, connection):
    if type(tx) in [CTransaction, CMutableTransaction, CBitcoinTransaction, CBitcoinMutableTransaction]:
        deposit_txid = connection._call(
            "sendrawtransaction", b2x(tx.serialize()))
        print(f"Sent transaction with txid {deposit_txid}.")
    else:
        raise TypeError(
            "Transaction broadcast failed. Transaction not formatted correctly.")
