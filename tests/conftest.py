import pytest

from collections import defaultdict
import time


@pytest.fixture(autouse=True)
def alarm_client_logging_config(monkeypatch):
    monkeypatch.setenv('LOG_LEVEL', 'ERROR')


class MockBlockchainClient(object):
    def __init__(self, *blocks):
        self.blocks = list(blocks)
        if not self.blocks:
            self.mine()

    def get_block_by_number(self, block_number, full_transactions=False):
        try:
            int_block_number = int(block_number, 16)
            hex_block_number = block_number
        except (ValueError, TypeError):
            int_block_number = block_number
            hex_block_number = hex(block_number)

        return {
            'blockNumber': hex_block_number,
            'timestamp': hex(self.blocks[int_block_number - 1]),
        }

    def get_block_number(self):
        return len(self.blocks)

    def mine(self, timestamp=None):
        if timestamp is None:
            timestamp = time.time()
        self.blocks.append(int(timestamp))


@pytest.fixture()
def mock_blockchain_client_class():
    return MockBlockchainClient


@pytest.fixture()
def mock_blockchain_client(mock_blockchain_client_class):
    return mock_blockchain_client_class()


class MockLogger(object):
    def __init__(self):
        self.logs = defaultdict(list)

    def info(self, *args, **kwargs):
        self.logs['info'].append((args, kwargs))

    def warning(self, *args, **kwargs):
        self.logs['warning'].append((args, kwargs))

    def debug(self, *args, **kwargs):
        self.logs['debug'].append((args, kwargs))

    def error(self, *args, **kwargs):
        self.logs['error'].append((args, kwargs))


@pytest.fixture()
def mock_logger():
    return MockLogger()


class MaxWaitExceeded(Exception):
    pass


def _wait_till(condition, max_wait=15, message=None):
    start = time.time()
    while time.time() - start < max_wait:
        if condition():
            break
        time.sleep(0.1)
    else:
        if message is None:
            message = "Condition not met within {0} seconds".format(max_wait)
        raise MaxWaitExceeded(message)


@pytest.fixture()
def wait_till():
    return _wait_till


@pytest.fixture(scope="session")
def denoms():
    from ethereum.utils import denoms as ether_denoms
    return ether_denoms
