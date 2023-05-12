import pytest
from unittest.mock import patch, DEFAULT
from nanolab.loggers.sources.rpc_logger import RPCLogger
from nanolab.loggers.contracts import LogData
from asyncio import sleep


@pytest.fixture
def mock_version():
    with patch('nanomock.modules.nl_rpc.NanoRpc.version',
               return_value={
                   "node_vendor": "Nano",
                   "build_info": "V25.0RC1 95eba85"
               }) as mock_version:
        yield mock_version


@pytest.fixture
def mock_block_count():
    with patch('nanomock.modules.nl_rpc.NanoRpc.block_count',
               return_value={
                   "count": "100",
                   "cemented": "50"
               }) as mock_block_count_100:
        yield mock_block_count_100


@pytest.fixture
def mock_fully_cemented():
    with patch('nanomock.modules.nl_rpc.NanoRpc.block_count',
               return_value={
                   "count": "100",
                   "cemented": "100"
               }) as mock_fully_cemented:
        yield mock_fully_cemented


def test_get_block_count(mock_version, mock_block_count):
    logger = RPCLogger(node_name="test_node",
                       rpc_url="http://test_url",
                       expected_blocks_count=99,
                       timeout=10)
    count, cemented = logger._get_block_count()
    assert count == 100
    assert cemented == 50


def test_is_fully_synced(mock_version, mock_fully_cemented):
    logger = RPCLogger(node_name="test_node",
                       rpc_url="http://test_url",
                       expected_blocks_count=99,
                       count_start=1,
                       cemented_start=1,
                       timeout=10)
    is_synced = logger.is_fully_synced(cemented=100)
    assert is_synced
    is_synced = logger.is_fully_synced(cemented=40)
    assert not is_synced


@pytest.mark.asyncio
async def test_fetch_logs(mock_version, mock_fully_cemented):
    logger = RPCLogger(node_name="test_node",
                       rpc_url="http://test_url",
                       expected_blocks_count=99,
                       count_start=1,
                       cemented_start=1,
                       timeout=0.5)
    logs = []
    async for log in logger.fetch_logs():
        logs.append(log)
    assert len(logs) == 1
    assert isinstance(logs[0], LogData)


@pytest.mark.asyncio
async def test_fetch_logs_timeout(mock_version, mock_fully_cemented):
    logger = RPCLogger(node_name="test_node",
                       rpc_url="http://test_url",
                       expected_blocks_count=500000,
                       timeout=0.3)
    logs = []
    async for log in logger.fetch_logs():
        logs.append(log)
    assert len(logs) > 1
    assert isinstance(logs[0], LogData)
    assert logs[0].elapsed_time == 0


def test_case_with_different_version(mock_fully_cemented):
    with patch('nanomock.modules.nl_rpc.NanoRpc.version',
               return_value=None) as mock_version:
        # rest of the test case...
        logger = RPCLogger(node_name="test_node",
                           rpc_url="http://test_url",
                           expected_blocks_count=99,
                           count_start=1,
                           cemented_start=1,
                           timeout=0.5)
        assert logger.node_version == "???"
