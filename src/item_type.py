#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import sqlite3
from dataclasses import dataclass, field
from typing import NamedTuple, TypedDict


class HourRecord(NamedTuple):
    iid: int
    start: sqlite3.Timestamp
    end: sqlite3.Timestamp


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
