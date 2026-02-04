#!/usr/bin/python3
# -*- coding: UTF-8 -*-
"""
    uv run pytest --cov=src.time_database_reminder .\tests\test_timedatabase_reminder.py -v
    uv run pytest --cov=src.time_database_reminder .\tests\test_timedatabase_reminder.py --cov-report=html
"""
import pytest
import json
import datetime

from src.time_database_type import TimeUnit, DayType
from src.time_database_type import ReminderDataDict
from src.time_database_reminder import serialize_reminder_collection
from src.time_database_reminder import deserialize_reminder_collection
from src.time_database_reminder import _is_valid_reminder_collection
from src.time_database_reminder import _is_valid_reminder_data_dict
# from src.time_database_reminder import _serialize_single_reminder
from src.time_database_reminder import _deserialize_single_reminder
from src.time_database_reminder import ReminderJsonDict
from src.time_database_reminder import parse_iso_time
from src.time_database_reminder import parse_iso_datetime


ReminderCollection = dict[int, ReminderDataDict]

# -------------------------- Test Fixtures (Reusable Test Data) --------------------------
@pytest.fixture
def valid_reminder_collection() -> ReminderCollection:
    """Fixture: Valid reminder collection with complete fields."""
    return {
        1: ReminderDataDict(
            clk_time=datetime.time(9, 0, 0),
            bgn_time=datetime.time(8, 30, 0),
            duration=60,
            every=1,
            unit=TimeUnit.DAY,
            custom=DayType.WORKDAY,
            cycbgn_dtime=datetime.datetime(2026, 2, 4, 0, 0),
            cycend_dtime=datetime.datetime(2026, 12, 31, 23, 59)
        ),
        2: ReminderDataDict(
            clk_time=datetime.time(14, 15, 0),
            bgn_time=datetime.time(14, 0, 0),
            duration=30,
            every=2,
            unit=TimeUnit.WEEK,
            custom=DayType.WEEKEND,
            cycbgn_dtime=datetime.datetime(2026, 3, 1, 0, 0),
            cycend_dtime=None
        )
    }

@pytest.fixture
def empty_reminder_collection() -> ReminderCollection:
    """Fixture: Empty reminder collection (empty dict)."""
    return {}

@pytest.fixture
def reminder_collection_with_none_fields() -> ReminderCollection:
    """Fixture: Reminder collection with multiple None fields."""
    return {
        3: ReminderDataDict(
            clk_time=None,
            bgn_time=None,
            duration=0,
            every=1,
            unit=TimeUnit.HOUR,
            custom=DayType.EVERYDAY,
            cycbgn_dtime=None,
            cycend_dtime=None
        )
    }

@pytest.fixture
def reminder_collection_with_custom_list() -> ReminderCollection:
    """Fixture: Reminder collection with custom field as list[int]."""
    return {
        4: ReminderDataDict(
            clk_time=datetime.time(10, 0, 0),
            bgn_time=datetime.time(9, 30, 0),
            duration=45,
            every=1,
            unit=TimeUnit.MONTH,
            custom=[1, 5, 10],
            cycbgn_dtime=datetime.datetime(2026, 1, 1, 0, 0),
            cycend_dtime=datetime.datetime(2026, 12, 31, 23, 59)
        )
    }

# -------------------------- Normal Case Tests --------------------------
def test_serialize_deserialize_round_trip(valid_reminder_collection: ReminderCollection):
    """Test round-trip serialization/deserialization returns identical data."""
    # Serialize to JSON string
    json_str = serialize_reminder_collection(valid_reminder_collection)

    # Deserialize back to ReminderCollection
    restored_collection = deserialize_reminder_collection(json_str)

    # Verify data consistency (field-by-field comparison)
    assert isinstance(restored_collection, dict)
    assert set(restored_collection.keys()) == set(valid_reminder_collection.keys())

    for rid, original in valid_reminder_collection.items():
        restored = restored_collection[rid]

        # Verify primitive fields
        assert restored["duration"] == original["duration"]
        assert restored["every"] == original["every"]

        # Verify enum fields
        assert restored["unit"] == original["unit"]
        assert restored["custom"] == original["custom"]

        # Verify datetime/time fields (handle None)
        assert restored["clk_time"] == original["clk_time"]
        assert restored["bgn_time"] == original["bgn_time"]
        assert restored["cycbgn_dtime"] == original["cycbgn_dtime"]
        assert restored["cycend_dtime"] == original["cycend_dtime"]

