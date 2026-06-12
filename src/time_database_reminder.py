#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import json
import datetime
from typing import TypedDict, TypeAlias, TypeGuard
from typing import cast

from src.time_database_type import TimeUnit, DayType
from src.time_database_type import ReminderDataDict

# Type alias for reminder collection (business layer)
ReminderCollection: TypeAlias = dict[int, ReminderDataDict]

# -------------------------- JSON Layer TypedDicts --------------------------
class ReminderJsonDict(TypedDict):
    """JSON-serializable structure for a single reminder (JSON layer).

    Maps directly to ReminderDataDict but with JSON-native types:
    - datetime.time → ISO 8601 time string (e.g., "09:00:00")
    - datetime.datetime → ISO 8601 datetime string (e.g., "2026-02-04T09:00:00")
    - IntEnum (TimeUnit/DayType) → integer value
    """
    clk_time: str | None
    bgn_time: str | None
    duration: int
    every: int
    unit: int
    custom: int | list[int]
    cycbgn_dtime: str | None
    cycend_dtime: str | None

class ReminderCollectionJsonDict(TypedDict):
    """JSON-serializable structure for a reminder collection (JSON layer).

    Key: Integer ID of the reminder
    Value: ReminderJsonDict (JSON-native representation of a single reminder)
    """
    __root__: dict[int, ReminderJsonDict]  # Special key for dict-based TypedDict

# -------------------------- Helper Functions --------------------------
def _is_valid_reminder_data_dict(obj: object) -> TypeGuard[ReminderDataDict]:
    """Validate if an object is a valid ReminderDataDict.

    Args:
        obj: Object to validate

    Returns:
        True if obj is a valid ReminderDataDict, False otherwise
    """
    if not isinstance(obj, dict):
        return False

    # Validate required fields and their types
    required_fields: dict[str, tuple[type, ...]] = {
        "duration": (int,),
        "every": (int,),
        "unit": (TimeUnit,),
        "custom": (DayType, list),
    }
    for field, expected_types in required_fields.items():
        if field not in obj:
            return False
        if not isinstance(obj[field], expected_types):
            return False

    # Validate optional fields and their types
    optional_fields: dict[str, tuple[type, ...]] = {
        "clk_time": (datetime.time, type(None)),
        "bgn_time": (datetime.time, type(None)),
        "cycbgn_dtime": (datetime.datetime, type(None)),
        "cycend_dtime": (datetime.datetime, type(None)),
    }
    for field, expected_types in optional_fields.items():
        if field in obj and not isinstance(obj[field], expected_types):
            return False

    # Validate custom field constraints (list must contain only integers)
    if isinstance(obj["custom"], list) and not all(isinstance(x, int) for x in obj["custom"]):
        return False

    # Validate numeric field constraints
    if obj["duration"] < 0 or obj["every"] < 0:
        return False

    return True

def _is_valid_reminder_collection(obj: object) -> TypeGuard[ReminderCollection]:
    """Validate if an object is a valid ReminderCollection (dict[int, ReminderDataDict]).

    Args:
        obj: Object to validate

    Returns:
        True if obj is a valid ReminderCollection, False otherwise
    """
    if not isinstance(obj, dict):
        return False

    # Validate all keys are integers and values are valid ReminderDataDict
    for key, value in obj.items():
        if not isinstance(key, int):
            return False
        if not _is_valid_reminder_data_dict(value):
            return False

    return True

def parse_iso_time(time_str: str | None) -> datetime.time | None:
    """Parse an ISO 8601 time string to datetime.time.

    Args:
        time_str: ISO 8601 time string (e.g., "09:00:00") or None or empty string

    Returns:
        Parsed datetime.time object or None

    Raises:
        ValueError: If the input string is not a valid ISO 8601 time
    """
    if not time_str:
        return None
    try:
        return datetime.time.fromisoformat(time_str)
    except ValueError as e:
        raise ValueError(
            f"Invalid ISO 8601 time format: '{time_str}'. Expected format like 'HH:MM:SS'."
        ) from e

