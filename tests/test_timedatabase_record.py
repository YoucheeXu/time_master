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

def test_del_record_nonexistent_rid(time_database: TimeDatabase, mocker):
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

def test_del_record_sql_format(time_database: TimeDatabase, mocker):
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
