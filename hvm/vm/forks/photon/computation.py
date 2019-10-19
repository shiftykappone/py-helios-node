from eth_utils.toolz import (
    merge,
)
from hvm.utils.address import force_bytes_to_address
from hvm.vm.forks.boson import BosonComputation
from hvm.vm.forks.boson.computation import BOSON_PRECOMPILES

from hvm.vm.forks.photon.transaction_context import PhotonTransactionContext
from hvm.vm.gas_meter import GasMeter, allow_negative_refund_strategy

from .opcodes import PHOTON_OPCODES

from hvm import constants

from hvm.utils.hexadecimal import (
    encode_hex,
)

from hvm.exceptions import (
    InsufficientFunds,
    StackDepthLimit,
)
from .constants import (
    GAS_ECADD,
    GAS_ECMUL,
    GAS_ECPAIRING_BASE,
    GAS_ECPAIRING_PER_POINT,
)

from typing import TYPE_CHECKING
from hvm import precompiles
if TYPE_CHECKING:
    from hvm.vm.forks.photon.state import PhotonState


PHOTON_PRECOMPILES = merge(
    BOSON_PRECOMPILES,
    {
        force_bytes_to_address(b'\x06'): precompiles.ecadd(gas_cost=GAS_ECADD),
        force_bytes_to_address(b'\x07'): precompiles.ecmul(gas_cost=GAS_ECMUL),
        force_bytes_to_address(b'\x08'): precompiles.ecpairing(
            gas_cost_base=GAS_ECPAIRING_BASE,
            gas_cost_per_point=GAS_ECPAIRING_PER_POINT,
        ),
        force_bytes_to_address(b'\x09'): precompiles.blake2b_fcompress,
    },
)

class PhotonComputation(BosonComputation):
    """
    A class for all execution computations in the ``Byzantium`` fork.
    Inherits from :class:`~hvm.vm.forks.spurious_dragon.computation.SpuriousDragonComputation`
    """
    # Override
    opcodes = PHOTON_OPCODES
    _precompiles = PHOTON_PRECOMPILES

    transaction_context: PhotonTransactionContext = None
    state: 'PhotonState' = None

    #
    # Gas Meter
    #

    def get_gas_meter(self) -> GasMeter:
        return GasMeter(
            self.msg.gas,
            allow_negative_refund_strategy
        )



    def apply_message(self, validate=True):
        snapshot = self.state.snapshot()
        # Take a snapshot of the current computation call nonce so that it can be reset if the computation fails
        computation_call_nonce_snapshot = self.state.execution_context.computation_call_nonce

        if self.msg.depth > constants.STACK_DEPTH_LIMIT:
            raise StackDepthLimit("Stack depth limit reached")

        if self.msg.should_transfer_value:
            if self.transaction_context.is_refund:
                if self.msg.refund_amount:
                    self.state.account_db.delta_balance(self.transaction_context.this_chain_address, self.msg.refund_amount)
                    self.logger.debug(
                        "REFUNDED: %s into %s",
                        self.msg.refund_amount,
                        encode_hex(self.transaction_context.this_chain_address),
                    )

            elif self.transaction_context.is_receive:

                if self.msg.value:
                    self.state.account_db.delta_balance(self.transaction_context.this_chain_address, self.msg.value)
                    self.logger.debug(
                        "RECEIVED: %s into %s",
                        self.msg.value,
                        encode_hex(self.transaction_context.this_chain_address),
                    )
            elif self.msg.value:
                # this is a send transaction
                if validate:
                    sender_balance = self.state.account_db.get_balance(self.transaction_context.this_chain_address)

                    if sender_balance < self.msg.value:
                        raise InsufficientFunds(
                            "Insufficient funds: {0} < {1}".format(sender_balance, self.msg.value)
                        )

                self.state.account_db.delta_balance(self.transaction_context.this_chain_address, -1 * self.msg.value)

                self.logger.debug(
                    "SENT: %s from %s to pending transactions",
                    self.msg.value,
                    encode_hex(self.transaction_context.this_chain_address),
                )

        self.state.account_db.touch_account(self.transaction_context.this_chain_address)

        if self.transaction_context.is_refund:
            # We never run computations on a refund
            self.state.commit(snapshot)
            computation = self

        elif self.transaction_context.is_receive:
            # this is when we run all computation normally

            computation = self.apply_computation(
                self.state,
                self.msg,
                self.transaction_context,
            )

            if computation.is_error:
                self.state.revert(snapshot)

                # Reset the computation call nonce on error.
                self.state.execution_context.computation_call_nonce = computation_call_nonce_snapshot
            else:
                self.state.commit(snapshot)

        else:
            # this is a send transaction. We only run computation if is_create = True, and in that case we only run it to determine
            # the gas cost. So we create a snapshot to remove any changes other thank calculating gas cost.
            # It will also run here if execute_on_send == True

            if self.msg.is_create:
                computation_snapshot = self.state.snapshot()
                initial_create_computation_call_nonce = self.state.execution_context.computation_call_nonce

                # need to set this_chain_address to the deployed address
                initial_this_chain_address = self.transaction_context.this_chain_address
                self.transaction_context.this_chain_address = self.msg.create_address

                # temporarily increase the balance on the receiver chain by the value amount
                self.state.account_db.delta_balance(self.transaction_context.this_chain_address, self.msg.value)

                computation = self.apply_computation(
                    self.state,
                    self.msg,
                    self.transaction_context,
                )

                # reset the changed variables
                self.transaction_context.this_chain_address = initial_this_chain_address

                if computation.is_error:
                    # This will revert the computation snapshot as well.
                    self.logger.debug(
                        "CREATE COMPUTATION FAILED ON SEND. NOT DEPLOYING."
                    )
                    self.state.revert(snapshot)
                    self.state.execution_context.computation_call_nonce = computation_call_nonce_snapshot
                else:
                    # computation worked, but we don't want it yet until the receive transaction. So lets revert the computation
                    # but commit the transaction above.
                    self.logger.debug(
                        "REVERTING COMPUTATION FOR CONTRACT DEPLOYMENT. WILL DEPLOY ON RECEIVE TX."
                    )
                    self.state.revert(computation_snapshot)
                    self.state.execution_context.computation_call_nonce = initial_create_computation_call_nonce
                    self.state.commit(snapshot)



            elif self.transaction_context.tx_execute_on_send:
                computation = self.apply_computation(
                    self.state,
                    self.msg,
                    self.transaction_context,
                )

                if computation.is_error:
                    # This will revert the computation snapshot as well.
                    self.state.revert(snapshot)
                    self.state.execution_context.computation_call_nonce = computation_call_nonce_snapshot
                else:
                    self.logger.debug(
                        "SUCCESSFULLY EXECUTED SEND PORTION OF TRANSACTION"
                    )
                    self.state.commit(snapshot)

            else:
                computation = self

        return computation