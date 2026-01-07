#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import sys
import os
import datetime
from typing import cast

root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_path)

from pyutilities.logit import pv, po, pe
from src.time_database import TimeDatabase


def test_modify_plan(db: TimeDatabase, pid: int, attrib: str, destval,
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


def main():
    file_path = os.path.dirname(os.path.abspath(__file__))
    if getattr(sys, 'frozen', False):
        file_path = os.path.dirname(os.path.abspath(sys.executable))
    proj_path = os.path.abspath(os.path.join(file_path, ".."))

    dbfile = os.path.join(proj_path, "data", "Youchee", "calendar.db")
    db = TimeDatabase()
    if os.path.isfile(dbfile):
        os.remove(dbfile)

    _ = db.open(dbfile)
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
    pid_habit = db.add_plan("Good habits")

    db.read_plans()
    pv(db.plan_dict)

    clock = datetime.time(10, 30)
    pid_brush = db.add_plan("Brush", "", -1, clock, None, None,
        1, "WK", "WD")

    db.read_plans()
    pv(db.plan_dict)

    newclock = datetime.time(10, 50)
    test_modify_plan(db, pid_brush, "clk_time", newclock)
    bgn_dtime = datetime.datetime.now()
    test_modify_plan(db, pid_brush, "cycbgn_dtime", bgn_dtime)
    test_modify_plan(db, pid_brush, "cycend_dtime",
        bgn_dtime + datetime.timedelta(hours=0.5))
    test_modify_plan(db, pid_brush, "name", "Brush before bedtime")
    test_modify_plan(db, pid_brush, "note", "(2,3)")

    # father without children to child
    test_modify_plan(db, pid_brush, "fid", pid_habit)
    # cal_db.read_plans()
    pv(db.plan_dict)

    # one's child -> another's child
    desfid = pid_habit - 1
    test_modify_plan(db, pid_brush, "fid", desfid)
    pv(db.plan_dict)

    try:
        # father with children to child
        test_modify_plan(db, desfid, "fid", 1, False)
    except RuntimeError as e:
        pv(e)
    pv(db.plan_dict)

    # one's child -> one's child
    test_modify_plan(db, pid_brush, "fid", desfid, False)
    pv(db.plan_dict)

    # child -> father
    test_modify_plan(db, pid_brush, "fid", -1)
    pv(db.plan_dict)

    # father -> father
    test_modify_plan(db, pid_brush, "fid", -1, False)
    pv(db.plan_dict)


if __name__ == "__main__":
    main()
