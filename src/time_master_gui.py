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
from pyutilities.tkwin import tkWin

from item_type import HourDict
from tab_hour import HourTab


class TimeMasterGui(tkWin):
    def __init__(self, path: str, xmlfile: str):
        super().__init__(path, xmlfile)
        self._tabhour: HourTab = HourTab(self)

    @override
    def process_message(self, idmsg: str, **kwargs: Any):
        pv(idmsg)
        if idmsg.startswith("btnItem"):
            iid = int(idmsg[7:])
            x, y = cast(tuple[int, int], kwargs["mousepos"])
            # self._hourdetail_dlg.do_show(self, x+20, y+20, id=iid)
            self._tabhour.show_hourdetaildlg(self, x+20, y+20, id=iid)
        elif idmsg.startswith("lblSum"):    # lblSumHour*
            iid = int(idmsg[10:])
            x, y = cast(tuple[int, int], kwargs["mousepos"])
            self._tabhour.show_recordhourdlg(self, x+20, y+20, id=iid)
        elif idmsg.startswith("btnClock"):
            iid = int(idmsg[8:])
            x, y = cast(tuple[int, int], kwargs["mousepos"])
            self._tabhour.show_selclockdlg(self, x+20, y+20, id=iid)
        else:
            match idmsg:
                case "NewUser":
                    userdb = tkFileDialog.asksaveasfilename(
                        defaultextension=".db",
                        title="Create user's db",
                        initialdir=os.path.join(self._cur_path, "data"),
                        filetypes=[("Database", "*.db")]
                    )
                    if userdb:
                        pv(userdb)
                        _ = self.process_message("newUser", db=userdb)
                case "OpenUser":
                    userdb = tkFileDialog.askopenfilename(
                        title="Select user's db",
                        initialdir=os.path.join(self._cur_path, "data")
                    )
                    if userdb:
                        pv(userdb)
                        _ = self.process_message("openUser", db=userdb)
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
                case _:
                    return super().process_message(idmsg, **kwargs)
        return True

    def _before_close(self):
        pass


if __name__ == '__main__':
    cur_path = os.path.dirname(os.path.abspath(__file__))
    if getattr(sys, 'frozen', False):
        cur_path = os.path.dirname(os.path.abspath(sys.executable))
    proj_path = os.path.join(cur_path, "..")
    win_xml = os.path.join(proj_path, 'resources', 'time_master.xml')
    gui = TimeMasterGui(proj_path, win_xml)
    # gui.create_window(win_xml)
    gui.go()
