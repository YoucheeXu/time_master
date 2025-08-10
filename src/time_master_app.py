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

from item_type import HourSqlTuple, HourDict, Hour, HourSqlRecord, HourRecordTuple
from item_type import MedSqlTuple, MedDict, MedSqlRecord, MedSqlUsage
from time_master_gui import TimeMasterGui
from bidirectionaldict import BidirectionalDict
from schedule import Schedule

from pyutilities.logit import pv, po
from pyutilities.sqlite import SQLite


class TimeMasterApp:
    _cascade_hours: dict[int, Hour] = {}
    _hours_record: dict[int, HourRecordTuple] = {}
    _meds_store: dict[int, MedDict] = {}
    _meds_record: dict[int, dict[int, float]] = {}    # {dict, {timestampe, dose}}
    # _meds_usage: dict[int, MedUsageDict] = {}
    def __init__(self, curpath: str, xmlfile: str):

        self._every_dict: BidirectionalDict[str, str] = \
            BidirectionalDict[str, str]({"P": "每", "E": "偶数", "O": "奇数"})
        self._day_dict: BidirectionalDict[str, str] = \
            BidirectionalDict[str, str]({"CD": "日", "WD": "工作日", "HD": "节假日"})
        self._period_dict: BidirectionalDict[str, str] = \
            BidirectionalDict[str, str]({"PD": "计划每日", "PW": "计划每周", "PM": "计划每月"})

        self._gui: TimeMasterGui = TimeMasterGui(curpath, xmlfile)

        msglst = ["OpenOrNewUser",
            "addItem", "GetHourDetail", "getChildren", "record", "ModifyHourAttr", "DelHour",
            "AddMed", "DelMed", "GetMedDetail", "ModifyMedAttr", "RecordMedUse"]
        self._gui.filter_message(self.process_message, 1, msglst)

        bell_path = os.path.join(curpath, "resources", "bell.mp3")
        self._schedule: Schedule = Schedule(bell_path)

        self._hours_db: SQLite = SQLite()
        self._medicine_db: SQLite = SQLite()

    def readcreate_hours(self):
        for hour in self._hours_db.each("SELECT * FROM ITEMS"):
            iid, name, ridstr, clock, schedule, sums, father = cast(HourSqlTuple, hour)
            if clock:
                self._schedule.add_event(clock, name)
            rid = ridstr.split("_")
            itemdata: HourDict = {"name": name, "rid": (int(rid[0]), int(rid[1])),
                "clock": self._clock_sql2app(clock), "schedule": self._schedule_sql2app(schedule),
                "sums": sums, "father": father}
            if father == -1:
                hour = Hour()
                hour.data = itemdata
                self._cascade_hours[iid] = hour
            else:
                self._cascade_hours[father].children[iid] = itemdata

        pv(self._cascade_hours)

        for iid, hour in self._cascade_hours.items():
            _ = self._gui.process_message("CreateHour", id=iid, item=hour.data["name"],
                rid=hour.data["rid"], clock= hour.data["clock"],
                sums=f"{hour.data["sums"]/60:.1f}", is_subitem=False)
            for sid, child in hour.children.items():
                _ = self._gui.process_message("CreateHour", id=sid, item=child["name"],
                    rid=child["rid"], clock= child["clock"],
                    sums=f"{child["sums"]/60:.1f}", is_subitem=True)

    def _delete_hours(self):
        for iid in self._cascade_hours.keys():
            _ = self._gui.process_message("DeleteFather", id=iid)
        self._cascade_hours.clear()

    def _new_hoursdb(self, hoursdb: str):
        po(f"new hours: {hoursdb}")
        self._delete_hours()
        _ = self._hours_db.open(hoursdb)
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
                start TIMESTAMP,
                end TIMESTAMP  
            )''')
        _ = self._hours_db.commit()

    def _open_hoursdb(self, hoursdb: str):
        po(f"open hours: {hoursdb}")
        self._delete_hours()
        _ = self._hours_db.open(hoursdb)
        self.readcreate_hours()

    def _new_medsdb(self, medsdb: str):
        po(f"new meds: {medsdb}")
        self._delete_meds()
        _ = self._medicine_db.open(medsdb)
        _ = self._medicine_db.execute('''
                PRAGMA foreign_keys = ON
            ''')
        _ = self._medicine_db.execute('''
            CREATE TABLE IF NOT EXISTS MEDICINES(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                rid TEXT,
                due DATE,
                sums REAL,
                unit TEXT
            )''')
        _ = self._medicine_db.execute('''
            CREATE TABLE IF NOT EXISTS USAGE(
                id INT NOT NULL REFERENCES MEDICINES(id) ON UPDATE CASCADE,
                schedule TEXT,
                strt DATE,
                end DATE
            )''')
        _ = self._medicine_db.execute('''
            CREATE TABLE IF NOT EXISTS RECORDS(
                id INT NOT NULL REFERENCES MEDICINES(id) ON UPDATE CASCADE,
                take TIMESTAMP,
                dose REAL
            )''')
        _ = self._medicine_db.commit()

    def readcreate_meds(self):
        for med in self._medicine_db.each("SELECT * FROM MEDICINES"):
            iid, name, ridstr, due, sums, unit = cast(MedSqlTuple, med)
            rid = ridstr.split("_")
            meddata: MedDict = {"name": name, "rid": (int(rid[0]), int(rid[1])),
                "due": due, "sums": sums, "unit": unit}
            self._meds_store[iid] = meddata

        meddata: MedDict = {"name": "创口贴", "rid": (0,0),
                "due": datetime.date(2025, 8, 15), "sums": 200, "unit": "片"}
        self._meds_store[1] = meddata

        meddata: MedDict = {"name": "芬必得", "rid": (0,1),
                "due": datetime.date(2025, 8, 15), "sums":200 , "unit": "个"}
        self._meds_store[2] = meddata

        meddata: MedDict = {"name": "碘伏", "rid": (0,2),
                "due": datetime.date(2025, 8, 15), "sums": 200, "unit": "支"}
        self._meds_store[3] = meddata

        pv(self._meds_store)

        for iid, med in self._meds_store.items():
            _ = self._gui.process_message("CreateMedStor", id=iid, item=med["name"],
                rid=med["rid"], due= med["due"], sums=med["sums"],
                unit=med["unit"])

    def _delete_meds(self):
        self._meds_store.clear()

    def _open_medsdb(self, medsdb: str):
        po(f"open meds: {medsdb}")
        self._delete_meds()
        _ = self._medicine_db.open(medsdb)
        self.readcreate_meds()

    def open_user(self, usrpath: str):
        hoursdbpath = os.path.join(usrpath, "hours.db")
        if not os.path.isfile(hoursdbpath):
            self._new_hoursdb(hoursdbpath)
        else:
            self._open_hoursdb(hoursdbpath)

        medicinedbpath = os.path.join(usrpath, "meds.db")
        if not os.path.isfile(medicinedbpath):
            self._new_medsdb(medicinedbpath)
        else:
            self._open_medsdb(medicinedbpath)

        self._schedule.event_to_schedule()

    def _add_hour(self, name: str, rid: tuple[int, int], clock: str,
            schedule: str, father: int, sums: int = 0) -> int:
        ridstr = f"{rid[0]}_{rid[1]}"
        _ = self._hours_db.execute1("""
                INSERT INTO ITEMS (name, rid, clock, schedule, sums, father)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                (name, ridstr, clock, schedule, sums, father)
            )
        iid = cast(int, self._hours_db.get(
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
    def _record_hour(self, iid: int, timecost: datetime.timedelta):
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

        _ = self._hours_db.execute1("""
                INSERT INTO RECORDS
                    (id, start, end)
                    VALUES (?, ?, ?)""",
                (iid, start_sql, end_sql)
            )

        po(f"id = {iid}, start = {start_sql}, end = {end_sql}")

    def _modify_hourattr(self, iid: int, attrib: str, newval: str | int):
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
    def _del_hour(self, iid: int):
        sql = f"DELETE FROM ITEMS WHERE id='{iid}'"
        pv(sql)
        _ = self._hours_db.execute1(sql)        

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
        return detail.get(attrib, None)

    def _add_med(self, name: str, rid: tuple[int, int], due: datetime.date,
            sums: float, unit: str) -> int:
        ridstr = f"{rid[0]}_{rid[1]}"
        _ = self._medicine_db.execute1("""
                INSERT INTO MEDICINES (name, rid, due, sums, unit)
                    VALUES (?, ?, ?, ?, ?)""",
                (name, ridstr, due, sums, unit)
            )
        iid = cast(int, self._medicine_db.get(
                "SELECT last_insert_rowid()"
            ))

        meddata: MedDict = {"name": name, "rid": (int(rid[0]), int(rid[1])),
                "due": due, "sums": sums, "unit": unit}

        self._meds_store[iid] = meddata
        print(f"create_item: {name}")
        if due:
            self._schedule.add_event(due, name)
            self._schedule.event_to_schedule()
        return iid

    # TODO: do we need to delete corresponding records?
    def _del_med(self, iid: int):
        sql = f"DELETE FROM MEDICINES WHERE id='{iid}'"
        pv(sql)
        _ = self._medicine_db.execute1(sql) 

    # TODO: wait to test
    def _record_meduse(self, iid: int, time: datetime.datetime, dose: float):
        """record med usage

        Args:
            iid (): item id
            time (): time of taking medicine
            dose (): amount of taking medicine

        Returns:
            None

        """
        self._meds_store[iid]["sums"] -= dose

        _ = self._hours_db.execute1("""
                INSERT INTO RECORDS
                    (id, take, dose)
                    VALUES (?, ?, ?)""",
                (iid, time, dose)
            )

        po(f"med id = {iid}, time = {time}, dose = {dose}, \
            rest={self._meds_store[iid]["sums"]}")

    def _modify_medattr(self, iid: int, attrib: str, newval: str | int):
        sql = f"UPDATE MEDICINES SET {attrib}='{newval}' WHERE id='{iid}'"
        _ = self._medicine_db.execute1(sql)
        po(f"update med {iid}'s {attrib} to {newval}")
        self._meds_store[iid][attrib] = newval

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

    def process_message(self, idmsg: str, **kwargs: Any):
        match idmsg:
            case "OpenOrNewUser":
                self.close()
                usrpath = cast(str, kwargs["path"])
                self.open_user(usrpath)
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
                self._record_hour(iid, timecost)
            case "ModifyHourAttr":
                iid = cast(int, kwargs["id"])
                attrib = cast(str, kwargs["attrib"])
                val = cast(str, kwargs["val"])
                pv(val)
                match attrib:
                    case "clock":
                        sqlval = self._clock_app2sql(val)
                        name = cast(str, self.get_hourattrib(iid, "name"))
                        # self.set_alarm(iid, name, sqlval)
                        self._schedule.add_event(sqlval, name)
                        self._schedule.event_to_schedule()
                    case "schedule":
                        sqlval = self._schedule_app2sql(val)
                    case "rid":
                        grp, idx = val
                        sqlval = f"{grp}_{idx}"
                    case "sums":
                        sqlval = val
                    case _:
                        raise ValueError(f"unsupport to modify {attrib}")
                pv(sqlval)
                self._modify_hourattr(iid, attrib, sqlval)
            case "DelHour":
                iid = cast(int, kwargs["id"])
                po(f"going to delete {iid} hour")
                if iid in self._cascade_hours:
                    del self._cascade_hours[iid]
                else:
                    for _, father in self._cascade_hours.items():
                        children = father.children
                        if iid in children:
                            del children[iid]
                            break
                pv(self._cascade_hours)
                self._del_hour(iid)
            case "AddMed":
                name = cast(str, kwargs["name"])
                grp, idx = cast(tuple[int, int], kwargs["rid"])
                due = cast(datetime.date, kwargs["due"])
                sums = cast(float, kwargs["sums"])
                unit = cast(str, kwargs["unit"])
                return self._add_med(name, (grp, idx), due, sums, unit)
            case "DelMed":
                iid = cast(int, kwargs["id"])
                po(f"going to delete {iid} med")
                del self._meds_store[iid]
                pv(self._meds_store)
                self._del_med(iid)
            case "GetMedDetail":
                iid = cast(int, kwargs["id"])
                return self._meds_store[iid]
            case "RecordMedUse":
                iid = cast(int, kwargs["id"])
                time = cast(datetime.datetime, kwargs["time"])
                dose = cast(int, kwargs["dose"])
                self._record_meduse(iid, time, dose)
            case "ModifyMedAttr":
                iid = cast(int, kwargs["id"])
                attrib = cast(str, kwargs["attrib"])
                val = cast(str, kwargs["val"])
                pv(val)
                match attrib:
                    case "rid":
                        grp, idx = val
                        sqlval = f"{grp}_{idx}"
                    case "sums" | "due":
                        sqlval = val
                    case _:
                        raise ValueError(f"unsupport to modify {attrib}")
                pv(sqlval)
                self._modify_medattr(iid, attrib, sqlval)
            case _:
                raise ValueError(f"unkown msg of {idmsg}: {kwargs}")
        return True

    def run(self):
        # asyncio.run(self._schedule.exec_schedule())
        # self._gui.go()
        r1 = Thread(target=self._schedule.exec_schedule)
        # r2 = Thread(target=self._gui.go)
        r1.daemon = True
        r1.start()
        r1.join(0.1)
        # r2.start()
        # r1.join()
        # r2.join()
        self._gui.go()

    def close(self):
        _ = self._hours_db.close()
        _ = self._medicine_db.close()
