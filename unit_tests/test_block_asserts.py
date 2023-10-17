import pytest
from unittest.mock import MagicMock, patch
from os import environ
from nanolab.publisher.block_asserts import BlockAsserts  # Import your class here
from nanolab.publisher.event_bus import EventBus
import asyncio
import itertools
import time


@pytest.fixture
def mock_rpc():
    with patch('nanolab.src.nano_rpc.NanoRpcV2') as mock:
        yield mock


@pytest.fixture
def block_asserts(mock_rpc):
    environ[
        'NL_CONF_DIR'] = 'unit_tests/nanomock/'  # Replace with your test directory
    environ[
        'NL_CONF_FILE'] = 'nl_config.toml'  # Replace with your test config file

    block_asserts = BlockAsserts(EventBus(), node_name='nanomock_pr1')
    return block_asserts


@pytest.mark.asyncio
async def test_assert_single_block_confirmed(block_asserts):
    # Test when block_info returns '{"error" : "block not found"}'
    block_asserts._fetch_block_info = MagicMock(return_value=asyncio.Future())
    block_asserts._fetch_block_info.return_value.set_result(
        {"error": "block not found"})
    with pytest.raises(AssertionError):
        await block_asserts.assert_single_block_confirmed("block_hash")

    # Test when block_info returns '{... confirmed = "false"}'
    block_asserts._fetch_block_info = MagicMock(return_value=asyncio.Future())
    block_asserts._fetch_block_info.return_value.set_result(
        {"confirmed": "false"})
    with pytest.raises(AssertionError):
        await block_asserts.assert_single_block_confirmed("block_hash")

    block_asserts._fetch_block_info = MagicMock(return_value=asyncio.Future())
    block_asserts._fetch_block_info.return_value.set_result(
        {"confirmed": "true"})

    # If confirmed is "true", no AssertionError should be raised
    try:
        await block_asserts.assert_single_block_confirmed("block_hash")
    except AssertionError:
        pytest.fail(
            "assert_single_block_confirmed() raised AssertionError unexpectedly!"
        )


@pytest.mark.asyncio
async def test_assert_blocks_confirmed(block_asserts):
    block_hashes = ["block_hash1", "block_hash2"]

    # Test when block_info returns '{"error" : "block not found"}' for all block hashes
    block_asserts._fetch_block_info = MagicMock(return_value=asyncio.Future())
    block_asserts._fetch_block_info.return_value.set_result(
        {"error": "block not found"})
    with pytest.raises(AssertionError):
        await block_asserts.assert_blocks_confirmed(block_hashes)

    # Test when block_info returns '{... confirmed = "false"}' for all block hashes
    block_asserts._fetch_block_info = MagicMock(return_value=asyncio.Future())
    block_asserts._fetch_block_info.return_value.set_result(
        {"confirmed": "false"})
    with pytest.raises(AssertionError):
        await block_asserts.assert_blocks_confirmed(block_hashes)

    # Test when block_info returns '{... confirmed = "true"}' for all block hashes
    block_asserts._fetch_block_info = MagicMock(return_value=asyncio.Future())
    block_asserts._fetch_block_info.return_value.set_result(
        {"confirmed": "true"})
    try:
        await block_asserts.assert_blocks_confirmed(block_hashes)
    except AssertionError:
        pytest.fail(
            "assert_blocks_confirmed() raised AssertionError unexpectedly!")


@pytest.mark.asyncio
async def test_assert_blocks_confirmed_wait(block_asserts):
    block_hashes = ["block_hash1", "block_hash2"]
    wait_s = 0.5
    interval = 0.1

    # Test when block_info returns '{"error" : "block not found"}' for all block hashes
    block_asserts._fetch_block_info = MagicMock(return_value=asyncio.Future())
    block_asserts._fetch_block_info.return_value.set_result(
        {"error": "block not found"})
    with pytest.raises(AssertionError):
        await block_asserts.assert_blocks_confirmed_wait(
            block_hashes, wait_s, interval)

    # Test when block_info returns '{... confirmed = "false"}' for all block hashes
    block_asserts._fetch_block_info = MagicMock(return_value=asyncio.Future())
    block_asserts._fetch_block_info.return_value.set_result(
        {"confirmed": "false"})
    with pytest.raises(AssertionError):
        await block_asserts.assert_blocks_confirmed_wait(
            block_hashes, wait_s, interval)

    # Test when block_info returns '{... confirmed = "true"}' for all block hashes
    block_asserts._fetch_block_info = MagicMock(return_value=asyncio.Future())
    block_asserts._fetch_block_info.return_value.set_result(
        {"confirmed": "true"})
    try:
        await block_asserts.assert_blocks_confirmed_wait(
            block_hashes, wait_s, interval)
    except AssertionError:
        pytest.fail(
            "assert_blocks_confirmed_wait() raised AssertionError unexpectedly!"
        )


