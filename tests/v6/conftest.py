import pytest


@pytest.fixture(scope="module")
def FutureBlockCall(contracts, deployed_contracts):
    from populus.contracts import (
        link_contract_dependency,
    )
    return link_contract_dependency(
        link_contract_dependency(contracts.FutureBlockCall, deployed_contracts.CallLib),
        deployed_contracts.AccountingLib,
    )


@pytest.fixture
def deploy_future_block_call(deploy_client, FutureBlockCall, deploy_coinbase):
    from populus.contracts import (
        deploy_contract,
    )
    from populus.utils import (
        get_contract_address_from_txn,
    )

    def _deploy_future_block_call(contract_function, scheduler_address=None,
                                  target_block=None, grace_period=64,
                                  suggested_gas=100000, payment=1, fee=1,
                                  endowment=None):
        if endowment is None:
            endowment = deploy_client.get_max_gas() * deploy_client.get_gas_price() + payment + fee

        if target_block is None:
            target_block = deploy_client.get_block_number() + 40

        if scheduler_address is None:
            scheduler_address = deploy_coinbase

        deploy_txn_hash = deploy_contract(
            deploy_client,
            FutureBlockCall,
            constructor_args=(
                scheduler_address,
                target_block,
                grace_period,
                contract_function._contract._meta.address,
                contract_function.encoded_abi_signature,
                suggested_gas,
                payment,
                fee,
            ),
            gas=int(deploy_client.get_max_gas() * 0.95),
            value=endowment,
        )

        call_address = get_contract_address_from_txn(deploy_client, deploy_txn_hash, 180)
        call = FutureBlockCall(call_address, deploy_client)
        return call
    return _deploy_future_block_call


@pytest.fixture()
def scheduled_call(deployed_contracts, deploy_future_block_call):
    call = deploy_future_block_call(deployed_contracts.TestCallExecution.setBool)
    return call


@pytest.fixture()
def call_contract(scheduled_call, deployed_contracts, deploy_client):
    from eth_alarm_client.call_contract import CallContract
    from eth_alarm_client.scheduler import Scheduler

    scheduler = Scheduler(deployed_contracts.Scheduler)
    call_contract = CallContract(
        call_address=scheduled_call._meta.address,
        blockchain_client=deploy_client,
        block_sage=scheduler.block_sage,
    )
    return call_contract


@pytest.fixture(scope="module")
def CallLib(deployed_contracts):
    return deployed_contracts.CallLib


@pytest.fixture(scope="module")
def SchedulerLib(deployed_contracts):
    return deployed_contracts.SchedulerLib


@pytest.fixture(scope="module")
def get_call(SchedulerLib, FutureBlockCall, deploy_client):
    def _get_call(txn_hash):
        call_scheduled_logs = SchedulerLib.CallScheduled.get_transaction_logs(txn_hash)
        assert len(call_scheduled_logs) == 1
        call_scheduled_data = SchedulerLib.CallScheduled.get_log_data(call_scheduled_logs[0])

        call_address = call_scheduled_data['call_address']
        call = FutureBlockCall(call_address, deploy_client)
        return call
    return _get_call