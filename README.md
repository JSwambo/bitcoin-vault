# bitcoin-vault
Implementation of a time-locked vault covenant using pre-signed transactions with secure key deletion.

Use these scripts to construct (vault, push-to-recovery) covenant transaction pairs. These scripts are for prototyping (bitcoin) Script variants and investigating how mempool policies regarding fees and dependent transactions will affect the intended use of these covenant pairs in custody protocols. 

# Dependencies
These scripts require an instance bitcoin core running. 
This protocol requires python-bitcoinlib. 

