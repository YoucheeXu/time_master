#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import datetime
from enum import IntEnum
from typing import Literal, NamedTuple, TypedDict
from dataclasses import dataclass, field

from src.action_sys import ActTyp


# HR: hour, DY: day, WK: Week, MH: Month, SZ: season, YR: year
VALID_TIMEUNIT = ["HR", "DY", "WK", "MH", "SZ", "YR"]
TimeUnit = Literal["HR", "DY", "WK", "MH", "SZ", "YR"]
# TimeUnit = Literal[*VALID_TIMEUNIT]

# ED: Every day, WD: Work day, HD: Holiday day
VALID_DAYTYPE = ["ED", "WD", "HD"]
DayType = Literal["ED", "WD", "HD"]
# DayType = Literal[*VALID_DAYTYPE]


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
        action ( ): _description_
        status (): _description_
        locstr (): _description_
    """
    pid: int
    name: str
    note: str
    tags: str
    iid: str
    fid: int
    action: int
    status: int
    locstr: str


class ReminderSqlTuple(NamedTuple):
    """ _summary_

    Attributes:
        cid (int): _description_
        pid (int): _description_
        clk_timestr ( ): reminder time
        bgn_timestr ( ): _description_
        end_timestr ( ): _description_        
        every (int): _description_
        unit (str): _description_
        customstr ( ): _description_
        cycbgn_timestamp ( ): _description_, cycle
        cycend_timestamp ( ): _description_, end cycle datetime
    """
    cid: int
    pid: int
    clk_timestr: str
    bgn_timestr: str
    end_timestr: str
    every: int
    unit: str
    customstr: str
    cycbgn_timestamp: float
    cycend_timestamp: float


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
        end_time ( ): _description_
        every (int): _description_
        unit (TimeUnit): _description_
        custom ( ): _description_
        cycbgn_dtime ( ): _description_
        cycend_dtime ( ): _description_
    """
    clk_time: datetime.time | None
    bgn_time: datetime.time | None
    end_time: datetime.time | None
    every: int
    unit: TimeUnit
    custom: DayType | list[int]
    cycbgn_dtime: datetime.datetime | None
    cycend_dtime: datetime.datetime | None

ReminderAttrType = Literal["clk_time", "bgn_time", "end_time", "every", \
    "unit", "custom", "cycbgn_dtime", "cycend_dtime"]
ReminderValType = datetime.time | int | TimeUnit  | DayType | list[int] \
    | datetime.datetime | None

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

PlanAttrType = Literal["name", "note", "tags", "iid", "fid", \
    "reminders", "action", "status", "location"]
PlanValType = str | list[str] | IconTuple \
    | int | ActTyp | StatusEnum | LocTuple| None

@dataclass
class Plan:
    """_summary_

    Attributes:
        data (): _description_
        children (): _description_
    """
    # TypedDict("ItemDict",{"id": 0, "name": "", "rid": 0, "clock": "", "schedule": "", "sums": 0, "father": -1})
    data: PlanDataDict = field(default_factory=PlanDataDict)
    children: dict[int, PlanDataDict] = field(default_factory=dict)


class RecordSqlTuple(NamedTuple):
    """_summary_

    Attributes:
        rid (int): _description_
        pid (int): _description_
        name (str): _description_
        bgn_timestamp (): _description_
        duration (): _description_, in minute
    """
    rid: int
    pid: int
    name: str
    bgn_timestamp: float
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
