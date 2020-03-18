from handle_transaction import store, load, broadcast
from generate_addresses import *
from config import MIN_FEE, TIMELOCK
from bitcointx.core.scripteval import SCRIPT_VERIFY_WITNESS, SCRIPT_VERIFY_CHECKSEQUENCEVERIFY, SCRIPT_VERIFY_P2SH, SCRIPT_VERIFY_NULLDUMMY
from bitcointx.core.bitcoinconsensus import ConsensusVerifyScript
from bitcointx.core import b2lx, lx, coins_to_satoshi, COutPoint, CTxOut, CTxIn, CTxInWitness, CTxWitness, CMutableTransaction, CMutableTxIn, Hash160, CTransaction
import pprint
import pickle

# # Connect to bitcoind through RPC
select_chain_params("bitcoin/testnet")

def new_consolidation_transaction(file_name):
    # # Specify which utxo to spend from
    connection = RPCCaller(allow_default_conf=True)
    unspents = connection._call("listunspent", 1, 9999999, [str(
        depositor_address)], True, {"minimumAmount": 0.0})

    # # Construct the inputs
    txins = []
    amounts = []

    for unspent in unspents:
        txid = unspent['txid']
        vout = unspent['vout']
        amounts.append(int(coins_to_satoshi(unspent["amount"])))
        txins.append(CTxIn(prevout=COutPoint(
            lx(txid), vout), scriptSig=CScript()))

    total_amount = sum(amounts)
    amount_less_fee = total_amount - 3*MIN_FEE

    # # Create the unsigned deposit transaction.
    txout_consolidated = CTxOut(amount_less_fee, depositor_redeemScript)
    tx = CMutableTransaction(txins, [txout_consolidated])

    # # Calculate the signature hash for each input of the transaction and sign using
    # # the private key that controls the UTXO being spent from at the given txin_index.
    sigs = []
    txin_index = 0
    for (txin, amount) in zip(txins, amounts):
        sighash = SignatureHash(depositor_witnessScript, tx, txin_index,
                                SIGHASH_ALL, amount=amount, sigversion=SIGVERSION_WITNESS_V0)
        sigs.append(depositor_privkey.sign(sighash) + bytes([SIGHASH_ALL]))
        txin_index += 1

    # # Construct a witness for this P2WSH transaction and add to tx.
    witnesses = []
    for sig in sigs:
        witnesses.append(CTxInWitness(CScriptWitness([sig, depositor_witnessScript])))
    tx.wit = CTxWitness(witnesses)

    # # Verify each witness using libbitcoinconsensus
    txin_index = 0
    for (sig, amount) in zip(sigs, amounts):
        ConsensusVerifyScript(CScript(), depositor_redeemScript, tx, txin_index, set([SCRIPT_VERIFY_WITNESS, SCRIPT_VERIFY_P2SH]), amount, CScriptWitness([sig, depositor_witnessScript]))
        txin_index += 1

    store(tx, file_name, connection)
    connection.close()

    return tx


def new_deposit_transaction(file_name):
    # # Specify which utxo to spend from
    connection = RPCCaller(allow_default_conf=True)
    unspents = connection._call("listunspent", 1, 9999999, [
        str(depositor_address)], True, {"minimumAmount": 0.0})

    utxo = unspents[0]
    txid = utxo['txid']
    vout = utxo['vout']
    amount = int(coins_to_satoshi(utxo["amount"]))
    amount_less_fee = amount - MIN_FEE

    # # Specify the percentage amount to deposit to the vault
    percentage_to_deposit = 0.5

    # # Create the unsigned deposit transaction.
    txin = CTxIn(prevout=COutPoint(lx(txid), vout), scriptSig=CScript())
    txout_vault = CTxOut(
        int(percentage_to_deposit * amount_less_fee), vault_in_redeemScript)
    txout_change = CTxOut(int((1 - percentage_to_deposit)
                              * amount_less_fee), depositor_redeemScript)
    tx = CMutableTransaction([txin], [txout_vault, txout_change])

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

    # # Verify the witness using libbitcoinconsensus
    ConsensusVerifyScript(CScript(), depositor_redeemScript, tx, txin_index, set([SCRIPT_VERIFY_WITNESS, SCRIPT_VERIFY_P2SH]), amount, witness)  

    store(tx, file_name, connection)
    connection.close()

    return tx


