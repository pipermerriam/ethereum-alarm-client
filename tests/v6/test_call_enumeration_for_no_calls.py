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



def test_enumerate_upcoming_calls_with_no_calls(deployed_contracts, scheduled_call):
    scheduler = Scheduler(deployed_contracts.Scheduler)

    last_target_block = scheduled_call[-1].targetBlock()

    actual_calls = tuple(scheduler.enumerate_calls(last_target_block, 1000000))
    assert not actual_calls
