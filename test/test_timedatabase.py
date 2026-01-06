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


def test_modify_plan(db: TimeDatabase, pid: int, attrib: str, destval):
    name = cast(str, db.get_planattr(pid, "name"))
    oldval = cast(int, db.get_planattr(pid, attrib))
    po(f"want to modify '{attrib}' of #{pid} plan '{name}' from '{oldval}' to '{destval}'")
    db.modify_plan(pid, attrib, destval)
    newval = cast(int, db.get_planattr(pid, attrib))
    po(f"'{attrib}' of #{pid} plan '{name}' has modified from '{oldval}' to '{newval}'")
    assert newval == destval

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
    plan_dict = db.plan_dict
    pv(plan_dict)

    clock = datetime.time(10, 30)
    pid_brush = db.add_plan("Brush", "", -1, clock, None, None,
        1, "WK", "WD")

    db.read_plans()
    plan_dict = db.plan_dict
    pv(plan_dict)

    newclock = datetime.time(10, 50)
    test_modify_plan(db, pid_brush, "clk_time", newclock)
    bgn_dtime = datetime.datetime.now()
    test_modify_plan(db, pid_brush, "cycbgn_dtime", bgn_dtime)
    test_modify_plan(db, pid_brush, "cycend_dtime", bgn_dtime + datetime.timedelta(hours=0.5))
    test_modify_plan(db, pid_brush, "name", "Brush before bedtime")

    # degreade from father to child
    test_modify_plan(db, pid_brush, "fid", pid_habit)
    # cal_db.read_plans()
    plan_dict = db.plan_dict
    pv(plan_dict)

    # change to another fater
    desfid = pid_habit - 1
    test_modify_plan(db, pid_brush, "fid", desfid)

    plan_dict = db.plan_dict
    pv(plan_dict)


if __name__ == "__main__":
    main()
