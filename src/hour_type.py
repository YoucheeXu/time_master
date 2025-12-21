#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import datetime
import sqlite3
from dataclasses import dataclass, field
from typing import NamedTuple, TypedDict


class HourSqlTuple(NamedTuple):
    """Database storage type of the hour item

    Attributes:
        iid (int): Id of hour item
        name (str): Name of hour item
        rid (str): Resource id of hour item
            format: i1_i2
                i1 (int): Group number of the resource
                i2 (int): Index number of the resource group
        clock (str): Reminder time of the hour item
            format: i1_i2_10:00
                i1: P: Per(Every), E: Even, O: Odd
                i2: CD: Calendar day, WD: Work day, HD: Holiday day
        schedule (str): Planned time spent within the cycle of the hour item
            format: i1_30m
                i1: PD: Per(Every) Day, PW: Per(Every) Week, PM: Per(Every) Month
        sums (int): Total time for hour item in minutes
        father (int): Parent ID of the hour item
    """
    iid: int
    name: str
    rid: str
    clock: str
    schedule: str
    sums: int   # minutes
    father: int


class HourTuple(NamedTuple):
    """_summary_

    Attributes:
        iid (int): Id of hour item
        name (str): Name of hour item
        rid (tuple[int, int]): Resource id of hour item, in (group number, index number)
        clock (str): Reminder time of the hour item, such as "偶数工作日 21:00"
        schedule (str): Planned time spent within the cycle of the hour item, such as "30 minutes per workday" 
        sums (int): Total time for hour item in minutes
        father (int): Parent ID of the hour item
    """
    iid: int
    name: str
    rid: tuple[int, int]
    clock: str
    schedule: str
    sums: int   # minutes
    father: int


class HourDict(TypedDict):
    """_summary_

    Attributes:
        name (str): Name of hour item
        rid (tuple[int, int]): Resource id of hour item, in (group number, index number)
        clock (str): Reminder time of the hour item, such as "偶数工作日 21:00"
        schedule (str): Planned time spent within the cycle of the hour item, such as "30 minutes per workday" 
        sums (int): Total time for hour item in minutes
        father (int): Parent ID of the hour item
    """
    name: str
    rid: tuple[int, int]
    clock: str
    schedule: str
    """in minutes"""
    sums: int   # minutes
    father: int


@dataclass
class Hour:
    """_summary_

    Attributes:
        data (HourDict): _description_
        children (dict[int, HourDict]): _description_
    """
    # TypedDict("ItemDict",{"id": 0, "name": "", "rid": 0, "clock": "", "schedule": "", "sums": 0, "father": -1})
    data: HourDict = field(default_factory=HourDict)
    children: dict[int, HourDict] = field(default_factory=dict)


class HourSqlRecord(NamedTuple):
    """_summary_

    Attributes:
        iid (int): _description_
        strt (datetime.datetime): _description_
        end (datetime.datetime): _description_
    """
    iid: int
    # strt: sqlite3.Timestamp
    strt: datetime.datetime
    # end: sqlite3.Timestamp
    end: datetime.datetime


class HourRecordTuple(NamedTuple):
    """_summary_

    Attributes:
        day (sqlite3.Date): _description_
        endure (int): _description_
    """
    day: sqlite3.Date
    endure: int
