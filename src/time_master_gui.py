#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import sys
import os
# from functools import partial
import tkinter.filedialog as tkFileDialog
# from tkinter import ttk
from typing import override, cast
from typing import Any
# from collections.abc import Mapping

from pyutilities.logit import po, pv, pe
from pyutilities.tkwin import tkWin, LabelCtrl

from tab_hour import HourTab
from tab_med import MedTab


class TimeMasterGui(tkWin):
    def __init__(self, path: str, xmlfile: str):
        super().__init__(path, xmlfile)
        self._tabhour: HourTab = HourTab(self)
        self._tabmed: MedTab = MedTab(self)

    @override
    def process_message(self, idmsg: str, **kwargs: Any):
        if idmsg.startswith("btnItem"):
            iid = int(idmsg[7:])
            x, y = cast(tuple[int, int], kwargs["mousepos"])
            self._tabhour.show_hourdetaildlg(self, x+20, y+20, id=iid)
        elif idmsg.startswith("lblSumHour"):
            iid = int(idmsg[10:])
            x, y = cast(tuple[int, int], kwargs["mousepos"])
            self._tabhour.show_recordhourdlg(self, x+20, y+20, id=iid)
        elif idmsg.startswith("btnClock"):
            iid = int(idmsg[8:])
            x, y = cast(tuple[int, int], kwargs["mousepos"])
            self._tabhour.show_selclockdlg(self, x+20, y+20, id=iid)
        elif idmsg.startswith("btnImageMedStor"):
            iid = int(idmsg[15:])
            x, y = cast(tuple[int, int], kwargs["mousepos"])
            self._tabmed.show_meddetaildlg(self, x+20, y+20, id=iid)
        elif idmsg.startswith("btnDueMedStor"):
            iid = int(idmsg[13:])
            name = self._tabmed.get_medstorattr(iid, "name")
            x, y = cast(tuple[int, int], kwargs["mousepos"])
            self._tabmed.show_selduedlg(self, x+20, y+20, id=iid,name=name)
        elif idmsg.startswith("lblSumMedStor"):
            iid = int(idmsg[13:])
            x, y = cast(tuple[int, int], kwargs["mousepos"])
            self._tabmed.show_recordmeddlg(self, x+20, y+20, id=iid)
        else:
            match idmsg:
                case "NewUser":
                    usrpath = tkFileDialog.askdirectory(
                        title="Create user's db",
                        initialdir=os.path.join(self._cur_path, "data")
                    )
                    if usrpath:
                        pv(usrpath)
                        _ = self.process_message("OpenOrNewUser", path=usrpath)
                case "OpenUser":
                    usrpath = tkFileDialog.askdirectory(
                        title="Select user's db",
                        initialdir=os.path.join(self._cur_path, "data")
                    )
                    if usrpath:
                        pv(usrpath)
                        _ = self.process_message("OpenOrNewUser", path=usrpath)
                case "CreateHour":
                    iid = cast(int, kwargs["id"])
                    item = cast(str, kwargs["item"])
                    rid = cast(tuple[int, int], kwargs["rid"])
                    clock = cast(str, kwargs["clock"])
                    sums = cast(str, kwargs["sums"])
                    is_subitem = cast(bool, kwargs["is_subitem"])
                    self._tabhour.create_hour(iid, item, rid,
                        clock, sums, is_subitem)
                case "DeleteFather":
                    iid = cast(int, kwargs["id"])
                    self._tabhour.delete_father(iid)
                case "CreateMedStor":
                    iid = cast(int, kwargs["id"])
                    item = cast(str, kwargs["item"])
                    rid = cast(tuple[int, int], kwargs["rid"])
                    due = cast(str, kwargs["due"])
                    sums = cast(str, kwargs["sums"])
                    unit = cast(str, kwargs["unit"])
                    self._tabmed.create_medstor(iid, item, rid,
                        due, sums, unit)
                case _:
                    return super().process_message(idmsg, **kwargs)
        return True


if __name__ == '__main__':
    cur_path = os.path.dirname(os.path.abspath(__file__))
    if getattr(sys, 'frozen', False):
        cur_path = os.path.dirname(os.path.abspath(sys.executable))
    proj_path = os.path.join(cur_path, "..")
    win_xml = os.path.join(proj_path, 'resources', 'time_master.xml')
    gui = TimeMasterGui(proj_path, win_xml)
    # gui.create_window(win_xml)
    gui.go()