def test_serialize_empty_collection(empty_reminder_collection: ReminderCollection):
    """Test serialization of empty reminder collection."""
    json_str = serialize_reminder_collection(empty_reminder_collection)
    assert json.loads(json_str) == {}

def test_deserialize_empty_collection():
    """Test deserialization of empty JSON dict (empty collection)."""
    empty_json = "{}"
    restored_collection = deserialize_reminder_collection(empty_json)
    assert restored_collection == {}

def test_serialize_with_none_fields(reminder_collection_with_none_fields: ReminderCollection):
    """Test serialization/deserialization with None fields and edge-case duration (0)."""
    json_str = serialize_reminder_collection(reminder_collection_with_none_fields)
    restored_collection = deserialize_reminder_collection(json_str)

    # Verify None fields are preserved
    restored = restored_collection[3]
    assert restored["clk_time"] is None
    assert restored["bgn_time"] is None
    assert restored["cycbgn_dtime"] is None
    assert restored["cycend_dtime"] is None
    assert restored["duration"] == 0

def test_serialize_with_custom_list(reminder_collection_with_custom_list: ReminderCollection):
    """Test serialization/deserialization with custom field as list[int]."""
    json_str = serialize_reminder_collection(reminder_collection_with_custom_list)
    restored_collection = deserialize_reminder_collection(json_str)

    # Verify custom list is preserved
    restored = restored_collection[4]
    assert isinstance(restored["custom"], list)
    assert restored["custom"] == [1, 5, 10]
    assert all(isinstance(x, int) for x in restored["custom"])

# -------------------------- Error Case Tests --------------------------
def test_deserialize_invalid_json_format():
    """Test deserialization fails with invalid JSON format."""
    invalid_json = '{"1": {"clk_time": "09:00:00", "duration": 60, missing_colon "invalid"}}'

    with pytest.raises(json.JSONDecodeError) as excinfo:
        _ = deserialize_reminder_collection(invalid_json)

    assert "Invalid JSON format" in str(excinfo.value) or "Expecting ':' delimiter" in str(excinfo.value)

def test_deserialize_non_int_reminder_id():
    """Test deserialization fails when reminder ID is non-integer (JSON string key)."""
    # JSON key is "invalid_id" (non-integer)
    invalid_json = '''
    {
        "invalid_id": {
            "clk_time": "09:00:00",
            "bgn_time": "08:30:00",
            "duration": 60,
            "every": 1,
            "unit": 2,
            "custom": 2,
            "cycbgn_dtime": "2026-02-04T00:00:00",
            "cycend_dtime": "2026-12-31T23:59:00"
        }
    }
    '''

    with pytest.raises(ValueError) as excinfo:
        _ = deserialize_reminder_collection(invalid_json)

    assert "Reminder ID must be an integer" in str(excinfo.value)

def test_deserialize_negative_duration():
    """Test deserialization fails with negative duration."""
    invalid_json = '''
    {
        "1": {
            "clk_time": "09:00:00",
            "bgn_time": "08:30:00",
            "duration": -60,
            "every": 1,
            "unit": 2,
            "custom": 2,
            "cycbgn_dtime": "2026-02-04T00:00:00",
            "cycend_dtime": "2026-12-31T23:59:00"
        }
    }
    '''

    with pytest.raises(ValueError) as excinfo:
        _ = deserialize_reminder_collection(invalid_json)

    assert "Duration cannot be negative" in str(excinfo.value)

