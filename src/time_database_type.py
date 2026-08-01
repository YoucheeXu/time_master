#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import re
import datetime
from enum import IntEnum, auto
from typing import NamedTuple, TypedDict
from typing import TypeVar
from dataclasses import dataclass, field
import warnings

from pyutilities_simple.logit import pv, po, pe

from src.action_sys import ActTyp


class TimeUnit(IntEnum):
    HOUR = auto()
    DAY = auto()
    WEEK = auto()
    MONTH = auto()
    SEASON = auto()
    YEAR = auto()

class DayType(IntEnum):
    EVERYDAY = auto()
    WORKDAY = auto()
    WEEKEND = auto()
    HOLIDAY = auto()

DAYTYPE_NAMES = {dt.name for dt in DayType}

T = TypeVar('T', bound=IntEnum)
def str_to_intenum(enum_cls: type[T], name_str: str) -> T:
    """
    Convert an exact-matching string to the corresponding IntEnum instance (name-based).
    Returns None if the string is not a valid IntEnum name (avoids KeyError).

    Args:
        enum_cls: Target IntEnum class (e.g., StatusEnum, ActTyp)
        name_str: String matching the IntEnum's NAME (e.g., "ONGOING", "NOACTION")

    Returns:
        Corresponding IntEnum instance, or None if invalid name
    """
    # __members__ = {name: IntEnumInstance, ...} → direct name lookup
    normalized_str = name_str.strip().upper()
    return enum_cls.__members__[normalized_str]


class GeoSqlTuple(NamedTuple):
    """_summary_

    Attributes:
        latitude (): latitude
        longitude (): longitude
    """
    latitude: float
    longitude: float


class PlanSqlTuple(NamedTuple):
    """ _summary_

    Attributes:
        pid (int): _description_
        name (): _description_
        note (): _description_
        tags (): _description_
        iid (): id of icon
        fid (): _description_
        reminders (): _description_
        action ( ): _description_
        status (): _description_
        location (): _description_
        sums (): _description_, in minute
    """
    pid: int
    name: str
    note: str
    tags: str
    iid: str
    fid: int
    reminders: str
    action: int
    status: int
    location: str
    sums: int


class StatusEnum(IntEnum):
    DELETED = -1
    ONGOING = 0
    COMPLETED = 1       # or archived


class LocTuple(NamedTuple):
    """_summary_

    Attributes:
        lat (): latitude
        lng (): longitude
        name (): _description_
        city (): _description_
        address (str | str): _description_
        altitude (float): _description_, default to 0
    """
    lat: float
    lng: float
    name: str = ""
    city: str = ""
    address: str | None = None
    altitude: float = 0.0


class IconTuple(NamedTuple):
    """_summary_

    Attributes:
        grpidx (): index of group
        eleidx (): index of element
    """
    grpidx: int
    eleidx: int


class ReminderDataDict(TypedDict):
    """ _summary_

    Attributes:
        clk_time ( ): _description_
        bgn_time ( ): _description_
        duration ( ): _description_, in minute
        every (int): _description_
        unit (TimeUnit): _description_
        custom ( ): _description_
        cycbgn_dtime ( ): _description_
        cycend_dtime ( ): _description_
    """
    clk_time: datetime.time | None
    bgn_time: datetime.time | None
    duration: int
    every: int
    unit: TimeUnit
    custom: DayType | list[int]
    cycbgn_dtime: datetime.datetime | None
    cycend_dtime: datetime.datetime | None

class ReminderDataOptionalDict(TypedDict, total=False):
    clk_time: datetime.time | None
    bgn_time: datetime.time | None
    duration: int
    every: int
    unit: TimeUnit
    custom: DayType | list[int]
    cycbgn_dtime: datetime.datetime | None
    cycend_dtime: datetime.datetime | None

ReminderAttr = list(ReminderDataDict.__annotations__.keys())

