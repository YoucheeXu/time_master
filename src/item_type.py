#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import sqlite3
from typing import NamedTuple, TypedDict


class Record(NamedTuple):
    id_: int
    start: sqlite3.Date
    end: sqlite3.Date


class ItemTuple(NamedTuple):
    id_: int
    name: str
    rid: int
    clock: str
    schedule: str
    sums: int   # minutes
    father: int


class ItemDict(TypedDict):
    id: int
    name: str
    rid: int
    clock: str
    schedule: str
    sums: int
    father: int

