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


@pytest.fixture(autouse=True)
def logging_config(monkeypatch):
    # Set to DEBUG for a better idea of what is going on in this test.
    monkeypatch.setenv('LOG_LEVEL', 'DEBUG')


FUTURE_OFFSET = 255 + 10 + 40 + 5


def test_scheduler(geth_node, deploy_client,
                   deployed_contracts, contracts,
                   get_call, denoms):
    block_sage = BlockSage(deploy_client)

    scheduler = deployed_contracts.Scheduler
    client_contract = deployed_contracts.TestCallExecution

    anchor_block = deploy_client.get_block_number()

    blocks = (1, 4, 4, 8, 30, 40, 50, 60)

    calls = []

    for n in blocks:
        scheduling_txn = scheduler.scheduleCall(
            client_contract._meta.address,
            client_contract.setBool.encoded_abi_signature,
            anchor_block + FUTURE_OFFSET + n,
            1000000,
            value=10 * denoms.ether,
            gas=3000000,
        )
        scheduling_receipt = deploy_client.wait_for_transaction(scheduling_txn)
        call = get_call(scheduling_txn)

        calls.append(call)

    scheduler = Scheduler(scheduler, block_sage=block_sage)
    scheduler.monitor_async()

    final_block = anchor_block + FUTURE_OFFSET + 80
    deploy_client.wait_for_block(
        final_block,
        2 * block_sage.estimated_time_to_block(final_block),
    )

    scheduler.stop()
    block_sage.stop()

    was_called = [call.wasCalled() for call in calls]
    assert all(was_called)
