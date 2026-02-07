#!/usr/bin/python3
# -*- coding: UTF-8 -*-
# import abc
import os
from ast import literal_eval
import copy
import sqlite3
import datetime
import uuid
from typing import Unpack, cast
from collections.abc import Generator

from pyutilities.logit import pv, po, pe
from pyutilities.sqlite import SQLite

from src.action_sys import ActTyp
from src.time_database_type import generate_sqlite_fields
from src.time_database_type import TimeUnit, DayType
from src.time_database_type import StatusEnum
from src.time_database_type import GeoSqlTuple, PlanSqlTuple
from src.time_database_type import ReminderAttr
from src.time_database_type import ReminderDataDict, ReminderDataOptionalDict
from src.time_database_type import default_reminder_data
from src.time_database_reminder import serialize_reminder_collection
from src.time_database_reminder import deserialize_reminder_collection
from src.time_database_type import PlanAttr, PlanAttrType, PlanValType
from src.time_database_type import PlanDataDict, default_plan_data
from src.time_database_type import IconTuple, LocTuple, Plan
from src.time_database_type import RecordSqlTuple, RecordDataDict
from src.time_database_type import RecordAttr, default_record_data


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
    | reminders | int ||  |
    | action | int | ActTyp |  |
    | status | int | StatusEnum |  |
    | location | str | LocTuple or None |  |
    | sums | int | in minute |  |
    |  |  |  |  |

    Records
    | Item | SqlType | PyType | Notes |
    | :--: | :--: | :--: | :--: | :--: | :--: | :--: |
    | rid | int ||  |
    | pid | int || refere to pid in Plan |
    | name | str ||  |
    | bgn_dtime | float | datetime.datetime |  |
    | duration | int || in minute |

    Attributes:
        _database (_type_): _description_
        _plan_dict (_type_): _description_
        _plandata_dict (_type_): flatten version of `_plan_dict` with sharing `Plan` with `_plan_dict`
    """
    def __init__(self):
        """_summary_
        """
        self._database: SQLite = SQLite()
        self._plan_dict: dict[int, Plan] = {}
        self._plandata_dict: dict[int, PlanDataDict] = {}

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
                reminders TEXT,
                action INT,
                status INT,
                location TEXT,
                sums INT
            )''')

        _ = self._database.execute('''
            CREATE TABLE IF NOT EXISTS RECORDS(
                rid INTEGER PRIMARY KEY AUTOINCREMENT,
                pid INT NOT NULL REFERENCES PLANS(pid) ON UPDATE CASCADE,
                name TEXT NOT NULL,
                bgn_dtime REAL,
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
            icon = cast(tuple[int, int], literal_eval(iidstr))
            return IconTuple(*icon)
        else:
            return None

    def _icon2str(self, icon: IconTuple | None):
        if icon is not None:
            iconstr= str(tuple(icon))
        else:
            iconstr  = "(0, 0)"
        return iconstr

    def _str2tags(self, tagstr: str) -> list[str]:
        if not tagstr:
            return []
        else:
            return cast(list[str], literal_eval(tagstr))

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

        for pid, name, note, tags, iid, fid, reminders, action, status, \
            location, sums in cast(Generator[PlanSqlTuple, None, None],
                self._database.each("SELECT * FROM PLANS")):
            fid = fid
            pid = pid
            geo = GeoSqlTuple(*literal_eval(location))
            locate_at = self._geo2loc(geo.latitude, geo.longitude)
            plandata: PlanDataDict = {
                "name": name,
                "note": note,
                "tags": self._str2tags(tags),
                "iid": self._str2icon(iid),
                "fid": fid,
                "reminders": deserialize_reminder_collection(reminders),
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
                if fid in self._plan_dict:
                    self._plan_dict[fid].children[pid] = plandata
            self._plandata_dict[pid] = plandata

        # pv(self._plan_dict)
        return copy.deepcopy(self._plandata_dict)

    def add_plan(self, **kwargs: Unpack[PlanDataDict]) -> int:
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
        plandata = default_plan_data()
        for key in PlanAttr:
            if key in kwargs:
                plandata[key] = kwargs[key]

        fid = plandata["fid"]
        tags = plandata["tags"]
        tagstr = str(tags)
        icon = plandata["iid"]
        locstr = self._loc2geo(plandata["location"])

        plandata_sql = PlanSqlTuple(-1,
            plandata["name"],
            plandata["note"],
            tagstr,
            self._icon2str(icon),
            plandata["fid"],
            "",
            plandata["action"],
            plandata["status"],
            locstr,
            plandata["sums"]
        )

        filtered_fields, field_string, placeholder_string = \
            generate_sqlite_fields(PlanSqlTuple, exclude_fields=['pid'])

        sql = f""" INSERT INTO PLANS ({field_string})
            VALUES ({placeholder_string})"""
        po(sql)
        # Convert PlanSqlTuple to dict, then extract filtered fields in order
        plan_dict_sql = plandata_sql._asdict()
        param_values = tuple(plan_dict_sql[field] for field in filtered_fields)
        po(param_values)

        _ = self._database.execute1(sql,param_values)
        data = self._database.get(
                "SELECT last_insert_rowid()"
            )
        if data is not None:
            pid = cast(int, data[0])
        else:
            raise RuntimeError("no last_insert_rowid")

        if fid == -1:
            plan = Plan()
            plan.data = plandata
            self._plan_dict[pid] = plan
        else:
            self._plan_dict[fid].children[pid] = plandata
        self._plandata_dict[pid] = plandata

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
                newval_sql = newval
            case "note":
                assert isinstance(newval, str)
                plan.data[attrib] = newval
                newval_sql = newval
            case "tags":
                assert isinstance(newval, list)
                plan.data[attrib] = newval
                newval_sql = str(newval)
            case "iid":
                pe(type(newval))
                assert isinstance(newval, IconTuple) or (newval is None)
                plan.data[attrib] = newval
                newval_sql = str(newval)
            case "fid":
                assert isinstance(newval, int)
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
                newval_sql = newval
            case "status":
                assert isinstance(newval, StatusEnum)
                plan.data[attrib] = newval
                newval_sql = newval
            case "location":
                assert isinstance(newval, LocTuple) or (newval is None)
                plan.data[attrib] = newval
                newval_sql = self._loc2geo(newval)
            case "sums":
                assert isinstance(newval, int)
                plan.data[attrib] = newval
                newval_sql = newval
            case _:
                raise KeyError(f"There is no {attrib} in Plan {pid}")

        sql = f"UPDATE PLANS SET {attrib} = ? WHERE pid = ?"
        _ = self._database.execute1(sql, (newval_sql, pid))

        po((f"update '{attrib}' of #{pid} plan '{plan.data["name"]}' "
            f"from '{oldval}' to '{newval}'"))

        return True

    def get_plandata(self, pid: int):
        plantdata = self._plandata_dict[pid]
        return copy.deepcopy(plantdata)

    # TODO: risk to modify plan
    def get_plan(self, pid: int):
        """_summary_

        Args:
            pid (int): _description_

        Raises:
            KeyError: _description_

        Returns:
            _type_: _description_
        """
        for fid, father in self._plan_dict.items():
            if fid == pid:
                return father.data
            for cid, childdata, in father.children.items():
                if cid == pid:
                    return childdata
        raise KeyError(f"There is no {pid} in self._plan_dict")

    def add_reminder(self, pid: int, **kwargs: Unpack[ReminderDataDict]) -> int:
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
        eid = uuid.uuid4().int
        reminder = default_reminder_data()
        for key in ReminderAttr:
            if key in kwargs:
                reminder[key] = kwargs[key]

        reminders = self.get_plan(pid)["reminders"]
        reminders[eid] = reminder

        attr_sql = "reminders"
        newval_sql = serialize_reminder_collection(reminders)
        sql = f"UPDATE PLANS SET {attr_sql} = ? WHERE pid = ?"
        _ = self._database.execute1(sql, (newval_sql, pid))

        po((f"update '{attr_sql}' of #{pid} plan "
            f"add #{eid} reminder"))

        return eid

    def del_reminder(self, pid: int, eid: int):
        """_summary_

        Args:
            eid (int): _description_
        """
        reminders = self.get_plan(pid)["reminders"]
        del reminders[eid]

        attr_sql = "reminders"
        newval_sql = serialize_reminder_collection(reminders)
        sql = f"UPDATE PLANS SET {attr_sql} = ? WHERE pid = ?"
        _ = self._database.execute1(sql, (newval_sql, pid))

    def modify_reminder(self, pid: int, eid: int,
            **kwargs: Unpack[ReminderDataOptionalDict]):
        """_summary_

        Args:
            pid (int): _description_
            eid (int): _description_
            attrib (str): _description_
            newval (_type_): _description_
        """
        plan = self.get_plan(pid)
        reminders = plan["reminders"]
        reminder = reminders[eid]

        po((f"Begin to upate '{eid}' reminders of #{pid} plan '{plan["name"]}':")
            )
        for key in ReminderAttr:
            if key in kwargs:
                po(f"from '{reminder[key]}' to '{kwargs[key]}'")
                reminder[key] = kwargs[key]

        attr_sql = "reminders"
        newval_sql = serialize_reminder_collection(reminders)
        sql = f"UPDATE PLANS SET {attr_sql} = ? WHERE pid = ?"
        _ = self._database.execute1(sql, (newval_sql, pid))

        po("End to update.")

        return copy.deepcopy(reminder)

    # TODO: return copy version
    def get_reminder(self, pid: int, eid: int):
        """_summary_

        Args:
            pi (int): _description_
            eid (int): _description_

        Returns:
            _type_: _description_
        """
        plan = self.get_plan(pid)
        reminders = copy.deepcopy(plan["reminders"])
        return  reminders[eid]

    def add_record(self, **kwargs: Unpack[RecordDataDict]):
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
        record = default_record_data()
        for key in RecordAttr:
            if key in kwargs:
                record[key] = kwargs[key]

        record_sql = RecordSqlTuple(-1,
            record["pid"],
            record["name"],
            self._datetime2timestamp(record["bgn_dtime"]),
            record["duration"],
        )

        filtered_fields, field_string, placeholder_string = \
            generate_sqlite_fields(RecordSqlTuple, exclude_fields=['rid'])

        sql = f""" INSERT INTO RECORDS ({field_string})
            VALUES ({placeholder_string})"""
        po(sql)
        # Convert RecordSqlTuple to dict, then extract filtered fields in order
        record_dict_sql = record_sql._asdict()
        param_values = tuple(record_dict_sql[field] for field in filtered_fields)
        po(param_values)

        _ = self._database.execute1(sql,param_values)
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
        for recordtuple in cast(Generator[RecordSqlTuple, None, None],
                self._database.each(query_sql, tuple(query_params))):
            record: RecordDataDict = {
                "pid": pid,
                "name": recordtuple.name,
                "bgn_dtime": self._timestamp2datetime(recordtuple.bgn_dtime),
                "duration": recordtuple.duration
            }
            record_dict[recordtuple.rid] = record

        return record_dict

    def close(self):
        """_summary_

        Returns:
            _type_: _description_
        """
        return self._database.close()
