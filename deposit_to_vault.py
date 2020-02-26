import hashlib
from bitcoin import SelectParams
from bitcoin.core import b2x, b2lx, lx, COIN, COutPoint, CTxOut, CTxIn, CTxInWitness, CTxWitness, CScriptWitness, CMutableTransaction, Hash160
from bitcoin.core.script import *
from bitcoin.wallet import CBitcoinAddress, CBitcoinSecret, P2SHBitcoinAddress, P2WSHBitcoinAddress
from bitcoin.rpc import Proxy
from address_gen import *
import pprint


# Connect to bitcoind through RPC
SelectParams("regtest")
connection = Proxy()

# Fund depositor address
# connection._call('generatetoaddress', 1, str(depositor_address))
# connection._call('generatetoaddress', 100, str(dummy_address))

# Give the private keys to bitcoind (for ismine, listunspent, etc).
# connection._call('importmulti', [
#     {
#         "scriptPubKey": {"address": str(depositor_address)},
#         "timestamp": 0,
#         "witnessscript": b2x(depositor_witnessScript),
#         "keys": [str(depositor_privkey)]
#     }
    # ,{
    #     "scriptPubKey": {"address": str(vault_in_address)},
    #     "timestamp": 0,
    #     "witnessscript": b2x(vault_in_witnessScript),
    #     "keys": [str(vault_in_privkey)]
    # },
    # {
    #     "scriptPubKey": {"address": str(vault_out_address)},
    #     "timestamp": 0,
    #     "redeemscript": serialized_vault_out_redeemscript,
    #     "keys": [str(x) for x in AW_privkeys]
    # },
    # {
    #     "scriptPubKey": {"address": str(p2rw_out_address)},
    #     "timestamp": 0,
    #     "redeemscript": serialized_p2rw_out_redeemscript,
    #     "keys": [str(x) for x in RW_privkeys]
    # }
    # ], {"rescan": True})


# Specify which utxo to spend from
unspents = connection._call("listunspent", 6, 9999, [str(depositor_address)], True, {"minimumAmount": 1.0})
utxo = unspents[0]
txid = utxo['txid']
vout = utxo['vout']
amount = int(float(utxo["amount"]) * COIN)

# # Calculate an amount for the upcoming new UTXO. Set a high fee to bypass
# # bitcoind minfee setting.
amount_less_fee = int(amount - (0.01 * COIN))

# # Create the unsigned deposit transaction.
txin = CTxIn(prevout=COutPoint(lx(txid), vout), scriptSig=CScript())
txout = CTxOut(amount_less_fee, vault_in_redeemScript)
tx = CMutableTransaction([txin], [txout])


# # Specify which transaction input is going to be signed for.
txin_index = 0

# # Calculate the signature hash for the transaction. This is then signed by the
# # private key that controls the UTXO being spent here at this txin_index.
sighash = SignatureHash(depositor_redeemScript, tx, txin_index, SIGHASH_ALL, amount=amount, sigversion=SIGVERSION_WITNESS_V0)
signature = depositor_privkey.sign(sighash) + bytes([SIGHASH_ALL])

# # Construct a witness for this P2WSH transaction input and add to tx.
witness = CScriptWitness([signature, depositor_witnessScript])
tx.wit = CTxWitness([CTxInWitness(witness)])


tx_dict = connection._call('decoderawtransaction', b2x(tx.serialize()))
# pprint.pprint(tx_dict)
# # Broadcast the transaction to the regtest network.
# spend_txid = connection.sendrawtransaction(tx)
