from helios.utils.async_dispatch import (
    async_method,
)


class AsyncChainMixin:

    coro_get_canonical_block_by_number = async_method('get_canonical_block_by_number')
    coro_get_block_by_hash = async_method('get_block_by_hash')
    coro_get_block_by_header = async_method('get_block_by_header')

    coro_import_block = async_method('import_block')
    coro_import_chain = async_method('import_chain')
    coro_get_block_stake_from_children = async_method('get_block_stake_from_children')
    coro_get_mature_stake = async_method('get_mature_stake')
    coro_get_all_chronological_blocks_for_window = async_method('get_all_chronological_blocks_for_window')
    coro_import_chronological_block_window = async_method('import_chronological_block_window')
    coro_update_current_network_tpc_capability = async_method('update_current_network_tpc_capability')
    coro_get_local_tpc_cap = async_method('get_local_tpc_cap')
    coro_re_initialize_historical_minimum_gas_price_at_genesis = async_method(
        're_initialize_historical_minimum_gas_price_at_genesis')

