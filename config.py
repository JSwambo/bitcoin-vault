import sys

PATH_TO_FUNCTIONAL = "~/bitcoin/test/functional"
PATH_TO_BITCOINTX = "~/python-bitcointx"
TEST_DATADIR = "tests/data"

sys.path.insert(0, PATH_TO_BITCOINTX)
sys.path.insert(0, PATH_TO_FUNCTIONAL)

from bitcointx import select_chain_params
from bitcointx.core import coins_to_satoshi

select_chain_params("bitcoin/regtest")

MIN_FEE = coins_to_satoshi(0.00000169)
TIMELOCK = 3
PORTION_TO_VAULT = 0.1