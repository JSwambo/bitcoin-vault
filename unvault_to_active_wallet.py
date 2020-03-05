from address_gen import *
import pickle
import pprint
from bitcoin.core import b2lx, lx, COIN, COutPoint, CTxOut, CTxIn, CTxInWitness, CTxWitness, CScriptWitness, CMutableTransaction, Hash160, CMutableTxIn
from bitcoin.core.scripteval import VerifyScript, SCRIPT_VERIFY_P2SH

# # Connect to bitcoind through RPC
SelectParams("regtest")
connection = Proxy()

# # Specify which utxo to spend from
with open('signed_vault_tx.pkl', 'rb') as f:
    signed_deposit_tx = pickle.load(f)

txid = signed_deposit_tx['txid']
vout = signed_deposit_tx['vout'][0]['n']
amount = int(float(signed_deposit_tx['vout'][0]['value']) * COIN)


# # # Calculate an amount for the upcoming new UTXO. Set a high fee to bypass
# # # bitcoind minfee setting.
amount_less_fee = int(amount - (0.01 * COIN))

# # Create the unsigned unvault spend transaction.
txin = CMutableTxIn(COutPoint(lx(txid), vout), nSequence=5)
txout = CTxOut(amount_less_fee, depositor_redeemScript)
tx = CMutableTransaction([txin], [txout], nLockTime=0, nVersion=2)

# # # Specify which transaction input is going to be signed for.
txin_index = 0

# Calculate the signature hash for that transaction. Note how the script we use
# is the redeemScript, not the scriptPubKey. That's because when the CHECKSIG
# operation happens EvalScript() will be evaluating the redeemScript, so the
# corresponding SignatureHash() function will use that same script when it
# replaces the scriptSig in the transaction being hashed with the script being
# executed.
sighash = SignatureHash(vault_out_redeemScript, tx, txin_index, SIGHASH_ALL)

# Now sign it. We have to append the type of signature we want to the end, in
# this case the usual SIGHASH_ALL.
sig1 = AW_privkeys[0].sign(sighash) + bytes([SIGHASH_ALL])
sig2 = AW_privkeys[1].sign(sighash) + bytes([SIGHASH_ALL])


# Allow time-lock to expire
print("Generating 6 blocks to ensure time-lock has expired")
connection._call('generatetoaddress', 6, str(dummy_address))

# Set the scriptSig of our transaction input appropriately. The OP_0 is a dummy variable to satisfy
# OP_CHECKMULTISIG. OP_1 accesses the IF (active wallet) execution path.
txin.scriptSig = CScript([OP_0, sig1, sig2, OP_1, vault_out_redeemScript])


# Verify the signature worked. This calls EvalScript() and actually executes
# the opcodes in the scripts to see if everything worked out. If it doesn't an
# exception will be raised.
VerifyScript(txin.scriptSig, vault_out_scriptPubkey,
             tx, 0, (SCRIPT_VERIFY_P2SH,))

# #  Broadcast the transaction to the regtest network.
spend_txid = connection.sendrawtransaction(tx)

file_name = "unvault_to_active_wallet.pkl"

with open(file_name, 'wb') as f:
    pickle.dump(connection._call(
        'decoderawtransaction', b2x(tx.serialize())), f)

print(f"Spent transaction {b2lx(spend_txid)} and saved to file {file_name}. \n")
pprint.pprint(connection._call('decoderawtransaction', b2x(tx.serialize())))
