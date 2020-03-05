import os
import time
from address_gen import *

# # Set up clean regtest environment

# Kill any running instances of bitcoind
os.system('killall bitcoind')
time.sleep(2)

# Delete old regtest data
try:
    os.rmdir('~/.bitcoin/regtest/')
except(FileNotFoundError):
    print("Delete failed. No previous regtest data found.")

# Start new instance of bitcoind
os.system('~/bitcoin/src/bitcoind -daemon')
time.sleep(4)

# # Begin vault-custody protocol

# deposit to vault
os.system("python3 deposit_to_vault.py")

# prepare vault transaction
os.system("python3 prepare_vault_tx.py")

# unvault_to_active_wallet.py
os.system("python3 unvault_to_active_wallet.py")

# push_to_recovery_wallet.py
# os.system("python3 push_to_recovery_wallet.py")