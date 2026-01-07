#!/usr/bin/python3
# -*- coding: UTF-8 -*-
# import abc
import os
from ast import literal_eval
import sqlite3
import datetime
from typing import cast
from collections.abc import Generator

from pyutilities.logit import pv, po, pe
from pyutilities.sqlite import SQLite

from src.bidirectionaldict import BidirectionalDict
from src.action_sys import ActTyp
from src.time_database_type import VALID_TIMEUNIT, TimeUnit, VALID_DAYTYPE, DayType
from src.time_database_type import StatusEnum
from src.time_database_type import GeoSqlTuple, PlanSqlTuple, RecordSqlTuple
from src.time_database_type import IconTuple, LocTuple, PlanDataDict, Plan, RecordDict


class TimeDatabase:
    """_summary_

    Plans
    | Item | SqlType | PyType | Notes |
    | :--: | :--: | :--: | :--: | :--: | :--: | :--: |
    | pid | int ||  |
    | name | str ||  |
    | note | str ||  |
    | tags | str | list[str] |  |
    | iid | str | tuple[int, int] | id of icon |
    | fid | int ||  |
    | clk_timestr | str | datetime.time or None ||  |
    | bgn_timestr | str | datetime.time or None |  |
    | end_timestr | str | datetime.time or None |  |
    | every | int ||  |
    | unit | str | TimeUnit | |
    | customstr | str  | DayType or list[int] | |
    | cycbgn_timestamp | float | datetime.datetime or None |  |
    | cycend_timestamp | float | datetime.datetime or None |  |
    | action | int | ActTyp |  |
    | status | int | StatusEnum |  |
    | locstr | str | LocDict or None |  |
    |  |  |  |  |

    Records
    | Item | SqlType | PyType | Notes |
    | :--: | :--: | :--: | :--: | :--: | :--: | :--: |
    | rid | int ||  |
    | pid | int || refere to pid in Plan |
    | bgn_timestamp | float | datetime.datetime |  |
    | end_timestamp | float | datetime.datetime |  |

    Attributes:
        _database (_type_): _description_
        _plan_dict (_type_): _description_
        _day_dict (_type_): _description_
        _period_dict (_type_): _description_
    """
    def __init__(self):
        """_summary_
        """
        self._database: SQLite = SQLite()
        self._plan_dict: dict[int, Plan] = {}

        self._day_dict: BidirectionalDict[str, str] = \
            BidirectionalDict[str, str]({"ED": "日", "WD": "工作日", "HD": "节假日"})
        self._period_dict: BidirectionalDict[str, str] = \
            BidirectionalDict[str, str]({"HR": "小时", "DY": "日", \
                "WK": "周", "MH": "月", "SZ": "季节", "YR": "年"})

    # TODO: check version
    def open(self, dbfile: str) -> tuple[int, str]:
        """_summary_

        Args:
            dbfile (_type_): _description_
        """
        if not os.path.isfile(dbfile):
            ret, str = self._database.open(dbfile, sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
            if ret == 1:
                self._new()
                return 1, f"OK to open {dbfile} and creat table 'Plans' and 'Records'."
        else:
            ret, str = self._database.open(dbfile, sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)   
        return ret, str

    # TODO: add version
    def _new(self):
        """_summary_
        """
        _ = self._database.execute('''
                PRAGMA foreign_keys = ON
            ''')

        _ = self._database.execute('''
            CREATE TABLE IF NOT EXISTS PLANS(
                pid INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                note TEXT,
                tags TEXT,                
                iid TEXT,
                fid INT,
                clk_timestr TEXT,
                bgn_timestr TEXT,
                end_timestr TEXT,
                every INT,
                unit TEXT,
                customstr TEXT,
                cycbgn_timestamp REAL,
                cycend_timestamp REAL,
                action INT,
                status INT,
                locstr TEXT)''')

        _ = self._database.execute('''
            CREATE TABLE IF NOT EXISTS RECORDS(
                rid INTEGER PRIMARY KEY AUTOINCREMENT,
                pid INT NOT NULL REFERENCES PLANS(pid) ON UPDATE CASCADE,
                bgn_timestamp REAL
                end_timestamp REAL
            )''')
        _ = self._database.commit()

    # TODO: convert geo to locatoin
    def _geo2loc(self, latitude: float, longitude: float):
        """_summary_

        Args:
            latitude (float): _description_
            longitude (float): _description_

        Returns:
            _type_: _description_
        """
        return LocTuple(latitude, longitude)

    def _loc2geo(self, location: LocTuple | None):
        """_summary_

        Args:
            location (LocTuple | None): _description_

        Returns:
            _type_: _description_
        """
        if location is None:
            lat, lng = 0, 0
        else:
            lat, lng = location.lat, location.lng
        return f"({lat}, {lng})"

    def _str2iid(self, iidstr: str):
        if iidstr:
            return cast(tuple[int, int], literal_eval(iidstr))
        else:
            return None

    def _str2tags(self, tagstr: str) -> list[str]:
        if not tagstr:
            return []
        else:
            return cast(list[str], literal_eval(tagstr))

    def _str2time(self, timestr: str):
        """_summary_

        Args:
            timestr (str): _description_

        Returns:
            _type_: _description_
        """
        if timestr:
            return datetime.datetime.strptime(timestr, "%H:%M").time()
        else:
            return None

    def _time2str(self, time: datetime.time | None):
        """_summary_

        Args:
            time (datetime.time | None): _description_

        Returns:
            _type_: _description_
        """
        if time is None:
            return ""
        return datetime.time.strftime(time, "%H:%M")

    def _timestamp2datetime(self, timestamp: float):
        """_summary_

        Args:
            timestamp (float): _description_

        Returns:
            _type_: _description_
        """
        if timestamp > 0:
            return datetime.datetime.fromtimestamp(timestamp)
        else:
            return None

    def _datetime2timestamp(self, dtime: datetime.datetime | None):
        """_summary_

        Args:
            dtime (datetime.datetime | None): _description_

        Returns:
            _type_: _description_
        """
        if dtime is None:
            return -1
        return dtime.timestamp()

    def _str2custom(self, specialstr: str):
        """_summary_

        Args:
            specialstr (str): _description_

        Returns:
            _type_: _description_
        """
        if specialstr in VALID_DAYTYPE:
            return cast(DayType, specialstr)
        else:
            return cast(list[int], literal_eval(specialstr))

    def read_plans(self):
        """ _summary_
        """
        for _, plan in self._plan_dict.items():
            plan.children.clear()
        self._plan_dict.clear()

        for pid, name, note, iid, tags, fid, \
            clk_timestr, bgn_timestr, end_timestr,  \
            every, unit, customstr, cycbgn_timestamp, cycend_timestamp, \
            action, status, locstr in \
                cast(Generator[PlanSqlTuple, None, None],
                self._database.each("SELECT * FROM PLANS")):
            clk_time = self._str2time(clk_timestr)
            bgn_time = self._str2time(bgn_timestr)
            end_time = self._str2time(end_timestr)
            custom = self._str2custom(customstr)
            cycbgn_dtime = self._timestamp2datetime(cycbgn_timestamp)
            cycend_dtime = self._timestamp2datetime(cycend_timestamp)
            geo = GeoSqlTuple(*literal_eval(locstr))
            locate_at = self._geo2loc(geo.latitude, geo.longitude)
            plandata: PlanDataDict = {
                "name": name,
                "note": note,
                "tags": self._str2tags(tags),
                "iid": self._str2iid(iid),
                "fid": fid,
                "clk_time": clk_time, "bgn_time": bgn_time, "end_time": end_time,
                "every": every, "unit": cast(TimeUnit, unit), "custom": custom,
                "cycbgn_dtime": cycbgn_dtime, "cycend_dtime": cycend_dtime,
                "action": ActTyp(action),
                "status": StatusEnum(status),
                "location": locate_at
            }
            if fid == -1:
                plan = Plan()
                plan.data = plandata
                self._plan_dict[pid] = plan
            else:
                self._plan_dict[fid].children[pid] = plandata

        # pv(self._plan_dict)

    def add_plan(self, name: str, note: str = "", tags: list[str] = [],
            iid: IconTuple | None = None, fid: int = -1,
            clk_time: datetime.time | None = None,
            bgn_time: datetime.time | None = None,
            end_time: datetime.time | None = None,
            every: int = 0, unit: TimeUnit = "WK",
            custom: DayType | list[int] = "ED",            
            cycbgn_dtime: datetime.datetime | None = None,
            cycend_dtime: datetime.datetime | None = None,
            action: ActTyp = ActTyp.NOACTION,
            status: StatusEnum = StatusEnum.ONGOING,
            locate_at: LocTuple | None = None) -> int:
        """_summary_

        Args:
            name (): _description_
            note (): _description_
            tags (): _description_
            iid (): id of icon
            fid (): _description_
            clk_time ( ): _description_
            bgn_time ( ): _description_
            end_time ( ): _description_
            every (int): _description_, cycle interval
            unit (str): _description_, cycle time unit
            custom ( ): _description_
            cycbgn_dtime ( ): _description_
            cycend_dtime ( ): _description_
            action ( ): _description_
            status (): _description_
            location (): _description_
        Raises:
            RuntimeError: _description_

        Returns:
            int: id of new plan
        """
        # if reminder_time is not None:
            # reminder_str = self._time2str(reminder_time)
        # else:
            # reminder_str = ""

        tagstr = str(tags)
        iidstr = str(iid)
        clk_timestr = self._time2str(clk_time)
        bgn_timestr = self._time2str(bgn_time)
        end_timestr = self._time2str(end_time)
        cycbgn_timestamp = self._datetime2timestamp(cycbgn_dtime)
        cycend_timestamp  = self._datetime2timestamp(cycend_dtime)
        locstr = self._loc2geo(locate_at)

        _ = self._database.execute1("""
            INSERT INTO PLANS (name, note, tags, iid, fid, clk_timestr, bgn_timestr, end_timestr,
                every, unit, customstr, cycbgn_timestamp, cycend_timestamp,
                action, status, locstr)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (name, note, tagstr, iidstr, fid, clk_timestr, bgn_timestr, end_timestr,  \
                every, unit, str(custom), cycbgn_timestamp, cycend_timestamp, \
                action, status, locstr)
        )
        data = self._database.get(
                "SELECT last_insert_rowid()"
            )
        if data is not None:
            pid = cast(int, data[0])
        else:
            raise RuntimeError("no last_insert_rowid")

        plandata: PlanDataDict = {
            "name": name, "note": note, "tags": tags, "iid": iid, "fid": fid,
            "clk_time": clk_time, "bgn_time": bgn_time, "end_time": end_time,
            "every": every, "unit": unit, "custom": custom,
            "cycbgn_dtime": cycbgn_dtime, "cycend_dtime": cycend_dtime,
            "action": action,
            "status": status,
            "location": locate_at
        }
        if fid == -1:
            plan = Plan()
            plan.data = plandata
            self._plan_dict[pid] = plan
        else:
            self._plan_dict[fid].children[pid] = plandata

        return pid

    def del_plan(self, pid: int):
        """_summary_

        Args:
            pid (int): _description_
        """
        sql = f"DELETE FROM PLANS WHERE eid='{pid}'"
        pv(sql)
        _ = self._database.execute1(sql)

    # TODO: attrib Literal
    def modify_plan(self, pid: int, attrib: str,
            newval: str | IconTuple | list[str] | int \
                | LocTuple | StatusEnum | TimeUnit | list[int] | DayType \
                | datetime.time | datetime.datetime | ActTyp | None):
        """_summary_

        Args:
            pid (int): _description_
            attrib (str): _description_
            newval (_type_): _description_
        """
        oldfid = -1
        plan = Plan()
        for fid, father in self._plan_dict.items():
            if fid == pid:
                oldfid = father.data["fid"]
                plan = father
                break
            for cid, child, in father.children.items():
                if cid == pid:
                    oldfid = child["fid"]
                    plan.data = child
                    break
        oldval = plan.data[attrib]
        match attrib:
            case "name":
                assert isinstance(newval, str)
                plan.data[attrib] = newval
                attr_sql = attrib
                newval_sql = newval
            case "note":
                assert isinstance(newval, str)
                plan.data[attrib] = newval
                attr_sql = attrib
                newval_sql = newval
            case "tags":
                assert isinstance(newval, list)
                plan.data[attrib] = cast(list[str], newval)
                attr_sql = attrib
                newval_sql = str(newval)
            case "iid":
                pe(type(newval))
                assert isinstance(newval, IconTuple) or (newval is None)
                plan.data[attrib] = newval
                attr_sql = attrib
                newval_sql = str(newval)
            case "fid":
                assert isinstance(newval, int)
                attr_sql = attrib
                newval_sql = newval

                newfid = newval
                if oldfid == -1:
                    if newfid == -1: # father -> father
                        warnmsg = (f"no support father #{pid} plan convert "
                            "to fatherr")
                        # raise RuntimeWarning(errmsg)
                        po(warnmsg)
                        return False
                    elif len(plan.children) > 0:   # father with child-> child 
                        raise RuntimeError((f"no support father #{pid} plan "
                            f"with children degrade to #{newfid} plan's child"))
                    elif newfid == pid:   # father without child-> child
                        raise RuntimeError((f"no support father #{pid} plan "
                            f"degrade to itself child"))
                    else:
                        self._plan_dict[newfid].children[pid] = plan.data
                        del self._plan_dict[pid]
                elif newfid == -1:    # child -> father
                    newplan = Plan()
                    newplan.data = plan.data
                    self._plan_dict[pid] = newplan
                    del self._plan_dict[oldfid].children[pid]
                elif oldfid != newfid:    # one's child -> another's child
                    self._plan_dict[newfid].children[pid] = plan.data
                    del self._plan_dict[oldfid].children[pid]
                else:   # one's child -> one's child 
                    warnmsg = (f"no support child #{pid} plan convert "
                        "its father to the same fatherr")
                    po(warnmsg)
                    return False
                plan.data[attrib] = newval
            case "clk_time" | "bgn_time" | "end_time":
                assert isinstance(newval, datetime.time)
                plan.data[attrib] = newval
                attr_sql = attrib + "str"
                newval_sql = self._time2str(newval)
            case "every":
                assert isinstance(newval, int)
                plan.data[attrib] = newval
                attr_sql = attrib
                newval_sql = newval
            case "unit":
                assert newval in VALID_TIMEUNIT
                plan.data[attrib] = cast(TimeUnit, newval)
                attr_sql = attrib
                newval_sql = newval
            case "custom":
                assert newval in VALID_DAYTYPE or isinstance(newval, list)
                plan.data[attrib] = cast(DayType | list[int], newval)
                attr_sql = "customstr"
                newval_sql = str(newval)
            case "cycbgn_dtime" | "cycend_dtime":
                assert isinstance(newval, datetime.datetime)
                plan.data[attrib] = newval
                attr_sql = attrib.replace("_dtime", "_timestamp")
                newval_sql = self._datetime2timestamp(newval)
            case "action":
                assert isinstance(newval, ActTyp)
                plan.data[attrib] = newval
                attr_sql = attrib
                newval_sql = newval
            case "status":
                assert isinstance(newval, StatusEnum)
                plan.data[attrib] = newval
                attr_sql = attrib
                newval_sql = newval
            case "location":
                assert isinstance(newval, LocTuple) or (newval is None)
                plan.data[attrib] = newval
                attr_sql = "locstr"
                newval_sql = self._loc2geo(newval)
            case _:
                raise KeyError(f"There is no {attrib} in Plan {pid}")

        sql = f"UPDATE PLANS SET {attr_sql} = ? WHERE pid = ?"
        pv(sql)
        _ = self._database.execute1(sql, (newval_sql, pid))

        po((f"update '{attrib}' of #{pid} plan '{plan.data["name"]}' "
            f"from '{oldval}' to '{newval}'"))

        return True

    def get_planattr(self, pid: int, attrib: str):
        """_summary_

        Args:
            pid (int): _description_
            attrib (str): _description_

        Raises:
            KeyError: _description_

        Returns:
            _type_: _description_
        """
        for fid, father in self._plan_dict.items():
            if fid == pid:
                return father.data[attrib]
            for cid, child, in father.children.items():
                if cid == pid:
                    return child[attrib]
        raise KeyError(f"There is no {attrib} in Plan {pid}")

    @property
    def plan_dict(self):
        return self._plan_dict

    # def read_allrecord(self):
        # for event, strt_dtime, end_dtime in \
                # cast(Generator[RecordSqlTuple, None, None],
                # self._database.each("SELECT * FROM RECORDS")):
            # iid, strt_date, end_date = cast(CalendarSqlRecord, calendarecord)
            # start_time = datetime.datetime.fromtimestamp(strt_dtime)
            # end_time = datetime.datetime.fromtimestamp(end_dtime)
            # date = start_time.date()
            # record = RecordDict(start_time, end_time)
            # self._record_dict[rid] = record
        # pv(self._record_dict)

    def add_record(self, pid: int, bgn_dtime: datetime.datetime, end_dtime: datetime.datetime | None = None):
        """_summary_

        Args:
            pid (int): _description_
            bgn_dtime (datetime.datetime): _description_
            end_dtime (datetime.datetime | None, optional): _description_. Defaults to None.
        """
        bgn_timestamp = self._datetime2timestamp(bgn_dtime)
        end_timestamp = self._datetime2timestamp(end_dtime)

        _ = self._database.execute1(
            """INSERT INTO RECORDS (pid, bgn_timestamp, end_timestamp) 
                VALUES (?, ?, ?)""",
            (pid, bgn_timestamp, end_timestamp)
        )
        data = self._database.get(
            "SELECT last_insert_rowid()"
        )
        if data is not None:
            rid = cast(int, data[0])
        else:
            raise RuntimeError("no last_insert_rowid")
        return rid

    def del_record(self, rid: int):
        """_summary_

        Args:
            rid (int): _description_
        """
        sql = f"DELETE FROM RECORDS WHERE rid='{rid}'"
        pv(sql)
        _ = self._database.execute1(sql)

    def get_records(self, date: datetime.date):
        """_summary_

        Args:
            date (datetime.date): _description_

        Returns:
            _type_: _description_
        """
        record_dict: dict[int, RecordDict] = {}
        for rid, pid, bgn_timestamp, end_timestamp in \
            cast(Generator[RecordSqlTuple, None, None],
                self._database.each(
                    "SELECT * FROM RECORDS WHERE date(bgn_timestamp) = ?",
                    (date,))):
            record: RecordDict = {
                "pid": pid,
                "bgn_dtime": self._timestamp2datetime(bgn_timestamp),
                "end_dtime": self._timestamp2datetime(end_timestamp)
            }
            record_dict[rid] = record

        return record_dict

    def close(self):
        """_summary_

        Returns:
            _type_: _description_
        """
        return self._database.close()