@pytest.mark.asyncio
async def test_assert_blocks_confirmed_2(block_asserts):
    block_hashes = ["block_hash1", "block_hash2", "block_hash3"]

    # Create futures with the desired results
    futures = [asyncio.Future(), asyncio.Future(), asyncio.Future()]
    futures[0].set_result({"confirmed": "false"})
    futures[1].set_result({"error": "block not found"})
    futures[2].set_result({"confirmed": "true"})

    # Define a side effect function that returns a different future
    # based on the input block hash
    def side_effect(block_hash):
        return futures[block_hashes.index(block_hash)]

    # Apply the side effect to the mock
    block_asserts._fetch_block_info = MagicMock(side_effect=side_effect)
    with pytest.raises(AssertionError):
        await block_asserts.assert_blocks_confirmed(block_hashes)

    # Test all combinations of two block hashes
    for combination in itertools.combinations(block_hashes, 2):
        with pytest.raises(AssertionError):
            await block_asserts.assert_blocks_confirmed(list(combination))


@pytest.mark.asyncio
async def test_assert_blocks_confirmed_wait_2(block_asserts):
    block_hashes = ["block_hash1"]
    wait_s = 1
    interval = 0.3

    # Create futures with the desired results
    futures = [asyncio.Future(), asyncio.Future(), asyncio.Future()]
    futures[0].set_result({"confirmed": "false"})
    futures[1].set_result({"confirmed": "false"})
    futures[2].set_result({"confirmed": "true"})

    # Mock _fetch_block_info to return {"confirmed": "false"} on the first call
    # and {"confirmed": "true"} on the second call
    block_asserts._fetch_block_info = MagicMock(side_effect=futures)

    start_time = time.time()
    try:
        await block_asserts.assert_blocks_confirmed_wait(
            block_hashes, wait_s, interval)
    except AssertionError:
        pytest.fail(
            "assert_blocks_confirmed_wait() raised AssertionError unexpectedly!"
        )
    end_time = time.time()

    # Check that the method waited approximately 2*interval before returning.
    # We use a small tolerance to account for the time spent on other operations.
    assert (end_time - start_time) < 2 * interval + 0.1
    assert (end_time - start_time) > 2 * interval - 0.1


@pytest.mark.asyncio
async def test_assert_blocks_confirmed_wait_3(block_asserts):
    block_hashes = ["block_hash1", "block_hash2"]
    wait_s = 2
    interval = 0.3

    # Create futures with the desired results for each block hash
    futures1 = [asyncio.Future(), asyncio.Future(), asyncio.Future()]
    futures1[0].set_result({"confirmed": "false"})
    futures1[1].set_result({"confirmed": "false"})
    futures1[2].set_result({"confirmed": "true"})

    futures2 = [
        asyncio.Future(),
        asyncio.Future(),
        asyncio.Future(),
        asyncio.Future(),
        asyncio.Future()
    ]
    futures2[0].set_result({"confirmed": "false"})
    futures2[1].set_result({"confirmed": "false"})
    futures2[2].set_result({"confirmed": "false"})
    futures2[3].set_result({"confirmed": "false"})
    futures2[4].set_result({"confirmed": "true"})

    # Mock _fetch_block_info to return different results for each block hash
    async def mock_fetch_block_info(block_hash):
        if block_hash == "block_hash1":
            return futures1.pop(0).result()
        elif block_hash == "block_hash2":
            return futures2.pop(0).result()

    block_asserts._fetch_block_info = mock_fetch_block_info

    start_time = time.time()
    try:
        await block_asserts.assert_blocks_confirmed_wait(
            block_hashes, wait_s, interval)
    except AssertionError:
        pytest.fail(
            "assert_blocks_confirmed_wait() raised AssertionError unexpectedly!"
        )
    end_time = time.time()

    # Check that the method waited approximately 4*interval before returning.
    # We use a small tolerance to account for the time spent on other operations.
    assert (end_time - start_time) < 4 * interval + 0.1
    assert (end_time - start_time) > 4 * interval - 0.1
