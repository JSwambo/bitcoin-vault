from bitcointx.core import b2x, b2lx, lx, coins_to_satoshi, COutPoint, CTxIn, CTxInWitness, CTxWitness, CMutableTransaction, CBitcoinTransaction, CMutableTxIn, Hash160, CTransaction, CBitcoinMutableTransaction
from bitcointx.rpc import RPCCaller
from bitcointx import select_chain_params
from bitcointx.core.bitcoinconsensus import ConsensusVerifyScript
from bitcointx.core.scripteval import SCRIPT_VERIFY_WITNESS, SCRIPT_VERIFY_CHECKSEQUENCEVERIFY, SCRIPT_VERIFY_P2SH, SCRIPT_VERIFY_NULLDUMMY
import pprint
import pickle
import binascii
from generate_addresses import *
from protocol_errors import ProtocolError

hexlify = binascii.hexlify
unhexlify = binascii.unhexlify

# # Connect to bitcoind through RPC
select_chain_params("bitcoin/testnet")

# TODO: Figure out when its necessary to pass connection into a function and when it isn't. (Compare store and load which both work)
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


def update_fee(file_name, fee):
    # # Load the transaction which will be updated with an additional input to bump the fee.
    sid = file_name.split('_')[0]
    tx_name = file_name.split('_')[1]
    try:
        tx = load(str(sid) + '_' + str(tx_name) + '_transaction.pkl')
    except FileNotFoundError:
        tx = load('sent_' + str(sid) + '_' + str(tx_name) + '_transaction.pkl')

    # # Specify which utxo to spend from
    connection = RPCCaller(allow_default_conf=True)
    unspents = connection._call("listunspent", 1, 9999999, [str(
        fee_wallet_address)], True, {"minimumAmount": 0.0})

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

    # # TODO: Generalize this so that a transaction with any number of inputs can be loaded and updated with a fee.
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

    decoded_tx = connection._call('decoderawtransaction', b2x(tx.serialize()))
    print(f"Transaction {decoded_tx['txid']} was updated with fee of {amount} satoshi. \n")
    pprint.pprint(decoded_tx)

    store(tx, file_name, connection)

    return tx