def default_reminder_data() -> ReminderDataDict:
    return {
        "clk_time": None,
        "bgn_time": None,
        "duration": 0,
        "every": 0,
        "unit": TimeUnit.WEEK,
        "custom": DayType.EVERYDAY,
        "cycbgn_dtime": None,
        "cycend_dtime": None
    }

# Weekday number to name mapping (1=Monday, 7=Sunday - conforms to common conventions)
WEEKDAY_MAPPING = {
    1: "Monday",
    2: "Tuesday",
    3: "Wednesday",
    4: "Thursday",
    5: "Friday",
    6: "Saturday",
    7: "Sunday"
}
# Reverse mapping for parsing (name → number)
WEEKDAY_NAME_TO_NUM = {v.lower(): k for k, v in WEEKDAY_MAPPING.items()}

# TODO: very limit
def reminder2str(reminder: ReminderDataDict) -> tuple[str, str]:
    """ Convert ReminderDataDict to a human-readable natural language description string

    Args:
        reminder: Dictionary conforming to ReminderDict type

    Returns:
        Natural language clock string (e.g., "Workday 21:00", "Monday of every 4 weeks 21:00")
        Natural language schedule string (e.g., "Workday 15m", "Monday of every 4 weeks 15m")

    Raises:
        ValueError: Raised when field values are invalid (e.g., every < 1, weekday numbers outside 1-7)
        TypeError: Raised when custom field has unsupported type (not str/List[int])
    """
    # 1. Extract and validate base fields
    clk_time = reminder["clk_time"]

    if clk_time is None:
        time_text = ""
    else:
        # 3. Process time text (format as HH:MM, e.g., 21:00)
        time_text = clk_time.strftime("%H:%M")

    duration = reminder["duration"]
    every = reminder["every"]
    if every < 0:
        raise ValueError(f"Value of 'every' must be >= 0, current value: {every}")
    elif every == 0:
        return time_text, f"{duration}m"

    unit = reminder["unit"]
    custom = reminder["custom"]

    # 2. Process frequency text (optimize singular/plural: no 's' for every=1, add 's' for every>1)
    unit_text = unit.name.lower()
    if every == 1:
        frequency_text = f"Every {unit_text}"
    else:
        frequency_text = f"Every {every} {unit_text}s"

    # 4. Process custom field by scenario to generate core description
    if unit == TimeUnit.HOUR:
        clk_str = f"{frequency_text} {time_text}" if time_text else ""
        schedule_str = f"{frequency_text} {duration}m"
    else:
        if isinstance(custom, DayType):
            # Scenario 1: custom is DayType (ED/WD/HD)
            custom_text = custom.name.capitalize()
            # Simplify description (omit frequency when every=1, e.g., "Work day 21:00")
            if every == 1:
                clk_str = f"{custom_text} {time_text}" if time_text else ""
                schedule_str = f"{custom_text} {duration}m"
            else:
                clk_str = f"{custom_text} of {frequency_text} {time_text}" if time_text else ""
                schedule_str = f"{custom_text} of {frequency_text} {duration}m"

        else:
            # Scenario 2: custom is list of weekday numbers (e.g., [1,3])
            if unit == TimeUnit.WEEK:
                # Validate number validity in list
                invalid_days = [day for day in custom if day not in WEEKDAY_MAPPING]
                if invalid_days:
                    raise ValueError(f"Weekday numbers must be between 1-7, invalid values: {invalid_days}")
                # Convert to weekday names (use comma separator for multiple days, e.g., "Monday, Wednesday")
                custom_names = [WEEKDAY_MAPPING[day] for day in custom]
            custom_names = [str(num) for num in custom]
            custom_text = ", ".join(custom_names)
            if custom_text:
                # Combine description (e.g., "Monday of every 4 weeks 21:00")
                clk_str = f"{custom_text} of {frequency_text} {time_text}" if time_text else ""
                schedule_str = f"{custom_text} of {frequency_text} {duration}m"
            else:
                clk_str = f"{frequency_text} {time_text}" if time_text else ""
                schedule_str = f"{frequency_text} {duration}m"

    return clk_str, schedule_str