def new_vault_transaction(file_name):
    # # Load the deposit transaction.
    sid = file_name.split('_')[0]
    try:
        deposit_tx = load(str(sid) + '_' + 'deposit_transaction.pkl', decoded=True)
    except FileNotFoundError:
        deposit_tx = load('sent_' + str(sid) + '_' +  'deposit_transaction.pkl', decoded=True)

    # # Specify which utxo to spend from.
    txid = deposit_tx['txid']
    vout = deposit_tx['vout'][0]['n']
    amount = int(coins_to_satoshi(deposit_tx['vout'][0]['value']))
    amount_less_fee = amount - MIN_FEE

    # # Create the unsigned vault transaction.
    txin = CTxIn(prevout=COutPoint(lx(txid), vout), scriptSig=CScript())
    txout = CTxOut(amount_less_fee, vault_out_redeemScript)
    tx = CMutableTransaction([txin], [txout])

    # # Specify which transaction input is going to be signed for.
    txin_index = 0

    # # Calculate the signature hash for the transaction. This is then signed by the
    # # private key that controls the UTXO being spent here at this txin_index.
    sighash = SignatureHash(vault_in_witnessScript, tx, txin_index,
                            SIGHASH_ALL, amount=amount, sigversion=SIGVERSION_WITNESS_V0)
    signature = vault_in_privkey.sign(sighash) + bytes([SIGHASH_ALL])

    # # Construct a witness for this P2WSH transaction input and add to tx.
    witness = CScriptWitness([signature, vault_in_witnessScript])
    tx.wit = CTxWitness([CTxInWitness(witness)])

    # # Verify the witness using libbitcoinconsensus
    ConsensusVerifyScript(CScript(), vault_in_redeemScript, tx, txin_index, set([SCRIPT_VERIFY_WITNESS, SCRIPT_VERIFY_P2SH]), amount, witness)

    connection = RPCCaller(allow_default_conf=True)
    store(tx, file_name, connection)
    connection.close()

    return tx


def new_unvault_transaction(file_name):
    # # Load the vault transaction.
    sid = file_name.split('_')[0]
    try:
        vault_tx = load(str(sid) + '_' + 'vault_transaction.pkl', decoded=True)
    except FileNotFoundError:
        vault_tx = load('sent_' + str(sid) + '_' +  'vault_transaction.pkl', decoded=True)

    # # Specify which utxo to spend from.
    txid = vault_tx['txid']
    vout = vault_tx['vout'][0]['n']
    amount = int(coins_to_satoshi(vault_tx['vout'][0]['value']))
    amount_less_fee = amount - MIN_FEE

    # # Create the unsigned unvault spend transaction.
    txin = CTxIn(COutPoint(lx(txid), vout), scriptSig=CScript(), nSequence=TIMELOCK)
    txout = CTxOut(amount_less_fee, depositor_redeemScript)
    tx = CMutableTransaction([txin], [txout], nLockTime=0, nVersion=2)

    # # Specify which transaction input is going to be signed for.
    txin_index = 0

    # # Calculate the signature hash for the transaction. This is then signed by the
    # # private keys that control the UTXO being spent here at this txin_index.
    sighash = SignatureHash(vault_out_witnessScript, tx, txin_index, SIGHASH_ALL, amount=amount, sigversion=SIGVERSION_WITNESS_V0)
    sig1 = AW_privkeys[0].sign(sighash) + bytes([SIGHASH_ALL])
    sig2 = AW_privkeys[1].sign(sighash) + bytes([SIGHASH_ALL])

    # # Construct a witness for this P2WSH transaction input and add to tx. The OP_0 is a dummy variable to satisfy
    # # OP_CHECKMULTISIG. OP_1 accesses the IF (active wallet) execution path.
    witness = CScriptWitness([OP_0, sig1, sig2, OP_1, vault_out_witnessScript])
    tx.wit = CTxWitness([CTxInWitness(witness)])

    # # Verify the scriptSig using libbitcoinconsensus
    ConsensusVerifyScript(CScript(), vault_out_redeemScript, tx, txin_index, set([SCRIPT_VERIFY_P2SH, SCRIPT_VERIFY_NULLDUMMY, SCRIPT_VERIFY_CHECKSEQUENCEVERIFY, SCRIPT_VERIFY_WITNESS]), amount, witness)

    connection = RPCCaller(allow_default_conf=True)
    store(tx, file_name, connection)
    connection.close()

    return tx


