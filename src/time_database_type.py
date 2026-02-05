#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import datetime
from enum import IntEnum, auto
from typing import Literal, NamedTuple, TypedDict
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
