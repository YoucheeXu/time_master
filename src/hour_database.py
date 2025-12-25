#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import datetime
import sqlite3
from typing import cast
from collections.abc import Generator

from pyutilities.logit import pv, po, pe
from pyutilities.sqlite import SQLite
from pyutilities.winbasic import Container

from bidirectionaldict import BidirectionalDict
from schedule import Schedule
from hour_type import HourSqlTuple, HourDict, Hour, HourSqlRecord, HourRecordTuple


class HourDatabase:
    """_summary_

    Attributes:
        _owner (_type_): _description_
        _hours_db (_type_): _description_
        _schedule (_type_): _description_
        _cascade_hours (dict[int, Hour]): _description_
        _hours_record (_type_): _description_
        _every_dict (_type_): _description_
        _day_dict (_type_): _description_
        _period_dict (_type_): _description_
    """
    def __init__(self, owner: Container, schedule: Schedule):
        self._owner: Container = owner
        self._schedule: Schedule = schedule
        self._hours_db: SQLite = SQLite()
        self._cascade_hours: dict[int, Hour] = {}
        self._hours_record: dict[int, list[HourRecordTuple]] = {}

        self._every_dict: BidirectionalDict[str, str] = \
            BidirectionalDict[str, str]({"P": "每", "E": "偶数", "O": "奇数"})
        self._day_dict: BidirectionalDict[str, str] = \
            BidirectionalDict[str, str]({"CD": "日", "WD": "工作日", "HD": "节假日"})
        self._period_dict: BidirectionalDict[str, str] = \
            BidirectionalDict[str, str]({"PD": "计划每日", "PW": "计划每周", "PM": "计划每月"})

    def new_hoursdb(self):
        """_summary_
        """
        _ = self._hours_db.execute('''
                PRAGMA foreign_keys = ON
            ''')
        _ = self._hours_db.execute('''
            CREATE TABLE IF NOT EXISTS ITEMS(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                rid TEXT,
                clock TEXT,
                schedule TEXT,
                sums INT,
                father INT
            )''')

        _ = self._hours_db.execute('''
            CREATE TABLE IF NOT EXISTS RECORDS(
                id INT NOT NULL REFERENCES ITEMS(id) ON UPDATE CASCADE,
                start timestamp,
                end timestamp  
            )''')
        _ = self._hours_db.commit()

    def open(self, dbpath: str):
        """_summary_
        Args:
            _dbpath (_type_): _description_
        """
        return self._hours_db.open(dbpath, sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)

    def readcreate_hours(self):
        """_summary_
        """
        for hid, name, ridstr, clock, schedule, sums, fid in \
                cast(Generator[HourSqlTuple, None, None],
                self._hours_db.each("SELECT * FROM ITEMS")):
            if clock:
                self._schedule.add_event(clock, name)
            rid = ridstr.split("_")
            itemdata: HourDict = {"name": name, "rid": (int(rid[0]), int(rid[1])),
                "clock": self.clock_sql2app(clock),
                "schedule": self.schedule_sql2app(schedule),
                "sums": sums, "father": fid}
            if fid == -1:
                hour = Hour()
                hour.data = itemdata
                self._cascade_hours[hid] = hour
            else:
                self._cascade_hours[fid].children[hid] = itemdata

        pv(self._cascade_hours)

        for hid, hour in self._cascade_hours.items():
            _ = self._owner.process_message("createHourCtrl", id=hid, name=hour.data["name"],
                rid=hour.data["rid"], clock= hour.data["clock"],
                sum=f"{hour.data["sums"]/60:.1f}", fid=-1)
            self._hours_record[hid] = []
            for cid, child in hour.children.items():
                _ = self._owner.process_message("createHourCtrl", id=cid, name=child["name"],
                    rid=child["rid"], clock= child["clock"],
                    sum=f"{child["sums"]/60:.1f}", fid=hid)
                self._hours_record[cid] = []

        for hid, strt_date, end_date in cast(Generator[HourSqlRecord, None, None],
                self._hours_db.each("SELECT * FROM RECORDS")):
            # iid, strt_date, end_date = cast(HourSqlRecord, hourecord)
            day = strt_date.date()
            delta = end_date - strt_date
            endure = int(delta.total_seconds() / 60)
            self._hours_record[hid].append(HourRecordTuple(day, endure))

        pv(self._hours_record)


    def clock_sql2app(self, sqlclock: str) ->str:
        """convert sql clock to app clock
            i1: P: Per(Every), E: Even, O: Odd
            i2: CD: Calendar day, WD: Work day, HD: Holiday day
        Args:
            sqlclock (): i1_i2_10:00

        Returns:
            str: 每日 10:00

        """
        sqlclock_list = sqlclock.split("_")
        pv(sqlclock_list)
        if len(sqlclock_list) != 3:
            return sqlclock
        i1 = self._every_dict.key_to_value(sqlclock_list[0])
        i2 = self._day_dict.key_to_value(sqlclock_list[1])
        appclock = f"{i1}{i2} {sqlclock_list[2]}"
        return appclock

    def clock_app2sql(self, appclock: str) ->str:
        """
        Args:
            i1_i2_10:00

            i1: P: Per(Every), E: Even, O: Odd
            i2: CD: Calendar day, WD: Work day, HD: Holiday day
        
        Returns:
            str: _description_
        """
        if len(appclock) < 8:
            return appclock

        if appclock[0] in self._every_dict.backward:
            # 每日 21:00
            i1 = self._every_dict.value_to_key(appclock[0])
            i2 = self._day_dict.value_to_key(appclock[1: -6])
            i3 = appclock[-5: ]
        elif appclock[0: 2] in self._every_dict.backward:
            # 偶数工作日 21:00
            i1 = self._every_dict.value_to_key(appclock[0: 2])
            i2 = self._day_dict.value_to_key(appclock[2: -6])
            i3 = appclock[-5: ]
        else:
            # 工作日 21:00
            i1 = "P"
            # pv(appclock[0: 3])
            i2 = self._day_dict.value_to_key(appclock[0: 3])
            i3 = appclock[-5: ]

        sqlclock = f"{i1}_{i2}_{i3}"
        return sqlclock

    def schedule_sql2app(self, sqlschedule: str) -> str:
        """
        Args:
            i1_30m

            i1: PD: Per(Every) Day, PW: Per(Every) Week, PM: Per(Every) Month
        
        Returns:
            str: _description_
        """
        sqlschedule_list = sqlschedule.split("_")
        if len(sqlschedule_list) < 2:
            return sqlschedule
        i1 = self._period_dict.key_to_value(sqlschedule_list[0])
        appschedule = f"{i1}{sqlschedule_list[1]}"
        return appschedule

    def schedule_app2sql(self, appschedule: str) -> str:
        """
        Args:
            i1_30m

            i1: PD: Per(Every) Day, PW: Per(Every) Week, PM: Per(Every) Month
        return:
            str: _description_
        """
        if len(appschedule) <= 3:
            return appschedule
        i1 = self._period_dict.value_to_key(appschedule[0: 4])
        sqlschedule = f"{i1}_{appschedule[4: ]}"
        return sqlschedule

    def add_hour(self, name: str, rid: tuple[int, int], clock: str,
            schedule: str, father: int, sums: int = 0) -> int:
        """_summary_

        Args:
            name (str): _description_
            rid (tuple[int, int]): _description_
            clock (str): _description_
            schedule (str): _description_
            father (int): _description_
            sums (int, optional): _description_. Defaults to 0.

        Raises:
            RuntimeError: _description_

        Returns:
            int: _description_
        """
        ridstr = f"{rid[0]}_{rid[1]}"
        _ = self._hours_db.execute1("""
                INSERT INTO ITEMS (name, rid, clock, schedule, sums, father)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                (name, ridstr, clock, schedule, sums, father)
            )
        data = self._hours_db.get(
                "SELECT last_insert_rowid()"
            )
        if data is not None:
            iid = cast(int, data[0])
        else:
            raise RuntimeError("no last_insert_rowid")

        itemdata: HourDict = {"father": father, "name": name,
                "rid": rid, "clock": clock,
                "schedule": schedule, "sums": sums}
        if father == -1:
            item = Hour(data=itemdata, children={})
            self._cascade_hours[iid] = item
        else:
            self._cascade_hours[father].children[iid] = itemdata

        print(f"create_item: {name}")
        if clock:
            # self.set_alarm(iid, name, clock)
            self._schedule.add_event(clock, name)
            self._schedule.event_to_schedule()
        return iid

    def delete_hours(self):
        """_summary_
        """
        for iid in self._cascade_hours.keys():
            _ = self._owner.process_message("DeleteFatherCtrl", id=iid)
        self._cascade_hours.clear()

    def record_hour(self, iid: int, strt: datetime.datetime, end: datetime.datetime):
        """record duration

        Args:
            iid (int): item id
            strt (): time of start
            end (): time of end

        Returns:
            None
        """
        _ = self._hours_db.execute1("""
                INSERT INTO 'RECORDS'
                    ('id', 'start', 'end')
                    VALUES (?, ?, ?)""",
                (iid, strt, end)
            )
        po(f"id = {iid}, start = {strt}, end = {end}")

        timecost = end - strt
        endure = int(timecost.total_seconds() / 60)
        sums = cast(int, self.get_hourattrib(iid, "sums")) + endure
        self.modify_hourattr(iid, "sums", sums)

    def modify_hourattr(self, iid: int, attrib: str, newval: str | int):
        """_summary_

        Args:
            iid (int): _description_
            attrib (str): _description_
            newval (str | int): _description_
        """
        sql = f"UPDATE ITEMS SET {attrib}='{newval}' WHERE id='{iid}'"
        _ = self._hours_db.execute1(sql)
        po(f"update hour {iid}'s {attrib} to {newval}")
        for fid, fitem in self._cascade_hours.items():
            if fid == iid:
                fitem.data[attrib] = newval
                return
            for sid, sitem, in fitem.children.items():
                if sid == iid:
                    sitem[attrib] = newval
                    return

    # TODO: do we need to delete corresponding records?
    def del_hour(self, hid: int):
        """_summary_

        Args:
            iid (int): _description_
        """

        if hid in self._cascade_hours:
            del self._cascade_hours[hid]
        else:
            for _, father in self._cascade_hours.items():
                children = father.children
                if hid in children:
                    del children[hid]
                    break
        pv(self._cascade_hours)

        sql = f"DELETE FROM ITEMS WHERE id='{hid}'"
        pv(sql)
        _ = self._hours_db.execute1(sql)

    def get_hourdetail(self, hid: int, detail: HourDict):
        """_summary_

        Args:
            hid (int): _description_
            detail (HourDict): _description_

        Raises:
            KeyError: _description_
        """
        # detail: HourDict = {"name": "", "rid": (0, 0), "clock": "", "schedule": "",
            # "sums": 0, "father": -1}
        if hid in self._cascade_hours:
            # return self._cascade_hours[iid].data
            data = self._cascade_hours[hid].data
            detail["name"] = data["name"]
            detail["rid"] = data["rid"]
            detail["clock"] = data["clock"]
            detail["schedule"] = data["schedule"]
            detail["sums"] = data["sums"]
            detail["father"] = data["father"]
            # detail = self._cascade_hours[iid].data.copy()
            return
        else:
            for _, father in self._cascade_hours.items():
                children = father.children
                if hid in children:
                    # return children[iid]
                    data = children[hid]
                    detail["name"] = data["name"]
                    detail["rid"] = data["rid"]
                    detail["clock"] = data["clock"]
                    detail["schedule"] = data["schedule"]
                    detail["sums"] = data["sums"]
                    detail["father"] = data["father"]
                    # detail = {**children[iid]}
                    # detail = children[iid].copy()
                    return
        raise KeyError(f"no item: {hid}")

    def get_hourattrib(self, hid: int, attrib: str):
        """_summary_

        Args:
            hid (int): _description_
            attrib (str): _description_

        Raises:
            KeyError: _description_

        Returns:
            _type_: _description_
        """
        # detail = self.get_hourdetail(hid)
        detail: HourDict = {"name": "", "rid": (0, 0), "clock": "", "schedule": "",
                        "sums": 0, "father": -1}
        self.get_hourdetail(hid, detail)
        if attrib not in detail:
            raise KeyError(f"no attrib: {attrib}")
        return detail.get(attrib)

    def get_hourstartdate(self, iid: int):
        """_summary_

        Args:
            iid (int): _description_

        Returns:
            _type_: _description_
        """
        first_date = ""
        sql = "SELECT * FROM RECORDS ORDER BY end ASC"
        for iid_record, _, end_date in cast(Generator[HourSqlRecord, None, None],
                self._hours_db.each(sql)):
            # iid_record, _, end_date = cast(HourSqlRecord, hourecord)
            if iid == iid_record and not first_date:
                first_date = end_date.date()
        return first_date

    def get_hourtotaldays(self, iid: int):
        """_summary_

        Args:
            iid (int): _description_

        Returns:
            _type_: _description_
        """
        total_days = 0
        last_date = datetime.datetime.strptime("1900-01-01", "%Y-%m-%d")
        sql = "SELECT * FROM RECORDS ORDER BY end ASC"
        for iid_record, _, end_date in cast(Generator[HourSqlRecord, None, None],
                self._hours_db.each(sql)):
            if iid == iid_record:
                if end_date.date() != last_date.date():
                    total_days += 1
                    last_date = end_date
        return total_days

    def get_hourseveryweek(self, iid: int):
        """_summary_

        Args:
            iid (int): _description_

        Returns:
            _type_: _description_
        """
        is_firstsave = False
        first_date = datetime.datetime.today()
        last_date = datetime.datetime.today()
        hours = 0.0
        sql = f"SELECT * FROM RECORDS WHERE id={iid} ORDER BY end ASC"
        # for hourecord in self._hours_db.each(sql):
        for _, strt_date, end_date in cast(Generator[HourSqlRecord, None, None],
                self._hours_db.each(sql)):
            # _, strt_date, end_date = cast(HourSqlRecord, hourecord)
            # if iid == iid_record:
            if not is_firstsave:
                first_date = end_date
                is_firstsave = True
            last_date = end_date
            delta = end_date - strt_date
            hours += delta.total_seconds() / 3600.0
        if hours > 0.08:
            endure_days = (last_date - first_date).days
            if endure_days != 0:
                hours = hours / endure_days * 7
        return hours

    def get_hourslast7days(self, iid: int):
        """_summary_

        Args:
            iid (int): _description_

        Returns:
            _type_: _description_
        """
        hours = 0.0
        # today = datetime.datetime.today()
        # last7day = today + datetime.timedelta(days=-7)
        # sql = f"SELECT * FROM RECORDS WHERE end >= datetime({last7day})"
        sql = f"SELECT * FROM RECORDS WHERE end>=date('now', '-7 days') AND id={iid}"
        # for hourecord in self._hours_db.each(sql):
        for _, strt_date, end_date in cast(Generator[HourSqlRecord, None, None],
                self._hours_db.each(sql)):
            # _, strt_date, end_date = cast(HourSqlRecord, hourecord)
            # if iid == iid_record:
            delta = end_date - strt_date
            hours += delta.total_seconds() / 3600.0
        return hours

    def get_hours2milestone(self, iid: int):
        """_summary_

        Args:
            iid (int): _description_

        Returns:
            _type_: _description_
        """
        return "∞"

    def get_hoursbyday(self, iid: int, day: datetime.date):
        """_summary_

        Args:
            iid (int): _description_
            day (datetime.date): _description_

        Returns:
            _type_: _description_
        """
        hours = 0.0
        # sql = f"SELECT * FROM RECORDS WHERE strftime('%F',end)=strftime('%F',{day}) AND id={iid}"
        sql = f"SELECT * FROM RECORDS WHERE id={iid}"
        # for hourecord in self._hours_db.each(sql):
        for  _, strt_date, end_date in cast(Generator[HourSqlRecord, None, None],
                self._hours_db.each(sql)):
            # _, strt_date, end_date = cast(HourSqlRecord, hourecord)
            if end_date.date() == day:
                delta = end_date - strt_date
                hours += delta.total_seconds() / 3600.0
        return hours

    def get_hoursbyweek(self, iid: int, week: int):
        """_summary_

        Args:
            iid (int): _description_
            week (int): _description_

        Returns:
            _type_: _description_
        """
        hours = 0.0
        # sql = f"SELECT * FROM RECORDS WHERE strftime('%W',end)={week} AND id={iid}"
        sql = f"SELECT * FROM RECORDS WHERE id={iid}"
        # for hourecord in self._hours_db.each(sql):
        for _, strt_date, end_date in cast(Generator[HourSqlRecord, None, None],
                self._hours_db.each(sql)):
            # _, strt_date, end_date = cast(HourSqlRecord, hourecord)
            if end_date.isocalendar()[1] == week:
                delta = end_date - strt_date
                hours += delta.total_seconds() / 3600.0
        return hours

    def get_hoursbymonth(self, iid: int, month: int):
        """_summary_

        Args:
            iid (int): _description_
            month (int): _description_

        Returns:
            _type_: _description_
        """
        hours = 0.0
        # sql = f"SELECT * FROM RECORDS WHERE strftime('%m',end)={month} AND id={iid}"
        sql = f"SELECT * FROM RECORDS WHERE id={iid}"
        # for hourecord in self._hours_db.each(sql):
        for _, strt_date, end_date in cast(Generator[HourSqlRecord, None, None],
                self._hours_db.each(sql)):
            # _, strt_date, end_date = cast(HourSqlRecord, hourecord)
            if end_date.month == month:
                delta = end_date - strt_date
                hours += delta.total_seconds() / 3600.0
        return hours

    def get_hoursbyyear(self, iid: int, year: int):
        """_summary_

        Args:
            iid (int): _description_
            year (int): _description_

        Returns:
            _type_: _description_
        """
        hours = 0.0
        # sql = f"SELECT * FROM RECORDS WHERE strftime('%Y',end)={year} AND id={iid}"
        sql = f"SELECT * FROM RECORDS WHERE id={iid}"
        # for hourecord in self._hours_db.each(sql):
        for _, strt_date, end_date in cast(Generator[HourSqlRecord, None, None],
                self._hours_db.each(sql)):
            # _, strt_date, end_date = cast(HourSqlRecord, hourecord)
            if end_date.year == year:
                delta = end_date - strt_date
                hours += delta.total_seconds() / 3600.0
        return hours

    def get_children(self, fid: int):
        if fid in self._cascade_hours:
            return self._cascade_hours[fid].children
        else:
            return cast(dict[int, HourDict], {})

    def close(self):
        return self._hours_db.close()
