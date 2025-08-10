#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import os
import datetime
# from typing import TypedDict
# from functools import partial
# from typing import Unpack
from typing import cast, Any

from item_type import HourSqlTuple, HourDict, Hour
# from sqlite3_database import ItemTuple, Sqlite3DataBase
from time_master_gui import TimeMasterGui
from bidirectionaldict import BidirectionalDict

from pyutilities.logit import pv, po
from pyutilities.sqlite import SQLite


class TimeMasterApp:
    _dbname: str = ""
    _cascade_items: dict[int, Hour] = {}
    def __init__(self, curpath: str, xmlfile: str, dbfile: str):

        self._every_dict : BidirectionalDict[str, str] = \
            BidirectionalDict[str, str]({"P": "每", "E": "偶数", "O": "奇数"})
        self._day_dict : BidirectionalDict[str, str] = \
            BidirectionalDict[str, str]({"CD": "日", "WD": "工作日", "HD": "节假日"})
        # self._clock_dict: dict[str, str] = {**self._every_dict.backward, **self._day_dict.backward}
        self._period_dict : BidirectionalDict[str, str] = \
            BidirectionalDict[str, str]({"PD": "计划每日", "PW": "计划每周", "PM": "计划每月"})

        self._gui: TimeMasterGui = TimeMasterGui(curpath, xmlfile)

        """
        # self._gui.register_eventhandler("addItem", self._additem_callback)
        # self._gui.register_eventhandler("addItem", self.process_message)
        add_item = partial(self.process_message, "addItem")
        self._gui.register_eventhandler("addItem", add_item)
        # self._gui.register_eventhandler("getChildren", self._getsubitems_callback)
        # self._gui.register_eventhandler("getChildren", self.process_message)
        get_children = partial(self.process_message, "getChildren")
        self._gui.register_eventhandler("getChildren", get_children)
        # self._gui.register_eventhandler("record", self._record_callback)
        # self._gui.register_eventhandler("record", self.process_message)
        record = partial(self.process_message, "record")
        self._gui.register_eventhandler("record", record)
        # self._gui.register_eventhandler("modify", self._modify_callback)
        # self._gui.register_eventhandler("modify", self.process_message)
        modify = partial(self.process_message, "modify")
        self._gui.register_eventhandler("modify", modify)

        # self._gui.register_eventhandler("getItemDetail", self.process_message)
        get_itemdetail = partial(self.process_message, "getItemDetail")
        self._gui.register_eventhandler("getItemDetail", get_itemdetail)
        """

        msglst = ["addItem", "getChildren", "record", "modify", "delete", "getItemDetail"]
        self._gui.filter_message(self.process_message, 1, msglst)

        self._db: SQLite = SQLite()
        self._open_user(dbfile)

    def read_create(self):
        for item in self._db.each("SELECT * FROM ITEMS"):
            # pv(Hour)
            iid, name, ridstr, clock, schedule, sums, father = cast(HourSqlTuple, item)
            # rid = ridstr.split("_")
            # TODO: for test
            rid = ["0", ridstr]
            itemdata: HourDict = {"name": name, "rid": (int(rid[0]), int(rid[1])),
                "clock": clock, "schedule": schedule, "sums": sums, "father": father}
            if father == -1:
                hour = Hour()
                hour.data = itemdata
                self._cascade_items[iid] = hour
                # is_subitem = False
            else:
                self._cascade_items[father].children[iid] = itemdata
                # is_subitem = True
        pv(self._cascade_items)
        i = 0
        for iid, item in self._cascade_items.items():
            """
            parent = self._gui.get_control("frmHour")
            xml = self._gui.create_xml("Frame", {"text":f"frmGroup{iid}", "id":f"frmGroup{iid}"})
                 # "options":"{'borderwidth':1,'relief':'ridge'}"})
            _, group = self._gui.create_control(parent, xml, 2)
            """
            # self._gui.create_hour(group, iid, item.data["name"], item.data["rid"],
            self._gui.create_hour(iid, item.data["name"], item.data["rid"],
                self._clock_sql2app(item.data["clock"]), f"{item.data["sums"]/60}h", False)
            for sid, child in item.children.items():
                # self._gui.create_hour(group, sid, child["name"], child["rid"],
                self._gui.create_hour(sid, child["name"], child["rid"],
                    self._clock_sql2app(child["clock"]), f"{child["sums"]/60}h", True)
            """
            if i == 0:
                pady1 = 10
            else:
                pady1 = 5
            self._gui.assemble_control(group, {"layout": "pack",
                "pack":f"{{'side':'top','pady':({pady1},5),'fill':'x'}}"}, f"{'  '*(2-1)}")
            i += 1
            """

    def _new_user(self, usr: str):
        _ = self._db.open(usr)
        _ = self._db.execute('''
                PRAGMA foreign_keys = ON
            ''')
        _ = self._db.execute('''
            CREATE TABLE IF NOT EXISTS ITEMS(
              id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                rid TEXT,
                clock TEXT,
                schedule TEXT,
                sums INT,
                father INT
            )''')

        _ = self._db.execute('''
            CREATE TABLE IF NOT EXISTS RECORD(
                id INT NOT NULL REFERENCES ITEMS(id) ON UPDATE CASCADE,
                start DATE,
                end DATE  
            )''')
        _ = self._db.commit()

    def _open_user(self, usrdb: str):
        if not os.path.isfile(usrdb):
            self._new_user(usrdb)
            po(f"new user: {usrdb}")
        else:
            _ = self._db.open(usrdb)
            po(f"open user: {usrdb}")
            self.read_create()

    # def _additem_callback(self, *args, **kwargs: Unpack[HourDict]) -> int:
    def _add_item(self, name: str, rid: tuple[int, int], clock: str,
            schedule: str, father: int, sums: int = 0) -> int:
        # ridstr = f"{rid[0]}_{rid[1]}"
        # _ = self._db.execute1("""
                # INSERT INTO ITEMS (name, rid, clock, schedule, sums, father)
                    # VALUES (?, ?, ?, ?, ?, ?)""",
                # (name, ridstr, clock, schedule, sums, father)
            # )
        # iid = cast(int, self._db.get(
                # "SELECT last_insert_rowid()"
            # ))
        iid = 10

        itemdata: HourDict = {"father": father, "name": name,
                "rid": rid, "clock": clock,
                "schedule": schedule, "sums": sums}
        if father == -1:
            hour = Hour(data=itemdata, children={})
            # self._items[id_].data = itemdata
            self._cascade_items[iid] = hour
        else:
            self._cascade_items[father].children[iid] = itemdata

        # print("_additem_callback", args, kwargs)
        # pv(self._items)
        print(f"create_hour: {name}")
        return iid

    # TODO: wait to test
    def _record(self, iid: int, timecost: datetime.timedelta):
        """record duration

        Args:
            id_ (int): Hour id
            timecost (datetime.timedelta): time of the Hour cost

        Returns:
            None

        Raises: 
            None
        """
        end_py = datetime.datetime.now()
        start_py: datetime.datetime = end_py - timecost
        start_sql = self._convert_date(start_py)
        end_sql = self._convert_date(end_py)

        # _ = self._db.execute1("""
                # INSERT INTO RECORD
                    # (id, start, end)
                    # VALUES (?, ?, ?)""",
                # (iid, start_sql, end_sql)
            # )

        po(f"id = {iid}, start = {start_sql}, end = {end_sql}")

    # def _modify_callback(self, id_: int, **kwargs):
        # print(f"app._modify: {args}, {kwargs}")
        # pv(kwargs)

    def _modify(self, iid: int, attrib: str, newval: str | int):
        # sql = f"UPDATE ITEMS SET {attrib}='{newval}' WHERE id='{iid}'"
        # _ = self._db.execute1(sql)
        po(f"update {iid}'s {attrib} to {newval}")
        for fid, fitem in self._cascade_items.items():
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
        _ = self._db.execute1(sql)        

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
        # pv(appschedule[0: 4])
        i1 = self._period_dict.value_to_key(appschedule[0: 4])
        sqlschedule = f"{i1}_{appschedule[4: ]}"
        return sqlschedule

    def get_itemdetail(self, iid: int) -> HourDict:
        if iid in self._cascade_items:
            return self._cascade_items[iid].data
        else:
            for _, father in self._cascade_items.items():
                children = father.children
                if iid in children:
                    return children[iid]

    # def get_itemdetail(self, id_: int, detail: HourDict) -> HourDict:
        # if id_ in self._items:
            # detail = self._items[id_].data
            # return
        # else:
            # for _, father in self._items.items():
                # children = father.children
                # if id_ in children:
                    # detail = children[id_]
                    # return

    def process_message(self, idmsg: str, **kwargs: Any):
        match idmsg:
            case "addItem":
                name = cast(str, kwargs["name"])
                father = cast(int, kwargs["father"])
                grp, idx = cast(tuple[int, int], kwargs["rid"])
                # rid = f"{grp}_{idx}"
                clock = self._clock_app2sql(cast(str, kwargs["clock"]))
                schedule = self._schedule_app2sql(cast(str, kwargs["schedule"]))
                # print(f"new Hour: {name}, {schedule}")
                return self._add_item(name, (grp, idx), clock, schedule, father)
            case "getItemDetail":
                iid = cast(int, kwargs["id"])
                return self.get_itemdetail(iid)
            case "getChildren":
                father = cast(int, kwargs["father"])
                if father in self._cascade_items:
                    return self._cascade_items[father].children
                else:
                    return {}
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
                if iid in self._cascade_items:
                    del self._cascade_items[iid]
                else:
                    for _, father in self._cascade_items.items():
                        children = father.children
                        if iid in children:
                            del children[iid]
                            break
                pv(self._cascade_items)
                # self._delete(iid)
            case _:
                raise ValueError(f"unkown msg of {idmsg}: {kwargs}")
        return True

    def run(self):
        """
        appclock = self._clock_sql2app("P_WD_12:00")
        pv(appclock)
        sqlclock = self._clock_app2sql(appclock)
        pv(sqlclock)

        appclock = self._clock_sql2app("E_WD_12:00")
        pv(appclock)
        sqlclock = self._clock_app2sql(appclock)
        pv(sqlclock)

        appschedule = self._schedule_sql2app("PW_2h")
        pv(appschedule)
        sqlschedule = self._schedule_app2sql(appschedule)
        pv(sqlschedule)
        """

        self._gui.go()

    def close(self):
        _ = self._db.close()
