import os
import json
import time

import click

from eth_rpc_client import Client

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

rpc_client = Client('127.0.0.1', '8545')


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
def scheduler(address):
    """
    Run the call scheduler.
    """
    SchedulerContract = get_contract('Scheduler')

    scheduler_contract = SchedulerContract(address, rpc_client)

    block_sage = BlockSage(rpc_client)
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
