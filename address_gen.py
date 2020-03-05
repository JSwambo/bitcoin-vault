import hashlib
from bitcoin import SelectParams
from bitcoin.core import b2x
from bitcoin.core.script import *
from bitcoin.wallet import CBitcoinAddress, CBitcoinSecret, P2SHBitcoinAddress, P2WSHBitcoinAddress
from bitcoin.rpc import Proxy

SelectParams("regtest")

# Create AW, RW and secret and public keys

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

# Create dummy address for newly minted coins
dummy_redeemScript = CScript([AW_privkeys[0], OP_CHECKSIG])
dummy_address = P2SHBitcoinAddress.from_redeemScript(dummy_redeemScript)


# Create P2WSH address for depositor.
depositor_witnessScript = CScript([depositor_pubkey, OP_CHECKSIG])
depositor_scripthash = hashlib.sha256(depositor_witnessScript).digest()
depositor_redeemScript = CScript([OP_0, depositor_scripthash])
depositor_address = P2WSHBitcoinAddress.from_scriptPubKey(
    depositor_redeemScript)


# Create P2WSH vault address.
vault_in_witnessScript = CScript([vault_in_pubkey, OP_CHECKSIG])
vault_in_scripthash = hashlib.sha256(vault_in_witnessScript).digest()
vault_in_redeemScript = CScript([OP_0, vault_in_scripthash])
vault_in_address = P2WSHBitcoinAddress.from_scriptPubKey(vault_in_redeemScript)


# Create P2SH output address for vault tx.
timelock = 5
vault_out_redeemScript = CScript([OP_IF, timelock, OP_CHECKSEQUENCEVERIFY, OP_DROP,
                                  2, AW_pubkeys[0], AW_pubkeys[1], AW_pubkeys[2], 3, OP_CHECKMULTISIG,
                                  OP_ELSE, 2, RW_pubkeys[0], RW_pubkeys[1], RW_pubkeys[2], 3, OP_CHECKMULTISIG, OP_ENDIF])
vault_out_scriptPubkey = vault_out_redeemScript.to_p2sh_scriptPubKey()
vault_out_address = CBitcoinAddress.from_scriptPubKey(vault_out_scriptPubkey)


# Create P2SH output address for P2RW tx
p2rw_out_redeemScript = CScript(
    [OP_2, RW_pubkeys[0], RW_pubkeys[1], RW_pubkeys[2], OP_3, OP_CHECKMULTISIG])
serialized_p2rw_out_redeemScript = b2x(p2rw_out_redeemScript)  # hex
p2rw_out_address = P2SHBitcoinAddress.from_redeemScript(
    p2rw_out_redeemScript)
