#!/usr/bin/python3
# -*- coding: UTF-8 -*-
"""
    uv run pytest --cov=src.time_database .\tests\test_timedatabase_record.py -v
    uv run pytest --cov=src.time_database .\tests -v
    uv run pytest --cov=src.time_database .\tests --cov-report=html
"""
import pytest
import sqlite3
import datetime
# from unittest.mock import MagicMock
from pytest_mock import MockerFixture

from src.time_database import TimeDatabase

# --------------------------
# Pytest Fixtures (Reusable Resources)
# --------------------------
@pytest.fixture(scope="function")
def time_database():
    """Fixture to create a TimeDatabase instance with test database"""
    # return TimeDatabase(database=sqlite_db)

    db = TimeDatabase()
    _ = db.open(":memory:")
    _ = db.add_plan("Wakeup")
    _ = db.add_plan("Sleep")
    yield db
    _ = db.close()


# --------------------------
# Test Cases
# --------------------------
def test_datetime_timestamp_conversion(time_database: TimeDatabase):
    """Test the datetime <-> timestamp conversion methods"""
    # Test 1: Valid datetime -> timestamp (float)
    test_datetime = datetime.datetime(2026, 1, 27, 10, 30, 0)
    expected_timestamp = test_datetime.timestamp()  # Float (e.g., 1740613800.0)
    converted_timestamp = time_database._datetime2timestamp(test_datetime)
    assert isinstance(converted_timestamp, float)
    assert converted_timestamp == expected_timestamp

    # Test 2: dtime = None -> returns -1.0 (NOT None)
    assert time_database._datetime2timestamp(None) == -1.0

    # Test 3: Valid timestamp (float >0) -> datetime
    converted_datetime = time_database._timestamp2datetime(expected_timestamp)
    assert converted_datetime == test_datetime

    # Test 4: Timestamp ≤0 -> returns None
    assert time_database._timestamp2datetime(0.0) is None  # 0 → None
    assert time_database._timestamp2datetime(-100.0) is None  # Negative → None

def test_add_record_raise_no_last_insert_rowid(time_database: TimeDatabase, mocker: MockerFixture):
    """Test add_record raises RuntimeError when last_insert_rowid() returns None"""
    # Step 1: Mock database.execute1 (INSERT) and database.get
    mock_execute1 = mocker.patch.object(time_database._database, "execute1")
    mock_execute1.return_value = None  # Simulate INSERT success
    mock_get = mocker.patch.object(time_database._database, "get")
    mock_get.return_value = None  # Trigger "no last_insert_rowid" error

    # Step 2: Test data
    test_name = "Failed Record (no rid)"
    test_bgn_dtime = datetime.datetime(2026, 1, 27, 9, 0, 0)
    test_pid = 1

    # Step 3: Verify exception is raised
    with pytest.raises(RuntimeError) as exc_info:
        _ = time_database.add_record(
            name=test_name,
            bgn_dtime=test_bgn_dtime,
            pid=test_pid,
            duration=None
        )

    # Critical assertion: verify the right error is thrown (core test goal)
    assert "no last_insert_rowid" in str(exc_info.value)

    # Step 4: Robust assertion (ignore SQL whitespace, focus on parameters)
    # Get the actual call arguments from the mock
    actual_call_args = mock_execute1.call_args[0]
    actual_sql = actual_call_args[0]
    actual_params = actual_call_args[1]

    # 1. Verify SQL is an INSERT into RECORDS (ignore whitespace)
    clean_sql = " ".join(actual_sql.split())  # Remove extra spaces/newlines
    assert "INSERT INTO RECORDS (pid, name, bgn_timestamp, end_timestamp) VALUES (?, ?, ?, ?)" in clean_sql

    # 2. Verify parameters are correct (the important part!)
    expected_bgn_ts = test_bgn_dtime.timestamp()
    expected_end_ts = -1.0 if isinstance(time_database._datetime2timestamp(None), float) else -1
    expected_params = (test_pid, test_name, expected_bgn_ts, expected_end_ts)

    # Allow minor type differences (int -1 vs float -1.0)
    normalized_actual_params = [
        p if not isinstance(p, float) or not p.is_integer() else int(p)
        for p in actual_params
    ]
    normalized_expected_params = [
        p if not isinstance(p, float) or not p.is_integer() else int(p)
        for p in expected_params
    ]

    assert normalized_actual_params == normalized_expected_params

    # 3. Verify get was called with the right query (simplified)
    mock_get.assert_called_once_with("SELECT last_insert_rowid()")