def  _parse_frequency(text: str):
    """ Parse frequency text (e.g., "every 4 weeks") into (every, unit).

    Args:
        text: Frequency substring (e.g., "every 4 weeks", "every day")

    Returns:
        Tuple of (every: int, unit: TimeUnit)

    Raises:
        ValueError: If unit is unrecognized or every is negative
    """
    # Regex to match: "every [number] [unit]" or "every [unit]" (implies every=1)
    freq_pattern = re.compile(r"every\s+(?:(\d+)\s+)?(\w+)", re.IGNORECASE)
    match = freq_pattern.search(text.lower())

    if not match:
        s = text.upper()
        if s in DAYTYPE_NAMES:
            return 1, TimeUnit.DAY
        else:
            return 0, TimeUnit.DAY

    every_str, unit_str = match.groups()
    every = int(every_str) if every_str else 1

    # Validate every (matches reminder2str's every ≥0 rule)
    if every < 0:
        raise ValueError(f"Value of 'every' must be >= 0, current value: {every}")

    # Map unit text to enum (handle singular/plural: weeks → week, days → day)
    unit_raw = unit_str.rstrip("s").upper()
    # if unit_str_upper not in UNIT_TEXT_TO_ENUM:
    #     raise ValueError(f"Unrecognized unit '{unit_str}' (allowed: minute/hour/day/week)")
    unit = TimeUnit[unit_raw]

    return every, unit

def _parse_custom(custom: str, every: int, unit: TimeUnit) -> DayType | list[int]:
    """Parse custom text (day type/weekdays) into DayType or list of weekday numbers.

    Args:
        text: Custom substring (e.g., "workday", "Monday", "Monday, Wednesday")
        every: Parsed every value (from _parse_frequency)
        unit: Parsed unit (from _parse_frequency)

    Returns:
        DayType (for workday/weekend) or List[int] (weekday numbers 1-7)

    Raises:
        ValueError: If weekday numbers are invalid (not 1-7) or custom text unrecognized
        TypeError: If custom type is not supported
    """
    if every >= 1:
        custom_upper = custom.upper().strip()
        # Case 1: Custom is DayType
        if unit == TimeUnit.DAY:
            custom_raw = custom_upper.replace(" ", "")
            return DayType[custom_raw]

        # Case 2: Custom is weekday names (e.g., "Monday", "Monday, Wednesday")
        if unit == TimeUnit.WEEK:
            # Split comma-separated weekdays (e.g., "Monday, Wednesday" → ["monday", "wednesday"])
            weekday_names = [name.strip() for name in custom_upper.split(",")]
            if len(weekday_names) == 1:
                return []

            weekday_nums: list[int] = []

            for name in weekday_names:
                if name not in WEEKDAY_NAME_TO_NUM:
                    raise ValueError(f"Unrecognized weekday '{name}' (allowed: {list(WEEKDAY_NAME_TO_NUM.keys())})")
                num = WEEKDAY_NAME_TO_NUM[name]
                # Validate weekday number (matches reminder2str's 1-7 rule)
                if num not in WEEKDAY_MAPPING:
                    raise ValueError(f"Weekday numbers must be between 1-7, invalid value: {num}")
                weekday_nums.append(num)

            return weekday_nums
        else:
            return [int(x) for x in custom_upper.split(',')]
    else:
        return []

def _parse_duration(text: str) -> int:
    """Parse duration string (Xm) into integer minutes.

    Args:
        text: Duration substring (e.g., "15m", "30m")

    Returns:
        Integer duration in minutes

    Raises:
        ValueError: If duration format is invalid (not Xm) or negative
    """
    if text:
        duration_pattern = re.compile(r"(\d+)m", re.IGNORECASE)
        match = duration_pattern.search(text.lower())

        if not match:
            raise ValueError(f"Invalid duration format '{text}' (expected Xm, e.g., 15m)")

        duration = int(match.group(1))
        if duration < 0:
            raise ValueError(f"Duration must be non-negative, current value: {duration}")
    else:
        duration = 0

    return duration

