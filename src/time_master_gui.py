#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import sys
import os
import datetime
from functools import partial
import tkinter as tk
from tkinter import ttk
from typing import override, cast

from item_type import HourDict
from pyutilities.tkwin import EntryCtrl, ComboboxCtrl, ImageBtttonCtrl, DialogCtrl
from pyutilities.tkwin import tkWin
from pyutilities.logit import pv


class TimeMasterGui(tkWin):
    _new_subid: int = 0
    _subitem_list: list[HourDict] = []
    _id: int = 0

    def __init__(self, path: str, xmlfile: str):
        super().__init__(path, xmlfile)
        self._images: dict[int, str] = {0: "CircleFlagsUsBetsyRoss.png"}

        self._additem_dlg: DialogCtrl = cast(DialogCtrl, self.get_control("dlgAddItem"))
        additem_callback = partial(self._show_additemdlg, father=-1)
        self.register_eventhandler("btnAddItem", additem_callback)

        self._selclock_dlg: DialogCtrl = cast(DialogCtrl, self.get_control("dlgSelClock"))
        self.register_eventhandler("lblSelClock", self._show_selclockdlg)

        self._selschedule_dlg: DialogCtrl = cast(DialogCtrl, self.get_control("dlgSelSchedule"))
        self.register_eventhandler("lblSelSchedule", self._show_selscheduledlg)

        self._record_dlg: DialogCtrl = cast(DialogCtrl, self.get_control("dlgRecord"))

        self._itemdetail_dlg: DialogCtrl = cast(DialogCtrl, self.get_control("dlgItemDetail"))

    # def update_items(self, id_: int, new_name: str, new_img: str, new_schedule: str):
    #     # btn_item = self.get_control(f"btnItem{id_}")
    #     lbl_item: ttk.Label = self.get_control(f"lblItem{id_}")
    #     _ = lbl_item.configure(text=new_name)
    #     lbl_schedule: ttk.Label = self.get_control(f"lblSchedule{id_}")
    #     _ = lbl_schedule.configure(text=new_schedule)

    def update_item(self, uid: int, attrib: str, val: str):
        match attrib:
            case "name":
                ctrl_item1: ttk.Label = cast(ttk.Label, self.get_control(f"lblItem{uid}"))
                # ctrl_item1['text'] = val
                _ = ctrl_item1.configure(text=val, anchor='w')
            case "img":
                ctrl_item2: ImageBtttonCtrl = cast(ImageBtttonCtrl, self.get_control(f"btnItem{uid}"))
                ctrl_item2.change_image(val)
            case "clock":
                ctrl_item3: ttk.Label = cast(ttk.Label, self.get_control(f"lblClock{uid}"))
                # ctrl_item3['text'] = val
                _ = ctrl_item3.configure(text=val)
            case "sums":
                ctrl_item4: ttk.Label = cast(ttk.Label, self.get_control(f"lblSum{uid}"))
                _ = ctrl_item4.configure(text=val)
            case _:
                raise KeyError(f"Unkonw arrtrib: {attrib}")

        # _ = self.process_message("modify", id_, attrib=attrib, val=val)

    def get_item(self, uid: int, attrib: str) -> str:
        val: str = ""
        match attrib:
            case "name":
                ctrl_item1: ttk.Label = cast(ttk.Label, self.get_control(f"lblItem{uid}"))
                val = ctrl_item1['text']
            # case "img":
                # ctrl_item2: ImageBtttonCtrl = self.get_control(f"btnItem{id_}")
                # raise NotImplementedError("")
            case "clcok":
                ctrl_item3: ttk.Label = cast(ttk.Label, self.get_control(f"lblClock{uid}"))
                val = ctrl_item3['text']
            case "sums":
                ctrl_item4: ttk.Label = cast(ttk.Label, self.get_control(f"lblSum{uid}"))
                val = ctrl_item4['text']
            case _:
                val = ""
        return val

    def create_item(self, uid: int, item: str, rid: int, clock: str, sums: str):
        item_img = self._images.get(rid, "CircleFlagsUsBetsyRoss.png")
        id_ctrl = item.replace(" ", "").replace(".", "_").replace("\n", "_")
        # parent = self.get_control("Plan")
        # print(f"get tab: {parent}")
        parent = self.get_control("frmMain")

        level = 2
        frm_item_xml = self.create_xml("Frame", {"text": f"frm{id_ctrl}", "id": f"frmItem{uid}"})
        _, frm_item = self.create_control(parent, frm_item_xml, level)

        level = 3

        btn_item_xml = self.create_xml("ImageButton", {"id": f"btnItem{uid}",
            "img": item_img, "options": "{'height':60, 'width':60}"}, frm_item_xml)
        _, btn_item = self.create_control(frm_item, btn_item_xml, level)
        self.assemble_control(btn_item, {"layout":"grid",
            "grid":"{'row':0,'column':0,'rowspan':2}"}, '  '*level)

        lbl_item_xml = self.create_xml("Label", {"text": item,
            "id": f"lblItem{uid}", "options": "{'width':48}"}, frm_item_xml)
        # pv(lbl_item_xml)
        _, lbl_item = self.create_control(frm_item, lbl_item_xml, level)
        self.assemble_control(lbl_item, {"layout":"grid",
            "grid":"{'row':0,'column':1,'sticky':'w'}"},
            f"{'  '*level}")

        btn_clock_xml = self.create_xml("ImageButton", {"id": f"btnClock{uid}",
            "text": clock, "img": "VaadinAlarm.png",
             "options": "{'height':20, 'width':20}"}, frm_item_xml)
        _, btn_clock = self.create_control(frm_item, btn_clock_xml, level)
        self.assemble_control(btn_clock, {"layout":"grid",
            "grid":"{'row':1,'column':1,'sticky':'w'}"}, f"{'  '*level}")        

        lbl_sum_xml = self.create_xml("Label",
            {"text": sums, "id": f"lblSum{uid}", "clickable":"true"}, frm_item_xml)
        _, lbl_sum = self.create_control(frm_item, lbl_sum_xml, level)
        self.assemble_control(lbl_sum, {"layout":"grid",
            "grid":"{'row':0,'column':2,'rowspan':2}"}, f"{'  '*level}")

        self.assemble_control(frm_item, {"layout": "grid",
            "grid": f"{{'row':{uid},'column':0,'pady':4}}"}, f"{'  '*(level-1)}")

    def get_subitem(self, uid: int, attrib: str) -> str:
        val: str = ""
        match attrib:
            case "name":
                ctrl_item1: ttk.Label = cast(ttk.Label, self.get_control(f"lblSubItem{uid}"))
                val = ctrl_item1['text']
            # case "img":
                # ctrl_item2: ImageBtttonCtrl = self.get_control(f"btnItem{id_}")
                # raise NotImplementedError("")
            # case "clcok":
                # ctrl_item3: ttk.Label = cast(ttk.Label, self.get_control(f"lblClock{id_}"))
                # val = ctrl_item3['text']
            case "sum":
                ctrl_item4: ttk.Label = cast(ttk.Label, self.get_control(f"lblSubSum{uid}"))
                val = ctrl_item4['text']
            case _:
                val = ""
        return val

    def _create_subitem(self, parent: tk.Misc, uid: int, sub_item: str, rid: int, sums: str):
        item_img = self._images.get(rid, "CircleFlagsUsBetsyRoss.png")

        level = 2
        frm_subitem_xml = self.create_xml("Frame", {"id": f"frmSub{uid}"})
        _, frm_subitem = self.create_control(parent, frm_subitem_xml, level)

        level = 3

        pnl_item_xml = self.create_xml("ImagePanel", {"id": f"pnlSubItem{uid}",
            "img": item_img, 
            "options": "{'height':20, 'width':20}"}, frm_subitem_xml)
        _, pnl_item = self.create_control(frm_subitem, pnl_item_xml, level)
        self.assemble_control(pnl_item, {"layout":"pack",
            "pack":"{'side':'left','anchor':'w'}"}, '  '*level)

        lbl_item_xml = self.create_xml("Label", {"id": f"lblSubItem{uid}", 
            "text": sub_item, "options": "{'width':40}"}, frm_subitem_xml)
        _, lbl_subitem = self.create_control(frm_subitem, lbl_item_xml, level)
        self.assemble_control(lbl_subitem, {"layout":"pack",
            "pack":"{'side':'left','anchor':'w'}"}, f"{'  '*level}")

        lbl_sum_xml = self.create_xml("Label", {"text": sums,
            "id": f"lblSubSum{uid}"}, frm_subitem_xml)
        _, lbl_sum = self.create_control(frm_subitem, lbl_sum_xml, level)
        self.assemble_control(lbl_sum, {"layout":"pack",
            "pack":"{'side':'left','anchor':'e'}"}, f"{'  '*level}")

        self.assemble_control(frm_subitem, {"layout": "grid",
            "grid": f"{{'row':{uid},'column':0,'pady':4}}"}, f"{'  '*(level-1)}")

    def _delete_subitems(self, uid: int):
        self.delete_control(f"frmSub{uid}")
        self.delete_control(f"pnlSubItem{uid}")
        self.delete_control(f"lblSubItem{uid}")
        self.delete_control(f"lblSubSum{uid}")

    def _fetch_subitems(self, father: int): 
        # sub_item = {"name": "Gramma", "rid": 0, "sums": "0h"}
        subitems: list[HourDict] = []
        subitems_len = self.process_message("getSubItems", father=father, subitems=subitems)
        pv(subitems_len)
        return subitems

    @override
    # def process_message(self, id_ctrl: str, *args, **kwargs):
    def process_message(self, id_ctrl: str, **kwargs):
        if id_ctrl.startswith("btnItem"):
            # pv(id_ctrl)
            id_ = int(id_ctrl[7:])
            # lbl_item: ttk.Label = cast(ttk.Label, self.get_control(f"lblItem{id_}"))
            # item: str = lbl_item['text']
            # lbl_sum: ttk.Label = cast(ttk.Label, self.get_control(f"lblSum{id_}"))
            # sums: str = lbl_item['text']
            self._id = id_
            self._show_itemdetaildlg(id_)
            return
        elif id_ctrl.startswith("lblSum"):
            # pv(id_ctrl)
            id_ = int(id_ctrl[6:])
            name = self.get_item(id_, "name")
            self._show_recorddlg(id=id_, name=name)
            return
        # elif id_ctrl.startswith("btnClock"):
            # pv(id_ctrl)
            # id_ = int(id_ctrl[8:])
            # name = self.get_item(id_, "name")
            # FIXME: error to confirm
            # self._show_selclockdlg(id_, name)
            # return
        match id_ctrl:
            case "btnAddSubItem":
                # self._show_additemdlg(*args, father=self._id)
                self._show_additemdlg(father=self._id)
            case _:
                # return super().process_message(id_ctrl, *args, **kwargs)
                return super().process_message(id_ctrl, **kwargs)

    def _additemdlg_confirmhandler(self, confirm: bool, **kwargs) -> tuple[bool, str]:
        if confirm:
            ctrl: EntryCtrl = cast(EntryCtrl, self._additem_dlg.get_control("txtItem"))
            name = ctrl.get_val()
            # pv(name)
            if len(name) == 0:
                return False, "Name should not be empty"
            lbl_selclock: ttk.Label = cast(ttk.Label, self._additem_dlg.get_control("lblSelClock"))
            clock: str = lbl_selclock['text']
            if clock == "选择定时提醒":
                clock_val = ""
            else:
                clock_val = clock
            lbl_selSchedule: ttk.Label = cast(ttk.Label, self._additem_dlg.get_control("lblSelSchedule"))
            schedule: str = lbl_selSchedule['text']
            if schedule == "选择时间投入计划":
                schedule_val = ""
            else:
                schedule_val = schedule
            rid: int = 0
            father: int = kwargs['father']
            if father == -1:
                id_: int = self.process_message("addItem",
                    name=name, rid=0, clock=clock_val, schedule=schedule_val, father=father)
                self.create_item(id_, name, rid, clock, '0h')
            else:
                id_ = self._new_subid
                parent = cast(tk.Frame, self.get_control("frmSubItmes"))
                self._create_subitem(parent, id_, name, rid, '0h')
                item: HourDict = {"id": -1, "name": name, "rid": 0,
                    "clock": clock, "schedule": schedule, "sums": 0, "father": father}
                self._subitem_list.append(item)
                lbl_totalsubitems = self.get_control("lblTotalSubItems")
                lbl_totalsubitems["text"] = f"共{len(self._subitem_list)}个子项目"
                self._new_subid += 1
        return True, ""

    def _show_additemdlg(self, *args, **kwargs):
        # pv(kwargs['father'])
        # assert self._additem_dlg
        confirm_callback = partial(self._additemdlg_confirmhandler, father=kwargs['father'])
        self._additem_dlg.register_callback("confirm", confirm_callback)
        self._additem_dlg.do_show()

    def _selclockdlg_confirmhandler(self, confirm: bool, **kwargs) -> tuple[bool, str]:
        if confirm:
            # id_ = cast(int, kwargs["id"])
            cmb_selday: ComboboxCtrl = cast(ComboboxCtrl, self._selclock_dlg.get_control("cmbSelDay"))
            sel_day = cmb_selday.get_val()
            pv(sel_day)
            cmb_selhour: ComboboxCtrl = cast(ComboboxCtrl, self._selclock_dlg.get_control("cmbSelHour"))
            sel_hour = cmb_selhour.get_val()
            pv(sel_hour)
            cmb_selminute: ComboboxCtrl = cast(ComboboxCtrl, self._selclock_dlg.get_control("cmbSelMinute"))
            sel_minute = cmb_selminute.get_val()
            pv(sel_minute)
            clock = f"{sel_day} {int(sel_hour[:-1]):02}: {int(sel_minute[:-1]):02}"
            pv(clock)
            lbl_selclock: ttk.Label = cast(ttk.Label, self._additem_dlg.get_control("lblSelClock"))
            lbl_selclock['text'] = clock
            # self.update_item(self._id, "clock", clock)
        return True, ""

    def _show_selclockdlg(self, *args, **kwargs):
        # assert self._selclock_dlg
        print("_show_record", args, kwargs)
        # id_ = cast(int, kwargs["id"])
        # item: str = args[1]
        # self._selclock_dlg.register_callback("confirm", self._selclockdlg_confirmhandler)
        selclockdlg_confirmhandler = partial(self._selclockdlg_confirmhandler, id=self._id)
        self._selclock_dlg.register_callback("confirm", selclockdlg_confirmhandler)
        self._selclock_dlg.do_show()

    def _selscheduledlg_confirmhandler(self, confirm: bool, **kwargs) -> tuple[bool, str]:
        # assert self._selclock_dlg
        if confirm:
            cmb_selunit: ComboboxCtrl = cast(ComboboxCtrl, self._selclock_dlg.get_control("cmbSelUnit"))
            sel_unit = cmb_selunit.get_val()
            pv(sel_unit)
            cmb_selval: ComboboxCtrl = cast(ComboboxCtrl, self._selclock_dlg.get_control("cmbSelVal"))
            sel_val = cmb_selval.get_val()
            pv(sel_val)
            schedule = sel_unit + sel_val
            lbl_selschedule: ttk.Label = cast(ttk.Label, self._additem_dlg.get_control("lblSelSchedule"))
            lbl_selschedule['text'] = schedule
        return True, ""

    def _show_selscheduledlg(self, *args, **kwargs):
        # assert self._selschedule_dlg
        self._selschedule_dlg.register_callback("confirm", self._selscheduledlg_confirmhandler)
        self._selschedule_dlg.do_show()

    def _recorddlg_beforego(self, *args, **kwargs):
        lbl_item: ttk.Label = cast(ttk.Label, self.get_control("lblItem"))
        lbl_item["text"] = kwargs["name"]
        today = datetime.date.today()
        lbl_day: ttk.Label = cast(ttk.Label, self.get_control("lblDay"))
        lbl_day["text"] = today

    # TODO
    def _recorddlg_confirmhandler(self, confirm: bool, **kwargs) -> tuple[bool, str]:
        if confirm:
            id_= cast(int, kwargs["id"])
            cmb_selhour: ComboboxCtrl = cast(ComboboxCtrl, self.get_control("cmbSelHour"))
            hour = int(cmb_selhour.get_val()[:-1])
            cmb_selminute: ComboboxCtrl = cast(ComboboxCtrl, self.get_control("cmbSelMinute"))
            minute = int(cmb_selminute.get_val()[:-1])
            delta = datetime.timedelta(hours=hour, minutes=minute)
            pv(delta)
            _ = self.process_message("record", id=id_, timecost=delta)
            sums = datetime.timedelta(hours=int(self.get_item(id_, "sums")[:-1]))
            sums += delta
            pv(sums)
            sums_hours = sums.days * 24.0 + sums.seconds / 3600.0
            self.update_item(id_, "sums", f"{sums_hours}h")
        return True, ""

    def _show_recorddlg(self, *args, **kwargs):
        print("_show_record", args, kwargs)
        id_ = cast(int, kwargs["id"])
        name = cast(str, kwargs["name"])
        self._record_dlg.register_callback("beforego", lambda: self._recorddlg_beforego(name=name))
        recorddlg_confirmhandler = partial(self._recorddlg_confirmhandler, id=id_)
        self._record_dlg.register_callback("confirm", recorddlg_confirmhandler)
        self._record_dlg.do_show()

    def _itemdetaildlg_beforego(self, id_: int, *args, **kwargs):
        lbl_item: ttk.Label = cast(ttk.Label, self.get_control(f"lblItem{id_}"))
        item: str = lbl_item['text']
        pv(item)
        lbl_itemx: ttk.Label = cast(ttk.Label, self.get_control("lblItemX"))
        lbl_itemx['text'] = item
        lbl_clock = cast(ttk.Label, self.get_control(f"btnClock{id_}"))
        clock: str = lbl_clock['text']
        pv(clock)
        lbl_sum: ttk.Label = cast(ttk.Label, self.get_control(f"lblSum{id_}"))
        sums: str = lbl_sum['text']
        pv(sums)
        lbl_sumx: ttk.Label = cast(ttk.Label, self.get_control("lblSumX"))
        lbl_sumx['text'] = sums[:-1]
        parent: tk.Frame = cast(tk.Frame, self.get_control("frmSubItmes"))
        # get subitem info(rid, name, sums) of id
        self._subitem_list = self._fetch_subitems(id_)
        for i, sub_item in enumerate(self._subitem_list):
            self._create_subitem(parent, i, sub_item["name"],
                sub_item["rid"], f"{sub_item["sums"] / 60}h")
        self._new_subid = len(self._subitem_list)
        lbl_totalsubitems: ttk.Label = cast(ttk.Label, self.get_control("lblTotalSubItems"))
        lbl_totalsubitems["text"] = f"共{len(self._subitem_list)}个子项目"
        # ...

    def _itemdetaildlg_confirmhandler(self, confirm: bool, **kwargs) -> tuple[bool, str]:
        for idx, subitem in enumerate(self._subitem_list):
            # pv(idx)
            if confirm:
                if idx >= self._new_subid - 1:
                    name = subitem["name"]
                    sums = subitem["sums"]
                    rid = subitem["rid"]
                    clock = subitem["clock"]
                    schedule = subitem["schedule"]
                    father = cast(int, kwargs["father"])
                    id_: int = self.process_message("addItem", father=father, name=name,
                        rid=rid, clock=clock, schedule=schedule, sums=sums)
                    self.create_item(id_, name, rid, clock, f"{sums / 60}h")
            self._delete_subitems(idx)
        return True, ""

    def _show_itemdetaildlg(self, id_: int):
        itemdetaildlg_confirmhandler = partial(self._itemdetaildlg_confirmhandler, father=id_)
        self._itemdetail_dlg.register_callback("confirm", itemdetaildlg_confirmhandler)
        self._itemdetail_dlg.register_callback("beforego", lambda: self._itemdetaildlg_beforego(id_))
        # itemdetaildlg_beforego_handler = partial(self._itemdetaildlg_beforego, id_)
        # self._itemdetail_dlg.register_callback("beforego", itemdetaildlg_beforego_handler)
        self._itemdetail_dlg.do_show()

    def _before_close(self):
        pass


if __name__ == '__main__':
    cur_path = os.path.dirname(os.path.abspath(__file__))
    if getattr(sys, 'frozen', False):
        cur_path = os.path.dirname(os.path.abspath(sys.executable))
    win_xml = os.path.join(cur_path, 'resources', 'time_master.xml')
    gui = TimeMasterGui(cur_path, win_xml)
    # gui.create_window(win_xml)
    gui.go()