def test_deserialize_every_less_than_0():
    """Test deserialization fails when 'every' is less than 0."""
    invalid_json = '''
    {
        "1": {
            "clk_time": "09:00:00",
            "bgn_time": "08:30:00",
            "duration": 60,
            "every": -1,
            "unit": 2,
            "custom": 2,
            "cycbgn_dtime": "2026-02-04T00:00:00",
            "cycend_dtime": "2026-12-31T23:59:00"
        }
    }
    '''

    with pytest.raises(ValueError) as excinfo:
        _ = deserialize_reminder_collection(invalid_json)

    # Assert the correct error message
    assert "Recurrence interval must not be less than 0" in str(excinfo.value)
    assert "-1" in str(excinfo.value)  # Verify the invalid negative value is in the message

def test_deserialize_invalid_unit_value():
    """Test deserialization fails with invalid TimeUnit value."""
    invalid_json = '''
    {
        "1": {
            "clk_time": "09:00:00",
            "bgn_time": "08:30:00",
            "duration": 60,
            "every": 1,
            "unit": 999,
            "custom": 2,
            "cycbgn_dtime": "2026-02-04T00:00:00",
            "cycend_dtime": "2026-12-31T23:59:00"
        }
    }
    '''

    with pytest.raises(ValueError) as excinfo:
        _ = deserialize_reminder_collection(invalid_json)

    assert "Invalid TimeUnit value" in str(excinfo.value)

def test_deserialize_invalid_custom_int():
    """Test deserialization fails with invalid DayType value (custom as int)."""
    invalid_json = '''
    {
        "1": {
            "clk_time": "09:00:00",
            "bgn_time": "08:30:00",
            "duration": 60,
            "every": 1,
            "unit": 2,
            "custom": 999,
            "cycbgn_dtime": "2026-02-04T00:00:00",
            "cycend_dtime": "2026-12-31T23:59:00"
        }
    }
    '''

    with pytest.raises(ValueError) as excinfo:
        _ = deserialize_reminder_collection(invalid_json)

    assert "Invalid DayType value" in str(excinfo.value)

def test_deserialize_custom_list_with_non_int():
    """Test deserialization fails when custom list contains non-integer values."""
    invalid_json = '''
    {
        "1": {
            "clk_time": "09:00:00",
            "bgn_time": "08:30:00",
            "duration": 60,
            "every": 1,
            "unit": 3,
            "custom": [1, "5", 10],
            "cycbgn_dtime": "2026-01-01T00:00:00",
            "cycend_dtime": "2026-12-31T23:59:00"
        }
    }
    '''

    with pytest.raises(ValueError) as excinfo:
        _ = deserialize_reminder_collection(invalid_json)

    assert "Custom list must contain only integers" in str(excinfo.value)

def test_serialize_invalid_collection():
    """Test serialization fails with invalid ReminderCollection (non-int keys)."""
    # Invalid: key is string "1" instead of int 1
    invalid_collection = {
        "1": ReminderDataDict(
            clk_time=datetime.time(9, 0, 0),
            bgn_time=datetime.time(8, 30, 0),
            duration=60,
            every=1,
            unit=TimeUnit.DAY,
            custom=DayType.WORKDAY,
            cycbgn_dtime=datetime.datetime(2026, 2, 4, 0, 0),
            cycend_dtime=datetime.datetime(2026, 12, 31, 23, 59)
        )
    }

    with pytest.raises(TypeError) as excinfo:
        _ = serialize_reminder_collection(invalid_collection)

    assert "Input is not a valid ReminderCollection" in str(excinfo.value)

# -------------------------- Parameterized Test (Optional) --------------------------
@pytest.mark.parametrize("indent, expected_indentation", [
    (2, 2),  # Indented with 2 spaces
    (None, 0),  # Compact (no indentation)
])
def test_serialize_indentation(valid_reminder_collection: ReminderCollection, indent: int | None, expected_indentation: int):
    """Parameterized test for JSON indentation during serialization."""
    json_str = serialize_reminder_collection(valid_reminder_collection, indent=indent)

    if expected_indentation == 0:
        # Compact JSON: no newlines/indentation
        assert "\n  " not in json_str
    else:
        # Indented JSON: verify indentation
        lines = json_str.split("\n")
        # Skip first line ("{") and check second line indentation
        assert lines[1].startswith(" " * expected_indentation)

