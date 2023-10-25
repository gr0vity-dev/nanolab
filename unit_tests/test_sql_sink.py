import os
import pytest
from nanolab_debug.loggers.sinks.sql_sink import SqlSink, LogData

# This fixture will run for each test_* function
# @pytest.fixture(autouse=True)
# def setup_and_teardown():
#     # Setup: Create the database
#     # (you can put any setup code here)

#     yield  # This is where the testing happens

#     # Teardown: Delete the database
#     os.remove('unit_tests/*.db')


def test_store_testcase():
    db_file = "unit_tests/test_store_testcase.db"
    if os.path.exists(db_file):
        os.remove(db_file)
    sink = SqlSink(db_uri=f'sqlite:///{db_file}',
                   milestones={10, 25, 50, 75, 90, 99, 100},
                   testcase_name='test1')
    id = sink.testcase_id
    assert id == 1

    # Fetch the testcase from the database and verify
    testcase = sink.get_testcase(id)
    assert testcase is not None
    assert testcase.testcase_name == 'test1'
    os.remove(db_file)


def test_store_logs():
    db_file = "unit_tests/test_store_logs.db"
    if os.path.exists(db_file):
        os.remove(db_file)
    sink = SqlSink(db_uri=f'sqlite:///{db_file}',
                   milestones={10, 25, 50, 75, 90, 99, 100},
                   testcase_name='test2')
    logs = LogData(node_name="unittest",
                   node_version="V1",
                   bps=100,
                   cps=100,
                   timestamp='2023-05-12 12:00:00',
                   elapsed_time=60,
                   check_count=100,
                   cemented_count=10,
                   percent_cemented=10,
                   percent_checked=10)
    sink.store_logs(logs)

    # Fetch the log from the database and verify
    stored_log = sink.get_log(sink.testcase_id)
    assert stored_log is not None
    assert stored_log.elapsed_time == logs.elapsed_time
    assert stored_log.check_count == logs.check_count
    os.remove(db_file)
    # Add more assertions for the other fields...


def test_update_testcase():
    db_file = "unit_tests/test_update_testcase.db"
    if os.path.exists(db_file):
        os.remove(db_file)
    sink = SqlSink(db_uri=f'sqlite:///{db_file}',
                   milestones={10, 25, 50, 75, 90, 99, 100},
                   testcase_name='test3')
    sink.update_testcase('FAIL')

    # Fetch the testcase from the database and verify status was updated correctly
    testcase = sink.get_testcase(sink.testcase_id)
    assert testcase is not None
    assert testcase.status == 'FAIL'
    os.remove(db_file)
