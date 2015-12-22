from eth_alarm_client.block_sage import BlockSage


def test_block_sage_keeps_up_with_block_number(mock_blockchain_client, wait_till):
    block_sage = BlockSage(blockchain_client=mock_blockchain_client)

    for i in range(1, 10):
        wait_till(lambda: block_sage.current_block_number == i)
        mock_blockchain_client.mine()


def test_block_sage_converges_on_block_time(mock_blockchain_client, wait_till):
    block_sage = BlockSage(blockchain_client=mock_blockchain_client)

    start_timestamp = mock_blockchain_client.blocks[0]
    block_time = 0

    for i in range(1, 25):
        wait_till(lambda: block_sage.current_block_number == i)
        mock_blockchain_client.mine(start_timestamp + i * 3)

        assert block_time < block_sage.block_time
        assert block_time < 3

    assert abs(block_sage.block_time - 3) < 0.1
