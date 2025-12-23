#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import os
# import asyncio
from threading import Thread
import tkinter.filedialog as tkFileDialog
from typing import cast, override

from pyutilities.logit import pv, po
from pyutilities.winbasic import Container
from pyutilities.tkwin import tkWin

from schedule import Schedule
from hour_type import HourDict
from hour_tab import HourTab


class TimeMasterApp(Container):
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
        super().__init__()
        self._app_path: str = curpath

        self._gui: tkWin = tkWin(self._app_path, xmlfile)
        self._gui.filter_message(self._gui_process_message)

        bell_path = os.path.join(self._app_path, "resources", "bell.mp3")
        self._schedule: Schedule = Schedule(bell_path)

        self._tabhour: HourTab = HourTab(self._gui, self._schedule)

    def open_user(self, usrpath: str):
        """_summary_

        Args:
            usrpath (str): _description_
        """
        hoursdbpath = os.path.join(usrpath, "hours.db")
        if not os.path.isfile(hoursdbpath):
            self._tabhour.new_hours(hoursdbpath)
        else:
            self._tabhour.open_hours(hoursdbpath)

        self._schedule.event_to_schedule()

    def _gui_process_message(self, idmsg: str, **kwargs: object):
        if idmsg.startswith("btnItem"):
            iid = int(idmsg[7:])
            x, y = cast(tuple[int, int], kwargs["mousepos"])
            self._tabhour.show_hourdetaildlg(self._tabhour, x+20, y+20, id=iid)
        elif idmsg.startswith("lblSumHour"):
            iid = int(idmsg[10:])
            x, y = cast(tuple[int, int], kwargs["mousepos"])
            self._tabhour.show_recordhourdlg(self._tabhour, x+20, y+20, id=iid)
        elif idmsg.startswith("btnClock"):
            iid = int(idmsg[8:])
            x, y = cast(tuple[int, int], kwargs["mousepos"])
            self._tabhour.show_selclockdlg(self._tabhour, x+20, y+20, id=iid)
        else:
            match idmsg:
                case "btnNewHour":
                    x, y = cast(tuple[int, int], kwargs["mousepos"])
                    self._tabhour.show_edithourdlg(self._tabhour, x+20, y+20, father=-1, id=0)
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
                # case "CreateHour":
                    # iid = cast(int, kwargs["id"])
                    # item = cast(str, kwargs["item"])
                    # rid = cast(tuple[int, int], kwargs["rid"])
                    # clock = cast(str, kwargs["clock"])
                    # sums = cast(str, kwargs["sums"])
                    # is_subitem = cast(bool, kwargs["is_subitem"])
                    # self._tabhour.create_hourctrl(iid, item, rid,
                        # clock, sums, is_subitem)
                case _:
                    return self.process_message(idmsg, **kwargs)
        return True

    @override
    def process_message(self, idmsg: str, **kwargs: object):
        match idmsg:
            case _:
                return super().process_message(idmsg, **kwargs)
        # return True

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
        _ = self._tabhour.close()
        print("App exit!")
