#!/usr/bin/python3
# -*- coding: UTF-8 -*-
"""
    set PYTHONPATH=..\time_master
    uv run .\\src\\schedule.py
"""
import os
import time
import math
import datetime
from dataclasses import dataclass
# from typing import Literal

from pyutilities.logit import pv, po

from src.action_sys import ActTyp, ActionSys
from src.time_database_type import TimeUnit, DayType


@dataclass
class Event:
    name: str
    clock: datetime.time
    every: int
    unit: TimeUnit
    custom: DayType | list[int]
    cycbgn_dtime: datetime.datetime
    cycend_dtime: datetime.datetime | None = None  # None means never end
    action: ActTyp = ActTyp.NOACTION


@dataclass
class Agenda:
    """_summary_
    Attributes:
        name (str): _description_
        clock (datetime.time): _description_
        action (ActTyp): _description_, default to ActTyp.NOACTION        
    """
    name: str
    clock: datetime.time
    action: ActTyp = ActTyp.NOACTION


class Schedule:
    """_summary_

    Attributes:
        _alarm_mp3 (str): _description_
        _tolerance_sec (int): _description_, default to 30
        _today (datetime.datetime): _description_
        _event_dict (dict[str, str]): _description_
        _agenda_list (list[Agenda]): _description_
        _actionsys (ActionSys): _description_
    """
    def __init__(self, alarm_mp3: str, dripping_water_mp3: str):
        """_summary_

        Args:
            alarm_mp3 (str): _description_
            dripping_water_mp3 (str): _description_
        """
        self._alarm_mp3: str = alarm_mp3
        self._dripping_water_mp3: str = dripping_water_mp3
        self._tolerance_sec: int = 30
        self._today: datetime.datetime = datetime.datetime.today()
        self._event_dict: dict[int, Event] = {}
        self._event_dirty: bool = False
        self._today_agenda_list: list[Agenda] = []
        self._extra_agenda_list: list[Agenda] = []

        self._actionsys: ActionSys = ActionSys()

    # TODO: wait to finish
    def _is_workday(self, dt: datetime.date):
        return True

    # TODO: wait to finish
    def _is_weekend(self, dt: datetime.date):
        return True

    # TODO: wait to finish
    def _is_holiday(self, dt: datetime.date):
        return False

    # def _judge_day(self, dt: datetime.date):
        # """ return today type
        # return:
            # first:
                # E: Even day; O: Odd day
            # second:
                # WD: Work day; HD: Holiday day
        # """
        # day = dt.day
        # interval_today = "E" if day % 2 == 0 else "O"
        # day_today = "WD" if self.is_workday(dt) else "HD"
        # return interval_today, day_today

    def add_event(self, eid: int, name: str, clock: datetime.time,
            every: int = 0, unit: TimeUnit = TimeUnit.DAY, custom: DayType | list[int] = DayType.EVERYDAY,
            cycbgn_dtime: datetime.datetime | None = None, cycend_dtime: datetime.datetime | None = None,
            action: ActTyp = ActTyp.NOACTION):
        if cycbgn_dtime is None:
            cycbgn_dtime = datetime.datetime.now()
        event = Event(name, clock, every, unit, custom, cycbgn_dtime, cycend_dtime, action)
        self._event_dict[eid] = event
        self._event_dirty = True

    def modify_event(self, eid: int, clock: datetime.time, cycbgn_dtime: datetime.datetime, name: str | None,
            every: int = 0, unit: TimeUnit = TimeUnit.DAY, custom: DayType | list[int] = DayType.EVERYDAY,
            cycend_dtime: datetime.datetime | None = None,
            action: ActTyp = ActTyp.NOACTION):
        event = self._event_dict[eid]
        event.name = name if name else event.name
        event.clock = clock
        event.every = every
        event.unit = unit
        event.custom = custom
        event.cycbgn_dtime = cycbgn_dtime
        event.cycend_dtime = cycend_dtime
        event.action = action
        self._event_dirty = True

    def del_event(self, eid: int):
        del self._event_dict[eid]
        self._event_dirty = True

    def _month_diff(self, strt: datetime.datetime | datetime.date,
            end: datetime.datetime | datetime.date):
        """ 精确计算月份差（考虑天数）
        Args:
            strt, end: date或datetime对象

        Return:
            整数（end - strt 的月份差，可正可负）
        """
        # 提取年月日（兼容datetime对象）
        y1, m1, day1 = strt.year, strt.month, strt.day
        y2, m2, day2 = end.year, end.month, end.day

        # 计算基础年月差
        months = (y2 - y1) * 12 + (m2 - m1)

        # 如果结束日 < 开始日，需减1个月（未完整度过当月）
        if day2 < day1:
            months -= 1

        return months

    def _count_days(self, start_date: datetime.date, end_date: datetime.date):
        """ 计算两个日期之间的工作日和节假日数量（包含起止日期）

        Args:
            start_date: 起始日期
            end_date: 结束日期

        Return:
            workdays: 工作日数量
            weekends: 
            holidays: 节假日数量
        """
        # 确保起始日期 <= 结束日期
        if start_date > end_date:
            start_date, end_date = end_date, start_date

        workdays = 0  # 工作日计数（含调休上班）
        weekends = 0
        holidays = 0   # 节假日计数（含周末、法定假日、调休休息）

        # 遍历日期范围内的每一天
        current_date = start_date
        while current_date <= end_date:
            if self._is_workday(current_date):
                workdays += 1
            if self._is_weekend(current_date):
                weekends += 1
            if self._is_holiday(current_date):
                holidays += 1
            # 日期加1天
            current_date += datetime.timedelta(days=1)

        return workdays, weekends, holidays

    def clear_agenda(self):
        self._today_agenda_list.clear()

    def _event_on_date(self, event: Event, date: datetime.date):
        # strtime = datetime.datetime.fromtimestamp(event.strtime)
        strtdate = event.cycbgn_dtime.date()
        if date < strtdate:
            return False
        if event.cycend_dtime is not None:
            endate = event.cycend_dtime.date()
            if date > endate:
                return False

        if event.every == 0:
            return True

        match event.unit:
            case TimeUnit.HOUR:
                return True
            case TimeUnit.DAY:
                interval_days = (date - strtdate).days
                if interval_days % event.every == 0:
                    return True
            case TimeUnit.WEEK:
                workdays, weekends, holidays = self._count_days(strtdate, date)
                match event.custom:
                    case DayType.EVERYDAY:
                        interval_days = workdays + holidays
                    case DayType.WORKDAY:
                        interval_days = workdays
                    case DayType.WEEKEND:
                        interval_days = weekends
                    case DayType.HOLIDAY:
                        interval_days = holidays
                    case _:
                        weekday = date.isoweekday()
                        if weekday not in event.custom:
                            return False
                        total_days = (date - strtdate).days
                        interval_days = math.ceil(total_days / 7)
                if (interval_days > 0) and ((interval_days % event.every) == 0):
                    return True
            case TimeUnit.MONTH:
                pass
            case TimeUnit.SEASON:
                pass
            case TimeUnit.YEAR:
                pass

    def clocks_on_date(self, event: Event, date: datetime.date):
        clock_list: list[datetime.time] = []

        if event.cycend_dtime is None:
            end_dtime = datetime.datetime.combine(date, datetime.time.max)
        else:
            end_dtime = min(datetime.datetime.combine(date, datetime.time.max), event.cycend_dtime)

        next_clock = datetime.datetime.combine(date, event.clock)
        while next_clock < end_dtime:
            next_clock += datetime.timedelta(hours=event.every)
            if next_clock > event.cycbgn_dtime:
                clock_list.append(next_clock.time())
        return clock_list

    def agendas_on_date(self, date: datetime.date):
        agenda_dict: dict[int, list[Agenda]] = {}
        for eid, event in self._event_dict.items():
            if event.unit != TimeUnit.HOUR:
                if self._event_on_date(event, date):
                    agenda_dict[eid] = [Agenda(event.name, event.clock, event.action)]
            else:
                clock_list = self.clocks_on_date(event, date)
                for clock in clock_list:
                    if eid not in agenda_dict:
                        agenda_dict[eid] = []
                    agenda_dict[eid].append(Agenda(event.name, clock, event.action))
        return agenda_dict

    def event_to_agenda(self):
        self.clear_agenda()
        # pv(self._event_dict)
        now = datetime.datetime.now()
        today = datetime.date.today()

        for _, event in self._event_dict.items():
            if event.unit != TimeUnit.HOUR:
                if self._event_on_date(event, today) and (event.clock > now.time()):
                    self._today_agenda_list.append(Agenda(event.name, event.clock, event.action))
            else:
                clock_list = self.clocks_on_date(event, today)
                for clock in clock_list:
                    # self.add_agenda(event.name, clock, event.action)
                    self._today_agenda_list.append(Agenda(event.name, clock, event.action))

        # pv(self._extra_agenda_list)
        self._today_agenda_list += self._extra_agenda_list
        self._today_agenda_list = self.sort_agenda(self._today_agenda_list)
        # pv(self._today_agenda_list)

    def sleep_to_nextday(self, today: datetime.datetime):
        """ _summary_

        Args:
            today (datetime.datetime): _description_

        Returns:
            _type_: _description_
        """
        pv(today)

        nextday = today + datetime.timedelta(days=1, hours=-today.hour, minutes=-today.minute,
            seconds=-today.second, microseconds=-today.microsecond)
        pv(nextday)

        delta_seconds = (nextday - today).seconds
        # pv(delta_seconds)
        time.sleep(delta_seconds)
        return nextday

    def _compare_time(self, time1: datetime.time, time2: datetime.time) -> int:
        """ compare time1 to time2.

        Args:
            time1 (): time to compare.
            time2 (): time to compare.

        Returns:
            1: time1 is older than time2.
            0: the error is less than self._tolerance_sec.
            -1: time1 is newer than time2.

        """
        time1_minute = time1.hour * 60 + time1.minute
        # print(f"time1: {v.hour:0=2d}:{time1.minute:0=2d}:{time1.second:0=2d}")
        time2_minute = time2.hour * 60 + time2.minute
        # print(f"time2: {time2.hour:0=2d}:{time2.minute:0=2d}:{time2.second:0=2d}")

        err_minute = time2_minute - time1_minute

        if err_minute < 0:
            return 1
        elif err_minute == 0:
            if time2.second <= self._tolerance_sec:
                return 0
            else:
                return 1
        else:
            return -1

    def add_agenda(self, event: str, clock: datetime.time, action: ActTyp = ActTyp.NOACTION):
        """ _summary_

        Args:
            event (str): _description_
            clock (datetime.time): _description_
            action (ActTyp, optional): _description_. Defaults to ActTyp.NOACTION
        """
        agenda = Agenda(event, clock, action)
        # self._today_agenda_list.append(agenda)
        self._extra_agenda_list.append(agenda)
        self._event_dirty = True

    def sort_agenda(self, agenda_list: list[Agenda]):
        """ _summary_
        """
        return sorted(agenda_list, key = lambda agenda: agenda.clock)

    def _next_agenda(self):
        """ _summary_

        Returns:
            _type_: _description_
        """
        now = datetime.datetime.now()
        if self._today.date() != now.date():     # next day
            self.event_to_agenda()
            _ = self._today.replace(
                year=now.year,
                month=now.month,
                day=now.day
            )

        if self._event_dirty:
            self.event_to_agenda()
            self._event_dirty = False

        for agenda in self._today_agenda_list:
            clock = agenda.clock
            if self._compare_time(clock, now.time()) > 0:
                # po((f"Next Clock: {clock.hour:0=2d}:{clock.minute:0=2d}:{clock.second:0=2d}"
                     # f" to do {agenda.hint}"))
                return agenda
        return None

    def exec(self):
        clock = datetime.datetime.now().time()
        while True:
            while (agenda := self._next_agenda()) is None:
                now = datetime.datetime.now().time()
                po(f"{now.hour:0=2d}:{now.minute:0=2d}:{now.second:0=2d}")
                time.sleep(self._tolerance_sec)
            event = agenda.name
            if clock != agenda.clock:
                clock = agenda.clock
                po((f"Next Clock: {clock.hour:0=2d}:{clock.minute:0=2d}:{clock.second:0=2d}"
                    f" to do {event}"))

            time.sleep(self._tolerance_sec)
            now = datetime.datetime.now().time()

            if self._compare_time(clock, now) == 0:
                po(f"{now.hour:0=2d}:{now.minute:0=2d}:{now.second:0=2d}, It's time to do {event}")

                if agenda.action == ActTyp.DRIPPING_WATER:
                    self._actionsys.exec_action(ActTyp.PLAY_MP3, self._dripping_water_mp3)
                else:
                    self._actionsys.exec_action(ActTyp.PLAY_MP3, self._alarm_mp3)
                    self._actionsys.exec_action(ActTyp.SPEECH_TEXT,
                        f'北京时间{now.hour}点{now.minute}分{now.second}秒')
                    self._actionsys.exec_action(ActTyp.SPEECH_TEXT, event)
                    if agenda.action != ActTyp.PLAY_MP3:
                        self._actionsys.exec_action(agenda.action)
            else:
                po(f"{now.hour:0=2d}:{now.minute:0=2d}:{now.second:0=2d}")


