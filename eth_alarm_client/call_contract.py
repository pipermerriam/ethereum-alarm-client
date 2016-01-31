import threading
import time
import math

from .block_sage import BlockSage
from .utils import (
    cached_property,
    cache_once,
    get_logger
)

from .contracts import (
    FutureBlockCall,
    CallLib,
)


EMPTY_ADDRESS = '0x0000000000000000000000000000000000000000'
CANCELLATION_WINDOW = 8

MAX_CALL_OVERHEAD_GAS = 200000
DEFAULT_CALL_GAS = 1000000


class CallContract(object):
    """
    Abstraction to represent an upcoming function call.
    """
    txn_hash = None
    txn_receipt = None
    txn = None

    _block_sage = None

    def __init__(self, call_address, blockchain_client, block_sage=None):
        self.blockchain_client = blockchain_client
        self.call_address = call_address
        self.call = FutureBlockCall(call_address, self.blockchain_client)
        self.logger = get_logger('call-{0}'.format(self.call_address))

        if block_sage is None:
            block_sage = BlockSage(self.blockchain_client)

        self._block_sage = block_sage

    @property
    def block_sage(self):
        if self._block_sage is None:
            self.stop()
            self.logger.error("Blocksage unexpectedly `None`")
            raise ValueError("Blocksage unexpectedly `None`")
        if not self._block_sage.is_alive:
            self.stop()
            self.logger.error("Blocksage died.  Killing Call")
            raise ValueError("Blocksage died")
        return self._block_sage

    #
    # Execution Pre Requesites
    #
    @cached_property
    def first_claimable_block(self):
        return self.target_block - 10 - 255

    @cached_property
    def first_profitable_claim_block(self):
        claim_cost = self.CLAIM_GAS_COST * self.blockchain_client.get_gas_price()
        block_number = min(240, int(math.ceil(claim_cost * 1.0 * 240 / self.base_payment)))
        return self.first_claimable_block + block_number

    @cached_property
    def last_claimable_block(self):
        return self.target_block - 10

    @property
    def get_claim_value(self, block_number):
        if block_number < self.first_claimable_block:
            return 0
        if block_number > self.target_block - 10 - 15:
            return self.base_payment
        n = block_number - self.first_claimable_block
        return int(self.base_payment * 1.0 * n / 240)

    @property
    def is_claimable(self):
        if self.is_cancelled:
            return False
        if self.claimer is not None:
            return False
        if self.block_sage.current_block_number < self.first_claimable_block:
            return False
        if self.block_sage.current_block_number > self.last_claimable_block:
            return False
        return True

    @property
    def is_callable(self):
        if self.was_called:
            return False
        elif self.is_cancelled:
            return False
        elif self.is_expired:
            return False
        elif not self.scheduler_can_pay:
            return False
        else:
            return True

    @property
    def is_expired(self):
        return self.block_sage.current_block_number >= self.last_block

    @property
    def scheduler_can_pay(self):
        gas_cost = self.get_execution_gas() * self.blockchain_client.get_gas_price()
        max_payment = 2 * self.base_payment
        max_donation = 2 * self.base_donation
        call_value = self.call_value

        return gas_cost + max_payment + max_donation + call_value < self.balance

    def stop(self):
        self._run = False

    def execute(self):
        # Blocks until we are within 3 blocks of the call window.
        self.logger.info("Sleeping until %s", self.target_block - 2)
        self.wait_for_call_window()
        self.logger.info("Entering call loop")

        while getattr(self, '_run', True):
            if self.is_expired:
                self.logger.error("Call window expired")
                break

            if self.was_called:
                self.logger.info("Call has already been executed")
                break

            if not self.scheduler_can_pay:
                self.logger.warning("Scheduler cannot pay for the call")
                break

            next_block_number = self.block_sage.current_block_number + 1
            if not self.should_call_on_block(next_block_number):
                time.sleep(2)
                continue

            # Execute the transaction
            self.logger.info("Attempting to execute call")
            txn_hash = self.call.execute(gas=self.get_execution_gas())

            # Wait for the transaction receipt.
            try:
                self.logger.debug("Waiting for transaction: %s", txn_hash)
                txn_receipt = self.blockchain_client.wait_for_transaction(
                    txn_hash,
                    self.block_sage.estimated_time_to_block(self.last_block) * 2,
                )
            except ValueError:
                self.logger.error("Unable to get transaction receipt: %s", txn_hash)
                break
            else:
                self.logger.info("Transaction accepted.")
                self.txn_hash = txn_hash
                self.txn_receipt = txn_receipt
                self.txn = self.blockchain_client.get_transaction_by_hash(txn_hash)

                # Check the log data from the executing transaction and log it.
                execution_logs = CallLib(None, self.blockchain_client).CallExecuted.get_transaction_logs(txn_hash)
                execution_data = tuple((
                    CallLib(None, self.blockchain_client).CallExecuted.get_log_data(log) for log in execution_logs
                ))
                abort_logs = CallLib(None, self.blockchain_client).CallAborted.get_transaction_logs(txn_hash)
                abort_data = tuple((
                    CallLib(None, self.blockchain_client).CallAborted.get_log_data(log) for log in abort_logs
                ))

                for entry in execution_data:
                    self.logger.info("Event:CallExecuted: %s", str(entry))
                for entry in abort_data:
                    self.logger.warning("Event:CallAborted: %s", str(entry))
                break

    def execute_async(self):
        self._run = True
        self._thread = threading.Thread(target=self.execute)
        self._thread.daemon = True
        self._thread.start()

    def wait_for_call_window(self, buffer=2):
        """
        wait for self.target_block - buffer (~30 seconds at 2 blocks)
        """
        if self.block_sage.current_block_number > self.last_block:
            raise ValueError("Already passed call execution window")

        while True:
            is_killed = not getattr(self, '_run', True)
            is_before_buffer = (
                self.block_sage.current_block_number < self.target_block - buffer
            )
            if not is_killed and is_before_buffer:
                time.sleep(
                    self.block_sage.estimated_time_to_block(
                        self.target_block - buffer,
                    ),
                )
            else:
                break

    #
    #  Meta Properties
    #
    @cached_property
    def coinbase(self):
        return self.blockchain_client.get_coinbase()

    @property
    def balance(self):
        """
        The account balance of the scheduler for this call.
        """
        return self.blockchain_client.get_balance(self.call_address)

    @cached_property
    def last_block(self):
        """
        The last block number that this call can be executed on.
        """
        return self.target_block + self.grace_period

    @cached_property
    def is_designated(self):
        return self.call.claimer != EMPTY_ADDRESS

    def can_call_at_block(self, block_number):
        return self.call.checkExecutionAuthorization(self.coinbase, block_number)

    def should_call_on_block(self, block_number):
        """
        Return whether an attempt to execute this call should be made on the
        provided block number.
        """
        # Before call window starts
        if self.target_block > block_number:
            return False

        # After call window ends.
        if block_number > self.last_block:
            return False

        if not self.is_designated:
            return True

        return self.can_call_at_block(block_number)

    def get_execution_gas(self):
        gas_limit = int(self.block_sage.current_block['gasLimit'], 16)
        return min(gas_limit, self.required_gas + 100000)

    #
    #  Call properties.
    #
    @cached_property
    def contract_address(self):
        return self.call.contractAddress()

    @cached_property
    def scheduler_address(self):
        return self.call.schedulerAddress()

    # The amount of gas to send with the claiming transaction.
    CLAIM_GAS = 500000

    # The cost in gas to claim the call.
    CLAIM_GAS_COST = 100000

    def claim(self, **kwargs):
        kwargs.setdefault('value', 2 * self.base_payment)
        kwargs.setdefault('gas', self.CLAIM_GAS)
        return self.call.claim(**kwargs)

    @cache_once(None)
    def claimer(self):
        _claimer = self.call.claimer()
        if _claimer == '0x0000000000000000000000000000000000000000':
            return None
        return _claimer

    @cache_once(0)
    def claimer_deposit(self):
        return self.call.claimerDeposit()

    @cache_once(0)
    def claim_amount(self):
        return self.call.claimAmount()

    @cached_property
    def target_block(self):
        return self.call.targetBlock()

    @cached_property
    def grace_period(self):
        return self.call.gracePeriod()

    @cached_property
    def call_value(self):
        return self.call.callValue()

    @cached_property
    def anchor_gas_price(self):
        return self.call.anchorGasPrice()

    @cached_property
    def required_gas(self):
        return self.call.requiredGas()

    @cached_property
    def required_stack_depth(self):
        return self.call.requiredStackDepth()

    @cached_property
    def base_payment(self):
        return self.call.basePayment()

    @cached_property
    def base_donation(self):
        return self.call.baseDonation()

    @cached_property
    def abi_signature(self):
        return self.call.abiSignature()

    @cache_once(False)
    def was_successful(self):
        return self.call.wasSuccessful()

    @cache_once(False)
    def was_called(self):
        return self.call.wasCalled()

    @cache_once(False)
    def is_cancelled(self):
        return self.call.isCancelled()
