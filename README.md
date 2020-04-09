# Bitcoin-vault
This implementation is used to test the correctness of components of the Vault Custody Protocol (as specified in an upcoming research paper). This includes testing the construction of vault covenants and push-to-recovery-wallet covenants. These covenants are implemented using pre-signed transactions with secure key deletion (as specified in a separate upcoming research paper). 

# Dependencies
This implementation requires [python-bitcointx](https://github.com/Simplexum/python-bitcointx), and uses bindings therein to libbitcoinconsensus to verify the transactions.
This implementation requires BitcoinTestFramework from [bitcoin-core/tests/functional](https://github.com/bitcoin/bitcoin/tree/master/test/functional). 

# Usage
These scripts are not intended for real-world use. They may inform the development of a new type of wallet that supports the Vault Custody Protocol. 

Run bitcointestframework.py to generate a local regtest network and perform tests including:\
    - Test of basic transaction flow for deposit -> vault -> unvault.\
    - Test of basic transaction flow for deposit -> vault -> p2rw -> recover.\
    - Test of mempool acceptance for unconfirmed deposit, vault, un-vault transactions.\
    - Test of mempool acceptance for unconfirmed deposit, vault, p2rw, recover transactions.\
    - Test of RBF for unvault and p2rw transactions.\
    - Test of recovery from vault transaction theft.