def main(alarm_mp3: str, dripping_water_mp3: str):

    schedule = Schedule(alarm_mp3, dripping_water_mp3)

    # now = datetime.datetime.now().time()
    # strtstamp = datetime.datetime.now().timestamp()
    # tomorrow = schedule.sleep_to_nextday(today)
    # print(f"tomorrow = {tomorrow}")
    schedule.add_event(1, "Stretch", datetime.time(0, 30), 1, TimeUnit.HOUR, DayType.EVERYDAY, None, None, ActTyp.DRIPPING_WATER)
    schedule.event_to_agenda()
    schedule.add_agenda("Lunch", datetime.time(12, 00), ActTyp.LOCK_SCREEN)
    # schedule.add_agenda("Nap", datetime.time(12, 30), ActTyp.LOCK_SCREEN)
    # schedule.add_agenda("MCE", datetime.time(14, 00))
    # schedule.add_agenda("Japanese", datetime.time(15, 30), ActTyp.LOCK_SCREEN)
    # schedule.add_agenda("Supper", datetime.time(18, 00), ActTyp.LOCK_SCREEN)
    # schedule.add_agenda("Off work", datetime.time(20, 00), ActTyp.LOCK_SCREEN)
    # schedule.add_agenda("Listen", datetime.time(21, 00), ActTyp.LOCK_SCREEN)
    # schedule.add_agenda("Exercise", datetime.time(22, 00), ActTyp.LOCK_SCREEN)
    schedule.add_agenda("Sleep", datetime.time(23, 00), ActTyp.LOCK_SCREEN)
    date = datetime.date.today()
    agenda_dict = schedule.agendas_on_date(date)
    for _, agenda_list in agenda_dict.items():
        agenda_list = schedule.sort_agenda(agenda_list)
        pv(agenda_list)
    schedule.exec()


if __name__ == "__main__":
    file_path = os.path.dirname(os.path.abspath(__file__))
    proj_path = os.path.abspath(os.path.join(file_path, "..", "public"))
    alarm_mp3 = os.path.join(proj_path, "resources", "bell.mp3")
    wather_mp3 = os.path.join(proj_path, "resources", "water-drop-close-sonorous.mp3")
    main(alarm_mp3, wather_mp3)
