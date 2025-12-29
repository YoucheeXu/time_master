#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import os
import sys

import time
import datetime
# import datetime as dt
from dataclasses import dataclass

from src.action_sys import ActTyp, ActionSys
from pyutilities.logit import pv, po


@dataclass
class Agenda:
    """_summary_
    Attributes:
        clock (datetime.datetime): _description_
        hintstr (str): _description_, default to ""
        action (ActTyp: _description_, default to ActTyp.NOACTION        
    """
    clock: datetime.datetime
    # clock: str = ""
    hint: str = ""
    action: ActTyp = ActTyp.NOACTION


class Schedule:
    """_summary_

    Attributes:
        _alarm_mp3 (str): _description_
        _tolerance_sec (int): _description_, default to 30
        _today_typ (str): _description_, default to "OWD"
        _today (datetime.datetime): _description_
        _event_dict (dict[str, str]): _description_
        _agenda_list (list[Agenda]): _description_
        _actionsys (ActionSys): _description_
    """
    def __init__(self, alarm_mp3: str):
        """_summary_

        Args:
            alarm_mp3 (str): _description_
        """
        self._alarm_mp3: str = alarm_mp3
        self._tolerance_sec: int = 30
        self._today_typ: str = "OWD"
        self._today: datetime.datetime = datetime.datetime.today()
        self._event_dict: dict[str, str] = {}
        self._agenda_list: list[Agenda] = []

        self._actionsys: ActionSys = ActionSys()

    def judge_day(self):
        """ return today type

        Returns:
            first leter:
                P: Per day; E: Even day; O: Odd day
            rest leter:
                CD: Calendar day; WD: Work day; HD: Holiday day
        """
        self._today_typ = "OWD"

    def add_event(self, clkstr: str, event: str):
        """_summary_

        Args:
            clkstr (str): _description_
            event (str): _description_
        """
        self._event_dict[clkstr] = event

    def remove_event(self, clkstr: str):
        """_summary_

        Args:
            clkstr (str): _description_
        """
        _ = self._event_dict.pop(clkstr)

    def clear_event(self):
        """_summary_
        """
        self._event_dict.clear()

    def event_to_schedule(self):
        """_summary_
        """
        pv(self._event_dict)
        interval_today = self._today_typ[0]
        day_today = self._today_typ[1: ]
        self.clear_schedule()
        for clk, event in self._event_dict.items():
            clklst = clk.split("_")
            interval = clklst[0]    # P: Per day; E: Even day; O: Odd day
            day = clklst[1]         # CD: Calendar day; WD: Work day; HD: Holiday day
            clock = clklst[2]
            if day in ["CD", day_today]:
                if interval in ["P", interval_today]:
                    self.add_schedule(clock, event, ActTyp.LOCK_SCREEN)
        self.sort_schedule()
        pv(self._agenda_list)

    def sleep_to_nextday(self, today: datetime.datetime):
        """_summary_

        Args:
            today (datetime.datetime): _description_

        Returns:
            _type_: _description_
        """
        pv(today)
        # nextday = datetime.datetime.strptime(f'2018-01-31', '%Y-%m-%d')
        nextday = today + datetime.timedelta(days=1, hours=-today.hour, minutes=-today.minute,
            seconds=-today.second, microseconds=-today.microsecond)
        pv(nextday)
        # delta_day = nextday - today
        delta_seconds = (nextday - today).seconds
        pv(delta_seconds)
        time.sleep(delta_seconds)
        return nextday

    def _compare_time(self, clock1: datetime.datetime, clock2: datetime.datetime) -> int:
        """ compare time to Now.

        Args:
            clock1 (): time to compare.
            clock2 (): time to compare.

        Returns:
            1: clock1 is older than clock2.
            0: the error is less than self._tolerance_sec.
            -1: clock1 is newer than clock2.

        """
        clock1_minute = clock1.hour * 60 + clock1.minute
        # print(f"Clock1: {clock1.hour:0=2d}:{clock1.minute:0=2d}:{clock1.second:0=2d}")
        clock2_minute = clock2.hour * 60 + clock2.minute
        # print(f"Clock2: {clock2.hour:0=2d}:{clock2.minute:0=2d}:{clock2.second:0=2d}")

        err_minute = clock2_minute - clock1_minute

        if err_minute < 0:
            return 1
        elif err_minute == 0:
            if clock2.second >= self._tolerance_sec:
                return 0
            else:
                return 1
        else:
            return -1

    def add_schedule(self, clock: str, hint: str, action: ActTyp = ActTyp.NOACTION,
            time_format: str = "%H:%M"):
        """_summary_

        Args:
            clock (str): _description_
            hint (str): _description_
            action (ActTyp, optional): _description_. Defaults to ActTyp.NOACTION.
            time_format (_type_, optional): _description_. Defaults to "%H:%M".
        """
        clock_ = datetime.datetime.strptime(clock, time_format)
        agenda = Agenda(clock_, hint, action)
        self._agenda_list.append(agenda)

    def sort_schedule(self):
        """_summary_
        """
        self._agenda_list = sorted(self._agenda_list, key = lambda agenda: agenda.clock)

    def _next_agenda(self):
        """_summary_

        Returns:
            _type_: _description_
        """
        now = datetime.datetime.now()
        if self._today.date() != now.date():     # next day
            self.judge_day()
            self.event_to_schedule()
            _ = self._today.replace(
                year=now.year,
                month=now.month,
                day=now.day
            )
        for agenda in self._agenda_list:
            clock = agenda.clock
            if self._compare_time(clock, now) > 0:
                # po((f"Next Clock: {clock.hour:0=2d}:{clock.minute:0=2d}:{clock.second:0=2d}"
                     # f" to do {agenda.hint}"))
                return agenda
        return None

    def clear_schedule(self):
        """_summary_
        """
        self._agenda_list.clear()

    def exec_schedule(self):
        """_summary_
        """
        clock = datetime.datetime.now()
        while True:
            while (agenda := self._next_agenda()) is None:
                now = datetime.datetime.now()
                po(f"{now.hour:0=2d}:{now.minute:0=2d}:{now.second:0=2d}")
                time.sleep(self._tolerance_sec)
            if clock != agenda.clock:
                clock = agenda.clock
                po((f"Next Clock: {clock.hour:0=2d}:{clock.minute:0=2d}:{clock.second:0=2d}"
                    f" to do {agenda.hint}"))

            time.sleep(self._tolerance_sec)
            now = datetime.datetime.now()

            if self._compare_time(clock, now) == 0:
                po(f"{now.hour:0=2d}:{now.minute:0=2d}:{now.second:0=2d} Time to do {agenda.hint}")
                self._actionsys.exec_action(ActTyp.PLAY_MP3, self._alarm_mp3)
                self._actionsys.exec_action(ActTyp.SPEECH_TEXT,
                    f'北京时间{now.hour}点{now.minute}分{now.second}秒')
                self._actionsys.exec_action(ActTyp.SPEECH_TEXT, agenda.hint)
                self._actionsys.exec_action(agenda.action)
            else:
                po(f"{now.hour:0=2d}:{now.minute:0=2d}:{now.second:0=2d}")


