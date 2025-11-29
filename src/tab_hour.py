#!/usr/bin/python3
# -*- coding: UTF-8 -*-
from __future__ import annotations
import datetime
from typing import cast
# import tkinter as tk

from pyutilities.logit import po, pv, pe
from pyutilities.winbasic import Widget, Dialog
from pyutilities.tkwin import tkWin
from pyutilities.tkwin import LabelCtrl, EntryCtrl, ButtonCtrl, ComboboxCtrl, ImageBtttonCtrl
from pyutilities.tkwin import PicsListviewCtrl, DialogCtrl, FrameCtrl
from pyutilities.matplot import MatPlotCtrl, LineData
# from pyutilities.calendarctrl import CalendarCtrl
from pyutilities.scrollpickerctrl import DateScrollPickerCtrl, TimeScrollPickerCtrl

from item_type import HourTuple, HourDict


class HourTab:
    _old_subid: int = 0
    # _subitem_list: list[ItemDict] = []
    _children: dict[int, HourTuple] = {}
    def __init__(self, gui: tkWin):
        self._gui: tkWin = gui
        self._images_dict: dict[int, dict[int, str]] = {
            0: {0: "items\\CircleFlagsUsBetsyRoss.png", 1: "items\\FlatUiNews.png", 
                2: "items\\gift.png", 3: "items\\VaadinAlarm.png"},
            1: {0: "items\\Course\\cpp.png", 1: "items\\Course\\MPC.png",
                2: "items\\Course\\Vehicle Engineering.png", 3: "items\\Course\\PMSM.png",
                4: "items\\Course\\Handwrite.png", 5: "items\\Course\\股票.png",
                6: "items\\Course\\管理.png", 7: "items\\Course\\绘画.png",
                8: "items\\Course\\机器视觉.png", 9: "items\\Course\\Calligraphy.png",
                10: "items\\Course\\语文.png", 11: "items\\Course\\自动化.png"},
            2: {0: "items\\Exercise\\锻炼.png", 1: "items\\Exercise\\俯卧撑.png",
                2: "items\\Exercise\\跑步.png", 3: "items\\Exercise\\平板支撑.png",
                4: "items\\Exercise\\足球.png"},
            3: {0: "items\\Language\\German.png", 1: "items\\Language\\Korean.png",
                2: "items\\Language\\Japanese.png", 3: "items\\Language\\English.png",
                4: "items\\Language\\Oral.png", 5: "items\\Language\\Listen.png",
                6: "items\\Language\\Read.png", 7: "items\\Language\\Write.png"},
            4: {0: "items\\Test\\CET-4.png", 1: "items\\Test\\CET-6.png",
                2: "items\\Test\\CFA.png", 3: "items\\Test\\CPA.png",
                4: "items\\Test\\GRE.png", 5: "items\\Test\\IELTS.png",
                6: "items\\Test\\TOEFL.png"}
        }

        self._selclock_dlg: DialogCtrl = cast(DialogCtrl, self._gui.get_control("dlgSelClock"))
        self._selclock_dlg.register_eventhandler("confirm", self._selclockdlg_confirm)

        self._selschedule_dlg: DialogCtrl = cast(DialogCtrl, self._gui.get_control("dlgSelSchedule"))
        self._selschedule_dlg.register_eventhandler("confirm", self._selscheduledlg_confirm)

        self._recordhour_dlg: DialogCtrl = cast(DialogCtrl, self._gui.get_control("dlgRecordHour"))
        self._recordhour_dlg.filter_message(self._recordhourdlg_processmessage)

        self._hourdetail_dlg: DialogCtrl = cast(DialogCtrl, self._gui.get_control("dlgHourDetail"))
        self._hourdetail_dlg.filter_message(self._hourdetaildlg_processmessage)

        self._edithour_dlg: DialogCtrl = cast(DialogCtrl, self._gui.get_control("dlgEditHour"))
        self._edithour_dlg.filter_message(self._edithourdlg_processmessage)

        msglst = ["btnNewHour", "changeClock", "ChangeSum",
            "changeSchedule", "changeItemImage", "deleteItem"]
        self._gui.filter_message(self._process_message, 1, msglst)

    def update_hour(self, uid: int, attrib: str, val: str | float):
        match attrib:
            case "name":
                ctrl_item1 = cast(LabelCtrl, self._gui.get_control(f"lblItem{uid}"))
                # ctrl_item1['text'] = val
                _ = ctrl_item1.configure(text=val, anchor='w')
            case "image":
                ctrl_item2 = cast(ImageBtttonCtrl, self._gui.get_control(f"btnItem{uid}"))
                ctrl_item2.change_image(cast(str, val))
            case "clock":
                if val in ["", "选择定时提醒"]:
                    return
                ctrl_item3 = cast(ImageBtttonCtrl, self._gui.get_control(f"btnClock{uid}"))
                if not ctrl_item3.visible:
                    ctrl_item3.show()
                # ctrl_item3['text'] = val
                _ = ctrl_item3.configure(text=val)
            case "sums":
                ctrl_item4 = cast(LabelCtrl, self._gui.get_control(f"lblSumHour{uid}"))
                _ = ctrl_item4.configure(text=f"{val:.1f}\nhours")
            case _:
                raise KeyError(f"Unkonw arrtrib: {attrib}")

        # _ = self._gui.process_message("modify", id_, attrib=attrib, val=val)

    def get_hour(self, uid: int, attrib: str) -> str:
        val: str = ""
        match attrib:
            case "name":
                ctrl_item1 = cast(LabelCtrl, self._gui.get_control(f"lblItem{uid}"))
                val = cast(str, ctrl_item1['text'])
            # case "image":
                # ctrl_item2 = cast(ImageBtttonCtrl, self._gui.get_control(f"btnItem{id_}")
                # raise NotImplementedError("")
            case "clock":
                ctrl_item3 = cast(ImageBtttonCtrl, self._gui.get_control(f"btnClock{uid}"))
                val = cast(str, ctrl_item3['text'])
            case "sums":
                ctrl_item4 = cast(LabelCtrl, self._gui.get_control(f"lblSumHour{uid}"))
                val = cast(str, ctrl_item4['text'])
            case _:
                val = ""
        return val

    def delete_father(self, father: int):
        children = cast(dict[int, HourDict], self._gui.process_message("getChildren", father=father))
        for sid in children.keys():
            self.delete_hour(father, sid)
        self.delete_hour(-1, father)

    def delete_hour(self, father: int, iid: int):
        self._gui.delete_control(f"frmItem{iid}")
        self._gui.delete_control(f"btnItem{iid}")
        self._gui.delete_control(f"lblItem{iid}")
        self._gui.delete_control(f"btnClock{iid}")
        self._gui.delete_control(f"lblSumHour{iid}")
        if father == -1:
            self._gui.delete_control(f"frmGroup{iid}")

    # def create_item(self, parent: object, iid: int, item: str, rid: int,
    def create_hour(self, iid: int, item: str, rid: tuple[int, int],
            clock: str, sums: str, is_subitem: bool = False):
        imagepath = self._get_imagepath(rid[0], rid[1])

        frmain = self._gui.get_control("frmHourMain")
        if is_subitem:
            # detail = cast(HourDict, self._gui.process_message("GetHourDetail", id=iid))
            detail = self._get_hourdetail(iid)
            fid = detail["father"]
            frmgroup = self._gui.get_control(f"frmGroup{fid}")
            item_padx1 = 15
            item_padx2 = 5
        else:
            xml = self._gui.create_xml("Frame", {"id":f"frmGroup{iid}"})
                 # "options":"{'borderwidth':1,'relief':'ridge'}"})
            _, frmgroup = self._gui.create_control(frmain, xml, 2)
            item_padx1 = 0
            item_padx2 = 5

        level = 3
        frmitem_xml = self._gui.create_xml("Frame", {"id": f"frmItem{iid}"})
        _, frm_item = self._gui.create_control(frmgroup, frmitem_xml, level)

        level = 4

        radio = 0.8 if is_subitem else 1.0

        btnitem_xml = self._gui.create_xml("ImageButton", {"id": f"btnItem{iid}",
            "image": imagepath,
            "options": f"{{'height': {int(60 * radio)}, 'width': {int(60 * radio)}}}"}, frmitem_xml)
        _, btn_item = self._gui.create_control(frm_item, btnitem_xml, level)
        self._gui.assemble_control(btn_item, {"layout":"grid",
            "grid":"{'row':0,'column':0,'rowspan':2}"}, '  '*level)

        lblitem_xml = self._gui.create_xml("Label", {"text": item,
            "id": f"lblItem{iid}", "options": "{'width':48}"}, frmitem_xml)
        # pv(lbl_item_xml)
        _, lbl_item = self._gui.create_control(frm_item, lblitem_xml, level)
        self._gui.assemble_control(lbl_item, {"layout":"grid",
            "grid":"{'row':0,'column':1,'sticky':'w'}"},
            f"{'  '*level}")

        btnclock_xml = self._gui.create_xml("ImageButton", {"id": f"btnClock{iid}",
            "text": clock, "image": "VaadinAlarm.png",
             "options": "{'height':20, 'width':20}"}, frmitem_xml)
        _, btn_clock = self._gui.create_control(frm_item, btnclock_xml, level)
        self._gui.assemble_control(btn_clock, {"layout":"grid",
            "grid":"{'row':1,'column':1,'sticky':'w'}"}, f"{'  '*level}")

        if clock in ["", "选择定时提醒"]:
            # cast(tk.Widget, btn_clock).grid_remove()
            cast(ImageBtttonCtrl, btn_clock).hide()

        lblsum_xml = self._gui.create_xml("Label", {"id": f"lblSumHour{iid}",
            "text": f"{sums}\nhours", "clickable": "true",
            "options":"{'justify':'center'}"}, frmitem_xml)
        _, lbl_sum = self._gui.create_control(frm_item, lblsum_xml, level)
        self._gui.assemble_control(lbl_sum, {"layout":"grid",
            "grid":"{'row':0,'column':2,'rowspan':2,'sticky':'w'}"}, f"{'  '*level}")

        self._gui.assemble_control(frm_item, {"layout": "pack",
            "pack": f"{{'side':'top','pady':1,'padx':({item_padx1},{item_padx2})}}"},
            f"{'  '*(level-1)}")

        if not is_subitem:
            if iid == 1:
                pady1 = 10
            else:
                pady1 = 5
            self._gui.assemble_control(frmgroup, {"layout": "pack",
                "pack":f"{{'side':'top','pady':({pady1},5),'fill':'x'}}"}, f"{'  '*(2-1)}")

    def get_childattrib(self, uid: int, attrib: str) -> str:
        val: str = ""
        match attrib:
            case "name":
                ctrl_item1 = cast(LabelCtrl, self._gui.get_control(f"lblChild{uid}"))
                val = cast(str, ctrl_item1['text'])
            # case "image":
                # ctrl_item2: = cast(ImageBtttonCtrl, self._gui.get_control(f"btnItem{id_}")
                # raise NotImplementedError("")
            # case "clcok":
                # ctrl_item3 = cast(LabelCtrl, self._gui.get_control(f"lblClock{id_}"))
                # val = ctrl_item3['text']
            case "sum":
                ctrl_item4 = cast(LabelCtrl, self._gui.get_control(f"lblSubSum{uid}"))
                val = cast(str, ctrl_item4['text'])
            case _:
                val = ""
        return val

    def _create_child(self, parent: Widget, uid: int, sub_item: str,
            rid: tuple[int, int], sums: str):
        imagepath = self._get_imagepath(rid[0], rid[1])

        level = 2
        frm_child_xml = self._gui.create_xml("Frame", {"id": f"frmSub{uid}"})
        _, frm_child = self._gui.create_control(parent, frm_child_xml, level)

        level = 3

        pnlitem_xml = self._gui.create_xml("ImagePanel", {"id": f"pnlChild{uid}",
            "image": imagepath, 
            "options": "{'height':20, 'width':20}"}, frm_child_xml)
        _, pnl_item = self._gui.create_control(frm_child, pnlitem_xml, level)
        self._gui.assemble_control(pnl_item, {"layout":"pack",
            "pack":"{'side':'left','anchor':'w'}"}, '  '*level)

        lblitem_xml = self._gui.create_xml("Label", {"id": f"lblChild{uid}", 
            "text": sub_item, "options": "{'width':40}"}, frm_child_xml)
        _, lbl_subitem = self._gui.create_control(frm_child, lblitem_xml, level)
        self._gui.assemble_control(lbl_subitem, {"layout":"pack",
            "pack":"{'side':'left','anchor':'w'}"}, f"{'  '*level}")

        lblsum_xml = self._gui.create_xml("Label", {"text": f"{sums}h",
            "id": f"lblSubSum{uid}"}, frm_child_xml)
        _, lbl_sum = self._gui.create_control(frm_child, lblsum_xml, level)
        self._gui.assemble_control(lbl_sum, {"layout":"pack",
            "pack":"{'side':'left','anchor':'e'}"}, f"{'  '*level}")

        self._gui.assemble_control(frm_child, {"layout": "grid",
            "grid": f"{{'row':{uid},'column':0,'pady':4}}"}, f"{'  '*(level-1)}")

    def _delete_child(self, sid: int):
        self._gui.delete_control(f"frmSub{sid}")
        self._gui.delete_control(f"pnlChild{sid}")
        self._gui.delete_control(f"lblChild{sid}")
        self._gui.delete_control(f"lblSubSum{sid}")

    def _get_imagepath(self, group: int, index: int):
        return self._images_dict[group].get(index, "CircleFlagsUsBetsyRoss.png")

    def show_selclockdlg(self, owner: Dialog | None = None, x: int = 0, y: int = 0, **kwargs: object):
        self._selclock_dlg.do_show(owner, x+20, y+20, **kwargs)

    def _selclockdlg_confirm(self, **kwargs: object) -> tuple[bool, str]:
        po(f"_selclockdlg_confirm: {kwargs}")
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
        _ = self._selclock_dlg.owner.process_message("changeClock", clock=clock, **kwargs)
        return True, ""

    def _selscheduledlg_confirm(self, **kwargs: object) -> tuple[bool, str]:
        po(f"_selscheduledlg_confirm: {kwargs}")
        cmb_selunit = cast(ComboboxCtrl, self._selclock_dlg.get_control("cmbSelUnit"))
        sel_unit = cmb_selunit.get_val()
        pv(sel_unit)
        cmb_selval = cast(ComboboxCtrl, self._selclock_dlg.get_control("cmbSelVal"))
        sel_val = cmb_selval.get_val()
        pv(sel_val)
        schedule = f"计划{sel_unit}{sel_val}"
        _ = self._selschedule_dlg.owner.process_message("changeSchedule", schedule=schedule, **kwargs)
        return True, ""

    def show_recordhourdlg(self, owner: Dialog | None = None, x: int = 0, y: int = 0,
            **kwargs: object):
        self._recordhour_dlg.do_show(owner, x+20, y+20, **kwargs)

    def _recordhourdlg_beforego(self, **kwargs: object):
        po(f"_recordhourdlg_beforego: {kwargs}")
        iid = cast(int, kwargs["id"])
        detail = self._get_hourdetail(iid)

        lbl_item = cast(LabelCtrl, self._gui.get_control("lblItemRecordHour"))
        lbl_item.set_text(detail["name"])

        today = datetime.date.today()
        lbl_day = cast(LabelCtrl, self._gui.get_control("lblSelDayRecordHour"))
        lbl_day.set_text(str(today))

        lbl_strtime = cast(LabelCtrl, self._gui.get_control("lblSelStrtRecordHour"))
        clock = detail["clock"]     # clock = 每工作日 21:00
        clock_val = clock[-5:].strip()
        if not clock_val:
            now = datetime.datetime.now()
            clock_val = f"{now.hour}:{now.minute:02d}"
        lbl_strtime.set_text(clock_val)

        lbl_lastime = cast(LabelCtrl, self._gui.get_control("lblSelLastRecordHour"))
        schedule = detail["schedule"]   # schedule = 计划每日45m
        schedule_val = schedule[4:]
        if not schedule_val:
            schedule_val = "15m"
        lbl_lastime.set_text(schedule_val)

    def _recordhourdlg_selday(self, **kwargs: object):
        x, y = cast(tuple[int, int], kwargs["mousepos"])
        scrollpicker = DateScrollPickerCtrl((x, y+20), "选择日期")
        date = scrollpicker.get_datestr()
        pv(date)
        lbl_day = cast(LabelCtrl, self._gui.get_control("lblSelDayRecordHour"))
        lbl_day.set_text(date)

    def _recordhourdlg_selstrtime(self, **kwargs: object):
        lbl_strtime = cast(LabelCtrl, self._gui.get_control("lblSelStrtRecordHour"))
        x, y = cast(tuple[int, int], kwargs["mousepos"])
        scrollpicker = TimeScrollPickerCtrl((x, y+20), "开始时间", lbl_strtime.get_text())
        strt_time = scrollpicker.get_datestr()
        pv(strt_time)
        lbl_strtime = cast(LabelCtrl, self._gui.get_control("lblSelStrtRecordHour"))
        lbl_strtime.set_text(strt_time)

    def _schedule_txt2clk(self, txt: str):
        if not txt:
            return "00:00"
        clk = txt.replace("h", ":").replace("m", "")
        if ":" not in clk:
            clk = "00:" + clk
        return clk

    def _recordhourdlg_selastime(self, **kwargs: object):
        lbl_lastime = cast(LabelCtrl, self._gui.get_control("lblSelLastRecordHour"))
        lastime = self._schedule_txt2clk(lbl_lastime.get_text())
        x, y = cast(tuple[int, int], kwargs["mousepos"])
        scrollpicker = TimeScrollPickerCtrl((x, y+20), "持续时间", lastime)
        lastime = scrollpicker.get_datestr()
        if lastime.startswith("00"):
            lastime = lastime[3:]
        lastime += "m"

        lbl_lastime = cast(LabelCtrl, self._gui.get_control("lblSelLastRecordHour"))
        lbl_lastime.set_text(lastime)

    def _recordhourdlg_confirm(self, **kwargs: object) -> tuple[bool, str]:
        po(f"_recordhourdlg_confirm: {kwargs}")
        iid = cast(int, kwargs["id"])

        lbl_day = cast(LabelCtrl, self._gui.get_control("lblSelDayRecordHour"))
        day = lbl_day.get_text()

        lbl_strtime = cast(LabelCtrl, self._gui.get_control("lblSelStrtRecordHour"))
        strt_time = lbl_strtime.get_text()

        strt = datetime.datetime.strptime(f"{day} {strt_time}", "%Y-%m-%d %H:%M")
        po(f"Start time: {strt}")

        lbl_lastime = cast(LabelCtrl, self._gui.get_control("lblSelLastRecordHour"))
        last_time = self._schedule_txt2clk(lbl_lastime.get_text()).split(":")
        # pv(last_time)
        last_hour = int(last_time[0])
        last_minute = int(last_time[1])
        delta = datetime.timedelta(hours=last_hour, minutes=last_minute)
        # pv(delta)
        end = strt + delta
        po(f"end time: {end}")
        _ = self._gui.process_message("RecordHour", id=iid, strt=strt, end=end)
        detail = self._get_hourdetail(iid)
        sums_hours = float(detail["sums"]) / 60
        pv(sums_hours)
        _ = self._recordhour_dlg.owner.process_message("ChangeSum", id=iid, sum=sums_hours)
        return True, ""

    def _recordhourdlg_processmessage(self, idmsg: str, **kwargs: object):
        if self._recordhour_dlg.alive:
            match idmsg:
                case "beforego":
                    self._recordhourdlg_beforego(**kwargs)
                case "lblSelDayRecordHour":
                    self._recordhourdlg_selday(**kwargs)
                case "lblSelStrtRecordHour":
                    self._recordhourdlg_selstrtime(**kwargs)
                case "lblSelLastRecordHour":
                    self._recordhourdlg_selastime(**kwargs)
                case "confirm":
                    return self._recordhourdlg_confirm(**kwargs)
                case _:
                    return None
            return True
        return None

    def _update_hourdetail(self, attrib: str, val: str | float):
        match attrib:
            case "name":
                lbl_item = cast(LabelCtrl, self._gui.get_control("lblInfoHourDetail"))
                text_list = lbl_item.get_text().split("\n")
                text_list[0] = str(val)
                lbl_item.set_text(f"{text_list[0]}\n{text_list[1]}")
            case "StartDate":
                lbl_item = cast(LabelCtrl, self._gui.get_control("lblInfoHourDetail"))
                text_list = lbl_item.get_text().split("\n")
                if val:
                    text_list[1] = str(val)
                else:
                    text_list[1] = "从未开始"
                lbl_item.set_text(f"{text_list[0]}\n{text_list[1]}")
            case "sum":
                lbl_sum = cast(LabelCtrl, self._gui.get_control("lblSumHourDetail"))
                lbl_sum.set_text(f"{val}\nhours")
            case "TotalDays":
                lbl_item = cast(LabelCtrl, self._gui.get_control("lblWholeHourDetail"))
                lbl_item.set_text(f"{val}\n坚持天数")
            case "HoursEveryWeek":
                lbl_item = cast(LabelCtrl, self._gui.get_control("lblAvrgHourDetail"))
                lbl_item.set_text(f"{val}h\n平均每周")
            case "HoursLast7Days":
                lbl_item = cast(LabelCtrl, self._gui.get_control("lblRecentHourDetail"))
                lbl_item.set_text(f"{val}h\n最近七天")
            case "RestHours2Milestone":
                lbl_item = cast(LabelCtrl, self._gui.get_control("lblRestHourDetail"))
                lbl_item.set_text(f"{val}\n距离里程碑")
            case _:
                raise KeyError(f"Unkonw arrtrib: {attrib}")

    def show_hourdetaildlg(self, owner: Dialog | None = None, x: int = 0, y: int = 0,
            **kwargs: object):
        self._hourdetail_dlg.do_show(owner, x+20, y+20, **kwargs)

    # TODO: Statistics
    def _hourdetaildlg_beforego(self, **kwargs: object):
        po(f"_hourdetaildlg_beforego: {kwargs}")
        iid = cast(int, kwargs["id"])
        # detail = cast(HourDict, self._gui.process_message("GetHourDetail", id=iid))
        detail = self._get_hourdetail(iid)
        # po(f"{iid}: {detail}")

        lbl_father = cast(LabelCtrl, self._gui.get_control("lblFatherItemDetail"))
        fid = detail["father"]
        if fid != -1:
            # detail_father = cast(HourDict, self._gui.process_message("GetHourDetail", id=id_father))
            detail_father = self._get_hourdetail(fid)
            name_father = detail_father["name"]
            pv(name_father)
            lbl_father['text'] = name_father
        else:
            lbl_father.hide()

        rid = detail["rid"]
        imagepath = self._get_imagepath(rid[0], rid[1])
        img_item = cast(ImageBtttonCtrl, self._gui.get_control("btnImageHourDetail"))
        img_item.change_image(imagepath)

        # self._update_hourdetail("name", detail["name"])
        strt_date = cast(str, self._gui.process_message("GetHourStartDate", id=iid))
        # self._update_hourdetail("StartDate", strt_date)
        lbl_item = cast(LabelCtrl, self._gui.get_control("lblInfoHourDetail"))
        lbl_item.set_text(f"{detail["name"]}\n从{strt_date}开始")
        self._update_hourdetail("sum", f"{detail["sums"]/ 60:.1f}")
        total_days = cast(float, self._gui.process_message("GetHourTotalDays", id=iid))
        self._update_hourdetail("TotalDays", total_days)
        hours_everyweek = cast(float, self._gui.process_message("GetHoursEveryWeek", id=iid))
        self._update_hourdetail("HoursEveryWeek", f"{hours_everyweek:.1f}")
        hours_last7days = cast(float, self._gui.process_message("GetHoursLast7Days", id=iid))
        self._update_hourdetail("HoursLast7Days", f"{hours_last7days:.1f}")
        hours_2milestone = cast(float, self._gui.process_message("GetHours2Milestone",
            id=iid))
        self._update_hourdetail("RestHours2Milestone", hours_2milestone)

        lbl_selclock = cast(LabelCtrl, self._gui.get_control("lblSelClockItemDetail"))
        # clock = data["clock"]
        lbl_selclock['text'] = detail["clock"]
        lbl_selschedule = cast(LabelCtrl, self._gui.get_control("lblSelScheduleItemDetail"))
        lbl_selschedule['text'] = detail["schedule"]

        parent = cast(FrameCtrl, self._gui.get_control("frmSubItmes"))
        # get subitem info(rid, name, sums) of id
        children = cast(dict[int, HourDict], self._gui.process_message("getChildren", father=iid))
        idx = 0
        for sid, child in children.items():
            self._children[idx] = HourTuple(iid=sid, name=child["name"], rid=child["rid"],
                clock=child["clock"], schedule=child["schedule"], sums=child["sums"],
                father=child["father"])
            self._create_child(parent, idx, child["name"],
                child["rid"], f"{child["sums"] / 60}")
            idx += 1
        pv(self._children)
        self._old_subid = len(self._children) - 1
        lbl_totalsubitems = cast(LabelCtrl, self._gui.get_control("lblTotalChildren"))
        lbl_totalsubitems["text"] = f"共{idx}个子项目"

        week_day = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

        limit_ydata: list[float] = [0] * 7
        
        schedule = detail["schedule"]   # schedule = 计划每日45m
        if schedule:
            per_typ = schedule[3]
            unit = 1
            match per_typ:
                case "日":
                    unit = 1
                case "周":
                    unit = 7
                case "月":
                    unit = 30
                case _:
                    unit = 360
            pv(unit)
            lastime = schedule[4:-1]
            hour_pos = lastime.find("h")
            total_minutes = 0
            if hour_pos == -1:
                total_minutes = int(lastime)
            else:
                total_minutes = int(lastime[:hour_pos])*60 + int(lastime[hour_pos + 1:])
            per_minutes = total_minutes / unit
            clock = detail["clock"]     # clock = 每工作日 21:00
            if clock:
                day_typ = clock[1:-6]
                pv(day_typ)
                match day_typ:
                    case "工作日":
                        limit_ydata = [per_minutes, per_minutes, per_minutes, \
                            per_minutes, per_minutes, 0, 0]
                    case "节假日":
                        limit_ydata = [0, 0, 0, 0, 0, per_minutes, per_minutes]
                    case _:
                        limit_ydata = [per_minutes, per_minutes, per_minutes, \
                            per_minutes, per_minutes, per_minutes, per_minutes]

        plt_everyday = cast(MatPlotCtrl, self._gui.get_control("pltEveryDayHour"))
        xdata: list[int] = []
        father_ydata: list[float] = []
        children_ydata: dict[int, list[float]] = {}
        labels: list[str] = []
        today = datetime.datetime.today().date()
        monday = today + datetime.timedelta(days=-today.weekday())
        for i in range(7):
            day = monday + datetime.timedelta(days=i)
            weekday = day.weekday()
            labels.append(f"{week_day[weekday]}\n{day.day}")
            xdata.append(i)
            minutes = cast(float, self._gui.process_message("GetHoursbyDay", id=iid, day=day)) * 60
            father_ydata.append(minutes)
            # limit_ydata.append(1.0)
            po(f"minutes of {day} is {minutes}")
            for sid in children.keys():
                minutes = cast(float, self._gui.process_message("GetHoursbyDay", id=sid, day=day)) * 60
                if children_ydata.get(sid) is None:
                    children_ydata[sid] = [minutes]
                else:
                    children_ydata[sid].append(minutes)
        plt_everyday.xdata = xdata
        father_yline = LineData(father_ydata,
            {"tick_label":labels,"width":0.4,"facecolor":"green"}, "bar")
            # {"width":0.4,"facecolor":"green"}, "bar")
        _ = plt_everyday.add_line(father_yline)
        bottom = father_ydata
        for sid, child_ydata in children_ydata.items():
            child_yline = LineData(child_ydata, {"width":0.4,"bottom":bottom}, "bar")
            bottom = child_ydata
            _ = plt_everyday.add_line(child_yline)
        limit_yline = LineData(limit_ydata, {"linestyle":"dotted","color":"red"})
        _ = plt_everyday.add_line(limit_yline)
        plt_everyday.draw()

        thismonth = today.month
        for i in range(6):
            month = thismonth - i
            hours = cast(float, self._gui.process_message("GetHoursbyMonth", id=iid, month=month))
            po(f"hours of {month} is {hours}")

        thisyear = today.year
        for i in range(6):
            year = thisyear - i
            hours = cast(float, self._gui.process_message("GetHoursbyYear", id=iid, year=year))
            po(f"hours of {year} is {hours}")

    def _hourdetaildlg_confirm(self, **kwargs: object) -> tuple[bool, str]:
        po(f"_hourdetaildlg_confirm: {kwargs}")
        for idx, child in self._children.items():
            if idx > self._old_subid:
                name =      child.name
                sums =      child.sums
                rid =       child.rid
                clock =     child.clock
                schedule =  child.schedule
                father = cast(int, kwargs["id"])
                iid = cast(int, self._gui.process_message("AddHour", father=father, name=name,
                    rid=rid, clock=clock, schedule=schedule, sums=sums))
                self.create_hour(iid, name, rid, clock, f"{sums/60:.1f}", True)
            self._delete_child(idx)
        self._children.clear()
        return True, ""

    def _hourdetaildlg_cancel(self, **kwargs: object) -> tuple[bool, str]:
        po(f"_hourdetaildlg_cancel: {kwargs}")
        for idx, _ in self._children.items():
            self._delete_child(idx)
        self._children.clear()
        return True, ""

    def _hourdetaildlg_processmessage(self, idmsg: str, **kwargs: object):
        if self._hourdetail_dlg.alive:
            iid = cast(int, kwargs["id"])
            match idmsg:
                case "beforego":
                    self._hourdetaildlg_beforego(**kwargs)
                case "changeItemImage":
                    grp = cast(int, kwargs["group"])
                    idx = cast(int, kwargs["index"])
                    imagebutton = cast(ImageBtttonCtrl, self._gui.get_control("btnImageHourDetail"))
                    imagepath = self._get_imagepath(grp, idx)
                    # pv(imagepath)
                    imagebutton.change_image(imagepath)
                    _ = self._hourdetail_dlg.owner.process_message("changeItemImage",
                        id=iid, group=grp, index=idx)
                case "changeClock":
                    clock = cast(str, kwargs["clock"])
                    lbl_selclock = cast(LabelCtrl,
                        self._gui.get_control("lblSelClockItemDetail"))
                    lbl_selclock['text'] = clock
                    self.update_hour(iid, "clock", clock)
                    _ = self._hourdetail_dlg.owner.process_message("changeClock", id=iid, clock=clock)
                case "changeSchedule":
                    schedule = cast(str, kwargs["schedule"])
                    lbl_selschedule = cast(LabelCtrl,
                        self._gui.get_control("lblSelScheduleItemDetail"))
                    lbl_selschedule['text'] = schedule
                    _ = self._hourdetail_dlg.owner.process_message("changeSchedule",
                        id=iid, schedule=schedule)
                case "ChangeSum":
                    sums_hours= cast(float, kwargs["sum"])
                    lbl_sum = cast(LabelCtrl, self._gui.get_control("lblSumHourDetail"))
                    lbl_sum.set_text(f"{sums_hours:.1f}\nhours")
                    self.update_hour(iid, "sums", sums_hours)
                case "btnImageHourDetail":
                    # detail = cast(HourDict, self._gui.process_message("GetHourDetail", id=iid))
                    detail = self._get_hourdetail(iid)
                    father = detail["father"]
                    x, y = cast(tuple[int, int], kwargs["mousepos"])
                    self._edithour_dlg.do_show(self._hourdetail_dlg, x+20, y+20,
                        father=father, id=iid)
                case "btnAddChild":
                    x, y = cast(tuple[int, int], kwargs["mousepos"])
                    self._edithour_dlg.do_show(self._hourdetail_dlg, x+20, y+20,
                        father=iid, id=0)
                case "btnRecordHourDetail":
                    # detail = cast(HourDict, self._gui.process_message("GetHourDetail", id=iid))
                    detail = self._get_hourdetail(iid)
                    father = detail["father"]
                    x, y = cast(tuple[int, int], kwargs["mousepos"])
                    self._recordhour_dlg.do_show(self._hourdetail_dlg, x+20, y+20,
                        father=father, id=iid)
                case "deleteItem":
                    self._hourdetail_dlg.destroy()
                    _ = self._hourdetail_dlg.owner.process_message("deleteItem", id=iid)
                case "confirm":
                    return self._hourdetaildlg_confirm(**kwargs)
                case "cancel":
                    return self._hourdetaildlg_cancel(**kwargs)
                case _:
                    return None
            return True
        return None

    def _edithourdlg_beforego(self, **kwargs: object):
        po(f"_edithourdlg_beforego: {kwargs}")
        fid = cast(int, kwargs["father"])
        iid = cast(int, kwargs["id"])

        if fid != -1:
            lbl_father = cast(LabelCtrl, self._gui.get_control("lblSelFatherEditHour"))
            # detail_father = cast(HourDict, self._gui.process_message("GetHourDetail", id=fid))
            detail_father = self._get_hourdetail(fid)
            name_father = detail_father["name"]
            pv(name_father)
            lbl_father['text'] = name_father

        if iid == 0:
            self._edithour_dlg.set_title("新建项目")
            btn_delhour = cast(ButtonCtrl, self._gui.get_control("btnDelItemEditHour"))
            btn_delhour.hide()
            grp, idx = 0, 0
        else:
            self._edithour_dlg.set_title("编辑项目")
            # detail = cast(HourDict, self._gui.process_message("GetHourDetail", id=iid))
            detail = self._get_hourdetail(iid)
            pv(detail)

            ent_name = cast(EntryCtrl, self._gui.get_control("txtItemEditHour"))
            ent_name.set_val(detail["name"])
            ent_name.disable()
            lbl_selclock = cast(LabelCtrl, self._gui.get_control("lblSelClockEditHour"))
            lbl_selclock['text'] = detail["clock"] if detail["clock"] else "选择定时提醒"
            lbl_selschedule = cast(LabelCtrl, self._gui.get_control("lblSelScheduleEditHour"))
            lbl_selschedule['text'] = detail["schedule"] if detail["schedule"] else "选择时间投入计划"
            grp, idx = detail["rid"]

        list_itemimage = cast(PicsListviewCtrl, self._gui.get_control("lstImageEditHour"))
        # list_itemimage.display_images(list(self._images_dict.values()))
        list_itemimage.add_imagegroup("一般", list(self._images_dict[0].values()))
        list_itemimage.add_imagegroup("课程", list(self._images_dict[1].values()))
        list_itemimage.add_imagegroup("锻炼", list(self._images_dict[2].values()))
        list_itemimage.add_imagegroup("语言", list(self._images_dict[3].values()))
        list_itemimage.add_imagegroup("考试", list(self._images_dict[4].values()))

        list_itemimage.select(grp, idx)

    # TODO: only change those which are modified
    def _edithourdlg_confirm(self, **kwargs: object):
        po(f"_edithourdlg_confirm: {kwargs}")
        father = cast(int, kwargs["father"])
        iid = cast(int, kwargs["id"])
        if iid != 0:    # edit item
            lbl_selclock = cast(LabelCtrl, self._gui.get_control("lblSelClockEditHour"))
            clock = cast(str, lbl_selclock['text'])
            pv(clock)
            _ = self._edithour_dlg.owner.process_message("changeClock", id=iid, clock=clock)

            lbl_selschedule = cast(LabelCtrl, self._gui.get_control("lblSelScheduleEditHour"))
            schedule = cast(str, lbl_selschedule['text'])
            pv(schedule)
            _ = self._edithour_dlg.owner.process_message("changeSchedule", id=iid, schedule=schedule)

            lst_itemimage = cast(PicsListviewCtrl,
                self._gui.get_control("lstImageEditHour"))
            grp, idx = lst_itemimage.get_selected()
            _ = self._edithour_dlg.owner.process_message("changeItemImage",
                id=iid, group=grp, index=idx)
        else:   # New item
            ent_name = cast(EntryCtrl, self._gui.get_control("txtItemEditHour"))
            name = ent_name.get_val()
            # pv(name)
            if len(name) == 0:
                return False, "Name should not be empty"
            lbl_selclock = cast(LabelCtrl, self._gui.get_control("lblSelClockEditHour"))
            clock  = cast(str, lbl_selclock['text'])
            clock_val = "" if clock == "选择定时提醒" else clock
            lbl_selschedule = cast(LabelCtrl, self._gui.get_control("lblSelScheduleEditHour"))
            schedule = cast(str, lbl_selschedule['text'])
            schedule_val = "" if schedule == "选择时间投入计划" else schedule
            lst_itemimage = cast(PicsListviewCtrl,
                self._gui.get_control("lstImageEditHour"))
            rid = lst_itemimage.get_selected()
            if father == -1:
                iid = cast(int, self._gui.process_message("AddHour",
                    name=name, rid=rid, clock=clock_val, schedule=schedule_val, father=father))
                self.create_hour(iid, name, rid, clock, '0.0')
            else:
                idx = len(self._children)
                parent = cast(FrameCtrl, self._gui.get_control("frmSubItmes"))
                self._create_child(parent, idx, name, rid, '0.0')
                self._children[idx] = HourTuple(iid=0, name=name, rid=rid,
                    clock=clock_val, schedule=schedule_val, sums=0, father=father)
                lbl_totalsubitems = cast(LabelCtrl, self._gui.get_control("lblTotalChildren"))
                lbl_totalsubitems["text"] = f"共{len(self._children)}个子项目"
                # self._old_subid += 1
        return True, ""

    def _edithourdlg_processmessage(self, idmsg: str, **kwargs: object):
        if self._edithour_dlg.alive:
            iid = cast(int, kwargs["id"])
            match idmsg:
                case "beforego":
                    self._edithourdlg_beforego(**kwargs)
                case "changeClock":
                    clock = cast(str, kwargs["clock"])
                    lbl_selclock = cast(LabelCtrl, self._gui.get_control("lblSelClockEditHour"))
                    lbl_selclock['text'] = clock
                case "changeSchedule":
                    schedule = cast(str, kwargs["schedule"])
                    lbl_selschedule = cast(LabelCtrl, self._gui.get_control("lblSelScheduleEditHour"))
                    lbl_selschedule['text'] = schedule
                case "lblSelClockEditHour":
                    pv(kwargs)
                    x, y = cast(tuple[int, int], kwargs["mousepos"])
                    self._selclock_dlg.do_show(self._edithour_dlg, x+20, y+20, **kwargs)
                case "lblSelScheduleEditHour":
                    pv(kwargs)
                    x, y = cast(tuple[int, int], kwargs["mousepos"])
                    self._selschedule_dlg.do_show(self._edithour_dlg, x+20, y+20, **kwargs)
                case "btnDelItemEditHour":
                    pv(kwargs)
                    iid = cast(int, self._hourdetail_dlg.owner.process_message("getId"))
                    self._edithour_dlg.destroy()
                    _ = self._edithour_dlg.owner.process_message("deleteItem", id=iid)
                case "confirm":
                    return self._edithourdlg_confirm(**kwargs)
                case _:
                    return None
            return True
        return None

    def _get_hourdetail(self, iid: int):
        detail: HourDict = {"name": "", "rid": (0, 0), "clock": "", "schedule": "",
            "sums": 0, "father": -1}
        _ = self._gui.process_message("GetHourDetail", id=iid, detail=detail)
        return detail

    def _process_message(self, idmsg: str, **kwargs: object):
        match idmsg:
            case "btnNewHour":
                x, y = cast(tuple[int, int], kwargs["mousepos"])
                self._edithour_dlg.do_show(self._gui, x+20, y+20, father=-1, id=0)
            case "changeItemImage":
                iid = cast(int, kwargs["id"])
                grp = cast(int, kwargs["group"])
                idx = cast(int, kwargs["index"])
                imagepath = self._get_imagepath(grp, idx)
                _ = self._gui.process_message("ModifyHourAttr", id=iid, attrib="rid", val=(grp, idx))
                self.update_hour(iid, "image", imagepath)
            case "changeClock":
                iid = cast(int, kwargs["id"])
                clock = cast(str, kwargs["clock"])
                clock = "" if clock=="选择定时提醒" else clock
                _ = self._gui.process_message("ModifyHourAttr", id=iid,
                    attrib="clock", val=clock)
                self.update_hour(iid, "clock", clock)
            case "changeSchedule":
                iid = cast(int, kwargs["id"])
                schedule = cast(str, kwargs["schedule"])
                schedule = "" if schedule=="选择时间投入计划" else schedule
                _ = self._gui.process_message("ModifyHourAttr", id=iid,
                    attrib="schedule", val=schedule)
            case "ChangeSum":
                iid = cast(int, kwargs["id"])
                sums_hours= cast(float, kwargs["sum"])
                self.update_hour(iid, "sums", sums_hours)
            case "deleteItem":
                iid = cast(int, kwargs["id"])
                # detail = cast(HourDict, self._gui.process_message("GetHourDetail", id=iid))
                detail = self._get_hourdetail(iid)
                id_father = detail["father"]
                if id_father == -1:
                    self._gui.delete_control(f"frmGroup{iid}")
                else:
                    self._gui.delete_control(f"frmItem{iid}")
                    self._gui.delete_control(f"btnItem{iid}")
                    self._gui.delete_control(f"lblItem{iid}")
                    self._gui.delete_control(f"btnClock{iid}")
                    self._gui.delete_control(f"lblSum{iid}")
                    _ = self._gui.process_message("DelHour", id=iid)
            case _:
                return self._gui.process_message(idmsg, **kwargs)
        return True