def test_add_record_success(time_database: TimeDatabase):
    """Test successful record insertion and auto-increment ID retrieval"""
    # Test data
    record_name = "Test Record"
    bgn_dtime = datetime.datetime(2026, 1, 27, 9, 0, 0)
    pid = 1
    end_dtime = datetime.datetime(2026, 1, 27, 17, 0, 0)

    # Insert record
    rid = time_database.add_record(
        name=record_name,
        bgn_dtime=bgn_dtime,
        pid=pid,
        duration=end_dtime
    )

    # Verify ID is integer and starts at 1 (first record)
    assert isinstance(rid, int)
    assert rid == 1

    # Verify record exists in database
    record = time_database._database.get(f"SELECT * FROM RECORDS WHERE rid = {rid}")
    assert record is not None
    assert record[1] == pid  # pid
    assert record[2] == record_name  # name
    assert record[3] == int(bgn_dtime.timestamp())  # bgn_timestamp
    assert record[4] == int(end_dtime.timestamp())  # end_timestamp

def test_add_record_with_none_end_dtime(time_database: TimeDatabase):
    """Test record insertion with end_dtime = None"""
    # Insert record with no end time
    rid = time_database.add_record(
        name="No End Time",
        bgn_dtime=datetime.datetime(2026, 1, 27, 8, 0, 0),
        pid=2,
        duration=None
    )

    assert rid == 1
    # Verify end_timestamp is NULL in database
    end_ts = time_database._database.get(f"SELECT end_timestamp FROM RECORDS WHERE rid = {rid}")
    assert end_ts[0] == -1

def test_add_record_failure(time_database: TimeDatabase):
    """Test exception handling when record insertion fails"""
    # Drop RECORDS table to force insertion failure
    time_database._database.execute("DROP TABLE RECORDS")

    # Verify RuntimeError is raised
    with pytest.raises(sqlite3.OperationalError) as exc_info:
        _ = time_database.add_record(
            name="Failed Record",
            bgn_dtime=datetime.datetime(2026, 1, 27, 10, 0, 0)
        )

    # Check error message contains key information
    assert "no such table: RECORDS" in str(exc_info.value)

def test_get_records_single_day(time_database: TimeDatabase):
    """Test querying records for a single day"""
    # Insert test records (same day)
    test_date = datetime.date(2026, 1, 27)
    bgn_dtime1 = datetime.datetime(2026, 1, 27, 9, 0, 0)
    bgn_dtime2 = datetime.datetime(2026, 1, 27, 14, 0, 0)

    _ = time_database.add_record(name="Record 1", bgn_dtime=bgn_dtime1, pid=1)
    _ = time_database.add_record(name="Record 2", bgn_dtime=bgn_dtime2, pid=2)

    # Query single day
    records = time_database.get_records(start_date=test_date)

    # Verify 2 records are returned
    assert len(records) == 2
    assert 1 in records  # rid 1
    assert 2 in records  # rid 2
    assert records[1]["name"] == "Record 1"
    assert records[2]["name"] == "Record 2"

def test_get_records_date_range(time_database: TimeDatabase):
    """Test querying records across a date range"""
    # Insert records across 3 days
    record1_dtime = datetime.datetime(2026, 1, 26, 10, 0, 0)  # 26th
    record2_dtime = datetime.datetime(2026, 1, 27, 10, 0, 0)  # 27th
    record3_dtime = datetime.datetime(2026, 1, 28, 10, 0, 0)  # 28th

    _ = time_database.add_record(name="Record 26", bgn_dtime=record1_dtime, pid=1)
    _ = time_database.add_record(name="Record 27", bgn_dtime=record2_dtime, pid=1)
    _ = time_database.add_record(name="Record 28", bgn_dtime=record3_dtime, pid=1)

    # Query range: 26th - 27th
    start_date = datetime.date(2026, 1, 26)
    end_date = datetime.date(2026, 1, 27)
    records = time_database.get_records(start_date=start_date, end_date=end_date)

    # Verify only 2 records (26th and 27th) are returned
    assert len(records) == 2
    assert records[1]["name"] == "Record 26"
    assert records[2]["name"] == "Record 27"
    assert 3 not in records  # 28th record excluded

def test_get_records_no_results(time_database: TimeDatabase):
    """Test query returns empty dict when no records match"""
    # Query a date with no records
    empty_date = datetime.date(2026, 1, 1)
    records = time_database.get_records(start_date=empty_date)

    assert len(records) == 0
    assert isinstance(records, dict)

