from config import *
from generate_addresses import *
from handle_transaction import store, load
from protocol_errors import ProtocolError
from bitcointx.core import *
from bitcointx.core.script import *
from bitcointx.core.scripteval import SCRIPT_VERIFY_WITNESS, SCRIPT_VERIFY_CHECKSEQUENCEVERIFY, SCRIPT_VERIFY_P2SH, SCRIPT_VERIFY_NULLDUMMY
from bitcointx.core.bitcoinconsensus import ConsensusVerifyScript


def new_deposit_transaction(file_name, unspents):
    utxo = unspents[0]
    txid = utxo['txid']
    vout = utxo['vout']
    amount = int(coins_to_satoshi(utxo["amount"]))
    amount_less_fee = amount - MIN_FEE

    # # Create the unsigned deposit transaction.
    txin = CTxIn(prevout=COutPoint(lx(txid), vout), scriptSig=CScript())
    txout_vault = CTxOut(
        int(PORTION_TO_VAULT * amount_less_fee), vault_in_redeemScript)
    txout_change = CTxOut(int((1 - PORTION_TO_VAULT)
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

    store(tx, file_name)
    return tx


def new_vault_transaction(file_name):
    # # Load the deposit transaction.
    prefix = file_name.split('vault_transaction.pkl')[0]
    deposit_tx = load(prefix + 'deposit_transaction.pkl')

    # # Specify which utxo to spend from.
    txid = b2x(deposit_tx.GetTxid()[::-1]) # Due to historical accident, the tx and block hashes that bitcoin core uses are byte-reversed.
    vout = 0
    amount = deposit_tx.vout[0].nValue
    amount_less_fee = amount - MIN_FEE

    # # # Create the unsigned vault transaction.
    txin = CTxIn(prevout=COutPoint(lx(txid), vout), scriptSig=CScript())
    txout = CTxOut(amount_less_fee, vault_out_redeemScript)
    tx = CMutableTransaction([txin], [txout])

    # # # Specify which transaction input is going to be signed for.
    txin_index = 0

    # # # Calculate the signature hash for the transaction. This is then signed by the
    # # # private key that controls the UTXO being spent here at this txin_index.
    sighash = SignatureHash(vault_in_witnessScript, tx, txin_index,
                            SIGHASH_ALL, amount=amount, sigversion=SIGVERSION_WITNESS_V0)
    signature = vault_in_privkey.sign(sighash) + bytes([SIGHASH_ALL])

    # # # Construct a witness for this P2WSH transaction input and add to tx.
    witness = CScriptWitness([signature, vault_in_witnessScript])
    tx.wit = CTxWitness([CTxInWitness(witness)])

    # # # Verify the witness using libbitcoinconsensus
    ConsensusVerifyScript(CScript(), vault_in_redeemScript, tx, txin_index, set([SCRIPT_VERIFY_WITNESS, SCRIPT_VERIFY_P2SH]), amount, witness)

    store(tx, file_name)
    return tx


def new_unvault_transaction(file_name):
    # # Load the vault transaction.
    prefix = file_name.split('unvault_transaction.pkl')[0]
    vault_tx = load(prefix + 'vault_transaction.pkl')

    # # Specify which utxo to spend from.
    txid = b2x(vault_tx.GetTxid()[::-1]) # Due to historical accident, the tx and block hashes that bitcoin core uses are byte-reversed.
    vout = 0
    amount = vault_tx.vout[0].nValue
    amount_less_fee = amount - MIN_FEE

    # # Create the unsigned unvault spend transaction.
    txin = CTxIn(COutPoint(lx(txid), vout), scriptSig=CScript(), nSequence=TIMELOCK)
    txout = CTxOut(amount_less_fee, depositor_redeemScript)
    tx = CMutableTransaction([txin], [txout], nLockTime=0, nVersion=2)

    # # Specify which transaction input is going to be signed for.
    txin_index = 0

    # # Calculate the signature hash for the transaction. This is then signed by the
    # # private keys that control the UTXO being spent here at this txin_index.
    sighash = SignatureHash(vault_out_witnessScript, tx, txin_index, SIGHASH_ANYONECANPAY.__or__(SIGHASH_ALL), amount=amount, sigversion=SIGVERSION_WITNESS_V0)
    sig1 = AW_privkeys[0].sign(sighash) + bytes([SIGHASH_ANYONECANPAY.__or__(SIGHASH_ALL)])
    sig2 = AW_privkeys[1].sign(sighash) + bytes([SIGHASH_ANYONECANPAY.__or__(SIGHASH_ALL)])

    # # Construct a witness for this P2WSH transaction input and add to tx. The OP_0 is a dummy variable to satisfy
    # # OP_CHECKMULTISIG. OP_1 (b'\x01' needed to avoid "OP_IF/NOTIF argument must be minimal" error) accesses the 
    # # IF (active wallet) execution path.
    witness = CScriptWitness([OP_0, sig1, sig2, b'\x01', vault_out_witnessScript])
    tx.wit = CTxWitness([CTxInWitness(witness)])

    # # Verify the scriptSig using libbitcoinconsensus
    ConsensusVerifyScript(CScript(), vault_out_redeemScript, tx, txin_index, set([SCRIPT_VERIFY_P2SH, SCRIPT_VERIFY_NULLDUMMY, SCRIPT_VERIFY_CHECKSEQUENCEVERIFY, SCRIPT_VERIFY_WITNESS]), amount, witness)

    store(tx, file_name)
    return tx


def new_p2rw_transaction(file_name):
    # # Load the vault transaction.
    prefix = file_name.split('p2rw_transaction.pkl')[0]
    vault_tx = load(prefix + 'vault_transaction.pkl')

    # # Specify which utxo to spend from.
    txid = b2x(vault_tx.GetTxid()[::-1]) # Due to historical accident, the tx and block hashes that bitcoin core uses are byte-reversed.
    vout = 0
    amount = vault_tx.vout[0].nValue
    amount_less_fee = amount - MIN_FEE

    # # Create the unsigned unvault spend transaction. Enable OPT-IN RBF by setting nSequence = 0xFFFFFFFF-2.
    txin = CTxIn(COutPoint(lx(txid), vout), CScript(), 0xFFFFFFFF-2)
    txout = CTxOut(amount_less_fee, p2rw_out_redeemScript)
    tx = CMutableTransaction([txin], [txout], nLockTime=0, nVersion=2)

    # # Specify which transaction input is going to be signed for.
    txin_index = 0

    # # Calculate the signature hash for the transaction. This is then signed by the
    # # private keys that control the UTXO being spent here at this txin_index.
    sighash = SignatureHash(vault_out_witnessScript, tx, txin_index, SIGHASH_ANYONECANPAY.__or__(SIGHASH_ALL), amount=amount, sigversion=SIGVERSION_WITNESS_V0)
    sig = vault_in_privkey.sign(sighash) + bytes([SIGHASH_ANYONECANPAY.__or__(SIGHASH_ALL)])

    # # Construct a witness for this P2WSH transaction input and add to tx.
    # # OP_0 accesses the IF (recovery wallet) execution path.
    witness = CScriptWitness([sig, OP_0, vault_out_witnessScript])
    tx.wit = CTxWitness([CTxInWitness(witness)])

    # # Verify the scriptSig using libbitcoinconsensus
    ConsensusVerifyScript(CScript(), vault_out_redeemScript, tx, txin_index, set([SCRIPT_VERIFY_P2SH, SCRIPT_VERIFY_WITNESS]), amount, witness)

    store(tx, file_name)
    return tx


def new_recover_transaction(file_name):
    # # Load the vault transaction.
    prefix = file_name.split('recover_transaction.pkl')[0]
    p2rw_tx = load(prefix + 'p2rw_transaction.pkl')

    # # Specify which utxo to spend from.
    txid = b2x(p2rw_tx.GetTxid()[::-1]) # Due to historical accident, the tx and block hashes that bitcoin core uses are byte-reversed.
    vout = 0
    amount = p2rw_tx.vout[0].nValue
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

    store(tx, file_name)
    return tx