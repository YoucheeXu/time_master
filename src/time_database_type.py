#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import datetime
from enum import IntEnum, auto
from typing import Literal, NamedTuple, TypedDict
from typing import TypeVar
from dataclasses import dataclass, field

from src.action_sys import ActTyp


# HR: hour, DY: day, WK: Week, MH: Month, SZ: season, YR: year
# VALID_TIMEUNIT = ["HR", "DY", "WK", "MH", "SZ", "YR"]
# TimeUnit = Literal["HR", "DY", "WK", "MH", "SZ", "YR"]
# TimeUnit = Literal[*VALID_TIMEUNIT]
class TimeUnit(IntEnum):
    HOUR = auto()
    DAY = auto()
    WEEK = auto()
    MONTH = auto()
    SEASON = auto()
    YEAR = auto()

# ED: Every day, WD: Work day, HD: Holiday day
# VALID_DAYTYPE = ["ED", "WD", "HD"]
# DayType = Literal["ED", "WD", "HD"]
# DayType = Literal[*VALID_DAYTYPE]
class DayType(IntEnum):
    EVERYDAY = auto()
    WORKDAY = auto()
    WEEKEND = auto()
    HOLIDAY = auto()

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

ReminderAttr = list(ReminderDataDict.__annotations__.keys())
ReminderAttrType = Literal["clk_time", "bgn_time", "duration", "every", \
    "unit", "custom", "cycbgn_dtime", "cycend_dtime"]
ReminderValType = datetime.time | int | TimeUnit  | DayType | list[int] \
    | datetime.datetime | None

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

# TODO: very limit
def reminder2clkstr(reminder: ReminderDataDict) -> str:
    """ Convert ReminderDataDict to a human-readable natural language description string

    Args:
        reminder: Dictionary conforming to ReminderDict type

    Returns:
        Natural language description string (e.g., "Work day 21:00", "Monday of every 4 weeks 21:00")

    Raises:
        ValueError: Raised when field values are invalid (e.g., every < 1, weekday numbers outside 1-7)
        TypeError: Raised when custom field has unsupported type (not str/List[int])
    """
    # 1. Extract and validate base fields
    clk_time = reminder["clk_time"]

    if clk_time is None:
        # raise ValueError("Value of 'clk_time' is None")
        return ""

    # 3. Process time text (format as HH:MM, e.g., 21:00)
    time_text = clk_time.strftime("%H:%M")

    every = reminder["every"]
    if every < 0:
        raise ValueError(f"Value of 'every' must be >= 0, current value: {every}")
    elif every == 0:
        return time_text
    unit = reminder["unit"]
    custom = reminder["custom"]

    # 2. Process frequency text (optimize singular/plural: no 's' for every=1, add 's' for every>1)
    unit_text = unit.name.lower()
    if every == 1:
        frequency_text = f"every {unit_text}"
    else:
        frequency_text = f"every {every} {unit_text}s"

    # 4. Process custom field by scenario to generate core description
    if isinstance(custom, DayType):
        # Scenario 1: custom is DayType (ED/WD/HD)
        custom_text = custom.name.lower()
        # Simplify description (omit frequency when every=1, e.g., "Work day 21:00")
        if every == 1:
            description = f"{custom_text} {time_text}"
        else:
            description = f"{custom_text} of {frequency_text} {time_text}"

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
        # Combine description (e.g., "Monday of every 4 weeks 21:00")
        description = f"{custom_text} of {frequency_text} {time_text}"

    return description


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

PlanAttr = list(PlanDataDict.__annotations__.keys())
PlanAttrType = Literal["name", "note", "tags", "iid", "fid", \
    "reminders", "action", "status", "location", "sums"]
PlanValType = str | list[str] | IconTuple \
    | int | ActTyp | StatusEnum | LocTuple| None


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
        children (dict[int, PlanDataDict]): Nested child plans (key = child ID, value = child plan data)
    """
    data: PlanDataDict = field(default_factory=default_plan_data)
    children: dict[int, PlanDataDict] = field(default_factory=dict)


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
