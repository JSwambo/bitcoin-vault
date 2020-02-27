from bitcoin.core import b2lx, lx, COIN, COutPoint, CTxOut, CTxIn, CTxInWitness, CTxWitness, CScriptWitness, CMutableTransaction, Hash160
from address_gen import *
import pprint
import pickle


# # Connect to bitcoind through RPC
SelectParams("regtest")
connection = Proxy()


# # Fund depositor address
connection._call('generatetoaddress', 1, str(depositor_address))
connection._call('generatetoaddress', 100, str(dummy_address))

# # Give the private keys to bitcoind (for ismine, listunspent, etc).
connection._call('importmulti', [
    {
        "scriptPubKey": {"address": str(depositor_address)},
        "timestamp": 0,
        "witnessscript": b2x(depositor_witnessScript),
        "keys": [str(depositor_privkey)]
    }
], {"rescan": True})


# # Specify which utxo to spend from
unspents = connection._call("listunspent", 6, 9999, [str(
    depositor_address)], True, {"minimumAmount": 1.0})
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
sighash = SignatureHash(depositor_witnessScript, tx, txin_index,
                        SIGHASH_ALL, amount=amount, sigversion=SIGVERSION_WITNESS_V0)
signature = depositor_privkey.sign(sighash) + bytes([SIGHASH_ALL])

# # Construct a witness for this P2WSH transaction input and add to tx.
witness = CScriptWitness([signature, depositor_witnessScript])
tx.wit = CTxWitness([CTxInWitness(witness)])

# # Broadcast the transaction to the regtest network.
spend_txid = connection.sendrawtransaction(tx)

file_name = "signed_deposit_tx.pkl"

with open(file_name, 'wb') as f:
    pickle.dump(connection._call('decoderawtransaction', b2x(tx.serialize())), f)

print(f"Spent transaction {b2lx(spend_txid)} and saved to file {file_name}. \n")
pprint.pprint(connection._call('decoderawtransaction', b2x(tx.serialize())))