def str2reminder(clock_str: str, schedule_str: str) :
    """Parse natural language clock/plan messages into ReminderDataDict (reverse of reminder2str).

    Exact reverse of reminder2str: handles all formats generated by the original function,
    including simple (e.g., "workday 21:00") and complex (e.g., "Monday of every 4 weeks 21:00")
    messages, with validation matching reminder2str's error rules.

    Args:
        clock_str: Natural language clock string (output of reminder2str's first return value).
            Examples:
            - Simple: "workday 21:00", "weekend 09:15"
            - Complex: "Monday of every 4 weeks 21:00", "Tuesday, Wednesday of every 2 days 14:30"
            - Edge case (every=0): "21:00"
        schedule_str: Natural language schedule string (output of reminder2str's second return value).
            Examples:
            - Simple: "workday 15m", "weekend 30m"
            - Complex: "Monday of every 4 weeks 15m", "Tuesday of every 1 hour 5m"
            - Edge case (every=0): "15m"

    Returns:
        ReminderDataDict with all required fields:
            - clk_time: datetime object (time part from clock_str, None if empty)
            - bgn_time: None (default, can be extended to match your schema)
            - duration: int (minutes parsed from schedule_str)
            - every: int (frequency count, 0 for edge case, ≥1 otherwise)
            - unit: TimeUnit
            - custom: DayType or list[int] (weekday numbers 1-7, month numbers 1-31, ...)
            - cycbgn_dtime: None (default, can be extended)
            - cycend_dtime: None (default, can be extended)

    Raises:
        ValueError:
            - Invalid time format (not HH:MM) in clock_str
            - Invalid duration format (not Xm) in schedule_str
            - Negative every/duration values (violates reminder2str's validation)
            - Invalid weekday numbers (not 1-7) or unrecognized units
        TypeError:
            - Unsupported custom type (not workday/weekend/weekday names)
            - Non-string inputs for clock_msg/plan_msg

    Examples:
        >>> # Simple case (workday, every=1)
        >>> clock_msg = "workday 21:00"
        >>> plan_msg = "workday 15m"
        >>> parse_reminder_message(clock_msg, plan_msg)
        {
            "clk_time": datetime.time(13, 21),
            "bgn_time": None,
            "duration": 15,
            "every": 1,
            "unit": TimeUnit.DAY,
            "custom": DayType.WORKDAY,
            "cycbgn_dtime": None,
            "cycend_dtime": None
        }

        >>> # Complex case (weekday frequency)
        >>> clock_str = "Monday of every 4 weeks 21:00"
        >>> schedule_str = "Monday of every 4 weeks 15m"
        >>> str2reminder(clock_str, schedule_str)
        {
            "clk_time": datetime.time(13, 21),
            "bgn_time": None,
            "duration": 15,
            "every": 4,
            "unit": TimeUnit.WEEK,
            "custom": [1],
            "cycbgn_dtime": None,
            "cycend_dtime": None
        }

        >>> # Edge case (every=0)
        >>> clock_str = "21:00"
        >>> schedule_str = "15m"
        >>> str2reminder(clock_str, schedule_str)
        {
            "clk_time": datetime.time(13, 21),
            "bgn_time": None,
            "duration": 15,
            "every": 0,
            "unit": TimeUnit.MINUTE,  # Default for every=0
            "custom": DayType.WORKDAY, # Default for every=0
            "cycbgn_dtime": None,
            "cycend_dtime": None
        }
    """
    # ------------------------------
    # Step 1: Input Validation (Type Check)
    # ------------------------------
    if not isinstance(clock_str, str) or not isinstance(schedule_str, str):  # pyright: ignore[reportUnnecessaryIsInstance]
        raise TypeError("clock_msg and plan_msg must be strings")  # pyright: ignore[reportUnreachable]
    clock_str_clean = clock_str.strip()
    schedule_str_clean = schedule_str.strip()

    # ------------------------------
    # Step 2: Handle Edge Case (every=0)
    # ------------------------------
    # Check if messages are just time/duration (no frequency/custom)
    # if not any(word in clock_str_clean.lower() for word in ["workday", "weekend", "every", "monday", "tuesday"]):
    if len(clock_str_clean.split()) == 1 or len(schedule_str_clean.split()) == 1:
        every = 0
        unit = TimeUnit.HOUR  # Default for every=0
        custom = DayType.WORKDAY  # Default for every=0
        clk_time = str2time(clock_str_clean)
        duration = _parse_duration(schedule_str_clean)
    else:
        # ------------------------------
        # Step 3: Parse Common Components (Shared by clock/schedule string)
        # ------------------------------
        # Extract frequency (every + unit) from either message (they are symmetric)
        every, unit = _parse_frequency(clock_str_clean if clock_str_clean else schedule_str_clean)

        # Extract custom text (day type/weekdays) - remove frequency/time/duration parts
        # Regex to remove "of every X unit" and time/duration
        custom_pattern = re.compile(r"\s* of every .+?\s* | \d{1,2}:\d{1,2} | \d+m", re.IGNORECASE | re.DOTALL | re.VERBOSE)
        custom_text_clock = custom_pattern.sub("", clock_str_clean).strip()
        custom_text_schedule = custom_pattern.sub("", schedule_str_clean).strip()

        # Custom text should be identical in clock/schedule string (validate symmetry)
        if custom_text_clock != custom_text_schedule:
            warnings.warn(f"Custom text mismatch: clock='{custom_text_clock}', schedule='{custom_text_schedule}' - using clock text")
        custom_text = custom_text_clock or custom_text_schedule

        # Parse custom (DayType or weekday numbers)
        custom = _parse_custom(custom_text, every, unit)

        # ------------------------------
        # Step 4: Parse Clock-Specific (Time) and Schedule-Specific (Duration)
        # ------------------------------
        result_serach = re.search(r"\d{1,2}:\d{1,2}", clock_str_clean)
        clk_time = str2time(result_serach.group() if result_serach else "")
        duration = _parse_duration(schedule_str_clean)

    # ------------------------------
    # Step 5: Construct ReminderDataDict
    # ------------------------------
    reminder_data: ReminderDataDict = {
        "clk_time": clk_time,
        "bgn_time": clk_time,  # Default
        "duration": duration,
        "every": every,
        "unit": unit,
        "custom": custom,
        "cycbgn_dtime": None,  # Default
        "cycend_dtime": None   # Default
    }

    # Final validation (matches reminder2str's rules)
    if reminder_data["every"] < 0:
        raise ValueError(f"Value of 'every' must be >= 0, current value: {reminder_data['every']}")
    if isinstance(reminder_data["custom"], list):
        invalid_days = [day for day in reminder_data["custom"] if day not in WEEKDAY_MAPPING]
        if invalid_days:
            raise ValueError(f"Weekday numbers must be between 1-7, invalid values: {invalid_days}")

    return reminder_data