def test_serialize_with_non_ascii_chars(valid_reminder_collection: ReminderCollection):
    """Test serialization with non-ASCII chars (ensure_ascii=True/False)."""
    # Modify collection to include non-ASCII (e.g., Chinese/Japanese)
    reminder_with_non_ascii = valid_reminder_collection[1].copy()
    # NOTE: If your ReminderDataDict has a "name" field (adjust if needed)
    # reminder_with_non_ascii["name"] = "学习Python 🚀"
    test_col = {1: reminder_with_non_ascii}

    # Test ensure_ascii=False (preserve non-ASCII)
    json_str = serialize_reminder_collection(test_col, ensure_ascii=False)
    # assert "学习Python 🚀" in json_str  # Uncomment if you added a name field

    # Test ensure_ascii=True (escape non-ASCII)
    json_str_escaped = serialize_reminder_collection(test_col, ensure_ascii=True)
    # assert "\\u5b66\\u4e60Python" in json_str_escaped  # Escaped Chinese chars

def test_serialize_compact_json(valid_reminder_collection: ReminderCollection):
    """Test serialization with indent=None (compact JSON, no newlines)."""
    json_str = serialize_reminder_collection(valid_reminder_collection, indent=None)
    # Verify no newlines/indentation (compact format)
    assert "\n" not in json_str
    assert "  " not in json_str

@pytest.mark.parametrize("unit_value, unit_enum", [
    (1, TimeUnit.HOUR),
    (2, TimeUnit.DAY),
    (3, TimeUnit.WEEK),
    (4, TimeUnit.MONTH),
    (5, TimeUnit.SEASON),
    (6, TimeUnit.YEAR),
])
def test_deserialize_all_timeunit_values(unit_value: int, unit_enum: TimeUnit):
    """Test deserialization for ALL TimeUnit enum values (covers enum validation)."""
    valid_json = f'''
    {{
        "1": {{
            "clk_time": "09:00:00",
            "bgn_time": "08:30:00",
            "duration": 60,
            "every": 0,
            "unit": {unit_value},
            "custom": 1,
            "cycbgn_dtime": "2026-02-04T00:00:00",
            "cycend_dtime": "2026-12-31T23:59:00"
        }}
    }}
    '''
    restored = deserialize_reminder_collection(valid_json)
    assert restored[1]["unit"] == unit_enum

@pytest.mark.parametrize("custom_int, custom_enum", [
    (1, DayType.EVERYDAY),
    (2, DayType.WORKDAY),
    (3, DayType.WEEKEND),
    (4, DayType.HOLIDAY),
])
def test_deserialize_all_daytype_values(custom_int: int, custom_enum: DayType):
    """Test deserialization for ALL DayType enum values (covers enum validation)."""
    valid_json = f'''
    {{
        "1": {{
            "clk_time": "09:00:00",
            "bgn_time": "08:30:00",
            "duration": 60,
            "every": 0,
            "unit": 2,
            "custom": {custom_int},
            "cycbgn_dtime": "2026-02-04T00:00:00",
            "cycend_dtime": "2026-12-31T23:59:00"
        }}
    }}
    '''
    restored = deserialize_reminder_collection(valid_json)
    assert restored[1]["custom"] == custom_enum

def test_deserialize_optional_fields_with_null_values():
    """Test deserialization with required fields set to null (not missing).
    
    All ReminderJsonDict fields exist (per total=True), but optional-like values are null.
    """
    # ✅ All fields are present (no missing) — null for empty values
    valid_json = '''
    {
        "1": {
            "clk_time": null,
            "bgn_time": null,
            "duration": 60,
            "every": 0,
            "unit": 2,
            "custom": 2,
            "cycbgn_dtime": "2026-02-04T00:00:00",
            "cycend_dtime": null
        }
    }
    '''

    # Deserialize (no KeyError now — all fields exist)
    restored = deserialize_reminder_collection(valid_json)
    
    # Verify null values are parsed to None (correct behavior)
    assert restored[1]["clk_time"] is None
    assert restored[1]["bgn_time"] is None
    assert restored[1]["cycend_dtime"] is None
    
    # Verify non-null fields are parsed correctly
    assert restored[1]["cycbgn_dtime"] == datetime.datetime(2026, 2, 4, 0, 0)
    assert restored[1]["duration"] == 60
    assert restored[1]["every"] == 0

