#!/usr/bin/python3
# -*- coding: UTF-8 -*-
"""
v0.1.1
  1. merge dlgAddItem to dlgEditItem
"""
import sys
import os
import datetime
# from functools import partial
import tkinter as tk
# from tkinter import ttk
from typing import override, cast
from typing import Any
# from collections.abc import Mapping

from item_type import HourTuple, HourDict
from pyutilities.tkwin import LabelCtrl, EntryCtrl, ButtonCtrl, ComboboxCtrl, ImageBtttonCtrl
from pyutilities.tkwin import PicsListviewCtrl, DialogCtrl
from pyutilities.tkwin import tkWin
from pyutilities.logit import po, pv


class TimeMasterGui(tkWin):
    _old_subid: int = 0
    # _subitem_list: list[HourDict] = []
    _children: dict[int, HourTuple] = {}
    # _id: int = 0

    def __init__(self, path: str, xmlfile: str):
        super().__init__(path, xmlfile)
        self._images_dict: dict[int, dict[int, str]] = {
            0: {0: "items\\CircleFlagsUsBetsyRoss.png", 1: "items\\FlatUiNews.png", 
                2: "items\\gift.png", 3: "items\\VaadinAlarm.png"},
            1: {0: "items\\Course\\cpp.png", 1: "items\\Course\\MPC.png",
                2: "items\\Course\\车辆工程.png", 3: "items\\Course\\伺服电机.png",
                4: "items\\Course\\钢笔书法.png", 5: "items\\Course\\股票.png",
                6: "items\\Course\\管理.png", 7: "items\\Course\\绘画.png",
                8: "items\\Course\\机器视觉.png", 9: "items\\Course\\毛笔书法.png",
                10: "items\\Course\\语文.png", 11: "items\\Course\\自动化.png"},
            2: {0: "items\\Exercise\\锻炼.png", 1: "items\\Exercise\\俯卧撑.png",
                2: "items\\Exercise\\跑步.png", 3: "items\\Exercise\\平板支撑.png",
                4: "items\\Exercise\\足球.png"},
            3: {0: "items\\Language\\德语.png", 1: "items\\Language\\韩语.png",
                2: "items\\Language\\日语.png", 3: "items\\Language\\英语.png",
                4: "items\\Language\\口语.png", 5: "items\\Language\\听力.png",
                6: "items\\Language\\阅读.png", 7: "items\\Language\\写作.png"},
            4: {0: "items\\Test\\CET-4.png", 1: "items\\Test\\CET-6.png",
                2: "items\\Test\\CFA.png", 3: "items\\Test\\CPA.png",
                4: "items\\Test\\GRE.png", 5: "items\\Test\\IELTS.png",
                6: "items\\Test\\TOEFL.png"}
        }

        self._selclock_dlg: DialogCtrl = cast(DialogCtrl, self.get_control("dlgSelClock"))
        self._selclock_dlg.register_eventhandler("confirm", self._selclockdlg_confirm)

        self._selschedule_dlg: DialogCtrl = cast(DialogCtrl, self.get_control("dlgSelSchedule"))
        self._selschedule_dlg.register_eventhandler("confirm", self._selscheduledlg_confirm)

        """
        self._additem_dlg: DialogCtrl = cast(DialogCtrl, self.get_control("dlgAddItem"))
        # additem_callback = partial(self._show_additemdlg, father=-1)
        # self.register_eventhandler("btnAddItem", additem_callback)
        self._additem_dlg.filter_message(self._additemdlg_processmessage)
        """

        self._record_dlg: DialogCtrl = cast(DialogCtrl, self.get_control("dlgRecord"))
        self._record_dlg.register_eventhandler("beforego", self._recorddlg_beforego)
        self._record_dlg.register_eventhandler("confirm", self._recorddlg_confirm)

        self._itemdetail_dlg: DialogCtrl = cast(DialogCtrl, self.get_control("dlgItemDetail"))
        self._itemdetail_dlg.filter_message(self._itemdetaildlg_processmessage)

        self._edititem_dlg: DialogCtrl = cast(DialogCtrl, self.get_control("dlgEditItem"))
        self._edititem_dlg.filter_message(self._edititemdlg_processmessage)

    def update_item(self, uid: int, attrib: str, val: str):
        match attrib:
            case "name":
                ctrl_item1 = cast(LabelCtrl, self.get_control(f"lblItem{uid}"))
                # ctrl_item1['text'] = val
                _ = ctrl_item1.configure(text=val, anchor='w')
            case "image":
                ctrl_item2 = cast(ImageBtttonCtrl, self.get_control(f"btnItem{uid}"))
                ctrl_item2.change_image(val)
            case "clock":
                if val in ["", "选择定时提醒"]:
                    return
                ctrl_item3 = cast(ImageBtttonCtrl, self.get_control(f"btnClock{uid}"))
                if not ctrl_item3.visible:
                    ctrl_item3.grid()
                # ctrl_item3['text'] = val
                _ = ctrl_item3.configure(text=val)
            case "sums":
                ctrl_item4 = cast(LabelCtrl, self.get_control(f"lblSum{uid}"))
                _ = ctrl_item4.configure(text=val)
            case _:
                raise KeyError(f"Unkonw arrtrib: {attrib}")

        # _ = self.process_message("modify", id_, attrib=attrib, val=val)

    def get_item(self, uid: int, attrib: str) -> str:
        val: str = ""
        match attrib:
            case "name":
                ctrl_item1 = cast(LabelCtrl, self.get_control(f"lblItem{uid}"))
                val = cast(str, ctrl_item1['text'])
            # case "img":
                # ctrl_item2 = cast(ImageBtttonCtrl, self.get_control(f"btnItem{id_}")
                # raise NotImplementedError("")
            case "clcok":
                ctrl_item3 = cast(ImageBtttonCtrl, self.get_control(f"btnClock{uid}"))
                val = cast(str, ctrl_item3['text'])
            case "sums":
                ctrl_item4 = cast(LabelCtrl, self.get_control(f"lblSum{uid}"))
                val = cast(str, ctrl_item4['text'])
            case _:
                val = ""
        return val

    # def create_item(self, parent: object, iid: int, item: str, rid: int,
    def create_item(self, iid: int, item: str, rid: tuple[int, int],
            clock: str, sums: str, is_subitem: bool = False):
        imagepath = self._get_imagepath(rid[0], rid[1])
        id_ctrl = item.replace(" ", "").replace(".", "_").replace("\n", "_")

        master = self.get_control("frmHour")
        if is_subitem:
            detail = cast(HourDict, self.process_message("getItemDetail", id=iid))
            idfather = detail["father"]
            parent = self.get_control(f"frmGroup{idfather}")
        else:
            xml = self.create_xml("Frame", {"text":f"frmGroup{iid}", "id":f"frmGroup{iid}"})
                 # "options":"{'borderwidth':1,'relief':'ridge'}"})
            _, parent = self.create_control(master, xml, 2)            

        level = 3
        frmitem_xml = self.create_xml("Frame", {"text": f"frm{id_ctrl}", "id": f"frmItem{iid}"})
        _, frm_item = self.create_control(parent, frmitem_xml, level)

        level = 4

        radio = 0.8 if is_subitem else 1

        btnitem_xml = self.create_xml("ImageButton", {"id": f"btnItem{iid}",
            "img": imagepath,
                "options": f"{{'height': {int(60 * radio)}, 'width': {int(60 * radio)}}}"}, frmitem_xml)
        _, btn_item = self.create_control(frm_item, btnitem_xml, level)
        self.assemble_control(btn_item, {"layout":"grid",
            "grid":"{'row':0,'column':0,'rowspan':2}"}, '  '*level)

        lblitem_xml = self.create_xml("Label", {"text": item,
            "id": f"lblItem{iid}", "options": "{'width':48}"}, frmitem_xml)
        # pv(lbl_item_xml)
        _, lbl_item = self.create_control(frm_item, lblitem_xml, level)
        self.assemble_control(lbl_item, {"layout":"grid",
            "grid":"{'row':0,'column':1,'sticky':'w'}"},
            f"{'  '*level}")

        btnclock_xml = self.create_xml("ImageButton", {"id": f"btnClock{iid}",
            "text": clock, "img": "VaadinAlarm.png",
             "options": "{'height':20, 'width':20}"}, frmitem_xml)
        _, btn_clock = self.create_control(frm_item, btnclock_xml, level)
        self.assemble_control(btn_clock, {"layout":"grid",
            "grid":"{'row':1,'column':1,'sticky':'w'}"}, f"{'  '*level}")

        if clock in ["", "选择定时提醒"]:
            # cast(tk.Widget, btn_clock).grid_remove()
            cast(ImageBtttonCtrl, btn_clock).hide()

        lblsum_xml = self.create_xml("Label",
            {"text": sums, "id": f"lblSum{iid}", "clickable": "true"}, frmitem_xml)
        _, lbl_sum = self.create_control(frm_item, lblsum_xml, level)
        self.assemble_control(lbl_sum, {"layout":"grid",
            "grid":"{'row':0,'column':2,'rowspan':2,'sticky':'w'}"}, f"{'  '*level}")

        # self.assemble_control(frm_item, {"layout": "grid",
            # "grid": f"{{'row':{uid},'column':0,'pady':4}}"}, f"{'  '*(level-1)}")

        # self._app.assemble_control(frm_bot, {"layout": "pack",
            # "pack": "{'side':'bottom','fill':'both','expand':True,'padx':5,'pady':5}"})

        self.assemble_control(frm_item, {"layout": "pack",
            "pack": "{'side':'top','anchor':'e','pady':1,'padx':7}"}, f"{'  '*(level-1)}")

        if not is_subitem:
            if iid == 1:
                pady1 = 10
            else:
                pady1 = 5
            self.assemble_control(parent, {"layout": "pack",
                "pack":f"{{'side':'top','pady':({pady1},5),'fill':'x'}}"}, f"{'  '*(2-1)}")

    def get_childattrib(self, uid: int, attrib: str) -> str:
        val: str = ""
        match attrib:
            case "name":
                ctrl_item1 = cast(LabelCtrl, self.get_control(f"lblChild{uid}"))
                val = cast(str, ctrl_item1['text'])
            # case "img":
                # ctrl_item2: = cast(ImageBtttonCtrl, self.get_control(f"btnItem{id_}")
                # raise NotImplementedError("")
            # case "clcok":
                # ctrl_item3 = cast(LabelCtrl, self.get_control(f"lblClock{id_}"))
                # val = ctrl_item3['text']
            case "sum":
                ctrl_item4 = cast(LabelCtrl, self.get_control(f"lblSubSum{uid}"))
                val = cast(str, ctrl_item4['text'])
            case _:
                val = ""
        return val

    def _create_child(self, parent: tk.Misc, uid: int, sub_item: str,
            rid: tuple[int, int], sums: str):
        imagepath = self._get_imagepath(rid[0], rid[1])

        level = 2
        frm_child_xml = self.create_xml("Frame", {"id": f"frmSub{uid}"})
        _, frm_child = self.create_control(parent, frm_child_xml, level)

        level = 3

        pnlitem_xml = self.create_xml("ImagePanel", {"id": f"pnlChild{uid}",
            "img": imagepath, 
            "options": "{'height':20, 'width':20}"}, frm_child_xml)
        _, pnl_item = self.create_control(frm_child, pnlitem_xml, level)
        self.assemble_control(pnl_item, {"layout":"pack",
            "pack":"{'side':'left','anchor':'w'}"}, '  '*level)

        lblitem_xml = self.create_xml("Label", {"id": f"lblChild{uid}", 
            "text": sub_item, "options": "{'width':40}"}, frm_child_xml)
        _, lbl_subitem = self.create_control(frm_child, lblitem_xml, level)
        self.assemble_control(lbl_subitem, {"layout":"pack",
            "pack":"{'side':'left','anchor':'w'}"}, f"{'  '*level}")

        lblsum_xml = self.create_xml("Label", {"text": sums,
            "id": f"lblSubSum{uid}"}, frm_child_xml)
        _, lbl_sum = self.create_control(frm_child, lblsum_xml, level)
        self.assemble_control(lbl_sum, {"layout":"pack",
            "pack":"{'side':'left','anchor':'e'}"}, f"{'  '*level}")

        self.assemble_control(frm_child, {"layout": "grid",
            "grid": f"{{'row':{uid},'column':0,'pady':4}}"}, f"{'  '*(level-1)}")

    def _delete_children(self, sid: int):
        self.delete_control(f"frmSub{sid}")
        self.delete_control(f"pnlChild{sid}")
        self.delete_control(f"lblChild{sid}")
        self.delete_control(f"lblSubSum{sid}")

    def _get_imagepath(self, group: int, index: int):
        return self._images_dict[group].get(index, "CircleFlagsUsBetsyRoss.png")

    # TODO: wait to test
    # def _additemdlg_confirmhandler(self, confirm: bool, **kwargs) -> tuple[bool, str]:
    def _additemdlg_confirm(self, **kwargs: Any) -> tuple[bool, str]:
        po(f"_additemdlg_confirm: {kwargs}")
        # father = -1
        # if self._additem_dlg.owner.title == "项目详情":
            # father = self._id
        father = cast(int, kwargs["father"])
        iid = cast(int, kwargs["id"])

        ctrl = cast(EntryCtrl, self._additem_dlg.get_control("txtItem"))
        name = ctrl.get_val()
        # pv(name)
        if len(name) == 0:
            return False, "Name should not be empty"
        lbl_selclock = cast(LabelCtrl, self._additem_dlg.get_control("lblSelClockAddItem"))
        clock  = cast(str, lbl_selclock['text'])
        if clock == "选择定时提醒":
            clock_val = ""
        else:
            clock_val = clock
        lbl_selschedule = cast(LabelCtrl, self._additem_dlg.get_control("lblSelScheduleAddItem"))
        schedule = cast(str, lbl_selschedule['text'])
        if schedule == "选择时间投入计划":
            schedule_val = ""
        else:
            schedule_val = schedule
        #TODO: rid
        rid = 0, 0
        # father: int = kwargs['father']
        if father == -1:
            idx: int = self.process_message("addItem",
                name=name, rid=0, clock=clock_val, schedule=schedule_val, father=father)
            self.create_item(idx, name, rid, clock, '0h')
        else:
            # iid = self._old_subid
            idx = len(self._children)
            parent = cast(tk.Frame, self.get_control("frmSubItmes"))
            self._create_child(parent, idx, name, rid, '0h')
            # item: HourDict = {"name": name, "rid": 0,
                # "clock": clock, "schedule": schedule, "sums": 0, "father": father}
            # self._children[idx] = item
            self._children[idx] = HourTuple(iid=0, name=name, rid=rid,
                clock=clock_val, schedule=schedule_val, sums=0, father=father)
            lbl_totalsubitems = cast(LabelCtrl, self.get_control("lblTotalChildren"))
            lbl_totalsubitems["text"] = f"共{len(self._children)}个子项目"
            # self._old_subid += 1
        return True, ""

    def _additemdlg_processmessage(self, idmsg: str, **kwargs: Any):
        if self._additem_dlg.alive:
            match idmsg:
                case "changeClock":
                    clock = cast(str, kwargs["clock"])
                    lbl_selclock: LabelCtrl = cast(LabelCtrl, self.get_control("lblSelClockAddItem"))
                    lbl_selclock['text'] = clock
                case "changeSchedule":
                    schedule = cast(str, kwargs["schedule"])
                    lbl_selschedule: LabelCtrl = cast(LabelCtrl, self.get_control("lblSelScheduleAddItem"))
                    lbl_selschedule['text'] = schedule
                case "lblSelClockAddItem":
                    x, y = cast(tuple[int, int], kwargs["mousepos"])
                    self._selclock_dlg.do_show(self._additem_dlg, x+20, y+20, **kwargs)
                case "lblSelScheduleAddItem":
                    x, y = cast(tuple[int, int], kwargs["mousepos"])
                    self._selschedule_dlg.do_show(self._additem_dlg, x+20, y+20, **kwargs)
                case "confirm":
                    return self._additemdlg_confirm(**kwargs)
                case _:
                    return None
            return True
        return None

    # def _selclockdlg_confirmhandler(self, confirm: bool, **kwargs) -> tuple[bool, str]:
    def _selclockdlg_confirm(self, **kwargs: Any) -> tuple[bool, str]:
        po(f"_selclockdlg_confirm: {kwargs}")
        # id_ = cast(int, kwargs["id"])
        cmb_selday = cast(ComboboxCtrl, self._selclock_dlg.get_control("cmbSelDay"))
        sel_day = cmb_selday.get_val()
        pv(sel_day)
        cmb_selhour = cast(ComboboxCtrl, self._selclock_dlg.get_control("cmbSelHour"))
        sel_hour = cmb_selhour.get_val()
        pv(sel_hour)
        cmb_selminute = cast(ComboboxCtrl, self._selclock_dlg.get_control("cmbSelMinute"))
        sel_minute = cmb_selminute.get_val()
        pv(sel_minute)
        clock = f"{sel_day} {int(sel_hour[:-1]):02}:{int(sel_minute[:-1]):02}"
        # pv(clock)
        self._selclock_dlg.owner.process_message("changeClock", clock=clock, **kwargs)
        return True, ""

    # def _selscheduledlg_confirmhandler(self, confirm: bool, **kwargs) -> tuple[bool, str]:
    def _selscheduledlg_confirm(self, **kwargs: Any) -> tuple[bool, str]:
        po(f"_selscheduledlg_confirm: {kwargs}")
        # id_ = cast(int, kwargs["id"])
        cmb_selunit = cast(ComboboxCtrl, self._selclock_dlg.get_control("cmbSelUnit"))
        sel_unit = cmb_selunit.get_val()
        pv(sel_unit)
        cmb_selval = cast(ComboboxCtrl, self._selclock_dlg.get_control("cmbSelVal"))
        sel_val = cmb_selval.get_val()
        pv(sel_val)
        schedule = f"计划{sel_unit}{sel_val}"
        # lbl_selschedule: LabelCtrl = cast(LabelCtrl, self._additem_dlg.get_control("lblSelSchedule"))
        # lbl_selschedule['text'] = schedule
        # self.process_message("changeSchedule", id = id_, schedule=schedule)
        self._selschedule_dlg.owner.process_message("changeSchedule", schedule=schedule, **kwargs)
        return True, ""

    def _recorddlg_beforego(self, **kwargs: Any):
        po(f"_recorddlg_beforego: {kwargs}")
        iid = cast(int, kwargs["id"])
        detail = cast(HourDict, self.process_message("getItemDetail", id=iid))
        lbl_item = cast(LabelCtrl, self.get_control("lblItem"))
        lbl_item["text"] = detail["name"]
        today = datetime.date.today()
        lbl_day = cast(LabelCtrl, self.get_control("lblDay"))
        lbl_day["text"] = today

    # TODO: wait to test
    # def _recorddlg_confirmhandler(self, confirm: bool, **kwargs) -> tuple[bool, str]:
    # def _recorddlg_confirm(self, **kwargs: Mapping[str, Any]) -> tuple[bool, str]:
    def _recorddlg_confirm(self, **kwargs: Any) -> tuple[bool, str]:
        po(f"_recorddlg_confirm: {kwargs}")
        iid = cast(int, kwargs["id"])
        # iid = self._id
        cmb_selhour = cast(ComboboxCtrl, self.get_control("cmbSelHour"))
        hour = int(cmb_selhour.get_val()[:-1])
        cmb_selminute = cast(ComboboxCtrl, self.get_control("cmbSelMinute"))
        minute = int(cmb_selminute.get_val()[:-1])
        delta = datetime.timedelta(hours=hour, minutes=minute)
        pv(delta)
        _ = self.process_message("record", id=iid, timecost=delta)
        sums = datetime.timedelta(hours=int(self.get_item(iid, "sums")[:-1]))
        sums += delta
        pv(sums)
        sums_hours = sums.days * 24.0 + sums.seconds / 3600.0
        self.update_item(iid, "sums", f"{sums_hours}h")
        return True, ""

    def _itemdetaildlg_beforego(self, **kwargs: Any):
        po(f"_itemdetaildlg_beforego: {kwargs}")
        # iid = cast(int, self._itemdetail_dlg.owner.process_message("getId"))
        iid = cast(int, kwargs["id"])
        # data = HourDict()
        # data = {}
        # self.process_message("getItemDetail", id=id_, detail=data)
        detail = cast(HourDict, self.process_message("getItemDetail", id=iid))
        # pv(iid)
        # pv(detail)

        lbl_father = cast(LabelCtrl, self.get_control("lblFatherItemDetail"))
        id_father = detail["father"]
        if id_father != -1:
            detail_father = cast(HourDict, self.process_message("getItemDetail", id=id_father))
            name_father = detail_father["name"]
            pv(name_father)
            lbl_father['text'] = name_father
        else:
            lbl_father.hide()

        lbl_item = cast(LabelCtrl, self.get_control("lblItemItemDetail"))
        lbl_item['text'] = detail["name"]
        lbl_sum = cast(LabelCtrl, self.get_control("lblSumItemDetail"))
        lbl_sum['text'] = f"{detail['sums'] / 60}"

        lbl_selclock = cast(LabelCtrl, self.get_control("lblSelClockItemDetail"))
        # clock = data["clock"]
        lbl_selclock['text'] = detail["clock"]
        lbl_selschedule = cast(LabelCtrl, self.get_control("lblSelScheduleItemDetail"))
        lbl_selschedule['text'] = detail["schedule"]

        parent: tk.Frame = cast(tk.Frame, self.get_control("frmSubItmes"))
        # get subitem info(rid, name, sums) of id
        children = cast(dict[int, HourDict], self.process_message("getChildren", father=iid))
        idx = 0
        for sid, child in children.items():
            self._children[idx] = HourTuple(iid=sid, name=child["name"], rid=child["rid"],
                clock=child["clock"], schedule=child["schedule"], sums=child["sums"],
                father=child["father"])
            self._create_child(parent, idx, child["name"],
                child["rid"], f"{child["sums"] / 60}h")
            idx += 1
        pv(self._children)
        self._old_subid = len(self._children) - 1
        lbl_totalsubitems = cast(LabelCtrl, self.get_control("lblTotalChildren"))
        lbl_totalsubitems["text"] = f"共{idx}个子项目"
        # ...

    def _itemdetaildlg_confirm(self, **kwargs: Any) -> tuple[bool, str]:
        po(f"_itemdetaildlg_confirm: {kwargs}")
        for idx, child in self._children.items():
            if idx > self._old_subid:
                name =      child.name
                sums =      child.sums
                rid =       child.rid
                clock =     child.clock
                schedule =  child.schedule
                # father = cast(int, kwargs["father"])
                # iid = cast(int, self.process_message("addItem", father=self._id, name=name,
                    # rid=rid, clock=clock, schedule=schedule, sums=sums))
                iid = 10
                # father = self.get_control(f"frmGroup{self._id}")
                # self.create_item(father, iid, name, rid, clock, f"{sums / 60}h", self._id != -1)
                self.create_item(iid, name, rid, clock, f"{sums / 60}h", self._id != -1)
            self._delete_children(idx)
        self._children.clear()
        return True, ""

    def _itemdetaildlg_cancel(self, **kwargs: Any) -> tuple[bool, str]:
        po(f"_itemdetaildlg_cancel: {kwargs}")
        for idx, _ in self._children.items():
            self._delete_children(idx)
        self._children.clear()
        return True, ""

    def _itemdetaildlg_processmessage(self, idmsg: str, **kwargs: Any):
        if self._itemdetail_dlg.alive:
            iid = cast(int, kwargs["id"])
            match idmsg:
                case "beforego":
                    self._itemdetaildlg_beforego(**kwargs)
                case "changeItemImage":
                    # iid = cast(int, kwargs["id"])
                    grp = cast(int, kwargs["group"])
                    idx = cast(int, kwargs["index"])
                    imagebutton = cast(ImageBtttonCtrl, self.get_control("imgItemDetail"))
                    imagepath = self._get_imagepath(grp, idx)
                    # pv(imagepath)
                    imagebutton.change_image(imagepath)
                    _ = self._itemdetail_dlg.owner.process_message("changeItemImage",
                        id=iid, group=grp, index=idx)
                case "changeClock":
                    clock = cast(str, kwargs["clock"])
                    lbl_selclock = cast(LabelCtrl,
                        self.get_control("lblSelClockItemDetail"))
                    lbl_selclock['text'] = clock
                    # self.update_item(self._id, "clock", clock)
                    self.update_item(iid, "clock", clock)
                    self._itemdetail_dlg.owner.process_message("changeClock", id=iid, clock=clock)
                case "changeSchedule":
                    schedule = cast(str, kwargs["schedule"])
                    lbl_selschedule = cast(LabelCtrl,
                        self.get_control("lblSelScheduleItemDetail"))
                    lbl_selschedule['text'] = schedule
                    self._itemdetail_dlg.owner.process_message("changeSchedule",
                        id=iid, schedule=schedule)
                case "imgItemDetail":
                    # pv(kwargs)
                    # iid = cast(int, self._itemdetail_dlg.owner.process_message("getId"))
                    detail = cast(HourDict, self.process_message("getItemDetail", id=iid))
                    father = detail["father"]
                    x, y = cast(tuple[int, int], kwargs["mousepos"])
                    self._edititem_dlg.do_show(self._itemdetail_dlg, x+20, y+20,
                        father=father, id=iid)
                case "btnAddChild":
                    # pv(kwargs)
                    # iid = cast(int, self._itemdetail_dlg.owner.process_message("getId"))
                    x, y = cast(tuple[int, int], kwargs["mousepos"])
                    self._edititem_dlg.do_show(self._itemdetail_dlg, x+20, y+20,
                        father=iid, id=0)
                case "btnRecordItemDetail":
                    # iid = cast(int, self._itemdetail_dlg.owner.process_message("getId"))
                    detail = cast(HourDict, self.process_message("getItemDetail", id=iid))
                    father = detail["father"]
                    x, y = cast(tuple[int, int], kwargs["mousepos"])
                    self._record_dlg.do_show(self._itemdetail_dlg, x+20, y+20,
                        father=father, id=iid)
                case "deleteItem":
                    # iid = cast(int, self._itemdetail_dlg.owner.process_message("getId"))
                    self._itemdetail_dlg.destroy()
                    self._itemdetail_dlg.owner.process_message("deleteItem", id=iid)
                case "confirm":
                    return self._itemdetaildlg_confirm(**kwargs)
                case "cancel":
                    return self._itemdetaildlg_cancel(**kwargs)
                case _:
                    return None
            return True
        return None

    def _edititemdlg_beforego(self, **kwargs: Any):
        father = cast(int, kwargs["father"])
        iid = cast(int, kwargs["id"])

        if father != -1:
            lbl_father = cast(LabelCtrl, self.get_control("lblSelFatherEditItem"))
            detail_father = cast(HourDict, self.process_message("getItemDetail", id=father))
            name_father = detail_father["name"]
            pv(name_father)
            lbl_father['text'] = name_father

        if iid == 0:
            self._edititem_dlg.set_title("新建项目")
            btn_delitem = cast(ButtonCtrl, self.get_control("btnDelItemEditItem"))
            btn_delitem.hide()
        else:
            self._edititem_dlg.set_title("编辑项目")
            detail = cast(HourDict, self.process_message("getItemDetail", id=iid))
            pv(detail)

            # lbl_name = cast(LabelCtrl, self.get_control("lblNameEditItem"))
            # lbl_name['text'] = detail["name"]
            ent_name = cast(EntryCtrl, self.get_control("txtItemEditItem"))
            ent_name.set_val(detail["name"])
            ent_name.disable()
            lbl_selclock = cast(LabelCtrl, self.get_control("lblSelClockEditItem"))
            lbl_selclock['text'] = detail["clock"] if detail["clock"] else "选择定时提醒"
            lbl_selschedule = cast(LabelCtrl, self.get_control("lblSelScheduleEditItem"))
            lbl_selschedule['text'] = detail["schedule"] if detail["schedule"] else "选择时间投入计划"

        list_itemimage = cast(PicsListviewCtrl, self.get_control("lstItemImageEditItem"))
        # list_itemimage.display_images(list(self._images_dict.values()))
        list_itemimage.add_imagegroup("一般", list(self._images_dict[0].values()))
        list_itemimage.add_imagegroup("课程", list(self._images_dict[1].values()))
        list_itemimage.add_imagegroup("锻炼", list(self._images_dict[2].values()))
        list_itemimage.add_imagegroup("语言", list(self._images_dict[3].values()))
        list_itemimage.add_imagegroup("考试", list(self._images_dict[4].values()))

    # TODO: only change those which are modified
    def _edititemdlg_confirm(self, **kwargs: Any):
        po(f"_edititemdlg_confirm: {kwargs}")
        father = cast(int, kwargs["father"])
        iid = cast(int, kwargs["id"])
        if iid != 0:    # edit item
            lbl_selclock = cast(LabelCtrl, self.get_control("lblSelClockEditItem"))
            clock = lbl_selclock['text']
            pv(clock)
            _ = self._edititem_dlg.owner.process_message("changeClock", id=iid, clock=clock)

            lbl_selschedule = cast(LabelCtrl, self.get_control("lblSelScheduleEditItem"))
            schedule = lbl_selschedule['text']
            pv(schedule)
            _ = self._edititem_dlg.owner.process_message("changeSchedule", id=iid, schedule=schedule)

            lst_itemimage = cast(PicsListviewCtrl,
                self.get_control("lstItemImageEditItem"))
            grp, idx = lst_itemimage.get_selected()
            _ = self._edititem_dlg.owner.process_message("changeItemImage",
                id=iid, group=grp, index=idx)
        else:   # New item
            # if self._additem_dlg.owner.title == "项目详情":
                # father = self._id
            ent_name = cast(EntryCtrl, self.get_control("txtItemEditItem"))
            name = ent_name.get_val()
            # pv(name)
            if len(name) == 0:
                return False, "Name should not be empty"
            lbl_selclock = cast(LabelCtrl, self.get_control("lblSelClockEditItem"))
            clock  = cast(str, lbl_selclock['text'])
            clock_val = "" if clock == "选择定时提醒" else clock
            lbl_selschedule = cast(LabelCtrl, self.get_control("lblSelScheduleEditItem"))
            schedule = cast(str, lbl_selschedule['text'])
            schedule_val = "" if schedule == "选择时间投入计划" else schedule
            lst_itemimage = cast(PicsListviewCtrl,
                self.get_control("lstItemImageEditItem"))
            rid = lst_itemimage.get_selected()
            if father == -1:
                iid = cast(int, self.process_message("addItem",
                    name=name, rid=0, clock=clock_val, schedule=schedule_val, father=father))
                self.create_item(iid, name, rid, clock, '0.0h')
            else:
                # iid = self._old_subid
                idx = len(self._children)
                parent = cast(tk.Frame, self.get_control("frmSubItmes"))
                self._create_child(parent, idx, name, rid, '0.0h')
                # item: HourDict = {"name": name, "rid": 0,
                    # "clock": clock, "schedule": schedule, "sums": 0, "father": father}
                # self._children[idx] = item
                self._children[idx] = HourTuple(iid=0, name=name, rid=rid,
                    clock=clock_val, schedule=schedule_val, sums=0, father=father)
                lbl_totalsubitems = cast(LabelCtrl, self.get_control("lblTotalChildren"))
                lbl_totalsubitems["text"] = f"共{len(self._children)}个子项目"
                # self._old_subid += 1
        return True, ""

    def _edititemdlg_processmessage(self, idmsg: str, **kwargs: Any):
        if self._edititem_dlg.alive:
            iid = cast(int, kwargs["id"])
            match idmsg:
                case "beforego":
                    self._edititemdlg_beforego(**kwargs)
                case "changeClock":
                    clock = cast(str, kwargs["clock"])
                    lbl_selclock = cast(LabelCtrl, self.get_control("lblSelClockEditItem"))
                    lbl_selclock['text'] = clock
                case "changeSchedule":
                    schedule = cast(str, kwargs["schedule"])
                    lbl_selschedule = cast(LabelCtrl, self.get_control("lblSelScheduleEditItem"))
                    lbl_selschedule['text'] = schedule
                case "lblSelClockEditItem":
                    pv(kwargs)
                    x, y = cast(tuple[int, int], kwargs["mousepos"])
                    self._selclock_dlg.do_show(self._edititem_dlg, x+20, y+20, **kwargs)
                case "lblSelScheduleEditItem":
                    pv(kwargs)
                    x, y = cast(tuple[int, int], kwargs["mousepos"])
                    self._selschedule_dlg.do_show(self._edititem_dlg, x+20, y+20, **kwargs)
                case "btnDelItemEditItem":
                    pv(kwargs)
                    iid = cast(int, self._itemdetail_dlg.owner.process_message("getId"))
                    self._edititem_dlg.destroy()
                    _ = self._edititem_dlg.owner.process_message("deleteItem", id=iid)
                case "confirm":
                    return self._edititemdlg_confirm(**kwargs)
                case _:
                    return None
            return True
        return None

    @override
    # def process_message(self, id_ctrl: str, *args, **kwargs):
    def process_message(self, idmsg: str, **kwargs: Any):
        if idmsg.startswith("btnItem"):
            iid = int(idmsg[7:])
            # self._id = iid
            x, y = cast(tuple[int, int], kwargs["mousepos"])
            self._itemdetail_dlg.do_show(self, x+20, y+20, id=iid)
        elif idmsg.startswith("lblSum"):
            iid = int(idmsg[6:])
            # self._id = iid
            x, y = cast(tuple[int, int], kwargs["mousepos"])
            self._record_dlg.do_show(self, x+20, y+20, id=iid)
        elif idmsg.startswith("btnClock"):
            iid = int(idmsg[8:])
            # self._id = iid
            x, y = cast(tuple[int, int], kwargs["mousepos"])
            self._selclock_dlg.do_show(self, x+20, y+20, id=iid)
        else:
            match idmsg:
                case "NewItem":
                    # self._id = -1
                    x, y = self.pos
                    self._edititem_dlg.do_show(self, x+20, y+20, father=-1, id=0)
                # case "getId":
                    # return self._id
                case "changeItemImage":
                    iid = cast(int, kwargs["id"])
                    grp = cast(int, kwargs["group"])
                    idx = cast(int, kwargs["index"])
                    imagepath = self._get_imagepath(grp, idx)
                    _ = self.process_message("modify", id=iid, attrib="rid", val=(grp, idx))
                    # self.update_item(self._id, "image", imagepath)
                    self.update_item(iid, "image", imagepath)
                case "changeClock":
                    iid = cast(int, kwargs["id"])
                    clock = cast(str, kwargs["clock"])
                    clock = "" if clock=="选择定时提醒" else clock
                    # _ = self.process_message("modify", id=self._id, attrib="clock", val=clock)
                    _ = self.process_message("modify", id=iid, attrib="clock", val=clock)
                    # self.update_item(self._id, "clock", clock)
                    self.update_item(iid, "clock", clock)
                case "changeSchedule":
                    iid = cast(int, kwargs["id"])
                    schedule = cast(str, kwargs["schedule"])
                    schedule = "" if schedule=="选择时间投入计划" else schedule
                    # _ = self.process_message("modify", id=self._id, attrib="schedule", val=schedule)
                    _ = self.process_message("modify", id=iid, attrib="schedule", val=schedule)
                case "deleteItem":
                    # iid = self._id
                    iid = cast(int, kwargs["id"])
                    detail = cast(HourDict, self.process_message("getItemDetail", id=iid))
                    id_father = detail["father"]
                    if id_father == -1:
                        self.delete_control(f"frmGroup{iid}")
                    else:
                        self.delete_control(f"frmItem{iid}")
                        self.delete_control(f"btnItem{iid}")
                        self.delete_control(f"lblItem{iid}")
                        self.delete_control(f"btnClock{iid}")
                        self.delete_control(f"lblSum{iid}")
                    _ = self.process_message("delete", id=iid)
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