def main(alarm_mp3: str):

    schedule = Schedule(alarm_mp3)

    today = datetime.datetime.today()
    # tomorrow = schedule.sleep_to_nextday(today)
    # print(f"tomorrow = {tomorrow}")
    schedule.add_event("P_CD_14:34", "Cooking")
    schedule.add_event("P_CD_14:36", "Japanese")
    schedule.event_to_schedule()
    # schedule.add_schedule("11:00", "Cooking", ActTyp.LOCK_SCREEN)
    # schedule.add_schedule("12:00", "Lunch", ActTyp.LOCK_SCREEN)
    # schedule.add_schedule("12:30", "Nap", ActTyp.LOCK_SCREEN)
    # schedule.add_schedule("14:00", "MCE")
    # schedule.add_schedule("15:30", "Japanese", ActTyp.LOCK_SCREEN)
    # schedule.add_schedule("18:00", "Supper", ActTyp.LOCK_SCREEN)
    # schedule.add_schedule("20:00", "Off work", ActTyp.LOCK_SCREEN)
    # schedule.add_schedule("21:00", "Listen", ActTyp.LOCK_SCREEN)
    # schedule.add_schedule("22:00", "Exercise", ActTyp.LOCK_SCREEN)
    # schedule.add_schedule("23:00", "Sleep", ActTyp.LOCK_SCREEN)
    # schedule.sort_schedule()
    schedule.exec_schedule()

    # tomorrow = schedule.sleep_to_nextday(today)
    # pv(tomorrow)


if __name__ == "__main__":
    proj_path = os.path.dirname(os.path.abspath(__file__))
    if getattr(sys, 'frozen', False):
        print("script is packaged!")
        proj_path = os.path.dirname(os.path.abspath(sys.executable))
    proj_path = os.path.join(proj_path, "..")
    alarm_mp3 = os.path.join(proj_path, "resources", "bell.mp3")
    main(alarm_mp3)
