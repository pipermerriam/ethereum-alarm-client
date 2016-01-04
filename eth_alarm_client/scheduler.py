import threading
import time

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
            self.cleanup_calls()
            time.sleep(self.block_sage.block_time)

    def schedule_calls(self):
        upcoming_calls = self.enumerate_calls(
            max(0, self.block_sage.current_block_number - self.minimum_grace_period),
            self.block_sage.current_block_number + 40,
        )

        for call_address in upcoming_calls:
            if call_address in self.active_calls:
                continue

            scheduled_call = CallContract(
                call_address=call_address,
                blockchain_client=self.blockchain_client,
                block_sage=self.block_sage,
            )

            if not scheduled_call.is_callable:
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
