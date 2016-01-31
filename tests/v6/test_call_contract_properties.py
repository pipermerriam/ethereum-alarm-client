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
    assert scheduled_call.requiredGas() == call_contract.required_gas
    assert scheduled_call.requiredStackDepth() == call_contract.required_stack_depth
    assert scheduled_call.basePayment() == call_contract.base_payment
    assert scheduled_call.baseDonation() == call_contract.base_donation
    assert scheduled_call.schedulerAddress() == call_contract.scheduler_address
    assert scheduled_call.contractAddress() == call_contract.contract_address
    assert scheduled_call.abiSignature() == call_contract.abi_signature
    assert scheduled_call.anchorGasPrice() == call_contract.anchor_gas_price
    assert scheduled_call.claimer() == '0x0000000000000000000000000000000000000000'
    assert scheduled_call.claimAmount() == call_contract.claim_amount
    assert scheduled_call.claimerDeposit() == call_contract.claimer_deposit
    assert scheduled_call.wasSuccessful() == call_contract.was_successful
    assert scheduled_call.wasCalled() == call_contract.was_called
    assert scheduled_call.isCancelled() == call_contract.is_cancelled

    assert call_contract.claimer is None


def test_should_call_at_block_method(call_contract):
    assert call_contract.should_call_on_block(call_contract.target_block - 1) is False
    assert call_contract.should_call_on_block(call_contract.last_block + 1) is False

    assert call_contract.should_call_on_block(call_contract.target_block) is True
    assert call_contract.should_call_on_block(call_contract.last_block) is True

    for i in range(call_contract.target_block, call_contract.last_block + 1):
        assert call_contract.should_call_on_block(i) is True