def parse_iso_datetime(datetime_str: str | None) -> datetime.datetime | None:
    """Parse an ISO 8601 datetime string to datetime.datetime.

    Args:
        datetime_str: ISO 8601 datetime string (e.g., "2026-02-04T09:00:00") or None or empty string

    Returns:
        Parsed datetime.datetime object or None

    Raises:
        ValueError: If the input string is not a valid ISO 8601 datetime
    """
    if not datetime_str:
        return None

    try:
        # Step 1: Parse ISO string (basic validation)
        dt = datetime.datetime.fromisoformat(datetime_str)

        # Step 2: Strict validation of day/month (fixes Python <3.11 leniency)
        _ = datetime.datetime(dt.year, dt.month, dt.day)
    
        return dt

    except ValueError as e:
        # Include the original error reason in the re-thrown message
        raise ValueError((
            f"Invalid ISO 8601 datetime format: '{datetime_str}'. "
            f"Expected format like 'YYYY-MM-DDTHH:MM:SS' (valid date/time only). "
            f"Error: {str(e)}"
        )) from e

def _serialize_single_reminder(reminder: ReminderDataDict) -> ReminderJsonDict:
    """Serialize a single ReminderDataDict to ReminderJsonDict.

    Converts non-JSON-native types to JSON-compatible types:
    - datetime.time → ISO 8601 string
    - datetime.datetime → ISO 8601 string
    - IntEnum → integer value

    Args:
        reminder: Valid ReminderDataDict to serialize

    Returns:
        JSON-native ReminderJsonDict
    """
    return ReminderJsonDict(
        clk_time=reminder["clk_time"].isoformat() if reminder["clk_time"] is not None else None,
        bgn_time=reminder["bgn_time"].isoformat() if reminder["bgn_time"] is not None else None,
        duration=reminder["duration"],
        every=reminder["every"],
        unit=int(reminder["unit"]),
        custom=int(reminder["custom"]) if isinstance(reminder["custom"], DayType) else reminder["custom"],
        cycbgn_dtime=reminder["cycbgn_dtime"].isoformat() if reminder["cycbgn_dtime"] is not None else None,
        cycend_dtime=reminder["cycend_dtime"].isoformat() if reminder["cycend_dtime"] is not None else None,
    )

def _deserialize_single_reminder(reminder_json: ReminderJsonDict) -> ReminderDataDict:
    """Deserialize a single ReminderJsonDict to ReminderDataDict.

    Converts JSON-native types back to business layer types:
    - ISO 8601 string → datetime.time/datetime.datetime
    - integer → IntEnum (TimeUnit/DayType)

    Args:
        reminder_json: Valid ReminderJsonDict to deserialize

    Returns:
        Business-layer ReminderDataDict

    Raises:
        ValueError: If enum values are invalid or numeric constraints are violated
    """
    # Validate numeric constraints
    if reminder_json["duration"] < 0:
        raise ValueError(f"Duration cannot be negative: {reminder_json['duration']}")
    if reminder_json["every"] < 0:
        raise ValueError(f"Recurrence interval must not be less than 0: {reminder_json['every']}")

    # Convert enum values
    try:
        unit = TimeUnit(reminder_json["unit"])
    except ValueError as e:
        raise ValueError(f"Invalid TimeUnit value: {reminder_json['unit']}. Valid values: {[e.value for e in TimeUnit]}") from e

    # Convert custom field
    custom: DayType | list[int]
    if isinstance(reminder_json["custom"], int):
        try:
            custom = DayType(reminder_json["custom"])
        except ValueError as e:
            raise ValueError(f"Invalid DayType value: {reminder_json['custom']}. Valid values: {[e.value for e in DayType]}") from e
    else:
        custom = reminder_json["custom"]
        if not all(isinstance(x, int) for x in custom):
            raise ValueError(f"Custom list must contain only integers: {custom}")

    return ReminderDataDict(
        clk_time=parse_iso_time(reminder_json["clk_time"]),
        bgn_time=parse_iso_time(reminder_json["bgn_time"]),
        duration=reminder_json["duration"],
        every=reminder_json["every"],
        unit=unit,
        custom=custom,
        cycbgn_dtime=parse_iso_datetime(reminder_json["cycbgn_dtime"]),
        cycend_dtime=parse_iso_datetime(reminder_json["cycend_dtime"]),
    )