def time2str(time: datetime.time | None):
    """ convert datetime.time to string "%H:%M"

    Args:
        time (datetime.time | None): _description_

    Returns:
        _type_: _description_
    """
    if time is None:
        return ""
    return datetime.time.strftime(time, "%H:%M")


def str2time(timestr: str):
    """ convert string "%H:%M" to datetime.time

    Args:
        timestr (str): _description_

    Returns:
        _type_: _description_
    """
    if timestr:
        return datetime.datetime.strptime(timestr, "%H:%M").time()
    else:
        return None

def date2str(date: datetime.date | None):
    if date is None:
        return ""
    return date.strftime("%Y-%m-%d %A")

class PlanDataDict(TypedDict):
    """ _summary_

    Attributes:
        name (): _description_
        note (): _description_
        tags (): _description_
        iid (): id of icon
        fid (): _description_
        reminders ( ): _description_
        action ( ): _description_
        status (): _description_
        location (): _description_
        sums (): _description_, in minute
    """
    name: str
    note: str
    tags: list[str]
    iid: IconTuple | None
    fid: int
    reminders: dict[int, ReminderDataDict]
    action: ActTyp
    status: StatusEnum
    location: LocTuple | None
    sums: int

class PlanDataOptionalDict(TypedDict, total=False):
    name: str
    note: str
    tags: list[str]
    iid: IconTuple | None
    fid: int
    reminders: dict[int, ReminderDataDict]
    action: ActTyp
    status: StatusEnum
    location: LocTuple | None
    sums: int