def new_p2rw_transaction(file_name):
    # # Load the vault transaction.
    sid = file_name.split('_')[0]
    try:
        vault_tx = load(str(sid) + '_' + 'vault_transaction.pkl', decoded=True)
    except FileNotFoundError:
        vault_tx = load('sent_' + str(sid) + '_' +  'vault_transaction.pkl', decoded=True)

    # # Specify which utxo to spend from.
    txid = vault_tx['txid']
    vout = vault_tx['vout'][0]['n']
    amount = int(coins_to_satoshi(vault_tx['vout'][0]['value']))
    amount_less_fee = amount - MIN_FEE

    # # Create the unsigned unvault spend transaction.
    txin = CTxIn(COutPoint(lx(txid), vout), CScript())
    txout = CTxOut(amount_less_fee, p2rw_out_redeemScript)
    tx = CMutableTransaction([txin], [txout], nLockTime=0, nVersion=2)

    # # Specify which transaction input is going to be signed for.
    txin_index = 0

    # # Calculate the signature hash for the transaction. This is then signed by the
    # # private keys that control the UTXO being spent here at this txin_index.
    sighash = SignatureHash(vault_out_witnessScript, tx, txin_index, SIGHASH_ALL, amount=amount, sigversion=SIGVERSION_WITNESS_V0)
    sig = vault_in_privkey.sign(sighash) + bytes([SIGHASH_ALL])

    # # Construct a witness for this P2WSH transaction input and add to tx.
    # # OP_0 accesses the IF (recovery wallet) execution path.
    witness = CScriptWitness([sig, OP_0, vault_out_witnessScript])
    tx.wit = CTxWitness([CTxInWitness(witness)])

    # # Verify the scriptSig using libbitcoinconsensus
    ConsensusVerifyScript(CScript(), vault_out_redeemScript, tx, txin_index, set([SCRIPT_VERIFY_P2SH, SCRIPT_VERIFY_WITNESS]), amount, witness)

    connection = RPCCaller(allow_default_conf=True)
    store(tx, file_name, connection)
    connection.close()

    return tx

def new_recover_transaction(file_name):
    # # Load the vault transaction.
    sid = file_name.split('_')[0]
    try:
        p2rw_tx = load(str(sid) + '_' + 'p2rw_transaction.pkl', decoded=True)
    except FileNotFoundError:
        p2rw_tx = load('sent_' + str(sid) + '_' +  'p2rw_transaction.pkl', decoded=True)

    # # Specify which utxo to spend from.
    txid = p2rw_tx['txid']
    vout = p2rw_tx['vout'][0]['n']
    amount = int(coins_to_satoshi(p2rw_tx['vout'][0]['value']))
    amount_less_fee = amount - MIN_FEE

    # # Create the unsigned unvault spend transaction.
    txin = CTxIn(COutPoint(lx(txid), vout), CScript())
    txout = CTxOut(amount_less_fee, depositor_redeemScript)
    tx = CMutableTransaction([txin], [txout])

    # # Specify which transaction input is going to be signed for.
    txin_index = 0

    # # Calculate the signature hash for the transaction. This is then signed by the
    # # private keys that control the UTXO being spent here at this txin_index.
    sighash = SignatureHash(p2rw_out_witnessScript, tx, txin_index, SIGHASH_ALL, amount=amount, sigversion=SIGVERSION_WITNESS_V0)
    sig1 = RW_privkeys[0].sign(sighash) + bytes([SIGHASH_ALL])
    sig2 = RW_privkeys[1].sign(sighash) + bytes([SIGHASH_ALL])

    # # Construct a witness for this P2WSH transaction input and add to tx. The OP_0 is a dummy variable to satisfy
    # # OP_CHECKMULTISIG. OP_1 accesses the IF (active wallet) execution path.
    witness = CScriptWitness([OP_0, sig1, sig2, p2rw_out_witnessScript])
    tx.wit = CTxWitness([CTxInWitness(witness)])

    # # Verify the scriptSig using libbitcoinconsensus
    ConsensusVerifyScript(CScript(), p2rw_out_redeemScript, tx, txin_index, set([SCRIPT_VERIFY_P2SH, SCRIPT_VERIFY_NULLDUMMY, SCRIPT_VERIFY_WITNESS]), amount, witness)

    connection = RPCCaller(allow_default_conf=True)
    store(tx, file_name, connection)
    connection.close()

    return tx