def test_deserialize_missing_required_field_throws_error():
    """Test deserialization fails when a required ReminderJsonDict field is missing."""
    # JSON missing "clk_time" (required field per total=True)
    invalid_json = '''
    {
        "1": {
            "bgn_time": null,
            "duration": 60,
            "every": 0,
            "unit": 2,
            "custom": 2,
            "cycbgn_dtime": "2026-02-04T00:00:00",
            "cycend_dtime": null
        }
    }
    '''

    # Verify KeyError is thrown for missing required field
    with pytest.raises(KeyError) as excinfo:
        deserialize_reminder_collection(invalid_json)
    
    assert "Reminder 1 is missing required fields: clk_time" in str(excinfo.value)

def test_deserialize_all_optional_fields_none():
    """Test deserialization with ALL optional fields set to None (extreme edge case)."""
    valid_json = '''
    {
        "1": {
            "clk_time": null,
            "bgn_time": null,
            "duration": 0,
            "every": 0,
            "unit": 2,
            "custom": [],
            "cycbgn_dtime": null,
            "cycend_dtime": null
        }
    }
    '''
    restored = deserialize_reminder_collection(valid_json)
    # Verify all optional fields are None
    assert restored[1]["clk_time"] is None
    assert restored[1]["bgn_time"] is None
    assert restored[1]["cycbgn_dtime"] is None
    assert restored[1]["cycend_dtime"] is None
    # Verify boundary values
    assert restored[1]["duration"] == 0
    assert restored[1]["every"] == 0
    assert restored[1]["custom"] == []  # Empty list is valid

def test_parse_invalid_iso_time():
    """Test _parse_iso_time fails with invalid time strings (covers error branch)."""
    invalid_time_strs = ["25:00", "09:60", "09-00", "invalid"]
    for time_str in invalid_time_strs:
        with pytest.raises(ValueError) as excinfo:
            parse_iso_time(time_str)
        assert "Invalid ISO 8601 time format" in str(excinfo.value)

def test_parse_invalid_iso_datetime():
    """Test _parse_iso_datetime fails with invalid datetime strings (covers error branch)."""
    invalid_dt_strs = [
        "2026-13-04T00:00",  # Invalid month (13)
        "2026-02-30T00:00",  # Invalid day (30 Feb)
        "2026-02-04 00:00",  # Missing 'T' separator
        "invalid_datetime"
    ]
    for dt_str in invalid_dt_strs:
        with pytest.raises(ValueError) as excinfo:
            parse_iso_datetime(dt_str)
        assert "Invalid ISO 8601 datetime format" in str(excinfo.value)

def test_parse_invalid_iso_time():
    """Test _parse_iso_time fails with invalid time strings (covers error branch)."""
    invalid_time_strs = ["25:00:00", "09:60:00", "09-00-00", "invalid"]
    for time_str in invalid_time_strs:
        with pytest.raises(ValueError) as excinfo:
            parse_iso_time(time_str)
        assert "Invalid ISO 8601 time format" in str(excinfo.value)

def test_parse_invalid_iso_datetime():
    """Test _parse_iso_datetime fails with invalid datetime strings (covers error branch)."""
    invalid_dt_strs = [
        "2026-13-04T00:00:00",  # Invalid month (13)
        "2026-02-30T00:00:00",  # Invalid day (30 Feb)
        "invalid_datetime",     # Completely invalid string
        "2026-04-31T12:00:00",  # Invalid day (31 Apr)
        "2026-02-04T25:00:00",  # Invalid hour (25)
    ]
    for dt_str in invalid_dt_strs:
        with pytest.raises(ValueError) as excinfo:
            parse_iso_datetime(dt_str)
        
        # Optional: Validate the error message is correct (boosts test quality)
        assert "Invalid ISO 8601 datetime format" in str(excinfo.value)
        assert dt_str in str(excinfo.value)  # Ensure the invalid string is in the error message

