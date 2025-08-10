#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import datetime
import sqlite3
from dataclasses import dataclass, field
from typing import NamedTuple, TypedDict


class HourSqlTuple(NamedTuple):
    iid: int
    name: str
    rid: str
    clock: str
    schedule: str
    sums: int   # minutes
    father: int


class HourTuple(NamedTuple):
    iid: int
    name: str
    rid: tuple[int, int]
    clock: str
    schedule: str
    sums: int   # minutes
    father: int


class HourDict(TypedDict):
    name: str
    rid: tuple[int, int]
    clock: str
    schedule: str
    sums: int   # minutes
    father: int


@dataclass
class Hour:
    # TypedDict("ItemDict",{"id": 0, "name": "", "rid": 0, "clock": "", "schedule": "", "sums": 0, "father": -1})
    data: HourDict = field(default_factory=HourDict)
    children: dict[int, HourDict] = field(default_factory=dict)


class HourSqlRecord(NamedTuple):
    iid: int
    # strt: sqlite3.Timestamp
    strt: datetime.datetime
    # end: sqlite3.Timestamp
    end: datetime.datetime


class HourRecordTuple(NamedTuple):
    day: sqlite3.Date
    endure: int


class MedSqlTuple(NamedTuple):
    iid: int
    name: str
    rid: str
    due: sqlite3.Date
    sums: float
    unit: str


class MedDict(TypedDict):
    name: str
    rid: tuple[int, int]
    due: sqlite3.Date
    sums: float
    unit: str


class MedSqlRecord(NamedTuple):
    iid: int
    take: sqlite3.Timestamp
    dose: float


class MedSqlUsage(NamedTuple):
    """
        QD意味着每天一次
        BID意味着每天两次
        TID意味着每天三次
        QID意味着每天四次
        QHS意味着睡前
        Q4H意味着每4小时
        Q6H意味着每6小时
        Q8H意味着每8小时
        QOD意味着每隔一天
        PRN是指根据需要 - PRN药物通常只用于轻微症状，如疼痛，恶心或瘙痒
        ac在餐前的意思（它也可以写成qac）
    """
    iid: int
    schedule: str
    strt: sqlite3.Date
    end: sqlite3.Date


class MedUsageTuple(NamedTuple):
    agenda: sqlite3.Time
    dose: float


class MedUsageDict(TypedDict):
    schedule: list[MedUsageTuple]
    strt: sqlite3.Date
    end: sqlite3.Date
