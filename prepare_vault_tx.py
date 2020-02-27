from bitcoin.core import b2lx, lx, COIN, COutPoint, CTxOut, CTxIn, CTxInWitness, CTxWitness, CScriptWitness, CMutableTransaction, Hash160
from address_gen import *
import pprint
import pickle

# # Connect to bitcoind through RPC
SelectParams("regtest")
connection = Proxy()

# # Mine deposit transaction and confirm with 6 new blocks
# connection._call('generatetoaddress', 6, str(dummy_address))

# Give the private keys to bitcoind (for ismine, listunspent, etc).
# connection._call('importmulti', [
#     {
#         "scriptPubKey": {"address": str(vault_in_address)},
#         "timestamp": 0,
#         "witnessscript": b2x(vault_in_witnessScript),
#         "keys": [str(vault_in_privkey)]
#     },
#     {
#         "scriptPubKey": {"address": str(vault_out_address)},
#         "timestamp": 0,
#         "redeemscript": serialized_vault_out_redeemscript,
#         "keys": [str(x) for x in AW_privkeys]
#     },
#     {
#         "scriptPubKey": {"address": str(p2rw_out_address)},
#         "timestamp": 0,
#         "redeemscript": serialized_p2rw_out_redeemscript,
#         "keys": [str(x) for x in RW_privkeys]
#     }
#     ], {"rescan": True})


# # Specify which utxo to spend from
with open('signed_deposit_tx.pkl', 'rb') as f:
    signed_deposit_tx = pickle.load(f)

txid = signed_deposit_tx['txid']
vout = signed_deposit_tx['vout'][0]['n']
amount = int(float(signed_deposit_tx['vout'][0]['value']) * COIN)


# # # Calculate an amount for the upcoming new UTXO. Set a high fee to bypass
# # # bitcoind minfee setting.
amount_less_fee = int(amount - (0.01 * COIN))

# # Create the unsigned deposit transaction.
txin = CTxIn(prevout=COutPoint(lx(txid), vout), scriptSig=CScript())
txout = CTxOut(amount_less_fee, vault_out_redeemScript)
tx = CMutableTransaction([txin], [txout])


# # # Specify which transaction input is going to be signed for.
txin_index = 0

# # # Calculate the signature hash for the transaction. This is then signed by the
# # # private key that controls the UTXO being spent here at this txin_index.
sighash = SignatureHash(vault_in_witnessScript, tx, txin_index, SIGHASH_ALL, amount=amount, sigversion=SIGVERSION_WITNESS_V0)
signature = vault_in_privkey.sign(sighash) + bytes([SIGHASH_ALL])

# # # Construct a witness for this P2WSH transaction input and add to tx.
witness = CScriptWitness([signature, vault_in_witnessScript])
tx.wit = CTxWitness([CTxInWitness(witness)])

# #  Broadcast the transaction to the regtest network.
spend_txid = connection.sendrawtransaction(tx)

file_name = "signed_vault_tx.pkl"

with open(file_name, 'wb') as f:
    pickle.dump(connection._call('decoderawtransaction', b2x(tx.serialize())), f)

print(f"Spent transaction {b2lx(spend_txid)} and saved to file {file_name}. \n")
pprint.pprint(connection._call('decoderawtransaction', b2x(tx.serialize())))