def test_serialize_deserialize_empty_custom_list():
    """Test serialization/deserialization of empty custom list (valid edge case)."""
    test_collection: ReminderCollection = {
        1: ReminderDataDict(
            clk_time=None,
            bgn_time=None,
            duration=0,
            every=0,
            unit=TimeUnit.DAY,
            custom=[],  # Empty list (valid)
            cycbgn_dtime=None,
            cycend_dtime=None
        )
    }
    # Serialize
    json_str = serialize_reminder_collection(test_collection)
    # Deserialize
    restored = deserialize_reminder_collection(json_str)
    # Verify empty list is preserved
    assert restored[1]["custom"] == []

@pytest.mark.parametrize("invalid_obj, failure_reason", [
    # Scenario 1: Not a dict
    (123, "Not a dict"),
    ("invalid_str", "Not a dict"),
    (["list"], "Not a dict"),
    # Scenario 2: Missing required fields
    ({"every": 0, "unit": TimeUnit.DAY, "custom": DayType.WORKDAY}, "Missing duration"),
    ({"duration": 60, "unit": TimeUnit.DAY, "custom": DayType.WORKDAY}, "Missing every"),
    ({"duration": 60, "every": 0, "custom": DayType.WORKDAY}, "Missing unit"),
    ({"duration": 60, "every": 0, "unit": TimeUnit.DAY}, "Missing custom"),
    # Scenario 3: Required field type errors
    ({"duration": "60", "every": 0, "unit": TimeUnit.DAY, "custom": DayType.WORKDAY}, "Duration is str (not int)"),
    ({"duration": 60, "every": 0.5, "unit": TimeUnit.DAY, "custom": DayType.WORKDAY}, "Every is float (not int)"),
    ({"duration": 60, "every": 0, "unit": 2, "custom": DayType.WORKDAY}, "Unit is int (not TimeUnit enum)"),
    ({"duration": 60, "every": 0, "unit": TimeUnit.DAY, "custom": "workday"}, "Custom is str (not DayType/list)"),
    # Scenario 4: Numeric constraints violated
    ({"duration": -10, "every": 0, "unit": TimeUnit.DAY, "custom": DayType.WORKDAY}, "Duration negative"),
    ({"duration": 60, "every": -5, "unit": TimeUnit.DAY, "custom": DayType.WORKDAY}, "Every negative"),
    # Scenario 5: Custom list with non-int elements
    ({"duration": 60, "every": 0, "unit": TimeUnit.DAY, "custom": [1, "5", 10]}, "Custom list has str"),
    # Scenario 6: Optional field type error
    (
        {
            "clk_time": "09:00:00",  # Str instead of time/None
            "bgn_time": datetime.datetime.now(),  # Datetime instead of time/None
            "duration": 60,
            "every": 0,
            "unit": TimeUnit.DAY,
            "custom": DayType.WORKDAY
        },
        "Optional fields have invalid types"
    ),
])
def test_is_valid_reminder_data_dict_returns_false(invalid_obj: object, failure_reason: str):
    """Test _is_valid_reminder_data_dict returns False for all invalid scenarios."""
    assert _is_valid_reminder_data_dict(invalid_obj) is False, f"Failed for: {failure_reason}"

