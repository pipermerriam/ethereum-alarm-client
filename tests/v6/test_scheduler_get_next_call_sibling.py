import os

from eth_alarm_client import (
    Scheduler,
)


V6_DIR = os.path.dirname(__file__)

project_dir = V6_DIR
deploy_contracts = [
    "Scheduler",
    "TestCallExecution",
]


def test_get_next_call_sibling(deployed_contracts, scheduled_calls, mock_blocksage):
    scheduler = Scheduler(deployed_contracts.Scheduler, block_sage=mock_blocksage)

    # same block
    next_call_a = scheduler.get_next_call_sibling(scheduled_calls[1]._meta.address)
    assert next_call_a == scheduled_calls[2]._meta.address

    # different blocks
    next_call_b = scheduler.get_next_call_sibling(scheduled_calls[2]._meta.address)
    assert next_call_b == scheduled_calls[3]._meta.address

    # no next call
    next_call_c = scheduler.get_next_call_sibling(scheduled_calls[-1]._meta.address)
    assert next_call_c is None