# --------------------------
# Test Data Setup (Helper)
# --------------------------
def insert_sample_records(time_database: TimeDatabase):
    """Insert sample records with different pids/dates for testing"""
    # Record 1: pid=1, 2026-01-27
    _ = time_database.add_record(
        name="Record 1 (pid1)",
        bgn_dtime=datetime.datetime(2026, 1, 27, 9, 0, 0),
        pid=1
    )

    # Record 2: pid=2, 2026-01-27
    _ = time_database.add_record(
        pid=2,
        name="Record 2 (pid2)",
        bgn_dtime=datetime.datetime(2026, 1, 27, 10, 0, 0)
    )

    # Record 3: pid=1, 2026-01-28 (different date)
    _ = time_database.add_record(
        name="Record 3 (pid1, 2026-01-28)",
        bgn_dtime=datetime.datetime(2026, 1, 28, 11, 0, 0),
        pid=1
    )

    # Record 4: pid=2, 2026-01-27 (unmatched pid)
    _ = time_database.add_record(
        name="Record 4 (pid2)",
        bgn_dtime=datetime.datetime(2026, 1, 27, 12, 0, 0),
        pid=2
    )

# --------------------------
# Core Test Cases for get_records
# --------------------------
def test_get_records_pid_default_all_records(time_database: TimeDatabase):
    """Test default pid=-1: returns ALL records in date range"""
    # Insert sample data
    insert_sample_records(time_database)

    # Query 2026-01-27 with default pid=-1 (all records)
    query_date = datetime.date(2026, 1, 27)
    records = time_database.get_records(start_date=query_date)

    # Verify: 3 records (pid1, pid2, pid2) from 2026-01-27
    assert len(records) == 3
    # Check all returned pids are in [1001, 1002, 9999]
    returned_pids = [record["pid"] for record in records.values()]
    assert set(returned_pids) == {1, 2, 2}

def test_get_records_pid_filter_specific(time_database: TimeDatabase):
    """Test specific pid (1): only returns matching pid records in date range"""
    # Insert sample data
    insert_sample_records(time_database)

    # Query 2026-01-27 with pid=1001
    query_date = datetime.date(2026, 1, 27)
    records = time_database.get_records(start_date=query_date, pid=1)

    # Verify: only 1 record (pid1, 2026-01-27)
    assert len(records) == 1
    # Check the only record has pid=1
    assert list(records.values())[0]["pid"] == 1
    # Check record name matches
    assert list(records.values())[0]["name"] == "Record 1 (pid1)"

def test_get_records_pid_filter_no_match(time_database: TimeDatabase):
    """Test specific pid with no matches: returns empty dict"""
    # Insert sample data
    insert_sample_records(time_database)

    # Query 2026-01-27 with pid=5555 (no matching records)
    query_date = datetime.date(2026, 1, 27)
    records = time_database.get_records(start_date=query_date, pid=5555)

    # Verify: empty dict (no matches)
    assert len(records) == 0
    assert isinstance(records, dict)

def test_get_records_pid_with_date_range(time_database: TimeDatabase):
    """Test pid filter + date range: returns matching pid in range"""
    # Insert sample data
    insert_sample_records(time_database)

    # Query 2026-01-27 to 2026-01-28 with pid=1001
    start_date = datetime.date(2026, 1, 27)
    end_date = datetime.date(2026, 1, 28)
    records = time_database.get_records(start_date=start_date, end_date=end_date, pid=1)

    # Verify: 2 records (pid1 on 27th + 28th)
    assert len(records) == 2
    # Check both records have pid=1
    returned_pids = [record["pid"] for record in records.values()]
    assert all(pid == 1 for pid in returned_pids)
    # Check record names (covers both dates)
    returned_names = [record["name"] for record in records.values()]
    assert set(returned_names) == {"Record 1 (pid1)", "Record 3 (pid1, 2026-01-28)"}

def test_get_records_pid_single_day_no_results(time_database: TimeDatabase):
    """Test pid filter + date with no records: returns empty dict"""
    # Insert sample data (only 2026-01-27 records)
    insert_sample_records(time_database)

    # Query 2026-01-29 (no records) with pid=1
    query_date = datetime.date(2026, 1, 29)
    records = time_database.get_records(start_date=query_date, pid=1)

    # Verify: empty dict
    assert len(records) == 0

