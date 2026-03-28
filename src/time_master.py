#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import os
import json
from threading import Thread
import tkinter.filedialog as tkFileDialog
from typing import override, cast

from pyutilities.logit import pv, po, pe
from pyutilities.winbasic import Container
from pyutilities.tkwin import tkWin

from src.schedule import Schedule
from src.hour_tab import HourTab


class TimeMasterApp(Container):
    """_summary_

    Attributes:
        _gui (_type_): _description_
        _schedule (_type_): _description_
        _tabhour (_type_): _description_
    """
    def __init__(self, curpath: str, xmlfile: str):
        """_summary_

        Args:
            curpath (str): _description_
            xmlfile (str): _description_
        """
        super().__init__()
        self._app_path: str = curpath

        self._gui: tkWin = tkWin(self._app_path, xmlfile)
        self._gui.filter_message(self._process_gui_message)

        bell_path = os.path.join(self._app_path, "resources", "bell.mp3")
        wather_mp3 = os.path.join(self._app_path, "resources", "water-drop-close-sonorous.mp3")
        self._schedule: Schedule = Schedule(bell_path, wather_mp3)

        self._tabhour: HourTab = HourTab(self._gui, self._schedule)

    def open_user(self, usr_path: str):
        """_summary_

        Args:
            usrpath (str): _description_
        """
        hoursdbpath = os.path.join(usr_path, "hours.db")
        if not os.path.isfile(hoursdbpath):
            self._tabhour.new_hours(hoursdbpath)
        else:
            self._tabhour.open_hours(hoursdbpath)

        self._schedule.event_to_agenda()

    def open(self, cfg_file: str):
        """_summary_

        Args:
            cfg_file (str): _description_
        """
        with open(cfg_file, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            last_user = cast(str, cfg["LastUser"])
            for usr_cfg in cfg["Users"]:
                if usr_cfg["Name"] == last_user:
                    user_path = os.path.join(self._app_path, cast(str, usr_cfg["Data"]))
                    self.open_user(user_path)
                    break

    def _process_gui_message(self, idmsg: str, **kwargs: object):
        return self.process_message(idmsg, **kwargs)

    @override
    def process_message(self, idmsg: str, **kwargs: object):
        match idmsg:
            case "NewUser":
                usrpath = tkFileDialog.askdirectory(
                    title="Create user path",
                    initialdir=os.path.join(self._app_path, "data")
                )
                if usrpath:
                    pv(usrpath)
                    self.open_user(usrpath)
            case "OpenUser":
                usrpath = tkFileDialog.askdirectory(
                    title="Select user path",
                    initialdir=os.path.join(self._app_path, "data")
                )
                if usrpath:
                    pv(usrpath)
                    self.open_user(usrpath)
            case _:
                return super().process_message(idmsg, **kwargs)
        return True

    def run(self):
        """_summary_
        """
        # asyncio.run(self._schedule.exec_schedule())
        # self._gui.go()
        r1 = Thread(target=self._schedule.exec)
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
        _ = self._tabhour.close()
        print("App exit!")
