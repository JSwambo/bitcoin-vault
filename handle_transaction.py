import pickle
import binascii
from config import *
from generate_addresses import *
from protocol_errors import ProtocolError
from bitcointx.core import *
from bitcointx.core.script import *
from bitcointx.core.bitcoinconsensus import ConsensusVerifyScript
from bitcointx.core.scripteval import SCRIPT_VERIFY_WITNESS, SCRIPT_VERIFY_CHECKSEQUENCEVERIFY, SCRIPT_VERIFY_P2SH, SCRIPT_VERIFY_NULLDUMMY

hexlify = binascii.hexlify
unhexlify = binascii.unhexlify

def store(tx, file_name):
    with open(file_name, 'wb') as f:
        pickle.dump(hexlify(tx.serialize()), f)

def load(file_name):
    with open(file_name, 'rb') as f:
        tx = pickle.load(f)
    tx = CTransaction.deserialize(unhexlify(tx))
    return tx

def update_fee(file_name, fee, unspents):
    # # Load the transaction which will be updated with an additional input to bump the fee.
    tx = load(file_name)

    txid = None
    for unspent in unspents:
        if unspent['label'] == "Fee Wallet Address":
            if float(unspent['amount']) == fee:
                txid = unspent['txid']
                vout = unspent['vout']
                amount = int(coins_to_satoshi(unspent["amount"]))
                break
    if not txid:
        raise(ProtocolError(
            f'No available unspent transaction output available in fee_wallet with amount {fee}'))

    # # Extract the input witness for the initial input.
    wit1 = tx.wit.vtxinwit[0]

    # # Generate a new, mutable version of the loaded transaction with an additional input
    fee_in = CTxIn(prevout=COutPoint(lx(txid), vout), scriptSig=CScript())
    tx = CMutableTransaction(
        [tx.vin[0], fee_in], tx.vout, tx.nLockTime, tx.nVersion)

    # # Calculate the signature hash for the transaction. This is then signed by the
    # # private key that controls the UTXO being spent here at this txin_index.
    txin_index = 1
    sighash = SignatureHash(fee_wallet_witnessScript, tx, txin_index,
                            SIGHASH_ALL, amount=amount, sigversion=SIGVERSION_WITNESS_V0)
    signature = fee_wallet_privkey.sign(sighash) + bytes([SIGHASH_ALL])
    wit2 = CTxInWitness(CScriptWitness([signature, fee_wallet_witnessScript]))
    tx.wit = CTxWitness([wit1, wit2])

    # # Verify the witness using libbitcoinconsensus
    ConsensusVerifyScript(CScript(), fee_wallet_redeemScript, tx, txin_index, set(
        [SCRIPT_VERIFY_WITNESS, SCRIPT_VERIFY_P2SH]), amount, wit2.scriptWitness)

    store(tx, file_name)
    return tx