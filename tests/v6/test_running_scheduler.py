import os
import time
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


@pytest.fixture(autouse=True)
def logging_config(monkeypatch):
    # Set to DEBUG for a better idea of what is going on in this test.
    monkeypatch.setenv('LOG_LEVEL', 'DEBUG')
    pass


def test_scheduler(deployed_contracts, deploy_client, scheduled_calls):
    block_sage = BlockSage(deploy_client)
    scheduler = Scheduler(deployed_contracts.Scheduler, block_sage=block_sage)
    scheduler.monitor_async()

    last_call = scheduled_calls[-1]
    final_block = last_call.targetBlock() + last_call.gracePeriod() + 1

    for call in scheduled_calls:
        deploy_client.wait_for_block(call.targetBlock() - 5)
        time.sleep(2)

    scheduler.stop()
    block_sage.stop()

    was_called = [call.wasCalled() for call in scheduled_calls]
    assert all(was_called)
