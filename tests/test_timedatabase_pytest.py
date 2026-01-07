#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import pytest
import sys
import os
import datetime
import uuid
from typing import cast

root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_path)

from pyutilities.logit import pv, po, pe
from src.time_database import TimeDatabase
"""
    uv run pytest --cov=src.time_database .\tests\test_timedatabase_pytest.py -v
"""


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
    clock = datetime.time(6, 50)
    _ = db.add_plan("Wakeup", "", -1, clock, None, None,
        1, "WK", "WD")
    clock = datetime.time(10, 50)
    _ = db.add_plan("Sleep", "", -1, clock, None, None,
        1, "WK", "WD")
    bgn_time = datetime.time(12, 30)
    end_time = datetime.time(13, 30)
    _ = db.add_plan("Nap", "", -1, None, bgn_time, end_time,
        1, "WK", "ED")
    _ = db.add_plan("Good habits")

    db.read_plans()
    pv(db.plan_dict)


def modify_plan(db: TimeDatabase, pid: int, attrib: str, destval,
        exp_ret: bool = True):
    name = cast(str, db.get_planattr(pid, "name"))
    oldval = cast(int, db.get_planattr(pid, attrib))
    po(f"want to modify '{attrib}' of #{pid} plan '{name}' from '{oldval}' to '{destval}'")
    ret = db.modify_plan(pid, attrib, destval)
    if ret:
        newval = cast(int, db.get_planattr(pid, attrib))
        assert newval == destval
        po(f"'{attrib}' of #{pid} plan '{name}' has modified from '{oldval}' to '{newval}'")
    assert ret == exp_ret


def test_modify_plan2(db: TimeDatabase):
    # db = test_add_plan(opendb)
    test_add_plan(db)
    # db = opendb
    clock = datetime.time(10, 30)
    pid_brush = db.add_plan("Brush", "", -1, clock, None, None,
        1, "WK", "WD")

    newclock = datetime.time(10, 50)
    modify_plan(db, pid_brush, "clk_time", newclock)
    bgn_dtime = datetime.datetime.now()
    modify_plan(db, pid_brush, "cycbgn_dtime", bgn_dtime)
    modify_plan(db, pid_brush, "cycend_dtime",
        bgn_dtime + datetime.timedelta(hours=0.5))
    modify_plan(db, pid_brush, "name", "Brush before bedtime")
    modify_plan(db, pid_brush, "note", "(2,3)")


def test_modify_plan_fid(db: TimeDatabase):
    test_add_plan(db)
    clock = datetime.time(10, 30)
    pid_brush = db.add_plan("Brush", "", -1, clock, None, None,
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
    test_add_plan(db)
    pid_brush = db.add_plan("Brush")
    modify_plan(db, pid_brush, "every", 1)
    modify_plan(db, pid_brush, "unit", "WK")
    modify_plan(db, pid_brush, "custom", "WD")
    modify_plan(db, pid_brush, "custom", [1, 3, 5])
    cycbgn_dtime = datetime.datetime(2026, 1, 1, 17, 30)
    modify_plan(db, pid_brush, "cycbgn_dtime", cycbgn_dtime)
    cycend_dtime = datetime.datetime(2026, 2, 1, 17, 30)
    modify_plan(db, pid_brush, "cycend_dtime", cycend_dtime)