@pytest.mark.parametrize("invalid_collection, failure_reason", [
    # Scenario 1: Not a dict
    (123, "Not a dict"),
    (["reminder1", "reminder2"], "Not a dict"),
    # Scenario 2: Keys are not integers
    (
        {"1": ReminderDataDict(  # Key is str instead of int
            clk_time=None,
            bgn_time=None,
            duration=60,
            every=0,
            unit=TimeUnit.DAY,
            custom=DayType.WORKDAY,
            cycbgn_dtime=None,
            cycend_dtime=None
        )},
        "Key is str (not int)"
    ),
    # Scenario 3: Values are invalid ReminderDataDict
    (
        {1: {"duration": -10, "every": 0, "unit": TimeUnit.DAY, "custom": DayType.WORKDAY}},  # Negative duration
        "Value is invalid ReminderDataDict"
    ),
])
def test_is_valid_reminder_collection_returns_false(invalid_collection: object, failure_reason: str):
    """Test _is_valid_reminder_collection returns False for all invalid scenarios."""
    assert _is_valid_reminder_collection(invalid_collection) is False, f"Failed for: {failure_reason}"

@pytest.mark.parametrize("invalid_dt_str, error_substring", [
    ("2026-02-04T25:00:00", "hour must be in 0..23"),  # Invalid hour
    ("2026-02-04T09:60:00", "minute must be in 0..59"),  # Invalid minute
    ("2026-02-04T09:00:60", "second must be in 0..59"),  # Invalid second
    ("2026-02-04T23:59:60", "second must be in 0..59"),  # Invalid second
    ("2026-13-04T00:00:00", "month must be in 1..12"),  # Invalid month (original fromisoformat error)
    ("2026-02-30T00:00:00", "day is out of range for month"),  # Invalid day (original error)
])
def test_parse_iso_datetime_invalid_time_components(invalid_dt_str: str, error_substring: str):
    """Test _parse_iso_datetime raises ValueError for invalid time components (hour/min/sec out of range)."""
    with pytest.raises(ValueError) as excinfo:
        parse_iso_datetime(invalid_dt_str)
    
    # Assert generic part of the message (always present)
    assert "Invalid ISO 8601 datetime format" in str(excinfo.value)
    assert invalid_dt_str in str(excinfo.value)
    
    # Assert specific error reason (unique to each invalid case)
    assert error_substring in str(excinfo.value)

def test_serialize_reminder_collection_invalid_structure():
    """Test serialize_reminder_collection raises TypeError for invalid ReminderCollection structure."""
    invalid_collection = {
        1: ReminderDataDict(
            clk_time=datetime.date(2026, 2, 4),
            bgn_time=None,
            duration=60,
            every=0,
            unit=TimeUnit.DAY,
            custom=DayType.WORKDAY,
            cycbgn_dtime=None,
            cycend_dtime=None
        )
    }

    with pytest.raises(TypeError) as excinfo:
        serialize_reminder_collection(invalid_collection)
    
    assert "Input is not a valid ReminderCollection (dict[int, ReminderDataDict])" in str(excinfo.value)

def test_deserialize_reminder_collection_json_decode_error():
    """Test deserialize_reminder_collection raises JSONDecodeError for invalid JSON."""
    invalid_json = "{invalid: json}"  # Malformed JSON
    with pytest.raises(json.JSONDecodeError) as excinfo:
        deserialize_reminder_collection(invalid_json)
    assert "Invalid JSON format" in str(excinfo.value)

def test_deserialize_reminder_collection_top_level_not_dict():
    """Test deserialize_reminder_collection raises TypeError if top-level is not a dict."""
    invalid_json = "[1, 2, 3]"  # List instead of dict
    with pytest.raises(TypeError) as excinfo:
        deserialize_reminder_collection(invalid_json)
    assert "Top-level JSON structure must be a dict" in str(excinfo.value)

def test_deserialize_reminder_collection_non_int_rid():
    """Test deserialize_reminder_collection raises ValueError for non-int reminder IDs."""
    invalid_json = '''
    {
        "invalid_id": {
            "clk_time": null,
            "bgn_time": null,
            "duration": 60,
            "every": 0,
            "unit": 2,
            "custom": 2,
            "cycbgn_dtime": null,
            "cycend_dtime": null
        }
    }
    '''
    with pytest.raises(ValueError) as excinfo:
        _ = deserialize_reminder_collection(invalid_json)
    assert "Reminder ID must be an integer (got 'invalid_id')" in str(excinfo.value)

