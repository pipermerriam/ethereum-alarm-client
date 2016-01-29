import os

from eth_alarm_client.call_contract import CallContract
from eth_alarm_client.scheduler import Scheduler


V6_DIR = os.path.dirname(__file__)

project_dir = V6_DIR

deploy_contracts = [
    "CallLib",
    "TestCallExecution",
    "Scheduler",
]
deploy_client_type = 'ipc'


def test_is_claimable_property(geth_node, deployed_contracts, deploy_client,
                               deploy_coinbase, deploy_future_block_call,
                               denoms):
    deploy_client.async_timeout = 60
    scheduled_call = deploy_future_block_call(
        deployed_contracts.TestCallExecution.setBool,
        target_block=deploy_client.get_block_number() + 255 + 10 + 40 + 1,
    )
    scheduler = Scheduler(deployed_contracts.Scheduler)
    call_contract = CallContract(
        call_address=scheduled_call._meta.address,
        blockchain_client=deploy_client,
        block_sage=scheduler.block_sage,
    )

    assert call_contract.is_claimable is False

    wait_til = call_contract.first_claimable_block + 10
    deploy_client.wait_for_block(
        wait_til,
        call_contract.block_sage.estimated_time_to_block(wait_til) * 2,
    )

    assert call_contract.is_claimable is True

    txn_hash = call_contract.claim()
    txn_receipt = deploy_client.wait_for_transaction(txn_hash)

    assert call_contract.is_claimable is False
    assert call_contract.claimer == deploy_coinbase
