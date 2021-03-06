import os

import rlp_cython as rlp

from cytoolz import first

from eth_utils import (
    to_normalized_address,
)

from hvm import MainnetChain
from hvm.db.atomic import AtomicDB
from hvm.utils.state import (
    diff_account_db,
)
from hvm.vm.forks import (
    HeliosTestnetVM
)


#
# State Setup
#
def setup_account_db(desired_state, account_db):
    for account, account_data in desired_state.items():
        for slot, value in account_data['storage'].items():
            account_db.set_storage(account, slot, value)

        nonce = account_data['nonce']
        code = account_data['code']
        balance = account_data['balance']

        account_db.set_nonce(account, nonce)
        account_db.set_code(account, code)
        account_db.set_balance(account, balance)
    account_db.persist()


def verify_account_db(expected_state, account_db):
    diff = diff_account_db(expected_state, account_db)
    if diff:
        error_messages = []
        for account, field, actual_value, expected_value in diff:
            if field == 'balance':
                error_messages.append(
                    "{0}({1}) | Actual: {2} | Expected: {3} | Delta: {4}".format(
                        to_normalized_address(account),
                        'balance',
                        actual_value,
                        expected_value,
                        expected_value - actual_value,
                    )
                )
            else:
                error_messages.append(
                    "{0}({1}) | Actual: {2} | Expected: {3}".format(
                        to_normalized_address(account),
                        field,
                        actual_value,
                        expected_value,
                    )
                )
        raise AssertionError(
            "State DB did not match expected state on {0} values:\n"
            "{1}".format(
                len(error_messages),
                "\n - ".join(error_messages),
            )
        )


def chain_vm_configuration(fixture):
    network = fixture['network']

    if network == 'HeliosTestnet':
        return (
            (0, HeliosTestnetVM),
        )
    else:
        raise ValueError("Network {0} does not match any known VM rules".format(network))


def genesis_params_from_fixture(fixture):
    return {
        'parent_hash': fixture['genesisBlockHeader']['parentHash'],
        'uncles_hash': fixture['genesisBlockHeader']['uncleHash'],
        'coinbase': fixture['genesisBlockHeader']['coinbase'],
        'state_root': fixture['genesisBlockHeader']['stateRoot'],
        'transaction_root': fixture['genesisBlockHeader']['transactionsTrie'],
        'receipt_root': fixture['genesisBlockHeader']['receiptTrie'],
        'bloom': fixture['genesisBlockHeader']['bloom'],
        'difficulty': fixture['genesisBlockHeader']['difficulty'],
        'block_number': fixture['genesisBlockHeader']['number'],
        'gas_limit': fixture['genesisBlockHeader']['gasLimit'],
        'gas_used': fixture['genesisBlockHeader']['gasUsed'],
        'timestamp': fixture['genesisBlockHeader']['timestamp'],
        'extra_data': fixture['genesisBlockHeader']['extraData'],
        'mix_hash': fixture['genesisBlockHeader']['mixHash'],
        'nonce': fixture['genesisBlockHeader']['nonce'],
    }


def new_chain_from_fixture(fixture, chain_cls=MainnetChain):
    base_db = AtomicDB()

    vm_config = chain_vm_configuration(fixture)

    ChainFromFixture = chain_cls.configure(
        'ChainFromFixture',
        vm_configuration=vm_config,
    )

    return ChainFromFixture.from_genesis(
        base_db,
        genesis_params=genesis_params_from_fixture(fixture),
        genesis_state=fixture['pre'],
    )


def apply_fixture_block_to_chain(block_fixture, chain):
    '''
    :return: (premined_block, mined_block, rlp_encoded_mined_block)
    '''
    # The block to import may be in a different block-class-range than the
    # chain's current one, so we use the block number specified in the
    # fixture to look up the correct block class.
    if 'blockHeader' in block_fixture:
        block_number = block_fixture['blockHeader']['number']
        block_class = chain.get_vm_class_for_block_number(block_number).get_block_class()
    else:
        block_class = chain.get_vm().get_block_class()

    block = rlp.decode(block_fixture['rlp_templates'], sedes=block_class)

    mined_block, _, _ = chain.import_block(block)

    rlp_encoded_mined_block = rlp.encode(mined_block, sedes=block_class)

    return (block, mined_block, rlp_encoded_mined_block)


def should_run_slow_tests():
    if os.environ.get('TRAVIS_EVENT_TYPE') == 'cron':
        return True
    return False


def get_test_name(filler):
    assert len(filler) == 1
    return first(filler)