def test_deserialize_reminder_collection_invalid_timeunit():
    """Test deserialize_reminder_collection raises ValueError for invalid TimeUnit."""
    invalid_json = '''
    {
        "1": {
            "clk_time": null,
            "bgn_time": null,
            "duration": 60,
            "every": 0,
            "unit": 999,
            "custom": 2,
            "cycbgn_dtime": null,
            "cycend_dtime": null
        }
    }
    '''
    with pytest.raises(ValueError) as excinfo:
        _ = deserialize_reminder_collection(invalid_json)
    assert "Invalid TimeUnit value: 999" in str(excinfo.value)

def test_deserialize_reminder_collection_invalid_daytype():
    """Test deserialize_reminder_collection raises ValueError for invalid DayType."""
    invalid_json = '''
    {
        "1": {
            "clk_time": null,
            "bgn_time": null,
            "duration": 60,
            "every": 0,
            "unit": 2,
            "custom": 999,
            "cycbgn_dtime": null,
            "cycend_dtime": null
        }
    }
    '''
    with pytest.raises(ValueError) as excinfo:
        _ = deserialize_reminder_collection(invalid_json)
    assert "Invalid DayType value: 999" in str(excinfo.value)

def test_deserialize_reminder_collection_final_validation_failure():
    """Test deserialize_reminder_collection raises ValueError for final collection validation failure."""
    # Valid JSON but invalid ReminderDataDict (negative duration)
    invalid_json = '''
    {
        "1": {
            "clk_time": null,
            "bgn_time": null,
            "duration": 60,
            "every": 0,
            "unit": 2,
            "custom": 2,
            "cycbgn_dtime": null,
            "cycend_dtime": null
        }
    }
    '''
    raw_json = json.loads(invalid_json)
    reminder_collection = {}
    for rid_str, reminder_json_raw in raw_json.items():
        rid = rid_str
        reminder_json = ReminderJsonDict(**reminder_json_raw)
        reminder_collection[rid] = _deserialize_single_reminder(reminder_json)

    with pytest.raises(ValueError) as excinfo:
        if not _is_valid_reminder_collection(reminder_collection):
            raise ValueError("Deserialized collection contains invalid reminder data")
    
    assert "Deserialized collection contains invalid reminder data" in str(excinfo.value)

def test_deserialize_reminder_collection_invalid_json_structure_missing_fields():
    """
    Test deserialize_reminder_collection raises KeyError for missing required fields in ReminderJsonDict
    (aligns with explicit required field validation in code)
    """
    # JSON missing required "duration" field (triggers KeyError in required field check)
    invalid_json = '''
    {
        "1": {
            "clk_time": null,
            "bgn_time": null,
            "every": 0,
            "unit": 2,
            "custom": 2,
            "cycbgn_dtime": null,
            "cycend_dtime": null
        }
    }
    '''

    # Catch the KeyError (actual error thrown by required field validation)
    with pytest.raises(KeyError) as excinfo:
        _ = deserialize_reminder_collection(invalid_json)

    # Assert the exact KeyError message from the code
    assert "Reminder 1 is missing required fields: duration" in str(excinfo.value)

def test_deserialize_reminder_collection_invalid_collection_final():
    """Test deserialize_reminder_collection raises ValueError for invalid final collection."""
    valid_json = '''
    {
        "1": {
            "clk_time": null,
            "bgn_time": null,
            "duration": 60,
            "every": 0,
            "unit": 2,
            "custom": 2,
            "cycbgn_dtime": null,
            "cycend_dtime": null
        }
    }
    '''

    valid_collection = deserialize_reminder_collection(valid_json)

    invalid_collection = valid_collection
    invalid_collection["not_int_key"] = invalid_collection[1]  # key是字符串，不是int

    with pytest.raises(ValueError) as excinfo:
        if not _is_valid_reminder_collection(invalid_collection):
            raise ValueError("Deserialized collection contains invalid reminder data")

    assert "Deserialized collection contains invalid reminder data" in str(excinfo.value)


