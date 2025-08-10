#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import os
# import asyncio
from threading import Thread
import datetime
# from typing import TypedDict
# from functools import partial
# from typing import Unpack
from typing import cast, Any

from item_type import HourRecord, HourSqlTuple, HourDict, Hour
from time_master_gui import TimeMasterGui
from bidirectionaldict import BidirectionalDict
from schedule import Schedule

from pyutilities.logit import pv, po
from pyutilities.sqlite import SQLite


class TimeMasterApp:
    _cascade_hours: dict[int, Hour] = {}
    # _alarm_dict: dict[int, tuple[str, str]] = {}
    def __init__(self, curpath: str, xmlfile: str, usrpath: str):

        self._every_dict: BidirectionalDict[str, str] = \
            BidirectionalDict[str, str]({"P": "每", "E": "偶数", "O": "奇数"})
        self._day_dict: BidirectionalDict[str, str] = \
            BidirectionalDict[str, str]({"CD": "日", "WD": "工作日", "HD": "节假日"})
        self._period_dict: BidirectionalDict[str, str] = \
            BidirectionalDict[str, str]({"PD": "计划每日", "PW": "计划每周", "PM": "计划每月"})

        self._gui: TimeMasterGui = TimeMasterGui(curpath, xmlfile)

        msglst = ["newUser", "openUser", "addItem", "getChildren", "record", "modify", "delete",
            "GetHourDetail"]
        self._gui.filter_message(self.process_message, 1, msglst)

        bell_path = os.path.join(curpath, "resources", "bell.mp3")
        self._schedule: Schedule = Schedule(bell_path)

        self._housrs_db: SQLite = SQLite()
        hoursdbpath = os.path.join(usrpath, "hours.db")
        self._open(hoursdbpath)

    def _open(self, usrdb: str):
        if not os.path.isfile(usrdb):
            self._new_user(usrdb)
        else:
            self._open_user(usrdb)

    def readcreate_hours(self):
        for hour in self._housrs_db.each("SELECT * FROM ITEMS"):
            iid, name, ridstr, clock, schedule, sums, father = cast(HourSqlTuple, hour)
            if clock:
                self._schedule.add_event(clock, name)
            if isinstance(ridstr, int):
                rid = [0, ridstr]
            else:
                rid = ridstr.split("_")
            itemdata: HourDict = {"name": name, "rid": (int(rid[0]), int(rid[1])),
                # "clock": clock, "schedule": schedule, "sums": sums, "father": father}
                "clock": self._clock_sql2app(clock), "schedule": self._schedule_sql2app(schedule),
                "sums": sums, "father": father}
            if father == -1:
                hour = Hour()
                hour.data = itemdata
                self._cascade_hours[iid] = hour
            else:
                self._cascade_hours[father].children[iid] = itemdata
        self._schedule.event_to_schedule()
        pv(self._cascade_hours)

        for iid, hour in self._cascade_hours.items():
            _ = self._gui.process_message("CreateHour", id=iid, item=hour.data["name"],
                rid=hour.data["rid"], clock= hour.data["clock"],
                sums=f"{hour.data["sums"]/60:.1f}h", is_subitem=False)
            for sid, child in hour.children.items():
                _ = self._gui.process_message("CreateHour", id=sid, item=child["name"],
                    rid=child["rid"], clock= child["clock"],
                    sums=f"{child["sums"]/60:.1f}h", is_subitem=True)

    def _delete_hours(self):
        for iid in self._cascade_hours.keys():
            _ = self._gui.process_message("DeleteFather", id=iid)
        self._cascade_hours.clear()      

    def _new_user(self, usr: str):
        po(f"new user: {usr}")
        self._delete_hours()
        _ = self._housrs_db.open(usr)
        _ = self._housrs_db.execute('''
                PRAGMA foreign_keys = ON
            ''')
        _ = self._housrs_db.execute('''
            CREATE TABLE IF NOT EXISTS ITEMS(
              id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                rid TEXT,
                clock TEXT,
                schedule TEXT,
                sums INT,
                father INT
            )''')

        _ = self._housrs_db.execute('''
            CREATE TABLE IF NOT EXISTS RECORD(
                id INT NOT NULL REFERENCES ITEMS(id) ON UPDATE CASCADE,
                start DATE,
                end DATE  
            )''')
        _ = self._housrs_db.commit()

    def _open_user(self, usrdb: str):
        po(f"open user: {usrdb}")
        self._delete_hours()
        _ = self._housrs_db.open(usrdb)
        self.readcreate_hours()

    def _add_hour(self, name: str, rid: tuple[int, int], clock: str,
            schedule: str, father: int, sums: int = 0) -> int:
        ridstr = f"{rid[0]}_{rid[1]}"
        _ = self._housrs_db.execute1("""
                INSERT INTO ITEMS (name, rid, clock, schedule, sums, father)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                (name, ridstr, clock, schedule, sums, father)
            )
        iid = cast(int, self._housrs_db.get(
                "SELECT last_insert_rowid()"
            ))

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

    # TODO: wait to test
    def _record(self, iid: int, timecost: datetime.timedelta):
        """record duration

        Args:
            id_ (int): item id
            timecost (datetime.timedelta): time of the item cost

        Returns:
            None

        Raises: 
            None
        """
        end_py = datetime.datetime.now()
        start_py: datetime.datetime = end_py - timecost
        start_sql = self._convert_date(start_py)
        end_sql = self._convert_date(end_py)

        _ = self._housrs_db.execute1("""
                INSERT INTO RECORD
                    (id, start, end)
                    VALUES (?, ?, ?)""",
                (iid, start_sql, end_sql)
            )

        po(f"id = {iid}, start = {start_sql}, end = {end_sql}")

    def _modify(self, iid: int, attrib: str, newval: str | int):
        sql = f"UPDATE ITEMS SET {attrib}='{newval}' WHERE id='{iid}'"
        _ = self._housrs_db.execute1(sql)
        po(f"update {iid}'s {attrib} to {newval}")
        for fid, fitem in self._cascade_hours.items():
            if fid == iid:
                fitem.data[attrib] = newval
                return
            for sid, sitem, in fitem.children.items():
                if sid == iid:
                    sitem[attrib] = newval
                    return

    # TODO: do we need to delete corresponding records?
    def _delete(self, iid: int):
        sql = f"DELETE FROM ITEMS WHERE id='{iid}'"
        pv(sql)
        _ = self._housrs_db.execute1(sql)        

    def _convert_date(self, date_py: datetime.datetime) -> str:
        date_sql = date_py.strftime('%Y-%m-%d %H:%M:%S')
        return date_sql

    def _clock_sql2app(self, sqlclock: str) ->str:
        """convert sql clock to app clock
            i1: P: Per(Every), E: Even, O: Odd
            i2: CD: Calendar day, WD: Work day, HD: Holiday day
        Args:
            sqlclock (): i1_i2_10:00

        Returns:
            str: 每日 22:00

        """
        sqlclock_list = sqlclock.split("_")
        if len(sqlclock_list) != 3:
            return sqlclock
        i1 = self._every_dict.key_to_value(sqlclock_list[0])
        i2 = self._day_dict.key_to_value(sqlclock_list[1])
        appclock = f"{i1}{i2} {sqlclock_list[2]}"
        return appclock

    def _clock_app2sql(self, appclock: str) ->str:
        """
            i1_i2_10:00

            i1: P: Per(Every), E: Even, O: Odd
            i2: CD: Calendar day, WD: Work day, HD: Holiday day
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

    def _schedule_sql2app(self, sqlschedule: str) -> str:
        """
            i1_30m

            i1: PD: Per(Every) Day, PW: Per(Every) Week, PM: Per(Every) Month
        """
        sqlschedule_list = sqlschedule.split("_")
        if len(sqlschedule_list) < 2:
            return sqlschedule
        i1 = self._period_dict.key_to_value(sqlschedule_list[0])
        appschedule = f"{i1}{sqlschedule_list[1]}"
        return appschedule

    def _schedule_app2sql(self, appschedule: str) -> str:
        """
            i1_30m

            i1: PD: Per(Every) Day, PW: Per(Every) Week, PM: Per(Every) Month
        """
        if len(appschedule) <= 3:
            return appschedule
        i1 = self._period_dict.value_to_key(appschedule[0: 4])
        sqlschedule = f"{i1}_{appschedule[4: ]}"
        return sqlschedule

    def get_hourdetail(self, iid: int) -> HourDict:
        if iid in self._cascade_hours:
            return self._cascade_hours[iid].data
        else:
            for _, father in self._cascade_hours.items():
                children = father.children
                if iid in children:
                    return children[iid]
        raise KeyError(f"no item: {iid}")

    def get_hourattrib(self, iid: int, attrib: str):
        detail = self.get_hourdetail(iid)
        return detail[attrib]

    # def set_alarm(self, iid: int, name: str, clock: str):
        # self._alarm_dict[iid] = name, clock

    def process_message(self, idmsg: str, **kwargs: Any):
        match idmsg:
            case "newUser":
                self.close()
                usrdb = cast(str, kwargs["db"])
                self._new_user(usrdb)
            case "openUser":
                self.close()
                usrdb = cast(str, kwargs["db"])
                self._open_user(usrdb)
            case "addItem":
                name = cast(str, kwargs["name"])
                father = cast(int, kwargs["father"])
                grp, idx = cast(tuple[int, int], kwargs["rid"])
                # rid = f"{grp}_{idx}"
                sqlclock = self._clock_app2sql(cast(str, kwargs["clock"]))
                schedule = self._schedule_app2sql(cast(str, kwargs["schedule"]))
                # print(f"new item: {name}, {schedule}")
                return self._add_hour(name, (grp, idx), sqlclock, schedule, father)
            case "GetHourDetail":
                iid = cast(int, kwargs["id"])
                return self.get_hourdetail(iid)
            case "getChildren":
                father = cast(int, kwargs["father"])
                if father in self._cascade_hours:
                    return self._cascade_hours[father].children
                else:
                    return cast(dict[str, HourDict], {})
            case "record":
                iid = cast(int, kwargs["id"])
                timecost = cast(datetime.timedelta, kwargs["timecost"])
                self._record(iid, timecost)
            case "modify":
                iid = cast(int, kwargs["id"])
                attrib = cast(str, kwargs["attrib"])
                appval = cast(str, kwargs["val"])
                pv(appval)
                match attrib:
                    case "clock":
                        sqlval = self._clock_app2sql(appval)
                        name = cast(str, self.get_hourattrib(iid, "name"))
                        # self.set_alarm(iid, name, sqlval)
                        self._schedule.add_event(sqlval, name)
                        self._schedule.event_to_schedule()
                    case "schedule":
                        sqlval = self._schedule_app2sql(appval)
                    case "rid":
                        grp, idx = appval
                        sqlval = f"{grp}_{idx}"
                    case "sums":
                        sqlval = appval
                    case _:
                        raise ValueError(f"unsupport to modify {attrib}")
                pv(sqlval)
                self._modify(iid, attrib, sqlval)
            case "delete":
                iid = cast(int, kwargs["id"])
                po(f"going to delete {iid}")
                if iid in self._cascade_hours:
                    del self._cascade_hours[iid]
                else:
                    for _, father in self._cascade_hours.items():
                        children = father.children
                        if iid in children:
                            del children[iid]
                            break
                pv(self._cascade_hours)
                self._delete(iid)
            case _:
                raise ValueError(f"unkown msg of {idmsg}: {kwargs}")
        return True

    def run(self):
        # asyncio.run(self._schedule.exec_schedule())
        # self._gui.go()
        r1 = Thread(target=self._schedule.exec_schedule)
        # r2 = Thread(target=self._gui.go)
        r1.start()
        # r2.start()
        # r1.join()
        # r2.join()
        self._gui.go()

    def close(self):
        _ = self._housrs_db.close()
