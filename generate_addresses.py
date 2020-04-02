import hashlib
from config import *
from bitcointx.core import b2x
from bitcointx.core.script import *
from bitcointx.wallet import CCoinAddress, CBitcoinSecret
import binascii

unhexlify = binascii.unhexlify

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

__all__ = (
    'AW_privkeys',
    'RW_privkeys',
    'AW_pubkeys',
    'RW_pubkeys',
    'depositor_privkey',
    'depositor_pubkey',
    'vault_in_privkey',
    'vault_in_pubkey',
    'fee_wallet_privkey',
    'fee_wallet_pubkey',
    'depositor_witnessScript',
    'depositor_scripthash',
    'depositor_redeemScript',
    'depositor_address',
    'fee_wallet_witnessScript',
    'fee_wallet_scripthash',
    'fee_wallet_redeemScript',
    'fee_wallet_address',
    'vault_in_witnessScript',
    'vault_in_scripthash',
    'vault_in_redeemScript',
    'vault_in_address',
    'vault_out_witnessScript',
    'vault_out_scripthash',
    'vault_out_redeemScript',
    'vault_out_address',
    'p2rw_out_witnessScript',
    'p2rw_out_scripthash',
    'p2rw_out_redeemScript',
    'p2rw_out_address',
)
