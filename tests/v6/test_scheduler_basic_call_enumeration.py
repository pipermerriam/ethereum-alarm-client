import os
import pytest

from eth_alarm_client import (
    Scheduler,
    BlockSage,
)


V6_DIR = os.path.dirname(__file__)

project_dir = V6_DIR
deploy_contracts = [
    "Scheduler",
    "TestCallExecution",
]
deploy_client_type = "rpc"


def test_basic_call_enumeration(geth_node, deployed_contracts, scheduled_calls):
    scheduler = Scheduler(deployed_contracts.Scheduler)

    left_block = scheduled_calls[1].targetBlock()
    right_block = scheduled_calls[5].targetBlock()

    call_addresses = tuple(scheduler.enumerate_calls(left_block, right_block))
    assert len(call_addresses) == 5

    expected_addresses = tuple(call._meta.address for call in scheduled_calls[1:6])
    assert call_addresses == expected_addresses
