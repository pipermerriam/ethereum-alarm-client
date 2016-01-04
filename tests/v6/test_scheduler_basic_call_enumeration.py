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
deploy_client_type = "ipc"


def test_basic_call_enumeration(geth_node, deployed_contracts, schedule_calls):
    calls = schedule_calls()

    scheduler = Scheduler(deployed_contracts.Scheduler)

    left_block = calls[1].targetBlock()
    right_block = calls[5].targetBlock()

    call_addresses = tuple(scheduler.enumerate_calls(left_block, right_block))
    assert len(call_addresses) == 5

    expected_addresses = tuple(call._meta.address for call in calls[1:5])
    assert call_addresses == expected_addresses
