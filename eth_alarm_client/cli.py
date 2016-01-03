import time

import click

from eth_rpc_client import Client as RPCClient
from eth_ipc_client import Client as IPCClient
from eth_ipc_client.utils import get_default_ipc_path

from populus.contracts import Contract

from eth_alarm_client import (
    BlockSage,
    Scheduler,
)
from eth_alarm_client.contracts import contract_json


LATEST_ADDRESS = '0xe109ecb193841af9da3110c80fdd365d1c23be2a'
DEFAULT_ADDRESS = LATEST_ADDRESS


scheduler_addresses = (
    ('0.6.0 (latest)', DEFAULT_ADDRESS),
)


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
    default='ipc',
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
