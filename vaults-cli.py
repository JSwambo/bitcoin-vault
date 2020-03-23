from protocol_errors import ProtocolError
from generate_addresses import *
import transaction_template as tt
import handle_transaction as ht
import os
import argparse


def new(file_name, transaction_type):
    if transaction_type == 'deposit':
        tx = tt.new_deposit_transaction(file_name)

    elif transaction_type == 'consolidate':
        tx = tt.new_consolidation_transaction(file_name)

    elif transaction_type == 'vault':
        tx = tt.new_vault_transaction(file_name)

    elif transaction_type == 'unvault':
        tx = tt.new_unvault_transaction_dynamic_fee(file_name)

    elif transaction_type == 'p2rw':
        tx = tt.new_p2rw_transaction_dynamic_fee(file_name)

    elif transaction_type == 'recover':
        tx = tt.new_recover_transaction(file_name)

    return tx


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="""Create and sign a transaction or load a transaction and optionally broadcast it. 
        Transaction types:
            Consolidation,
            Deposit, 
            Vault, 
            Unvault,
            P2RW,  
            Recover.
            """)

    group = parser.add_mutually_exclusive_group()
    group.add_argument('-c', '--consolidate', action='store_const',
                       const='consolidation_transaction.pkl')
    group.add_argument('-d', '--deposit', action='store_const',
                       const='deposit_transaction.pkl')
    group.add_argument('-v', '--vault', action='store_const',
                       const='vault_transaction.pkl')
    group.add_argument('-u', '--unvault', action='store_const',
                       const='unvault_transaction.pkl')
    group.add_argument('-p', '--p2rw', action='store_const',
                       const='p2rw_transaction.pkl')
    group.add_argument('-r', '--recover', action='store_const',
                       const='recover_transaction.pkl')

    parser.add_argument('--new', action='store_true')
    parser.add_argument('--load', action='store_true')
    parser.add_argument('--broadcast', action='store_true')
    parser.add_argument('--add_fee', action='store', nargs=1, default=None)
    parser.add_argument('-sid', '--session_id',
                        action='store', nargs='?', default=0)

    args = vars(parser.parse_args())

    sid = args['session_id']
    if len(sid.split("_")) != 1:
        raise(ProtocolError("Please don't use underscores for the session_id text."))
    try:
        fee = float(args['add_fee'][0])
    except(TypeError):
        fee = None

    transaction_type = {key: value for (
        key, value) in args.items() if type(value) == str}
    if transaction_type == {}:
        raise(ProtocolError(
            'Please provide a valid transaction type (any of: --consolidate, --deposit, --vault, --unvault or --recover)'))
    else:
        file_name = str(sid) + '_' + \
            [value for (key, value) in transaction_type.items()][0]

    script_procedures = {key: value for (key, value) in args.items() if key in [
        'new', 'load', 'broadcast']}

    if not any(script_procedures.values()):
        raise(ProtocolError(
            'Please provide one or more of the following instructions; --new, --load, --broadcast'))

    if script_procedures['new'] and script_procedures['load']:
        raise(ProtocolError(
            f'Cannot simultaneously create and load {file_name}'))

    connection = RPCCaller(allow_default_conf=True)

    if script_procedures['new']:
        tx = new(file_name, list(transaction_type)[0])
        if fee:
            ht.update_fee(file_name, fee)

    if script_procedures['load']:
        if fee:
            tx = ht.update_fee(file_name, fee)
        else:
            tx = ht.load(file_name)

    # # Broadcast the transaction to the network.
    if script_procedures['broadcast']:
        if script_procedures['new'] or script_procedures['load']:
            ht.broadcast(tx, connection)
            os.rename(file_name, "sent_" + file_name)
        else:
            raise(ProtocolError(
                f'Please either load or create a new {file_name} to broadcast.'))
