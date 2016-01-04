import os

from ethereum import utils

from eth_alarm_client import (
    Scheduler,
)


V6_DIR = os.path.dirname(__file__)

project_dir = V6_DIR
deploy_contracts = [
    "Scheduler",
    "TestCallExecution",
]



def test_enumerate_upcoming_calls(deployed_contracts, scheduled_calls):
    scheduler = Scheduler(deployed_contracts.Scheduler)

    expected_calls = tuple(call._meta.address for call in scheduled_calls)
    actual_calls = tuple(scheduler.enumerate_calls(
        scheduled_calls[0].targetBlock(),
        scheduled_calls[-1].targetBlock(),
    ))
    assert actual_calls == expected_calls
