import time

import click

from eth_rpc_client import Client as RPCClient
from eth_ipc_client import Client as IPCClient
from eth_ipc_client.utils import get_default_ipc_path

from populus.contracts import Contract
from populus.contracts.common import EmptyDataError

from eth_alarm_client import (
    BlockSage,
    Scheduler,
)
from eth_alarm_client.contracts import contract_json


DEFAULT_ADDRESS = '0x6c8f2a135f6ed072de4503bd7c4999a1a17f824b'


def get_contract(contract_name):
    return Contract(contract_json[contract_name], contract_name)


@click.group()
def main():
    pass


@main.command()
@click.option(
    '--address',
    '-a',
    default=DEFAULT_ADDRESS,
    help="Runs the call execution scheduler",
)
@click.option(
    '--client',
    '-c',
    default='rpc',
    type=click.Choice(['rpc', 'ipc']),
    help="Whether the RPC or IPC client should be used.",
)
@click.option(
    '--rpchost',
    '-r',
    default='127.0.0.1',
    help="The RPC Host",
)
@click.option(
    '--rpcport',
    '-p',
    default='8545',
    help="The RPC Port",
)
@click.option(
    '--ipcpath',
    '-i',
    default=get_default_ipc_path,
    type=click.Path(exists=True, dir_okay=False),
    help="The RPC Port",
)
def scheduler(address, client, rpchost, rpcport, ipcpath):
    """
    Run the call scheduler.
    """
    if client == 'ipc':
        blockchain_client = IPCClient(ipc_path=ipcpath)
    elif client == 'rpc':
        blockchain_client = RPCClient(host=rpchost, port=rpcport)

    SchedulerContract = get_contract('Scheduler')

    scheduler_contract = SchedulerContract(address, blockchain_client)
    try:
        api_version = scheduler_contract.callAPIVersion()
        if api_version != 7:
            raise click.ClickException(
                "The scheduling contract address does not appear to have a compatable API"
            )
    except EmptyDataError:
        raise click.ClickException(
            "The scheduler address seems to not be correct.  Using {0}.  You "
            "may need to specify the address using `--address` if you are "
            "running the client against a test network".format(address)
        )

    block_sage = BlockSage(blockchain_client)
    scheduler = Scheduler(scheduler_contract, block_sage=block_sage)

    scheduler.monitor_async()

    try:
        while scheduler._thread.is_alive():
            time.sleep(1)

    except KeyboardInterrupt:
        scheduler.stop()
        scheduler.block_sage.stop()
        for scheduled_call in scheduler.active_calls.values():
            scheduled_call.stop()
        scheduler._thread.join(5)


if __name__ == '__main__':
    main()
