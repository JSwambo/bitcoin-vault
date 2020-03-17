# Bitcoin-vault
Implementation of a time-locked vault covenant using pre-signed transactions with secure key deletion.

Use these scripts to construct (vault, push-to-recovery) covenant transaction pairs. These scripts are for prototyping (bitcoin) Script variants and investigating how mempool policies regarding fees and dependent transactions will affect the intended use of these covenant pairs in custody protocols. 

# Dependencies
These scripts require a running instance of bitcoin core in testnet mode. 
This protocol requires python-bitcointx. 

# Usage

First run generate_addresses.py to get an address to fund with testnet coins, and to import the address and private keys to bitcoind.

Then use vaults-cli.py to create (--new flag), load (--load flag), and spend (--broadcast flag) various transaction types used in this protocol. The transaction types are utxo consolidation transaction (-c), deposit-to-vault transaction (-d), vault transaction (-v), unvault transaction (-u), push-to-recovery-wallet transaction (-p), recover transaction (-r). A session ID can be specified (-sid [num]) to ensure that saved transactions from a session aren't read or written to in a different session. 

