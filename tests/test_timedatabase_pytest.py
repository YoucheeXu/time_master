#!/usr/bin/python3
# -*- coding: UTF-8 -*-
"""
    uv run pytest --cov=src.time_database .\tests\test_timedatabase_pytest.py -v
"""
import pytest
import sys
import os
import datetime
import uuid
from typing import cast

from pyutilities.logit import pv, po, pe
from src.time_database_type import IconTuple
from src.time_database_type import ReminderAttrType, ReminderValType, PlanAttrType, PlanValType
from src.time_database_type import RecordDataDict
from src.time_database import TimeDatabase


@pytest.fixture(scope="function")
def db():
    file_path = os.path.dirname(os.path.abspath(__file__))
    if getattr(sys, 'frozen', False):
        file_path = os.path.dirname(os.path.abspath(sys.executable))
    proj_path = os.path.abspath(os.path.join(file_path, ".."))

    dbfile = os.path.join(proj_path, "data", "test",
        f"calendar_{uuid.uuid4()}.db")
    db = TimeDatabase()
    if os.path.isfile(dbfile):
        os.remove(dbfile)
    _ = db.open(dbfile)
    yield db
    _ = db.close()


def test_add_plan(db: TimeDatabase):
    pid = db.add_plan("Wakeup")
    clock = datetime.time(6, 50)
    _ = db.add_reminder(pid, clock, None, None,
        1, "WK", "WD")

    pid = db.add_plan("Sleep")
    clock = datetime.time(10, 50)
    _ = db.add_reminder(pid, clock, None, None,
        1, "WK", "WD")

    pid = db.add_plan("Nap")
    begin = datetime.time(12, 30)
    end = datetime.time(13, 30)
    _ = db.add_reminder(pid, None, begin, end,
        1, "WK", "ED")

    _ = db.add_plan("Good habits")

    db.read_plans()
    pv(db.plan_dict)


def modify_plan(db: TimeDatabase, pid: int, attrib: PlanAttrType, 
        destval: PlanValType, exp_ret: bool = True):
    name = cast(str, db.get_plan(pid, "name"))
    oldval = cast(int, db.get_plan(pid, attrib))
    po((f"want to modif '{attrib}' of #{pid} plan '{name}' "
        f"from '{oldval}' to '{destval}'"))
    ret = db.modify_plan(pid, attrib, destval)
    if ret:
        newval = cast(int, db.get_plan(pid, attrib))
        assert newval == destval
        po((f"'{attrib}' of #{pid} plan '{name}' has modified "
            f"from '{oldval}' to '{newval}'"))
    assert ret == exp_ret


def modify_reminder(db: TimeDatabase, pid: int, cid: int, attrib: ReminderAttrType, 
        destval: ReminderValType, exp_ret: bool = True):
    oldval = cast(int, db.get_reminder(pid, cid, attrib))
    po((f"want to modify '{attrib}' of #{cid} 'cycle_reminder' in #{pid} plan "
        f"from '{oldval}' to '{destval}'"))
    ret = db.modify_reminder(pid, cid, attrib, destval)
    if ret:
        newval = cast(int, db.get_reminder(pid, cid, attrib))
        assert newval == destval
        po((f"'{attrib}' of #{cid} 'cycle_reminder' in #{pid} plan has "
            f"modified from '{oldval}' to '{newval}'"))
    assert ret == exp_ret


def test_modify_plan2(db: TimeDatabase):
    # db = test_add_plan(opendb)
    test_add_plan(db)
    # db = opendb
    pid_brush = db.add_plan("Brush")
    modify_plan(db, pid_brush, "name", "Brush before bedtime")
    modify_plan(db, pid_brush, "note", "(2,3)")


def test_modify_plan_fid(db: TimeDatabase):
    test_add_plan(db)
    pid_brush = db.add_plan("Brush")
    clock = datetime.time(10, 30)
    _ = db.add_reminder(pid_brush, clock, None, None,
        1, "WK", "WD")

    pid_habit = 4

    # father without children to child
    modify_plan(db, pid_brush, "fid", pid_habit)
    # cal_db.read_plans()
    pv(db.plan_dict)

    # one's child -> another's child
    desfid = pid_habit - 1
    modify_plan(db, pid_brush, "fid", desfid)
    pv(db.plan_dict)

    with pytest.raises(RuntimeError):
        # father with children to child
        modify_plan(db, desfid, "fid", 1, False)
    pv(db.plan_dict)

    # one's child -> one's child
    modify_plan(db, pid_brush, "fid", desfid, False)
    pv(db.plan_dict)

    # child -> father
    modify_plan(db, pid_brush, "fid", -1)
    pv(db.plan_dict)

    # father -> father
    modify_plan(db, pid_brush, "fid", -1, False)
    pv(db.plan_dict)

    with pytest.raises(RuntimeError):
        # father -> itself child
        modify_plan(db, pid_brush, "fid", pid_brush, False)
    pv(db.plan_dict)


def test_modify_plan_cycle(db: TimeDatabase):
    # test_add_plan(db)
    pid_brush = db.add_plan("Brush")

    cid = db.add_reminder(pid_brush)
    modify_reminder(db, cid, pid_brush, "every", 1)
    modify_reminder(db, cid, pid_brush, "unit", "WK")
    modify_reminder(db, cid, pid_brush, "custom", "WD")
    modify_reminder(db, cid, pid_brush, "custom", [1, 3, 5])
    cycbgn_dtime = datetime.datetime(2026, 1, 1, 17, 30)
    modify_reminder(db, cid, pid_brush, "cycbgn_dtime", cycbgn_dtime)
    cycend_dtime = datetime.datetime(2026, 2, 1, 17, 30)
    modify_reminder(db, cid, pid_brush, "cycend_dtime", cycend_dtime)

    clock = datetime.time(10, 30)
    cid = db.add_reminder(pid_brush, clock, None, None,
        1, "WK", "WD")
    newclock = datetime.time(10, 50)
    modify_reminder(db, pid_brush, cid, "clk_time", newclock)
    bgn_dtime = datetime.datetime.now()
    modify_reminder(db, pid_brush, cid, "cycbgn_dtime", bgn_dtime)
    modify_reminder(db, pid_brush, cid, "cycend_dtime",
        bgn_dtime + datetime.timedelta(hours=0.5))


def test_modify_plan3(db: TimeDatabase):
    test_add_plan(db)
    pid_brush = db.add_plan("Brush")
    modify_plan(db, pid_brush, "tags", ["Shopping"])
    modify_plan(db, pid_brush, "tags", [])
    icon = IconTuple(1,1)
    modify_plan(db, pid_brush, "iid", icon)
    modify_plan(db, pid_brush, "iid", None)


def add_record(db: TimeDatabase, name: str, bgn_dtime: datetime.datetime,
        pid: int = -1,
        end_dtime: datetime.datetime | None = None):
    rid = db.add_record(name, bgn_dtime, pid, end_dtime)
    record: RecordDataDict = {
        "pid": pid,
        "name": name,
        "bgn_dtime": bgn_dtime,
        "end_dtime": end_dtime
    }
    speic_day = bgn_dtime.date()
    print(f"speic_day = {speic_day}")
    records = db.get_records(speic_day)
    print(f"records = {records}")

    assert record == records[rid]


def test_add_record(db: TimeDatabase):
    test_add_plan(db)
    clock1 = datetime.datetime(2016, 1, 16, 7, 45)
    add_record(db, "Wakeup", clock1, 1)
    clock2 = datetime.datetime(2016, 1, 16, 7, 50)
    add_record(db, "Brush", clock1, 1, clock2)
