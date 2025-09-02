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
