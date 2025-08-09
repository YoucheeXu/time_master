#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import os
import datetime
from dataclasses import dataclass, field
# from typing import TypedDict
from typing import cast, Unpack, Any

from item_type import Record, ItemTuple, ItemDict
# from sqlite3_database import ItemTuple, Sqlite3DataBase
from time_manager_gui import TimeManagerGui

from pyutilities.logit import pv, po
from pyutilities.sqlite import SQLite


@dataclass
class Item:
    # TypedDict("ItemDict",{"id": 0, "name": "", "rid": 0, "clock": "", "schedule": "", "sums": 0, "father": -1})
    data: ItemDict = field(default_factory=ItemDict)
    subitems: list[ItemDict] = field(default_factory=list)


class TimeMangerApp:
    _dbname: str = ""
    _items: dict[int, Item] = {}
    _id: int = 1
    def __init__(self, curpath: str, xmlfile, dbfile: str):
        self._gui: TimeManagerGui = TimeManagerGui(curpath, xmlfile)

        # self._gui.register_eventhandler("addItem", self._additem_callback)
        self._gui.register_eventhandler("addItem", self.process_message)
        # self._gui.register_eventhandler("getSubItems", self._getsubitems_callback)
        self._gui.register_eventhandler("getSubItems", self.process_message)
        # self._gui.register_eventhandler("record", self._record_callback)
        self._gui.register_eventhandler("record", self.process_message)
        # self._gui.register_eventhandler("modify", self._modify_callback)
        self._gui.register_eventhandler("modify", self.process_message)

        self._db: SQLite = SQLite()
        self._open_user(dbfile)

    def read_create(self):
        # items: list[ItemTuple] = 
        # pv(items)
        for item in self._db.each("SELECT * FROM ITEMS"):
            pv(item)
            id_, name, rid, clock, schedule, sums, father = cast(ItemTuple, item)
            itemdata: ItemDict = {"id": id_, "name": name, "rid": rid, "clock": clock,
                "schedule": schedule, "sums": sums, "father": father}
            if father == -1:
                item = Item()
                item.data = itemdata
                self._items[id_] = item
            else:
                self._items[father].subitems.append(itemdata)
            self._gui.create_item(id_, name, rid, clock, f"{sums / 60}h")

    def _new_user(self, usr: str):
        _ = self._db.open(usr)
        _ = self._db.execute('''
                PRAGMA foreign_keys = ON
            ''')
        _ = self._db.execute('''
            CREATE TABLE IF NOT EXISTS ITEMS(
              id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                rid INT,
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

    # def _additem_callback(self, *args, **kwargs: Unpack[ItemDict]) -> int:
    def _add_item(self, name: str, rid: int, clock: str, schedule: str, father: int, sums: int = 0) -> int:
        _ = self._db.execute1("""
                INSERT INTO ITEMS (name, rid, clock, schedule, sums, father)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                (name, rid, clock, schedule, sums, father)
            )
        id_ = self._db.get(
                "SELECT last_insert_rowid()"
            )

        # id_ = self._id

        itemdata: ItemDict = {"id": id_, "father": father, "name": name,
                "rid": rid, "clock": clock, "schedule": schedule, "sums": sums}
        if father == -1:
            item = Item(data=itemdata, subitems=[])
            # self._items[id_].data = itemdata
            self._items[id_] = item
        else:
            self._items[father].subitems.append(itemdata)

        # print("_additem_callback", args, kwargs)
        # self._id += 1
        # pv(self._items)
        print(f"create_item: {name}")
        return id_

    # def _getsubitems_callback(self, father: int, *args, **kwargs) -> int:
        # subitem_list = cast(list[ItemDict], kwargs["subitems"])
    def _get_subitems(self, father: int, subitem_list: list[ItemDict]) -> int:
        subitem_list.clear()
        if father in self._items:
            subitems = self._items[father].subitems
            subitem_list += subitems
        pv(subitem_list)
        return len(subitem_list)

    # TODO: update sums
    # def _record_callback(self, id_: int, **kwargs):
        # print(f"app._record: {args}, {kwargs}")
        # pv(kwargs)
        # id_ = cast(int, args[0])
    def _record(self, id_: int, timecost: datetime.timedelta):
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

        _ = self._db.execute1("""
                INSERT INTO RECORD
                    (id, start, end)
                    VALUES (?, ?, ?)""",
                (id_, start_sql, end_sql)
            )

        po(f"id = {id_}, start = {start_sql}, end = {end_sql}")

    # def _modify_callback(self, id_: int, **kwargs):
        # print(f"app._modify: {args}, {kwargs}")
        # pv(kwargs)
    def _modify(self, id_: int, attrib: str, newval):
        _ = self._db.execute1(
            f"UPDATE ITEMS SET {attrib}={newval} WHERE id='{id_}'"
        )
        po(f"update {id_}'s {attrib} to {newval}")

    def _convert_date(self, date_py: datetime.datetime) -> str:
        date_sql = date_py.strftime('%Y-%m-%d %H:%M:%S')
        return date_sql

    def process_message(self, id_ctrl: str, **kwargs: Any):
        match id_ctrl:
            case "addItem":
                name = cast(str, kwargs["name"])
                father = cast(int, kwargs["father"])
                rid = cast(int, kwargs["rid"])
                clock = cast(str, kwargs["clock"])
                schedule = cast(str, kwargs["schedule"])
                return self._add_item(name, rid, clock, schedule, father)
            case "getSubItems":
                father = cast(int, kwargs["father"])
                subitem_list = cast(list[ItemDict], kwargs["subitems"])
                return self._get_subitems(father, subitem_list)
            case "record":
                id_ = cast(int, kwargs["id"])
                timecost = cast(datetime.timedelta, kwargs["timecost"])
                return self._record(id_, timecost)
            case "modify":
                id_ = cast(int, kwargs["id"])
                attrib = cast(str, kwargs["attrib"])
                newval = kwargs["val"]
                return self._modify(id_, attrib, newval)
            case _:
                raise ValueError(f"unkown msg of {id_ctrl}: {kwargs}")

    def run(self):
        self._gui.go()

    def close(self):
        _ = self._db.close()

