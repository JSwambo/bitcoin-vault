"""Functional tests for the prototype code of the Vault-Custody protocol.

The tests include:
    - Test of basic transaction flow for deposit -> vault -> unvault.
    - Test of basic transaction flow for deposit -> vault -> p2rw -> recover.
    - Test of mempool acceptance for unconfirmed deposit, vault, un-vault transactions.
    - Test of mempool acceptance for unconfirmed deposit, vault, p2rw, recover transactions.
    - Test of RBF for unvault and p2rw transactions.
    - Test of recovery from vault transaction theft.
"""
import os
from config import *
from test_framework.test_framework import (
    BitcoinTestFramework,
    TestStatus,
    )
from handle_transaction import load, update_fee
from test_framework.util import connect_nodes, disconnect_nodes
from test_framework.authproxy import JSONRPCException
from generate_addresses import depositor_address, fee_wallet_address
from transaction_template import (
    new_deposit_transaction, 
    new_vault_transaction, 
    new_unvault_transaction,
    new_p2rw_transaction,
    new_recover_transaction,
    )
from bitcointx.core import b2x
from bitcointx.core import CTransaction

class VaultCustodyTest(BitcoinTestFramework):

    def set_test_params(self):
        self.num_nodes = 3

        self.extra_args = [
            [
                    '-segwitheight=1'
            ],
            [
                    '-segwitheight=1'
            ],
            [
                    '-segwitheight=1'
            ],
        ]

    def setup_network(self):

        self.setup_nodes()
        connect_nodes(self.nodes[0], 1)
        connect_nodes(self.nodes[0], 2)

    def run_test(self):
        """Main test logic"""

        self.log.info(f"Generating 10 utxos for node 0 at Depositor Address and Fee Wallet Address")
        node = self.nodes[0]
        node.generate(100)
        node.importaddress(address=str(depositor_address), label="Depositor Address", rescan=False)
        node.importaddress(address=str(fee_wallet_address), label="Fee Wallet Address", rescan=False)
        self.nodes[1].importaddress(address=str(fee_wallet_address), label="Fee Wallet Address", rescan=False)
        for i in range(0,10):
            node.sendtoaddress(address=str(depositor_address), amount=50)
            node.sendtoaddress(address=str(fee_wallet_address), amount=0.0001)
        node.generate(1)

        self.log.info(f"Testing basic transaction flow for deposit -> vault -> unvault.")
        self.test_unvault_tx_flow()

        self.log.info(f"Testing basic transaction flow for deposit -> vault -> p2rw -> recover.")
        self.test_recovery_tx_flow()

        self.log.info(f"Testing mempool acceptance for unconfirmed deposit, vault, un-vault transactions.")
        self.test_mempool_accept_unconfirmed_ancestors_unvault()

        self.log.info(f"Testing mempool acceptance for unconfirmed deposit, vault, p2rw, recover transactions.")
        self.test_mempool_accept_unconfirmed_ancestors_recovery()

        self.log.info(f"Testing RBF for unvault and p2rw transactions.")
        self.test_RBF()

        self.log.info(f"Testing recovery from vault transaction theft.")
        self.test_vault_theft_recover()

        self.tear_down()

        self.success = TestStatus.PASSED

    def test_unvault_tx_flow(self):
        node = self.nodes[0]
        
        unspents = node.listunspent(minconf=1, addresses=[str(depositor_address)], include_unsafe=True, query_options={"minimumAmount": 0.0})
        new_deposit_transaction(TEST_DATADIR + "/test_deposit_transaction.pkl", unspents)
        deposit_tx = load(TEST_DATADIR + "/test_deposit_transaction.pkl")
        decoded_tx = node.decoderawtransaction(b2x(deposit_tx.serialize()))
        node.sendrawtransaction(b2x(deposit_tx.serialize()))
        self.log.info(f"Deposit Transaction with txid {decoded_tx['txid']} accepted.")
        node.generate(1)
        self.log.info(f"Deposit Transaction with txid {decoded_tx['txid']} mined.")

        new_vault_transaction(TEST_DATADIR + "/test_vault_transaction.pkl")
        vault_tx = load(TEST_DATADIR + "/test_vault_transaction.pkl")
        decoded_tx = node.decoderawtransaction(b2x(vault_tx.serialize()))
        node.sendrawtransaction(b2x(vault_tx.serialize()))
        self.log.info(f"Vault Transaction with txid {decoded_tx['txid']} accepted.")
        node.generate(1)
        self.log.info(f"Vault Transaction with txid {decoded_tx['txid']} mined.")

        new_unvault_transaction(TEST_DATADIR + "/test_unvault_transaction.pkl")
        unvault_tx = load(TEST_DATADIR + "/test_unvault_transaction.pkl")
        decoded_tx = node.decoderawtransaction(b2x(unvault_tx.serialize()))
        try: # Expect transaction rejection (non-BIP68-final)
            node.sendrawtransaction(b2x(unvault_tx.serialize()))
        except(JSONRPCException):
            node.generate(TIMELOCK-1) # Wait for time-lock to expire
            node.sendrawtransaction(b2x(unvault_tx.serialize()))
        self.log.info(f"Un-vault Transaction with txid {decoded_tx['txid']} accepted.")
        node.generate(1)
        self.log.info(f"Un-vault Transaction with txid {decoded_tx['txid']} mined.")

    def test_recovery_tx_flow(self):
        node = self.nodes[0]
        
        unspents = node.listunspent(minconf=1, addresses=[str(depositor_address)], include_unsafe=True, query_options={"minimumAmount": 0.0})
        new_deposit_transaction(TEST_DATADIR + "/test_deposit_transaction.pkl", unspents)
        deposit_tx = load(TEST_DATADIR + "/test_deposit_transaction.pkl")
        decoded_tx = node.decoderawtransaction(b2x(deposit_tx.serialize()))
        node.sendrawtransaction(b2x(deposit_tx.serialize()))
        self.log.info(f"Deposit Transaction with txid {decoded_tx['txid']} accepted.")
        node.generate(1)
        self.log.info(f"Deposit Transaction with txid {decoded_tx['txid']} mined.")

        new_vault_transaction(TEST_DATADIR + "/test_vault_transaction.pkl")
        vault_tx = load(TEST_DATADIR + "/test_vault_transaction.pkl")
        decoded_tx = node.decoderawtransaction(b2x(vault_tx.serialize()))
        node.sendrawtransaction(b2x(vault_tx.serialize()))
        self.log.info(f"Vault Transaction with txid {decoded_tx['txid']} accepted.")
        node.generate(1)
        self.log.info(f"Vault Transaction with txid {decoded_tx['txid']} mined.")

        new_p2rw_transaction(TEST_DATADIR + "/test_p2rw_transaction.pkl")
        p2rw_tx = load(TEST_DATADIR + "/test_p2rw_transaction.pkl")
        decoded_tx = node.decoderawtransaction(b2x(p2rw_tx.serialize()))
        node.sendrawtransaction(b2x(p2rw_tx.serialize()))
        self.log.info(f"P2RW Transaction with txid {decoded_tx['txid']} accepted.")
        node.generate(1)
        self.log.info(f"P2RW Transaction with txid {decoded_tx['txid']} mined.")

        new_recover_transaction(TEST_DATADIR + "/test_recover_transaction.pkl")
        recover_tx = load(TEST_DATADIR + "/test_recover_transaction.pkl")
        decoded_tx = node.decoderawtransaction(b2x(recover_tx.serialize()))
        node.sendrawtransaction(b2x(recover_tx.serialize()))
        self.log.info(f"Recover Transaction with txid {decoded_tx['txid']} accepted.")
        node.generate(1)
        self.log.info(f"Recover Transaction with txid {decoded_tx['txid']} mined.")

    def test_mempool_accept_unconfirmed_ancestors_unvault(self):
        node = self.nodes[0]

        unspents = node.listunspent(minconf=1, addresses=[str(depositor_address)], include_unsafe=True, query_options={"minimumAmount": 0.0})
        new_deposit_transaction(TEST_DATADIR + "/test_deposit_transaction.pkl", unspents)
        deposit_tx = load(TEST_DATADIR + "/test_deposit_transaction.pkl")
        decoded_tx = node.decoderawtransaction(b2x(deposit_tx.serialize()))
        node.sendrawtransaction(b2x(deposit_tx.serialize()))
        self.log.info(f"Deposit Transaction with txid {decoded_tx['txid']} accepted.")

        new_vault_transaction(TEST_DATADIR + "/test_vault_transaction.pkl")
        vault_tx = load(TEST_DATADIR + "/test_vault_transaction.pkl")
        decoded_tx = node.decoderawtransaction(b2x(vault_tx.serialize()))
        node.sendrawtransaction(b2x(vault_tx.serialize()))
        self.log.info(f"Vault Transaction with txid {decoded_tx['txid']} accepted.")

        new_unvault_transaction(TEST_DATADIR + "/test_unvault_transaction.pkl")
        unvault_tx = load(TEST_DATADIR + "/test_unvault_transaction.pkl")
        decoded_tx = node.decoderawtransaction(b2x(unvault_tx.serialize()))
        try:
            node.sendrawtransaction(b2x(unvault_tx.serialize()))
        except(JSONRPCException):
            self.log.info(f"Un-vault Transaction with txid {decoded_tx['txid']} rejected (non-BIP68-final).")

    def test_mempool_accept_unconfirmed_ancestors_recovery(self):
        node = self.nodes[0]

        unspents = node.listunspent(minconf=1, addresses=[str(depositor_address)], include_unsafe=True, query_options={"minimumAmount": 0.0})
        new_deposit_transaction(TEST_DATADIR + "/test_deposit_transaction.pkl", unspents)
        deposit_tx = load(TEST_DATADIR + "/test_deposit_transaction.pkl")
        decoded_tx = node.decoderawtransaction(b2x(deposit_tx.serialize()))
        node.sendrawtransaction(b2x(deposit_tx.serialize()))
        self.log.info(f"Deposit Transaction with txid {decoded_tx['txid']} accepted.")

        new_vault_transaction(TEST_DATADIR + "/test_vault_transaction.pkl")
        vault_tx = load(TEST_DATADIR + "/test_vault_transaction.pkl")
        decoded_tx = node.decoderawtransaction(b2x(vault_tx.serialize()))
        node.sendrawtransaction(b2x(vault_tx.serialize()))
        self.log.info(f"Vault Transaction with txid {decoded_tx['txid']} accepted.")

        new_p2rw_transaction(TEST_DATADIR + "/test_p2rw_transaction.pkl")
        p2rw_tx = load(TEST_DATADIR + "/test_p2rw_transaction.pkl")
        decoded_tx = node.decoderawtransaction(b2x(p2rw_tx.serialize()))
        node.sendrawtransaction(b2x(p2rw_tx.serialize()))
        self.log.info(f"P2RW Transaction with txid {decoded_tx['txid']} accepted.")

        new_recover_transaction(TEST_DATADIR + "/test_recover_transaction.pkl")
        recover_tx = load(TEST_DATADIR + "/test_recover_transaction.pkl")
        decoded_tx = node.decoderawtransaction(b2x(recover_tx.serialize()))
        node.sendrawtransaction(b2x(recover_tx.serialize()))
        self.log.info(f"Recover Transaction with txid {decoded_tx['txid']} accepted.")

    def test_RBF(self):
        node = self.nodes[0]
        
        deposit_address_unspents = node.listunspent(minconf=1, addresses=[str(depositor_address)], include_unsafe=True, query_options={"minimumAmount": 0.0})
        new_deposit_transaction(TEST_DATADIR + "/test_deposit_transaction.pkl", deposit_address_unspents)
        deposit_tx = load(TEST_DATADIR + "/test_deposit_transaction.pkl")
        decoded_tx = node.decoderawtransaction(b2x(deposit_tx.serialize()))
        node.sendrawtransaction(b2x(deposit_tx.serialize()))
        self.log.info(f"Deposit Transaction with txid {decoded_tx['txid']} accepted.")

        new_vault_transaction(TEST_DATADIR + "/test_vault_transaction.pkl")
        vault_tx = load(TEST_DATADIR + "/test_vault_transaction.pkl")
        decoded_tx = node.decoderawtransaction(b2x(vault_tx.serialize()))
        node.sendrawtransaction(b2x(vault_tx.serialize()))
        self.log.info(f"Vault Transaction with txid {decoded_tx['txid']} accepted.")
        node.generate(TIMELOCK)
        self.log.info(f"Deposit and Vault Transactions mined.")

        self.sync_all() # Synce node 0 and 1 after mining deposit and vault transactions.
        disconnect_nodes(self.nodes[0], 1) # Now split the network to test transaction types on different nodes.

        # Use node 0 to test update fee for unvault transaction
        new_unvault_transaction(TEST_DATADIR + "/test_unvault_transaction.pkl")
        unvault_tx = load(TEST_DATADIR + "/test_unvault_transaction.pkl")
        decoded_tx = node.decoderawtransaction(b2x(unvault_tx.serialize()))
        node.sendrawtransaction(b2x(unvault_tx.serialize()))
        self.log.info(f"Un-vault Transaction with txid {decoded_tx['txid']} accepted by node 0.")
        fee_wallet_unspents = node.listunspent(minconf=1, addresses=[str(fee_wallet_address)], include_unsafe=True, query_options={"minimumAmount": 0.0})
        unvault_tx = update_fee(TEST_DATADIR + "/test_unvault_transaction.pkl", 0.0001, fee_wallet_unspents)
        decoded_tx = node.decoderawtransaction(b2x(unvault_tx.serialize()))
        node.sendrawtransaction(b2x(unvault_tx.serialize()))
        self.log.info(f"Updated Un-vault Transaction with txid {decoded_tx['txid']} accepted by node 0.")
        node.generate(1)
        self.log.info(f"Un-vault Transaction with txid {decoded_tx['txid']} mined by node 0.")

        # Use node 1 to test update fee for pr2w transaction
        node = self.nodes[1]
        new_p2rw_transaction(TEST_DATADIR + "/test_p2rw_transaction.pkl")
        p2rw_tx = load(TEST_DATADIR + "/test_p2rw_transaction.pkl")
        decoded_tx = node.decoderawtransaction(b2x(p2rw_tx.serialize()))
        node.sendrawtransaction(b2x(p2rw_tx.serialize()))
        self.log.info(f"P2RW Transaction with txid {decoded_tx['txid']} accepted by node 1.")
        fee_wallet_unspents = node.listunspent(minconf=1, addresses=[str(fee_wallet_address)], include_unsafe=True, query_options={"minimumAmount": 0.0})
        p2rw_tx = update_fee(TEST_DATADIR + "/test_p2rw_transaction.pkl", 0.0001, fee_wallet_unspents)
        decoded_tx = node.decoderawtransaction(b2x(p2rw_tx.serialize()))
        node.sendrawtransaction(b2x(p2rw_tx.serialize()))
        self.log.info(f"Updated P2RW Transaction with txid {decoded_tx['txid']} accepted by node 1.")
        node.generate(1)
        self.log.info(f"P2RW Transaction with txid {decoded_tx['txid']} mined by node 1.")

    def test_vault_theft_recover(self):
        node0 = self.nodes[0] # Wallet Owner
        node2 = self.nodes[2] # Attacker
        
        deposit_address_unspents = node0.listunspent(minconf=1, addresses=[str(depositor_address)], include_unsafe=True, query_options={"minimumAmount": 0.0})
        new_deposit_transaction(TEST_DATADIR + "/test_deposit_transaction.pkl", deposit_address_unspents)
        deposit_tx = load(TEST_DATADIR + "/test_deposit_transaction.pkl")
        decoded_tx = node0.decoderawtransaction(b2x(deposit_tx.serialize()))
        node0.sendrawtransaction(b2x(deposit_tx.serialize()))
        self.log.info(f"Deposit Transaction with txid {decoded_tx['txid']} accepted.")

        new_vault_transaction(TEST_DATADIR + "/test_vault_transaction.pkl")
        vault_tx = load(TEST_DATADIR + "/test_vault_transaction.pkl")
        decoded_tx = node0.decoderawtransaction(b2x(vault_tx.serialize()))
        node0.sendrawtransaction(b2x(vault_tx.serialize()))
        self.log.info(f"Vault Transaction with txid {decoded_tx['txid']} accepted.")

        new_p2rw_transaction(TEST_DATADIR + "/test_p2rw_transaction.pkl")
        p2rw_tx = load(TEST_DATADIR + "/test_p2rw_transaction.pkl")
        fee_wallet_unspents = node0.listunspent(minconf=1, addresses=[str(fee_wallet_address)], include_unsafe=True, query_options={"minimumAmount": 0.0})
        p2rw_tx = update_fee(TEST_DATADIR + "/test_p2rw_transaction.pkl", 0.0001, fee_wallet_unspents)
        self.log.info("P2RW transaction prepared with high fee.")

        node0.generate(1)
        self.log.info(f"Deposit and Vault Transactions mined.")

        new_unvault_transaction(TEST_DATADIR + "/test_unvault_transaction.pkl")
        unvault_tx = load(TEST_DATADIR + "/test_unvault_transaction.pkl")
        decoded_tx = node2.decoderawtransaction(b2x(unvault_tx.serialize()))
        try:
            node2.sendrawtransaction(b2x(unvault_tx.serialize()))
        except(JSONRPCException):
            self.log.info(f"Un-vault Transaction broadcast early by attacker, rejected since time-lock not expired.")
        node2.generate(TIMELOCK-1)
        self.log.info("Time-lock expired, theft transaction broadcast again by attacker.")
        node2.sendrawtransaction(b2x(unvault_tx.serialize()))
        node0.sendrawtransaction(b2x(p2rw_tx.serialize()))
        self.log.info(f"P2RW Transaction broadcast by wallet owner and replaced attacker's theft transaction.")
        node0.generate(1)
        self.log.info(f"P2RW Transaction with txid {decoded_tx['txid']} mined.")

    def tear_down(self):
        os.remove(TEST_DATADIR + "/test_deposit_transaction.pkl")
        os.remove(TEST_DATADIR + "/test_vault_transaction.pkl")
        os.remove(TEST_DATADIR + "/test_unvault_transaction.pkl")
        os.remove(TEST_DATADIR + "/test_p2rw_transaction.pkl")
        os.remove(TEST_DATADIR + "/test_recover_transaction.pkl")
        self.log.info("Deleted all persisted data used in testing.")


if __name__ == '__main__':
    VaultCustodyTest().main()