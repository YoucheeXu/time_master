#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import os
# import asyncio
import datetime
from threading import Thread
from typing import cast

from pyutilities.logit import pv, po

from bidirectionaldict import BidirectionalDict
from schedule import Schedule
from time_master_gui import TimeMasterGui
from hour_type import HourDict
from hour_database import HourDatabase


class TimeMasterApp:
    """_summary_

    Attributes:
        _every_dict (_type_): _description_
        _day_dict (_type_): _description_
        _period_dict (_type_): _description_
        _gui (_type_): _description_
        _schedule (_type_): _description_

    Raises:
        RuntimeError: _description_
        KeyError: _description_
        KeyError: _description_
        ValueError: _description_
        ValueError: _description_
    """
    def __init__(self, curpath: str, xmlfile: str):
        """_summary_

        Args:
            curpath (str): _description_
            xmlfile (str): _description_
        """
        self._every_dict: BidirectionalDict[str, str] = \
            BidirectionalDict[str, str]({"P": "每", "E": "偶数", "O": "奇数"})
        self._day_dict: BidirectionalDict[str, str] = \
            BidirectionalDict[str, str]({"CD": "日", "WD": "工作日", "HD": "节假日"})
        self._period_dict: BidirectionalDict[str, str] = \
            BidirectionalDict[str, str]({"PD": "计划每日", "PW": "计划每周", "PM": "计划每月"})

        self._gui: TimeMasterGui = TimeMasterGui(curpath, xmlfile)

        msglst = ["OpenOrNewUser",
            "AddHour", "GetHourDetail", "getChildren", "RecordHour", "ModifyHourAttr", "DelHour",
            "GetHourStartDate", "GetHourTotalDays", "GetHoursEveryWeek",
            "GetHoursLast7Days", "GetHours2Milestone",
            "GetHoursbyDay", "GetHoursbyWeek", "GetHoursbyMonth", "GetHoursbyYear"
        ]
        self._gui.filter_message(self.process_message, 1, msglst)

        bell_path = os.path.join(curpath, "resources", "bell.mp3")
        self._schedule: Schedule = Schedule(bell_path)

        self._hours_db: HourDatabase = HourDatabase(self, self._gui, self._schedule)

    def open_user(self, usrpath: str):
        """_summary_

        Args:
            usrpath (str): _description_
        """
        hoursdbpath = os.path.join(usrpath, "hours.db")
        _ = self._hours_db.open(hoursdbpath)
        self._hours_db.delete_hours()
        if not os.path.isfile(hoursdbpath):
            self._hours_db.new_hoursdb()
        else:
            self._hours_db.readcreate_hours()

        self._schedule.event_to_schedule()

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

    def process_message(self, idmsg: str, **kwargs: object):
        match idmsg:
            case "OpenOrNewUser":
                self.close()
                usrpath = cast(str, kwargs["path"])
                self.open_user(usrpath)
            case "AddHour":
                name = cast(str, kwargs["name"])
                fid = cast(int, kwargs["father"])
                grp, idx = cast(tuple[int, int], kwargs["rid"])
                # rid = f"{grp}_{idx}"
                sqlclock = self.clock_app2sql(cast(str, kwargs["clock"]))
                schedule = self.schedule_app2sql(cast(str, kwargs["schedule"]))
                # print(f"new item: {name}, {schedule}")
                return self._hours_db.add_hour(name, (grp, idx), sqlclock, schedule, fid)
            case "GetHourDetail":
                hid = cast(int, kwargs["id"])
                detail = cast(HourDict, kwargs["detail"])
                self._hours_db.get_hourdetail(hid, detail)
            case "getChildren":
                fid = cast(int, kwargs["father"])
                return self._hours_db.get_children(fid)
            case "RecordHour":
                hid = cast(int, kwargs["id"])
                strt = cast(datetime.datetime, kwargs["strt"])
                end = cast(datetime.datetime, kwargs["end"])
                self._hours_db.record_hour(hid, strt, end)
            case "ModifyHourAttr":
                hid = cast(int, kwargs["id"])
                attrib = cast(str, kwargs["attrib"])
                val = cast(str, kwargs["val"])
                pv(val)
                match attrib:
                    case "clock":
                        sqlval = self.clock_app2sql(val)
                        name = cast(str, self._hours_db.get_hourattrib(hid, "name"))
                        # self.set_alarm(iid, name, sqlval)
                        if val:
                            self._schedule.add_event(sqlval, name)
                            self._schedule.event_to_schedule()
                    case "schedule":
                        sqlval = self.schedule_app2sql(val)
                    case "rid":
                        grp, idx = val
                        sqlval = f"{grp}_{idx}"
                    case "sum":
                        sqlval = val
                    case _:
                        raise ValueError(f"unsupport to modify {attrib}")
                pv(sqlval)
                self._hours_db.modify_hourattr(hid, attrib, sqlval)
            case "GetHourStartDate":
                hid = cast(int, kwargs["id"])
                return self._hours_db.get_hourstartdate(hid)
            case "GetHourTotalDays":
                hid = cast(int, kwargs["id"])
                return self._hours_db.get_hourtotaldays(hid)
            case "GetHoursEveryWeek":
                hid = cast(int, kwargs["id"])
                return self._hours_db.get_hourseveryweek(hid)
            case "GetHoursLast7Days":
                hid = cast(int, kwargs["id"])
                return self._hours_db.get_hourslast7days(hid)
            case "GetHours2Milestone":
                hid = cast(int, kwargs["id"])
                return self._hours_db.get_hours2milestone(hid)
            case "GetHoursbyDay":
                hid = cast(int, kwargs["id"])
                day = cast(datetime.date, kwargs["day"])
                return self._hours_db.get_hoursbyday(hid, day)
            case "GetHoursbyWeek":
                hid = cast(int, kwargs["id"])
                week = cast(int, kwargs["week"])
                return self._hours_db.get_hoursbyweek(hid, week)
            case "GetHoursbyMonth":
                hid = cast(int, kwargs["id"])
                month = cast(int, kwargs["month"])
                return self._hours_db.get_hoursbymonth(hid, month)
            case "GetHoursbyYear":
                hid = cast(int, kwargs["id"])
                year = cast(int, kwargs["year"])
                return self._hours_db.get_hoursbyyear(hid, year)
            case "DelHour":
                hid = cast(int, kwargs["id"])
                po(f"going to delete hour {hid}")
                self._hours_db.del_hour(hid)
            case _:
                raise ValueError(f"unkown msg of {idmsg}: {kwargs}")
        return True

    def run(self):
        """_summary_
        """
        # asyncio.run(self._schedule.exec_schedule())
        # self._gui.go()
        r1 = Thread(target=self._schedule.exec_schedule)
        # r2 = Thread(target=self._gui.go)
        r1.daemon = True
        r1.start()
        # r1.join(0.1)
        # r2.start()
        # r1.join()
        # r2.join()
        self._gui.go()

    def close(self):
        """_summary_
        """
        _ = self._hours_db.close()
        print("App exit!")
