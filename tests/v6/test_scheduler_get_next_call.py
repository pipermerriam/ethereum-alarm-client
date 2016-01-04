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


def test_get_next_call(deployed_contracts, scheduled_calls):
    scheduler = Scheduler(deployed_contracts.Scheduler)

    # target block - 1
    next_call_a = scheduler.get_next_call(scheduled_calls[1].targetBlock() - 1)
    assert next_call_a == scheduled_calls[1]._meta.address

    # target block - 1
    next_call_b = scheduler.get_next_call(scheduled_calls[1].targetBlock())
    assert next_call_b == scheduled_calls[1]._meta.address

    # before all scheduled_calls
    next_call_c = scheduler.get_next_call(0)
    assert next_call_c == scheduled_calls[0]._meta.address

    # after all scheduled_calls
    next_call_d = scheduler.get_next_call(scheduled_calls[-1].targetBlock() + 1)
    assert next_call_d is None
