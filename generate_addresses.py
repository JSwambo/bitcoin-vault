import hashlib
from bitcointx import select_chain_params, get_current_chain_params
from bitcointx.core import b2x
from bitcointx.core.script import *
from bitcointx.wallet import CCoinAddress, CBitcoinSecret
from bitcointx.rpc import RPCCaller
from config import TIMELOCK
from bitcointx.base58 import encode

# importing binascii to be able to convert hexadecimal strings to binary data
import binascii
unhexlify = binascii.unhexlify

select_chain_params("bitcoin/testnet")

# # Create AW, RW and secret and public keys
AW_privkeys = [
    CBitcoinSecret.from_secret_bytes(
        hashlib.sha256(b'Active Wallet Brain Secret 1').digest()),
    CBitcoinSecret.from_secret_bytes(
        hashlib.sha256(b'Active Wallet Brain Secret 2').digest()),
    CBitcoinSecret.from_secret_bytes(
        hashlib.sha256(b'Active Wallet Brain Secret 3').digest())
]
RW_privkeys = [
    CBitcoinSecret.from_secret_bytes(
        hashlib.sha256(b'Recovery Wallet Brain Secret 1').digest()),
    CBitcoinSecret.from_secret_bytes(
        hashlib.sha256(b'Recovery Wallet Brain Secret 2').digest()),
    CBitcoinSecret.from_secret_bytes(
        hashlib.sha256(b'Recovery Wallet Brain Secret 3').digest())
]

AW_pubkeys = [x.pub for x in AW_privkeys]

RW_pubkeys = [x.pub for x in RW_privkeys]

depositor_privkey = CBitcoinSecret.from_secret_bytes(
    hashlib.sha256(b'Depositor Brain Secret').digest())

depositor_pubkey = depositor_privkey.pub

vault_in_privkey = CBitcoinSecret.from_secret_bytes(
    hashlib.sha256(b'Vault Tx Brain Secret').digest())

vault_in_pubkey = vault_in_privkey.pub

fee_wallet_privkey = CBitcoinSecret.from_secret_bytes(
    hashlib.sha256(b'Fee Wallet Brain Secret').digest())

fee_wallet_pubkey = fee_wallet_privkey.pub


# # Create P2WSH address for depositor.
depositor_witnessScript = CScript([depositor_pubkey, OP_CHECKSIG])
depositor_scripthash = hashlib.sha256(depositor_witnessScript).digest()
depositor_redeemScript = CScript([OP_0, depositor_scripthash])
depositor_address = CCoinAddress.from_scriptPubKey(
    depositor_redeemScript)

# # Create P2WSH address for fee_wallet.
fee_wallet_witnessScript = CScript([fee_wallet_pubkey, OP_CHECKSIG])
fee_wallet_scripthash = hashlib.sha256(fee_wallet_witnessScript).digest()
fee_wallet_redeemScript = CScript([OP_0, fee_wallet_scripthash])
fee_wallet_address = CCoinAddress.from_scriptPubKey(
    fee_wallet_redeemScript)


# # Create P2WSH vault address (used for vault_transaction and p2rw_transaction)
vault_in_witnessScript = CScript([vault_in_pubkey, OP_CHECKSIG])
vault_in_scripthash = hashlib.sha256(vault_in_witnessScript).digest()
vault_in_redeemScript = CScript([OP_0, vault_in_scripthash])
vault_in_address = CCoinAddress.from_scriptPubKey(vault_in_redeemScript)


# # Create P2WSH output address for vault tx.
vault_out_witnessScript = CScript([OP_IF, TIMELOCK, OP_CHECKSEQUENCEVERIFY, OP_DROP,
                                   2, AW_pubkeys[0], AW_pubkeys[1], AW_pubkeys[2], 3, OP_CHECKMULTISIG,
                                   OP_ELSE, vault_in_pubkey, OP_CHECKSIG, OP_ENDIF])
vault_out_scripthash = hashlib.sha256(vault_out_witnessScript).digest()
vault_out_redeemScript = CScript([OP_0, vault_out_scripthash])
vault_out_address = CCoinAddress.from_scriptPubKey(
    depositor_redeemScript)


# # Create P2WSH output address for p2rw transaction
p2rw_out_witnessScript = CScript(
    [OP_2, RW_pubkeys[0], RW_pubkeys[1], RW_pubkeys[2], OP_3, OP_CHECKMULTISIG])
p2rw_out_scripthash = hashlib.sha256(p2rw_out_witnessScript).digest()
p2rw_out_redeemScript = CScript([OP_0, p2rw_out_scripthash])
p2rw_out_address = CCoinAddress.from_scriptPubKey(
    p2rw_out_redeemScript)

if __name__ == '__main__':
    print(f"Pay to main wallet: {depositor_address}")
    print(f"Pay to fee wallet: {fee_wallet_address}")

    connection = RPCCaller(allow_default_conf=True)
    connection._call('importaddress', str(
        depositor_address), "Depositor Address", False)
    connection._call('importaddress', str(fee_wallet_address),
                     "Fee Wallet Address", False)
    connection.close()