PlanAttr = list(PlanDataDict.__annotations__.keys())

def default_plan_data() -> PlanDataDict:
    """ Independent factory function to return default PlanDataDict values.
    Replaces the inline lambda for better maintainability and testability.

    Returns:
        PlanDataDict: Default data structure for Plan.data field
    """
    return {
        "name": "",
        "note": "",
        "tags": [],
        "iid": None,
        "fid": -1,
        "reminders": {},
        "action": ActTyp.NOACTION,
        "status": StatusEnum.ONGOING,
        "location": None,
        "sums": 0
    }

@dataclass
class Plan:
    """ Data class representing a plan with core data and child plans.

    Attributes:
        data (PlanDataDict): Core plan metadata (name, status, reminders, etc.)
        children (dict[int, Plan]): Nested child plans (key = child ID, value = child plan data)
    """
    data: PlanDataDict = field(default_factory=default_plan_data)
    children: dict[int, "Plan"] = field(default_factory=dict)


class RecordSqlTuple(NamedTuple):
    """_summary_

    Attributes:
        rid (int): _description_
        pid (int): _description_
        name (str): _description_
        bgn_dtime (): _description_
        duration (): _description_, in minute
    """
    rid: int
    pid: int
    name: str
    bgn_dtime: float
    duration: int


class RecordDataDict(TypedDict):
    """_summary_

    Attributes:
        pid (int): _description_
        name (str): _description_
        bgn_dtime (): _description_
        duration (): _description_, in minute
    """
    pid: int
    name: str
    bgn_dtime: datetime.datetime | None
    duration: int

RecordAttr = list(RecordDataDict.__annotations__.keys())

def default_record_data() ->RecordDataDict:
    return {
        "pid": -1,
        "name": "",
        "bgn_dtime": None,
        "duration": 0,
    }


def generate_sqlite_fields(tuple_class: type[NamedTuple],
        exclude_fields: list[str] | None = None):
    """ Generate safe field names, placeholder string, and field string for SQL.

    Returns:
        tuple: (filtered_fields list, field_string "name, note...", placeholder_string "?, ?...")
    """
    # all fields
    all_fields = list(tuple_class._fields)
    # Validate excluded fields (prevent typos)
    if exclude_fields is not None:
        invalid_fields = [f for f in exclude_fields if f not in all_fields]
        if invalid_fields:
            raise ValueError(f"Invalid excluded fields: {invalid_fields}")

        # Filter fields (remove excluded ones)
        filtered_fields = [f for f in all_fields if f not in exclude_fields]
    else:

        filtered_fields = all_fields

    # Generate safe strings (field names = static, no injection risk)
    field_string = ", ".join(filtered_fields)  # e.g., "name, note, tags..."
    placeholder_string = ", ".join(["?"] * len(filtered_fields))  # e.g., "?, ?, ?..."

    return filtered_fields, field_string, placeholder_string
