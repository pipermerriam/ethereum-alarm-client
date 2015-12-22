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


def test_contract_properties(call_contract, scheduled_call):
    # Sanity check for all of the queriable call values.
    assert scheduled_call.targetBlock() == call_contract.target_block
    assert scheduled_call.gracePeriod() == call_contract.grace_period
    assert scheduled_call.suggestedGas() == call_contract.suggested_gas
    assert scheduled_call.basePayment() == call_contract.base_payment
    assert scheduled_call.baseFee() == call_contract.base_fee
    assert scheduled_call.schedulerAddress() == call_contract.scheduler_address
    assert scheduled_call.contractAddress() == call_contract.contract_address
    assert scheduled_call.abiSignature() == call_contract.abi_signature
    assert scheduled_call.anchorGasPrice() == call_contract.anchor_gas_price
    assert scheduled_call.claimer() == call_contract.claimer
    assert scheduled_call.claimAmount() == call_contract.claim_amount
    assert scheduled_call.claimerDeposit() == call_contract.claimer_deposit
    assert scheduled_call.wasSuccessful() == call_contract.was_successful
    assert scheduled_call.wasCalled() == call_contract.was_called
    assert scheduled_call.isCancelled() == call_contract.is_cancelled


def test_callable_blocks_property(call_contract):
    assert len(call_contract.callable_blocks) == call_contract.grace_period
    expected_blocks = range(call_contract.target_block, call_contract.last_block)
    assert set(call_contract.callable_blocks) == set(expected_blocks)


def test_should_call_at_block_method(call_contract):
    assert call_contract.should_call_on_block(call_contract.target_block - 1) is False
    assert call_contract.should_call_on_block(call_contract.last_block + 1) is False

    assert call_contract.should_call_on_block(call_contract.target_block) is True
    assert call_contract.should_call_on_block(call_contract.last_block) is True

    for i in range(call_contract.target_block, call_contract.last_block + 1):
        assert call_contract.should_call_on_block(i) is True
