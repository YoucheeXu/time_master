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
from src.time_database_type import TimeUnit, DayType
from src.time_database_type import StatusEnum
from src.time_database_type import GeoSqlTuple, ReminderSqlTuple, PlanSqlTuple, RecordSqlTuple
from src.time_database_type import ReminderAttrType, ReminderValType, PlanAttrType, PlanValType
from src.time_database_type import IconTuple, LocTuple, ReminderDataDict, PlanDataDict, Plan, RecordDataDict


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
    | action | int | ActTyp |  |
    | status | int | StatusEnum |  |
    | locstr | str | LocDict or None |  |
    | sums | int | in minute |  |
    |  |  |  |  |

    Reminders
    | Item | SqlType | PyType | Notes |
    | :--: | :--: | :--: | :--: | :--: | :--: | :--: |
    | eid | int ||  |
    | pid | int || refere to pid in Plan |
    | clk_timestr | str | datetime.time or None ||  |
    | bgn_timestr | str | datetime.time or None |  |
    | duration | int || in minute |
    | every | int ||  |
    | unit | str | TimeUnit | |
    | customstr | str  | DayType or list[int] | |
    | cycbgn_timestamp | float | datetime.datetime or None |  |
    | cycend_timestamp | float | datetime.datetime or None |  |

    Records
    | Item | SqlType | PyType | Notes |
    | :--: | :--: | :--: | :--: | :--: | :--: | :--: |
    | rid | int ||  |
    | pid | int || refere to pid in Plan |
    | name | str ||  |
    | bgn_timestamp | float | datetime.datetime |  |
    | duration | int || in minute |

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

    def open(self, dbfile: str, req_ver: int = 0) -> tuple[int, str]:
        """_summary_

        Args:
            dbfile (_type_): _description_
        """
        if not os.path.isfile(dbfile):
            ret, str = self._database.open(dbfile,
                sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
            ver = self._database.read_version()
            if ver != req_ver:
                return -1, (f"Version don't match, require version is "
                    f"{req_ver}, version of database actaully is {ver}")
            if ret == 1:
                self._new(req_ver)
                return 1, f"OK to open {dbfile} and creat table 'Plans' and 'Records'."
        else:
            ret, str = self._database.open(dbfile, sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)   
        return ret, str

    def _new(self, ver: int):
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
                action INT,
                status INT,
                locstr TEXT,
                susm INT
            )''')

        _ = self._database.execute('''
            CREATE TABLE IF NOT EXISTS REMINDERS(
                eid INTEGER PRIMARY KEY AUTOINCREMENT,
                pid INT NOT NULL REFERENCES PLANS(pid) ON UPDATE CASCADE,
                clk_timestr TEXT,
                bgn_timestr TEXT,
                duration INT,
                every INT,
                unit TEXT,
                customstr TEXT,
                cycbgn_timestamp REAL,
                cycend_timestamp REAL,
                FOREIGN KEY (pid) REFERENCES PLANS(pid) ON DELETE CASCADE
            )''')

        _ = self._database.execute('''
            CREATE TABLE IF NOT EXISTS RECORDS(
                rid INTEGER PRIMARY KEY AUTOINCREMENT,
                pid INT NOT NULL REFERENCES PLANS(pid) ON UPDATE CASCADE,
                name TEXT NOT NULL,
                bgn_timestamp REAL,
                duration INT,
                FOREIGN KEY (pid) REFERENCES PLANS(pid) ON DELETE CASCADE
            )''')

        _ = self._database.commit()
        if ver != 0:
            self._database.write_version(ver)

    # TODO: convert geo to location
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

    def _str2icon(self, iidstr: str):
        if iidstr:
            iid = cast(tuple[int, int], literal_eval(iidstr))
            icon = IconTuple(iid[0], iid[1])
            return icon
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
        # if specialstr in VALID_DAYTYPE:
        #     return cast(DayType, specialstr)
        # else:
        #     return cast(list[int], literal_eval(specialstr))
        custom = cast(int | list[int], literal_eval(specialstr))
        if isinstance(custom, int):
            return DayType(custom)
        else:
            return custom

    def read_plans(self):
        """ _summary_
        """
        for _, plan in self._plan_dict.items():
            plan.children.clear()
        self._plan_dict.clear()

        for pid, name, note, iid, tags, fid, \
            action, status, locstr, sums in \
                cast(Generator[PlanSqlTuple, None, None],
                self._database.each("SELECT * FROM PLANS")):
            geo = GeoSqlTuple(*literal_eval(locstr))
            locate_at = self._geo2loc(geo.latitude, geo.longitude)
            plandata: PlanDataDict = {
                "name": name,
                "note": note,
                "tags": self._str2tags(tags),
                "iid": self._str2icon(iid),
                "fid": fid,
                "reminders": {},
                "action": ActTyp(action),
                "status": StatusEnum(status),
                "location": locate_at,
                "sums": sums
            }
            if fid == -1:
                plan = Plan()
                plan.data = plandata
                self._plan_dict[pid] = plan
            else:
                self._plan_dict[fid].children[pid] = plandata

        for eid, pid, \
            clk_timestr, bgn_timestr, duration,  \
            every, unit, customstr, cycbgn_timestamp, cycend_timestamp in \
                cast(Generator[ReminderSqlTuple, None, None],
                self._database.each("SELECT * FROM REMINDERS")):
            clk_time = self._str2time(clk_timestr)
            bgn_time = self._str2time(bgn_timestr)
            custom = self._str2custom(customstr)
            cycbgn_dtime = self._timestamp2datetime(cycbgn_timestamp)
            cycend_dtime = self._timestamp2datetime(cycend_timestamp)
            reminder: ReminderDataDict = {
                "clk_time": clk_time,
                "bgn_time": bgn_time,
                "duration": duration,
                "every": every,
                "unit": TimeUnit(unit),
                "custom": custom,
                "cycbgn_dtime": cycbgn_dtime,
                "cycend_dtime": cycend_dtime
            }
            self._plan_dict[pid].data["reminders"][eid] = reminder

        # pv(self._plan_dict)

    def add_plan(self, name: str, note: str = "", tags: list[str] | None = None,
            icon: IconTuple | None = None, fid: int = -1,
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
        if tags is None:
            tags = []
            tagstr = ""
        iconstr = str(icon)
        locstr = self._loc2geo(locate_at)

        _ = self._database.execute1("""
            INSERT INTO PLANS (name, note, tags, iid, fid,
                action, status, locstr)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (name, note, tagstr, iconstr, fid,  \
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
            "name": name, "note": note, "tags": tags, "iid": icon, "fid": fid,
            "reminders": {},
            "action": action,
            "status": status,
            "location": locate_at,
            "sums": 0
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

    def modify_plan(self, pid: int, attrib: PlanAttrType,
            newval: PlanValType):
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
                plan.data[attrib] = newval
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
            case "sums":
                assert isinstance(newval, int)
                plan.data[attrib] = newval
                attr_sql = attrib
                newval_sql = newval
            case _:
                raise KeyError(f"There is no {attrib} in Plan {pid}")

        sql = f"UPDATE PLANS SET {attr_sql} = ? WHERE pid = ?"
        _ = self._database.execute1(sql, (newval_sql, pid))

        po((f"update '{attrib}' of #{pid} plan '{plan.data["name"]}' "
            f"from '{oldval}' to '{newval}'"))

        return True

    def get_plan_attr(self, pid: int, attrib: str):
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
                return cast(PlanValType, father.data[attrib])
            for cid, child, in father.children.items():
                if cid == pid:
                    return cast(PlanValType, child[attrib])
        raise KeyError(f"There is no {attrib} in Plan {pid}")

    @property
    def plan_dict(self):
        return self._plan_dict

    def add_reminder(self, pid: int,
            clk_time: datetime.time | None = None,
            bgn_time: datetime.time | None = None,
            duration: int = 0,
            every: int = 0, unit: TimeUnit = TimeUnit.WEEK,
            custom: DayType | list[int] = DayType.EVERYDAY,            
            cycbgn_dtime: datetime.datetime | None = None,
            cycend_dtime: datetime.datetime | None = None) -> int:
        """_summary_

        Args:
            pid (): _description_
            clk_time ( ): _description_
            bgn_time ( ): _description_
            duration ( ): _description_, in minute
            every (int): _description_, cycle interval
            unit (str): _description_, cycle time unit
            custom ( ): _description_
            cycbgn_dtime ( ): _description_
            cycend_dtime ( ): _description_
        Raises:
            RuntimeError: _description_

        Returns:
            int: id of new reminder
        """
        clk_timestr = self._time2str(clk_time)
        bgn_timestr = self._time2str(bgn_time)
        cycbgn_timestamp = self._datetime2timestamp(cycbgn_dtime)
        cycend_timestamp  = self._datetime2timestamp(cycend_dtime)

        _ = self._database.execute1("""
            INSERT INTO REMINDERS (pid, clk_timestr, bgn_timestr, duration,
                every, unit, customstr, cycbgn_timestamp, cycend_timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (pid, clk_timestr, bgn_timestr, duration,  \
                every, unit, str(custom), cycbgn_timestamp, cycend_timestamp)
        )
        data = self._database.get(
                "SELECT last_insert_rowid()"
            )
        if data is not None:
            eid = cast(int, data[0])
        else:
            raise RuntimeError("no last_insert_rowid")

        reminder: ReminderDataDict = {
            "clk_time": clk_time,
            "bgn_time": bgn_time,
            "duration": duration,
            "every": every,
            "unit": unit,
            "custom": custom,
            "cycbgn_dtime": cycbgn_dtime,
            "cycend_dtime": cycend_dtime
        }
        self._plan_dict[pid].data["reminders"][eid] = reminder

        return eid

    def del_reminder(self, eid: int):
        """_summary_

        Args:
            eid (int): _description_
        """
        sql = f"DELETE FROM REMINDERS WHERE eid='{eid}'"
        pv(sql)
        _ = self._database.execute1(sql)

    def modify_reminder(self, pid: int, eid: int, attrib: ReminderAttrType,
            newval: ReminderValType):
        """_summary_

        Args:
            pid (int): _description_
            eid (int): _description_
            attrib (str): _description_
            newval (_type_): _description_
        """
        plan = Plan()
        for fid, father in self._plan_dict.items():
            if fid == pid:
                plan = father
                break
            for eid, child, in father.children.items():
                if eid == pid:
                    plan.data = child
                    break
        reminder = plan.data["reminders"][eid]
        oldval = reminder[attrib]
        match attrib:
            case "clk_time" | "bgn_time":
                assert isinstance(newval, datetime.time)
                reminder[attrib] = newval
                attr_sql = attrib + "str"
                newval_sql = self._time2str(newval)
            case "duration" | "every":
                assert isinstance(newval, int)
                reminder[attrib] = newval
                attr_sql = attrib
                newval_sql = newval
            case "unit":
                assert isinstance(newval, TimeUnit)
                reminder[attrib] = newval
                attr_sql = attrib
                newval_sql = newval
            case "custom":
                assert isinstance(newval, DayType) or isinstance(newval, list)
                reminder[attrib] = newval
                attr_sql = "customstr"
                newval_sql = str(newval)
            case "cycbgn_dtime" | "cycend_dtime":
                assert isinstance(newval, datetime.datetime)
                reminder[attrib] = newval
                attr_sql = attrib.replace("_dtime", "_timestamp")
                newval_sql = self._datetime2timestamp(newval)
            # case _:
            #     raise KeyError(f"There is no {attrib} in Plan {pid}")

        sql = f"UPDATE REMINDERS SET {attr_sql} = ? WHERE pid = ?"
        pv(sql)
        _ = self._database.execute1(sql, (newval_sql, pid))

        po((f"update '{attrib}' of #{eid} 'cycle_reminder' in #{pid} plan "
            f"from '{oldval}' to '{newval}'"))

        return True

    def get_reminder_attr(self, pid: int, eid: int, attrib: str):
        """_summary_

        Args:
            pi (int): _description_
            eid (int): _description_
            attrib (str): _description_

        Raises:
            KeyError: _description_

        Returns:
            _type_: _description_
        """
        for fid, father in self._plan_dict.items():
            if fid == pid:
                return cast(ReminderValType, 
                    father.data["reminders"][eid][attrib])
            for eid, child, in father.children.items():
                if eid == pid:
                    return cast(ReminderValType,
                        child["reminders"][eid][attrib])
        raise KeyError(f"There is no {attrib} in Plan {pid}")

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

    def add_record(self, name: str, bgn_dtime: datetime.datetime,
            pid: int = -1,
            duration: int = 0):
        """ Insert a new record into the RECORDS table

        Args:
            name (str): Name of the record
            bgn_dtime (datetime.datetime): Start datetime of the record
            pid (int, optional): Associated pid, default value is -1
            duration (int, optional): duration of the record in minute, default value is 0
        
        Returns:
            int: Auto-increment ID (rid) of the newly added record
        
        Raises:
            RuntimeError: Raised when insertion fails or
                auto-increment ID cannot be obtained
        """
        bgn_timestamp = self._datetime2timestamp(bgn_dtime)

        _ = self._database.execute1(
            """INSERT INTO RECORDS (pid, name, bgn_timestamp, duration) 
                VALUES (?, ?, ?, ?)""",
            (pid, name, bgn_timestamp, duration)
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
        """Delete a record by rid

        Args:
            rid (int): Record ID to delete (must be positive integer)

        Raises:
            TypeError: If rid is not an integer
            ValueError: If rid is a non-positive integer (invalid for AUTOINCREMENT)
        """
        # Step 1: Validate rid type (enforce int, even in dynamic Python)
        if not isinstance(rid, int):
            raise TypeError(f"rid must be an integer (got {type(rid).__name__}: {rid})")

        # Step 2: Validate rid value (AUTOINCREMENT rid is always positive)
        if rid <= 0:
            raise ValueError(f"rid must be a positive integer (got {rid})")

        # Step 3: Build and execute SQL (keep your original logic)
        sql = f"DELETE FROM RECORDS WHERE rid='{rid}'"
        pv(sql)
        _ = self._database.execute1(sql)

    def get_records(self, start_date: datetime.date, pid: int = -1,
            end_date: datetime.date | None = None):
        """ Query records within the specified date range from the RECORDS table

        Args:
            start_date (datetime.date): Start date of record
            pid (int, optional): Filter records by pid; use -1 to query all pids (default: -1)
            end_date (datetime.date | None): End date of the record,
                defaults to start_date if None (single-day query)

        Returns:
            dict[int, RecordDict]: Dictionary with record ID (rid) as key and record details as value
        """
        record_dict: dict[int, RecordDataDict] = {}
        # Handle default case when end_date is None: query single day
        if end_date is None:
            end_date = start_date

        # Convert dates to ISO format (YYYY-MM-DD) for SQL query
        start_date_iso = start_date.isoformat()
        end_date_iso = end_date.isoformat()
        print((f"Query date range: {start_date_iso} to {end_date_iso}, "
            f"pid filter: {pid if pid != -1 else 'all'}"))

        # Step 1: Dynamically build SQL query and parameters based on pid
        query_parts = [
            "SELECT * FROM RECORDS",
            "WHERE date(bgn_timestamp, 'unixepoch', 'localtime') BETWEEN ? AND ?"
        ]
        query_params = [start_date_iso, end_date_iso]

        # Add pid condition if pid != -1 (ignore pid when pid = -1)
        if pid != -1:
            query_parts.append("AND pid = ?")
            query_params.append(str(pid))

        # Combine query parts into final SQL
        query_sql = "\n    ".join(query_parts)

        # Step 2: Iterate over query results and build record dictionary
        for rid, pid, name, bgn_timestamp, duration in \
            cast(Generator[RecordSqlTuple, None, None],
                self._database.each(query_sql, tuple(query_params))):
            record: RecordDataDict = {
                "pid": pid,
                "name": name,
                "bgn_dtime": self._timestamp2datetime(bgn_timestamp),
                "duration": duration
            }
            record_dict[rid] = record

        return record_dict

    def close(self):
        """_summary_

        Returns:
            _type_: _description_
        """
        return self._database.close()
