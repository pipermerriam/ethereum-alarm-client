import threading
import time
import random

from ethereum.utils import denoms as denoms

from .block_sage import BlockSage
from .call_contract import CallContract
from .contracts import FutureBlockCall
from .utils import (
    get_logger,
    cached_property,
)


EMPTY_ADDRESS = '0x0000000000000000000000000000000000000000'


class Scheduler(object):
    _block_sage = None

    def __init__(self, scheduler, block_sage=None):
        self.logger = get_logger('scheduler')
        self.scheduler = scheduler

        if block_sage is None:
            block_sage = BlockSage(self.blockchain_client)
        self._block_sage = block_sage

        self.active_calls = {}
        self.active_claims = {}

    @property
    def block_sage(self):
        if self._block_sage is None:
            self.logger.error("Blocksage unexpectedly `None`")
            self._block_sage = BlockSage(self.blockchain_client)
        if not self._block_sage.is_alive:
            self.logger.error("Blocksage died.  Respawning")
            self._block_sage = BlockSage(self.blockchain_client)
        return self._block_sage

    @property
    def blockchain_client(self):
        return self.scheduler._meta.blockchain_client

    @cached_property
    def coinbase(self):
        return self.blockchain_client.get_coinbase()

    @property
    def is_alive(self):
        return self._thread.is_alive()

    @cached_property
    def minimum_grace_period(self):
        return self.scheduler.getMinimumGracePeriod()

    def monitor_async(self):
        self._run = True
        self._thread = threading.Thread(target=self.monitor)
        self._thread.daemon = True
        self._thread.start()

    def stop(self):
        self._run = False

    def monitor(self):
        while getattr(self, '_run', True):
            self.schedule_calls()
            self.claim_calls()
            self.cleanup_calls()
            self.cleanup_claim_threads()
            time.sleep(self.block_sage.block_time)

    def claim_calls(self):
        start_block = self.block_sage.current_block_number + 10 + 1
        end_block = self.block_sage.current_block_number + 255 + 10 - 1
        self.logger.debug("Looking for claimable calls between %s-%s", start_block, end_block)
        upcoming_calls = self.enumerate_calls(start_block, end_block)

        for call_address in upcoming_calls:
            if call_address in self.active_claims:
                self.logger.debug("Call %s already claimed", call_address)
                continue

            scheduled_call = CallContract(
                call_address=call_address,
                blockchain_client=self.blockchain_client,
                block_sage=self.block_sage,
            )

            if not scheduled_call.is_claimable:
                self.logger.debug("Call %s not claimable", call_address)
                continue

            current_balance = self.blockchain_client.get_balance(self.coinbase)
            if current_balance - 2 * scheduled_call.base_payment < 2 * denoms.ether:
                self.logger.error(
                    "Insufficient funds to claim %s.  Base Payment is %s ether",
                    scheduled_call.call_address,
                    scheduled_call.base_payment * 1.0 / denoms.ether,
                )
                continue

            fpcb = scheduled_call.first_profitable_claim_block
            if self.block_sage.current_block_number < fpcb:
                # claiming the call at this point would be committing to
                # execute it at a loss, and thus we will wait till at least the
                # maximum payment value for this call.
                self.logger.debug(
                    "Waiting till block %s to claim %s.  To claim before this block would be operating at a loss.",
                    fpcb,
                    scheduled_call.call_address,
                )
                continue

            # Random strategy.  Roll a number between 1-255.  If we are at
            # least this many blocks into the call window then claim the call.
            cbn = self.block_sage.current_block_number
            fcb = scheduled_call.first_claimable_block
            claim_block = cbn - fcb

            claim_if_above = random.randint(0, 255)

            self.logger.debug(
                "Claiming roll for %s, Rolled %s: Needed: %s",
                scheduled_call.call_address,
                claim_if_above,
                claim_block,
            )

            if claim_block > claim_if_above:
                # Asynchronously claim the call.  We don't want to wait for
                # these transactions since they could take a while and there
                # could be a lot of them.
                claim_thread = threading.Thread(target=self.claim_call, args=(scheduled_call,))
                claim_thread.daemon = True
                claim_thread.start()
                self.active_claims[call_address] = claim_thread

    def claim_call(self, scheduled_call):
        """
        Claim a call.
        """
        cbn = self.block_sage.current_block_number
        fcb = scheduled_call.first_claimable_block
        claim_block = cbn - fcb

        self.logger.info(
            "Attempting to claim call %s at block %s",
            scheduled_call.call_address,
            claim_block,
        )
        claim_txn = scheduled_call.claim()
        try:
            claim_receipt = self.blockchain_client.wait_for_transaction(
                claim_txn,
                10 * self.block_sage.block_time,
            )
            self.logger.info(
                "Call %s claimed with txn %s at claim block %s for %s ethers",
                scheduled_call.call_address,
                claim_txn,
                claim_block,
                scheduled_call.claim_amount * 1.0 / denoms.ether,
            )
            return claim_receipt
        except ValueError:
            # Handle timeout waiting for transaction.
            self.logger.error(
                "Timeout waiting for claim transaction %s for call %s",
                claim_txn,
                scheduled_call.call_address,
            )
            raise

    def schedule_calls(self):
        start_block = max(0, self.block_sage.current_block_number - self.minimum_grace_period)
        end_block = self.block_sage.current_block_number + 40
        self.logger.debug("Looking for calls between %s-%s", start_block, end_block)
        upcoming_calls = self.enumerate_calls(start_block, end_block)

        for call_address in upcoming_calls:
            self.logger.debug("Evaluating %s for scheduling", call_address)
            if call_address in self.active_calls:
                self.logger.debug("Call %s already scheduled", call_address)
                continue

            scheduled_call = CallContract(
                call_address=call_address,
                blockchain_client=self.blockchain_client,
                block_sage=self.block_sage,
            )

            if not scheduled_call.is_callable:
                self.logger.debug("Call %s not callable", call_address)
                continue

            self.logger.info("Tracking call: %s", scheduled_call.call_address)
            scheduled_call.execute_async()
            self.active_calls[call_address] = scheduled_call

    def cleanup_calls(self):
        for call_address, scheduled_call in tuple(self.active_calls.items()):

            if scheduled_call.txn_hash:
                self.logger.info("Removing finished call: %s", call_address)
                self.active_calls.pop(call_address)
            elif scheduled_call.last_block < self.block_sage.current_block_number:
                scheduled_call.stop()
                self.logger.info("Removing expired call: %s", call_address)
                self.active_calls.pop(call_address)
            elif not scheduled_call._thread.is_alive():
                self.logger.info("Removing dead call: %s", call_address)
                self.active_calls.pop(call_address)

    def cleanup_claim_threads(self):
        keys = tuple(self.active_claims.keys())
        for key in keys:
            if not self.active_claims[key].is_alive():
                self.active_claims.pop(key)

    def get_next_call(self, block_number):
        next_call = self.scheduler.getNextCall(block_number)
        if next_call == EMPTY_ADDRESS:
            return None
        return next_call

    def get_next_call_sibling(self, call_address):
        next_call = self.scheduler.getNextCallSibling(call_address)
        if next_call == EMPTY_ADDRESS:
            return None
        return next_call

    def enumerate_calls(self, left_block, right_block):
        """
        Query the scheduler contract for any calls that should be executed during
        the next 40 block window.
        """
        call_address = self.get_next_call(left_block)

        while call_address is not None:
            call = FutureBlockCall(call_address, self.blockchain_client)

            if left_block <= call.targetBlock() <= right_block:
                yield call_address
            else:
                break

            call_address = self.get_next_call_sibling(call_address)