# -------------------------- Main Serialization/Deserialization Functions --------------------------
def serialize_reminder_collection(
    reminder_collection: ReminderCollection,
    indent: int | None = 2,
    ensure_ascii: bool = False
) -> str:
    """Serialize a reminder collection to a JSON string.

    Converts a dict[int, ReminderDataDict] to a JSON string with proper
    handling of non-JSON-native types (datetime, enums).

    Args:
        reminder_collection: Valid reminder collection (dict[int, ReminderDataDict])
        indent: Number of spaces for JSON indentation (None for compact output)
        ensure_ascii: If True, escape non-ASCII characters (False for UTF-8 support)

    Returns:
        JSON string representing the reminder collection

    Raises:
        TypeError: If input is not a valid ReminderCollection
        ValueError: If reminder data contains invalid values (e.g., negative duration)
    """
    # Validate input collection
    if not _is_valid_reminder_collection(reminder_collection):
        raise TypeError("Input is not a valid ReminderCollection (dict[int, ReminderDataDict])")

    # Serialize each reminder in the collection
    collection_json: ReminderCollectionJsonDict = {
        "__root__": {
            rid: _serialize_single_reminder(reminder)
            for rid, reminder in reminder_collection.items()
        }
    }

    # Convert to JSON string
    # try:
    return json.dumps(
        collection_json["__root__"],
        ensure_ascii=ensure_ascii,
        indent=indent
    )
    # except TypeError as e:
        # raise TypeError(f"Failed to serialize reminder collection to JSON: {str(e)}") from e

def deserialize_reminder_collection(json_str: str) -> ReminderCollection:
    """Deserialize a JSON string to a reminder collection.

    Converts a JSON string back to dict[int, ReminderDataDict] with proper
    type conversion and validation.

    Args:
        json_str: Valid JSON string of a reminder collection

    Returns:
        Business-layer reminder collection (dict[int, ReminderDataDict])

    Raises:
        json.JSONDecodeError: If input string is not valid JSON
        KeyError: If required fields are missing in the JSON structure
        ValueError: If enum values are invalid or numeric constraints are violated
        TypeError: If JSON structure does not match ReminderCollectionJsonDict
    """
    # Parse JSON string to raw dict
    try:
        raw_json = cast(object, json.loads(json_str))
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            msg=f"Invalid JSON format: {e.msg}",
            doc=e.doc,
            pos=e.pos
        ) from e

    # Validate top-level structure is a dict with integer keys
    if not isinstance(raw_json, dict):
        raise TypeError(f"Top-level JSON structure must be a dict, got {type(raw_json).__name__}")

    reminder_collection: ReminderCollection = {}
    for eid_str, reminder_json_raw in raw_json.items():
        # Convert string keys to integers (JSON only supports string keys)
        try:
            eid = int(eid_str)
        except ValueError as e:
            raise ValueError(f"Reminder ID must be an integer (got '{eid_str}'): {str(e)}") from e

        # Validate ALL ReminderJsonDict fields exist (enforce total=True)
        required_json_fields = [
            "clk_time", "bgn_time", "duration", "every",
            "unit", "custom", "cycbgn_dtime", "cycend_dtime"
        ]
        missing_fields = [f for f in required_json_fields if f not in reminder_json_raw]
        if missing_fields:
            raise KeyError(f"Reminder {eid} is missing required fields: {', '.join(missing_fields)}")

        # Validate single reminder JSON structure
        try:
            reminder_json = ReminderJsonDict(**reminder_json_raw)
        except TypeError as e:
            raise TypeError((
                f"Reminder {eid} has invalid JSON structure: {str(e)}. "
                "Missing or extra fields in ReminderJsonDict."
            )) from e

        # Deserialize single reminder and add to collection
        reminder_collection[eid] = _deserialize_single_reminder(reminder_json)

    # Final validation of the collection
    if not _is_valid_reminder_collection(reminder_collection):
        raise ValueError("Deserialized collection contains invalid reminder data")

    return reminder_collection