# --------------------------
# Regression Tests (Ensure Date Logic Still Works)
# --------------------------
def test_get_records_date_range_no_pid_filter(time_database: TimeDatabase):
    """Regression: date range logic works with pid=-1 (all records)"""
    # Insert sample data
    insert_sample_records(time_database)

    # Query 2026-01-27 to 2026-01-28 (pid=-1: all records)
    start_date = datetime.date(2026, 1, 27)
    end_date = datetime.date(2026, 1, 28)
    records = time_database.get_records(start_date=start_date, end_date=end_date)

    # Verify: 4 records (all sample records: 27th x3 + 28th x1)
    assert len(records) == 4
    returned_names = [record["name"] for record in records.values()]
    assert set(returned_names) == {
        "Record 1 (pid1)",
        "Record 2 (pid2)",
        "Record 3 (pid1, 2026-01-28)",
        "Record 4 (pid2)"
    }

# --------------------------
# Test Cases for del_record
# --------------------------
def test_del_record_success(time_database: TimeDatabase):
    """Test successful deletion of an existing record"""
    # Step 1: Insert a test record and get its rid
    test_pid = 1
    test_name = "To Be Deleted"
    test_bgn_dtime = datetime.datetime(2026, 1, 27, 9, 0, 0)
    rid = time_database.add_record(
        pid=test_pid,
        name=test_name,
        bgn_dtime=test_bgn_dtime
    )

    # Verify the record exists before deletion
    record = time_database._database.get(f"SELECT * FROM RECORDS WHERE rid = {rid}")
    assert rid == record[0], "Test record should exist before deletion"

    # Step 2: Call del_record to delete the record
    time_database.del_record(rid=rid)

    # Step 3: Verify the record is deleted
    record = time_database._database.get(f"SELECT * FROM RECORDS WHERE rid = {rid}")
    assert record is None, "Test record should be deleted"

def test_del_record_nonexistent_rid(time_database: TimeDatabase, mocker: MockerFixture):
    """Test deletion of a non-existent rid (no error, no database changes)"""
    # Step 1: Insert a valid record (to ensure DB isn't empty)
    existing_rid = time_database.add_record(
        pid=2,
        name="Existing Record",
        bgn_dtime=datetime.datetime(2026, 1, 27, 10, 0, 0)
    )

    # Step 2: Mock execute1 to verify it's called (no error expected)
    # mock_execute1 = mocker.patch.object(time_database._database, "execute1")
    # mock_execute1.return_value = None

    # Step 3: Call del_record with a non-existent rid (e.g., 2)
    nonexistent_rid = 2
    time_database.del_record(rid=nonexistent_rid)  # Should NOT raise an error

    # Step 4: Verify existing record is still present (no unintended deletion)
    record = time_database._database.get(f"SELECT * FROM RECORDS WHERE rid = {existing_rid}")
    assert existing_rid == record[0], "Existing record should remain after deleting non-existent rid"

    # Step 5: Verify execute1 was called with the correct SQL
    # expected_sql = f"DELETE FROM RECORDS WHERE rid='{nonexistent_rid}'"
    # mock_execute1.assert_called_once_with(expected_sql)

def test_del_record_sql_format(time_database: TimeDatabase, mocker: MockerFixture):
    """Test the generated DELETE SQL has the correct format"""
    # Step 1: Mock execute1 and pv (to suppress print output)
    mock_execute1 = mocker.patch.object(time_database._database, "execute1")
    mock_pv = mocker.patch("src.time_database.pv")  # Replace "your_module" with where pv is defined

    # Step 2: Call del_record with a test rid
    test_rid = 123
    time_database.del_record(rid=test_rid)

    # Step 3: Verify pv was called with the correct SQL (optional, if pv is important)
    expected_sql = f"DELETE FROM RECORDS WHERE rid='{test_rid}'"
    mock_pv.assert_called_once_with(expected_sql)

    # Step 4: Verify execute1 was called with the correct SQL
    mock_execute1.assert_called_once_with(expected_sql)

def test_del_record_invalid_rid_type(time_database: TimeDatabase):
    """Test del_record raises TypeError for non-integer rid"""
    # Step 1: Test string rid (should raise TypeError)
    invalid_rid_str = "invalid_rid"
    with pytest.raises(TypeError) as exc_info:
        time_database.del_record(rid=invalid_rid_str)
    
    # Verify error message is meaningful
    assert "rid must be an integer (got str: invalid_rid)" in str(exc_info.value)

    # Step 2: (Optional) Test non-positive integer rid (raises ValueError)
    invalid_rid_negative = -5
    with pytest.raises(ValueError) as exc_info:
        time_database.del_record(rid=invalid_rid_negative)
    
    assert f"rid must be a positive integer (got {invalid_rid_negative})" in str(exc_info.value)
