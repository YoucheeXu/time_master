#!/usr/bin/python3
# -*- coding: UTF-8 -*-
from __future__ import annotations

import datetime
import math
import re
import tkinter as tk
import uuid
import xml.etree.ElementTree as et
from enum import IntEnum
from typing import NamedTuple, TypedDict, cast, override

from matplotlib import backend_bases
from matplotlib.colors import to_hex
from matplotlib.container import BarContainer
from matplotlib.patches import Rectangle
from pygui_simple.tkmatplot import LineData, MatPlotCtrl

# from pygui.tkcalendar import CalendarCtrl
from pygui_simple.tkscrollpicker import DateScrollPickerDialog, TimeScrollPickerDialog
from pygui_simple.tkslideswitch import SlideSwitchCtrl
from pygui_simple.tkwin import (
    ButtonCtrl,
    CanvasCtrl,
    ComboboxCtrl,
    DialogCtrl,
    EntryCtrl,
    FrameCtrl,
    ImageBtttonCtrl,
    ImagePanelCtrl,
    LabelCtrl,
    PicsListviewCtrl,
    tkWin,
)
from pygui_simple.winbasic import Container, Dialog, Widget
from pyutilities_simple.logit import pe, po, pv

from src.action_sys import ActTyp
from src.schedule import Schedule
from src.time_database import TimeDatabase
from src.time_database_type import (
    DayType,
    IconTuple,
    PlanDataDict,
    ReminderDataDict,
    TimeUnit,
    default_plan_data,
    default_reminder_data,
    reminder2str,
    str2reminder,
    time2str,
)


class HourTuple(NamedTuple):
    hid: int
    name: str
    iid: IconTuple
    fid: int
    reminders: dict[int, ReminderDataDict]
    sums: int


class RecordHourDlg(DialogCtrl):
    """_summary_

    """
    def __init__(self, app: tkWin, dlg_cfg: et.Element):
        """_summary_

        Args:
            app (tkWin): _description_
            dlg_cfg (et.Element): _description_
        """
        super().__init__(app, dlg_cfg)

    def _get_hourdetail(self, db: TimeDatabase, hid: int):
        """_summary_

        Args:P
            iid (int): _description_

        Returns:
            _type_: _description_
        """
        return db.get_plandata(hid)

    @override
    def _beforego(self, **kwargs: object):
        iid = cast(int, kwargs["id"])
        db = cast(TimeDatabase, kwargs["db"])
        detail = self._get_hourdetail(db, iid)

        lbl_item = cast(LabelCtrl, self.get_control("lblItemRecordHour"))
        lbl_item.set_text(detail["name"])

        today = datetime.date.today()
        lbl_day = cast(LabelCtrl, self.get_control("lblSelDayRecordHour"))
        lbl_day.set_text(str(today))

        # TODO: get now's nearby reminder
        reminders = detail["reminders"]
        reminder = next(iter(reminders.values()))

        lbl_strtime = cast(LabelCtrl, self.get_control("lblSelStrtRecordHour"))
        clock_val = time2str(reminder['clk_time'])
        if not clock_val:
            now = datetime.datetime.now()
            clock_val = f"{now.hour}:{now.minute:02d}"
        lbl_strtime.set_text(clock_val)

        lbl_lastime = cast(LabelCtrl, self.get_control("lblSelLastRecordHour"))
        schedule = reminder["duration"]
        schedule_val = f"{schedule}m"
        lbl_lastime.set_text(schedule_val)

    def _select_day(self, **kwargs: object):
        """_summary_
        """
        x, y = cast(tuple[int, int], kwargs["mousepos"])
        scrollpicker = DateScrollPickerDialog((x, y+20), "选择日期")
        date = scrollpicker.get_datestr()
        pv(date)
        lbl_day = cast(LabelCtrl, self.get_control("lblSelDayRecordHour"))
        lbl_day.set_text(date)

    def _select_strtime(self, **kwargs: object):
        """_summary_
        """
        lbl_strtime = cast(LabelCtrl, self.get_control("lblSelStrtRecordHour"))
        x, y = cast(tuple[int, int], kwargs["mousepos"])
        scrollpicker = TimeScrollPickerDialog((x, y+20), "选择时间", lbl_strtime.get_text())
        strt_time = scrollpicker.get_timestr()
        pv(strt_time)
        lbl_strtime = cast(LabelCtrl, self.get_control("lblSelStrtRecordHour"))
        lbl_strtime.set_text(strt_time)

    def _schedule_txt2clk(self, txt: str):
        """_summary_

        Args:
            txt (str): _description_

        Returns:
            _type_: _description_
        """
        if not txt:
            return "00:00"
        clk = txt.replace("h", ":").replace("m", "")
        if ":" not in clk:
            clk = "00:" + clk
        return clk

    def _select_lastime(self, **kwargs: object):
        """_summary_
        """
        lbl_lastime = cast(LabelCtrl, self.get_control("lblSelLastRecordHour"))
        lastime = self._schedule_txt2clk(lbl_lastime.get_text())
        x, y = cast(tuple[int, int], kwargs["mousepos"])
        scrollpicker = TimeScrollPickerDialog((x, y+20), "持续时间", lastime)
        lastime = scrollpicker.get_timestr()
        if lastime.startswith("00"):
            lastime = lastime[3:]
        lastime += "m"

        lbl_lastime = cast(LabelCtrl, self.get_control("lblSelLastRecordHour"))
        lbl_lastime.set_text(lastime)

    @override
    def _confirm(self, **kwargs: object):
        hid = cast(int, kwargs["id"])
        db = cast(TimeDatabase, kwargs["db"])
        owner = cast(Dialog, self.owner)

        lbl_day = cast(LabelCtrl, self.get_control("lblSelDayRecordHour"))
        day = lbl_day.get_text()

        lbl_strtime = cast(LabelCtrl, self.get_control("lblSelStrtRecordHour"))
        strt_time = lbl_strtime.get_text()

        strt_dtime = datetime.datetime.strptime(f"{day} {strt_time}", "%Y-%m-%d %H:%M")
        po(f"Start time: {strt_dtime}")

        lbl_lastime = cast(LabelCtrl, self.get_control("lblSelLastRecordHour"))
        last_time = self._schedule_txt2clk(lbl_lastime.get_text()).split(":")
        # pv(last_time)
        duration = int(last_time[0]) * 60 + int(last_time[1])
        po(f"duration: {duration}")
        _ = owner.process_message("RecordHour", id=hid,
            strt_dtime=strt_dtime, duration=duration)
        detail = self._get_hourdetail(db, hid)
        sum_minutes = detail["sums"] + duration
        pv(sum_minutes)
        _ = owner.process_message("ChangeSum", id=hid, sum=sum_minutes)
        return True, ""

    @override
    def process_message(self, idmsg: str, **kwargs: object):
        if self.alive:
            kwargs.update(self._extral_msg)
            match idmsg:
                case "lblSelDayRecordHour":
                    self._select_day(**kwargs)
                case "lblSelStrtRecordHour":
                    self._select_strtime(**kwargs)
                case "lblSelLastRecordHour":
                    self._select_lastime(**kwargs)
                case _:
                    return super().process_message(idmsg, **kwargs)
            return True
        return super().process_message(idmsg, **kwargs)

class ReminderStatusEnum(IntEnum):
    DELETE = -1
    HOLD = 0
    NEW = 1
    MODIFY = 2

class Reminder(TypedDict):
    eid: int
    data: ReminderDataDict
    status: ReminderStatusEnum

class EditHourDlg(DialogCtrl):
    """_summary_

    """
    def __init__(self, app: tkWin, dlg_cfg: et.Element):
        """_summary_

        Args:
            app (tkWin): _description_
            dlg_cfg (et.Element): _description_
        """
        super().__init__(app, dlg_cfg)
        self._old_fid: int = -1
        self._old_iid: IconTuple = IconTuple(0, 0)
        self._hid: int = 0
        self._reminders: list[Reminder] = []
        self._schedule: Reminder = {
            "eid": -1,
            "data": default_reminder_data(),
            "status": ReminderStatusEnum.HOLD
        }

    def _add_clockctrl(self, eid: int, clkstr: str, isnew: bool = True):
        del_image = "del.png"

        frm_clock = cast(Widget, self.get_control("frmClockEditHour"))

        level = 1

        cid = len(self._reminders)

        btndel_xml = self.create_xml("ImageButton", {"id": f"btnDelClock{cid}EditHour",
            "image": del_image,
            "options": "{'height': 20, 'width': 20, 'bg':'white'}"})
        id_btndel, btn_del = self.create_control(frm_clock, btndel_xml, level)
        self._idctrl_dict[id_btndel] = btn_del
        self.assemble_control(btn_del, {"layout":"grid",
            "grid":f"{{'row':{cid+1},'column':0,'sticky':'w'}}"}
        )

        lblclock_xml = self.create_xml("Label", {"id": f"lblClock{cid}EditHour",
            "text": clkstr, "clickable": "true",
            "options": "{'style':'BW.TLabel'}"})
        # pv(lbl_item_xml)
        id_lblclock, lbl_clock = self.create_control(frm_clock, lblclock_xml, level)
        self._idctrl_dict[id_lblclock] = lbl_clock
        self.assemble_control(lbl_clock, {"layout":"grid",
            "grid":f"{{'row':{cid+1},'column':1,'sticky':'w'}}"}
        )

        data = str2reminder(clkstr, "")
        reminder: Reminder = {
            "eid": eid,
            "data": data,
            "status": ReminderStatusEnum.NEW if isnew else ReminderStatusEnum.HOLD
        }
        self._reminders.append(reminder)

    @override
    def _beforego(self, **kwargs: object):
        po(f"_edithourdlg_beforego: {kwargs}")
        fid = cast(int, kwargs["fid"])
        self._old_fid = fid
        hid = cast(int, kwargs["id"])
        self._hid = hid
        db = cast(TimeDatabase, kwargs["db"])
        owner = cast(Dialog, self.owner)

        if fid != -1:
            lbl_father = cast(LabelCtrl, self.get_control("lblSelFatherEditHour"))
            detail_father = self._get_hourdetail(db, fid)
            name_father = detail_father["name"]
            pv(name_father)
            lbl_father['text'] = name_father

        lbl_addclock = cast(LabelCtrl, self.get_control("lblAddClockEditHour"))
        sls_clock = cast(SlideSwitchCtrl, self.get_control("slsClockEditHour"))

        if hid == 0:
            self.set_title("New Item")
            btn_delhour = cast(ButtonCtrl, self.get_control("btnDelItemEditHour"))
            btn_delhour.hide()
            lbl_addclock.show()
            sls_clock.hide()
            grp, idx = 0, 0
        else:
            self.set_title("Edit Item")
            detail = self._get_hourdetail(db, hid)
            pv(detail)

            ent_name = cast(EntryCtrl, self.get_control("txtItemEditHour"))
            ent_name.set_val(detail["name"])
            ent_name.disable()

            lbl_clock = cast(LabelCtrl, self.get_control("lblClockEditHour"))
            schedule_str = ""
            i = 0
            for eid, reminderdata in detail["reminders"].items():
                if reminderdata["clk_time"]:
                    clk_str, _ = reminder2str(reminderdata)
                    lbl_clock['text'] = "提醒已开启"
                    lbl_addclock.hide()
                    self._add_clockctrl(eid, clk_str, False)
                    i += 1
                else:
                    _, schedule_str = reminder2str(reminderdata)
                    self._schedule["eid"] = eid
                    self._schedule["data"] = reminderdata

            if i <= 0:
                lbl_clock['text'] = "定时提醒"
                lbl_addclock['text'] = "点击添加"
                lbl_addclock.show()
                sls_clock.hide()
            else:
                sls_clock.set_state(True)
                sls_clock.show()

            lbl_selschedule = cast(LabelCtrl, self.get_control("lblSelScheduleEditHour"))
            lbl_selschedule['text'] = schedule_str if schedule_str else "选择时间投入计划"

            icon = detail["iid"] if detail["iid"] is not None else IconTuple(0, 0)
            self._old_iid = icon
            grp, idx = tuple(icon)

        images_dict = cast(dict[int, dict[int, str]], owner.process_message("getImagesDict"))
        list_itemimage = cast(PicsListviewCtrl, self.get_control("lstImageEditHour"))
        # list_itemimage.display_images(list(self._images_dict.values()))
        list_itemimage.add_imagegroup("一般", list(images_dict[0].values()))
        list_itemimage.add_imagegroup("课程", list(images_dict[1].values()))
        list_itemimage.add_imagegroup("锻炼", list(images_dict[2].values()))
        list_itemimage.add_imagegroup("语言", list(images_dict[3].values()))
        list_itemimage.add_imagegroup("考试", list(images_dict[4].values()))

        list_itemimage.select(grp, idx)

    @override
    def _confirm(self, **kwargs: object):
        po(f"_edithourdlg_confirm: {kwargs}")
        owner = cast(Dialog, self.owner)
        fid = cast(int, kwargs["fid"])
        hid = cast(int, kwargs["id"])

        reminders: dict[int, ReminderDataDict] = {}
        for reminder in self._reminders:
            reminders[reminder["eid"]] = reminder["data"]

        ent_name = cast(EntryCtrl, self.get_control("txtItemEditHour"))
        name = ent_name.get_val()

        if hid != 0:    # edit item
            for reminder in self._reminders:
                eid = reminder["eid"]
                data = reminder["data"]
                status = reminder["status"]
                clk_time = data["clk_time"]
                custom = data["custom"]
                clk_str, _ = reminder2str(data)

                if status == ReminderStatusEnum.NEW:
                    _ = owner.process_message("NewClock", hid=hid, name=name, reminder=data)
                elif status == ReminderStatusEnum.MODIFY:
                    _ = owner.process_message("changeClock", id=hid, eid=eid,
                    clk_time=clk_time, custom=custom, clk_str=clk_str)
                elif status == ReminderStatusEnum.DELETE:
                    _ = owner.process_message("DelClock", hid=hid, eid=eid, reminder=data)
                else:
                    pass

            if self._schedule["status"] == ReminderStatusEnum.MODIFY:
                _ = owner.process_message("ModifySchedule", hid=hid, eid=self._schedule["eid"], reminder=self._schedule["data"])
            elif self._schedule["status"] == ReminderStatusEnum.NEW:
                _ = owner.process_message("NewSchedule", hid=hid, reminder=self._schedule["data"])
            elif self._schedule["status"] == ReminderStatusEnum.DELETE:
                _ = owner.process_message("DelSchedule", hid=hid, eid=self._schedule["eid"])

            lst_itemimage = cast(PicsListviewCtrl,
                self.get_control("lstImageEditHour"))
            grp, idx = lst_itemimage.get_selected()
            if IconTuple(grp, idx) != self._old_iid:
                _ = owner.process_message("changeItemImage",
                    id=hid, group=grp, index=idx)
        else:   # New item
            # pv(name)
            if len(name) == 0:
                return False, "Name should not be empty"

            lst_itemimage = cast(PicsListviewCtrl,
                self.get_control("lstImageEditHour"))
            iid = lst_itemimage.get_selected()
            icon = IconTuple(*iid)
            if fid == -1:
                # reminder = str2reminder(clock_val, schedule_val)
                # reminders = {0: reminder}
                _ = owner.process_message("NewHour",
                    name=name, fid=fid, iid=icon,
                    reminders=reminders)
            else:
                _ = owner.process_message("CreateChild", name=name, iid=icon,
                    fid=fid, reminders=reminders)
        return True, ""

    def _get_hourdetail(self, db: TimeDatabase, hid: int):
        """_summary_

        Args:
            hid (int): _description_

        Returns:
            _type_: _description_
        """
        plandata = db.get_plandata(hid)
        return plandata

    def _del_clock(self, cid: int):
        lbl_clock = cast(LabelCtrl, self.get_control("lblClockEditHour"))
        lbl_clock['text'] = "定时提醒"
        lbl_addclock = cast(LabelCtrl, self.get_control("lblAddClockEditHour"))
        lbl_addclock['text'] = "点击添加"
        lbl_addclock.show()
        sls_clock = cast(SlideSwitchCtrl, self.get_control("slsClockEditHour"))
        sls_clock.hide()

        self.delete_control(f"btnDelClock{cid}EditHour")
        self.delete_control(f"lblClock{cid}EditHour")

        if self._hid == 0:
            del self._reminders[cid]
        else:
            self._reminders[cid]["data"]["clk_time"] = None
            self._reminders[cid]["status"] = ReminderStatusEnum.DELETE

    @override
    def process_message(self, idmsg: str, **kwargs: object):
        if self.alive:
            kwargs.update(self._extral_msg)
            owner = cast(Dialog, self.owner)
            if idmsg.startswith("btnDelClock"):
                cid = int(idmsg[11:12])
                self._del_clock(cid)
                return True
            elif idmsg.startswith("lblClock"):
                cid = int(idmsg[8: -8])
                lbl_clk = cast(LabelCtrl, self.get_control(idmsg))
                oldclkstr = cast(str, lbl_clk['text'])
                x, y = cast(tuple[int, int], kwargs["mousepos"])
                kwargs.update({"clkstr": oldclkstr})
                clkstr = cast(str, owner.process_message("showSelClockDlg", owner=self,
                    pos=(x+20,y+20), options=kwargs))
                if clkstr != oldclkstr:
                    lbl_clk['text'] = clkstr
                    reminder1 = str2reminder(clkstr, "")
                    reminder2 = self._reminders[cid]
                    reminder2["data"]["clk_time"] = reminder1["clk_time"]
                return True
            match idmsg:
                case "lblAddClockEditHour":
                    pv(kwargs)
                    lbl_addclock = cast(LabelCtrl, self.get_control("lblAddClockEditHour"))
                    lbl_addclock.hide()
                    sls_clock = cast(SlideSwitchCtrl, self.get_control("slsClockEditHour"))
                    sls_clock.show()
                    sls_clock.set_state(True)
                    eid = uuid.uuid4().int
                    clkstr = "Everyday 14:00"
                    self._add_clockctrl(eid, clkstr, True)
                case "lblSelScheduleEditHour":
                    pv(kwargs)
                    x, y = cast(tuple[int, int], kwargs["mousepos"])
                    lbl_selschedule = cast(LabelCtrl, self.get_control("lblSelScheduleEditHour"))
                    old_schedulestr = lbl_selschedule.get_text()
                    schedulestr = old_schedulestr
                    if old_schedulestr == "选择时间投入计划":
                        schedulestr = "Workday 15m"
                    kwargs.update({"schedulestr": schedulestr})
                    schedule_str = cast(str, owner.process_message("showSelScheduleDlg", owner=self,
                        pos=(x+20,y+20), options=kwargs))
                    pv(schedule_str)
                    pv(old_schedulestr)
                    if schedule_str != old_schedulestr:
                        lbl_selschedule.set_text(schedule_str)
                        if schedule_str:
                            reminder = str2reminder("", schedule_str)
                            pv(reminder)
                            self._schedule["data"] = reminder
                            if old_schedulestr == "选择时间投入计划":
                                self._schedule["status"] = ReminderStatusEnum.NEW
                            else:
                                self._schedule["status"] = ReminderStatusEnum.MODIFY
                        else:
                            self._schedule["data"] = default_reminder_data()
                            self._schedule["status"] = ReminderStatusEnum.DELETE
                    return True
                case "btnDelItemEditHour":
                    pv(kwargs)
                    iid = cast(int, owner.process_message("getId"))
                    self.destroy()
                    return owner.process_message("deleteItem", id=iid)
                case _:
                    return super().process_message(idmsg, **kwargs)
            return True
        return super().process_message(idmsg, **kwargs)


class HourDetailDlg(DialogCtrl):
    """_summary_

    Attributes:
        _last_cid (int): the previous old child index
        _children (_type_): _description_
    """
    def __init__(self, app: tkWin, dlg_cfg: et.Element):
        """_summary_

        Args:
            app (tkWin): _description_
            dlg_cfg (et.Element): _description_
        """
        super().__init__(app, dlg_cfg)
        self._last_cid: int = 0
        self._children: dict[int, HourTuple] = {}

        self._hid: int = 0
        self._detail: PlanDataDict = default_plan_data()
        self._db: TimeDatabase | None = None
        self._firstday: datetime.date = datetime.date(2025,12,25)

    def _update_hourdetailctrl(self, attrib: str, val: str | float):
        """_summary_

        Args:
            attrib (str): _description_
            val (str | float): _description_

        Raises:
            KeyError: _description_
        """
        match attrib:
            case "name":
                lbl_item = cast(LabelCtrl, self.get_control("lblInfoHourDetail"))
                text_list = lbl_item.get_text().split("\n")
                text_list[0] = str(val)
                lbl_item.set_text(f"{text_list[0]}\n{text_list[1]}")
            case "StartDate":
                lbl_item = cast(LabelCtrl, self.get_control("lblInfoHourDetail"))
                text_list = lbl_item.get_text().split("\n")
                if val:
                    text_list[1] = str(val)
                else:
                    text_list[1] = "从未开始"
                lbl_item.set_text(f"{text_list[0]}\n{text_list[1]}")
            case "sum":
                lbl_sum = cast(LabelCtrl, self.get_control("lblSumHourDetail"))
                lbl_sum.set_text(f"{val}\nhours")
            case "TotalDays":
                lbl_item = cast(LabelCtrl, self.get_control("lblWholeHourDetail"))
                lbl_item.set_text(f"{val}\n坚持天数")
            case "HoursEveryWeek":
                lbl_item = cast(LabelCtrl, self.get_control("lblAvrgHourDetail"))
                lbl_item.set_text(f"{val}h\n平均每周")
            case "HoursLast7Days":
                lbl_item = cast(LabelCtrl, self.get_control("lblRecentHourDetail"))
                lbl_item.set_text(f"{val}h\n最近七天")
            case "RestHours2Milestone":
                lbl_item = cast(LabelCtrl, self.get_control("lblRestHourDetail"))
                lbl_item.set_text(f"{val}\n距离里程碑")
            case _:
                raise KeyError(f"Unkonw arrtrib: {attrib}")

    def _get_hourdetail(self, db: TimeDatabase, hid: int):
        """_summary_

        Args:
            hid (int): _description_

        Returns:
            _type_: _description_
        """
        plandata = db.get_plandata(hid)
        return plandata

    def _get_minutes_byday(self, hid: int, day: datetime.date):
        assert self._db is not None
        records = self._db.get_records(day, hid)
        total_minutes = 0
        for record in records.values():
            total_minutes += record['duration']
        return total_minutes

    def _plot_weekview(self, hid: int, detail: PlanDataDict, db: TimeDatabase,
            firstday: datetime.date):
        name_labels: list[str] = []
        actual_data: list[list[float]] = []
        bar_list: list[BarContainer] = []
        color_list: list[str] = []
        aim_data: list[list[float]] = []
        icon_path_list: list[str] = []

        children = db.get_children(hid)
        week_day = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

        target_ydata: list[float] = [0] * 7

        if len(detail["reminders"]) == 0:
            return

        reminder = default_reminder_data()
        for rmd in detail["reminders"].values():
            if rmd["clk_time"] is None:
                reminder = rmd
                break

        pv(reminder)

        unit = 1
        match reminder['unit']:
            case TimeUnit.DAY:
                unit = 1
            case TimeUnit.WEEK:
                unit = 7
            case TimeUnit.MONTH:
                unit = 30
            case _:
                unit = 360

        total_minutes = reminder['duration']
        per_minutes = total_minutes / unit

        custom = reminder['custom']
        if isinstance(custom, DayType):
            match custom:
                case DayType.WORKDAY:
                    target_ydata = [per_minutes, per_minutes, per_minutes, \
                        per_minutes, per_minutes, 0, 0]
                case DayType.WEEKEND:
                    target_ydata = [0, 0, 0, 0, 0, per_minutes, per_minutes]
                case _:
                    target_ydata = [per_minutes, per_minutes, per_minutes, \
                        per_minutes, per_minutes, per_minutes, per_minutes]
        else:
            target_ydata = [per_minutes, per_minutes, per_minutes, \
                per_minutes, per_minutes, per_minutes, per_minutes]

        xdata: list[int] = []
        father_ydata: list[float] = []
        children_ydata: dict[int, list[float]] = {}
        labels: list[str] = []
        for i in range(7):
            day = firstday + datetime.timedelta(days=i)
            weekday = day.weekday()
            labels.append(f"{week_day[weekday]}\n{day.day}")
            xdata.append(i)
            minutes = self._get_minutes_byday(hid, day)
            father_ydata.append(minutes)
            po(f"minutes of day {day} is {minutes}")
            for cid in children:
                minutes = self._get_minutes_byday(cid, day)
                if children_ydata.get(cid) is None:
                    children_ydata[cid] = [minutes]
                else:
                    children_ydata[cid].append(minutes)

        name_labels.append(detail["name"])
        actual_data.append(father_ydata)
        aim_data.append(target_ydata)
        icon = cast(IconTuple, detail["iid"])
        imagepath = self._get_imagepath(icon.grpidx, icon.eleidx)
        icon_path_list.append(imagepath)
        for cid, child in children.items():
            name_labels.append(child.data["name"])
            actual_data.append(children_ydata[cid])
            aim_data.append([45, 45, 45, 45, 45, 45, 45])
            icon = cast(IconTuple, child.data["iid"])
            imagepath = self._get_imagepath(icon.grpidx, icon.eleidx)
            icon_path_list.append(imagepath)

        # draw bar
        plt_weekview = cast(MatPlotCtrl, self.get_control("pltEveryDayHour"))
        plt_weekview.clear_canvas()        
        plt_weekview.xdata = xdata
        father_yline = LineData(father_ydata,
            {"tick_label":labels,"width":0.4,"facecolor":"green"}, "bar")
        _ = plt_weekview.add_line(father_yline)
        bar = cast(BarContainer, father_yline.line)
        bar_list.append(bar)
        color_list.append(to_hex(bar.patches[0].get_facecolor()))

        bottom_ydata = father_ydata.copy()
        for child_ydata in children_ydata.values():
            child_yline = LineData(child_ydata, {"width":0.4,"bottom":bottom_ydata}, "bar")
            _ = plt_weekview.add_line(child_yline)
            bar = cast(BarContainer, child_yline.line)
            bar_list.append(bar)
            color_list.append(to_hex(bar.patches[0].get_facecolor()))
            for i in range(7):
                bottom_ydata[i] += child_ydata[i]
        limit_yline = LineData(target_ydata, {"linestyle":"dotted","color":"red"})
        _ = plt_weekview.add_line(limit_yline)
        plt_weekview.draw()

        # Hover tip
        patch_map: dict[Rectangle, tuple[str, float]] = {}
        for idx, bar_container in enumerate(bar_list):
            item_name = name_labels[idx]
            item_y_list = actual_data[idx]
            # Bind each single bar patch with its subject name and daily value
            for patch, val in zip(bar_container.patches, item_y_list):
                patch_map[patch] = (item_name, val)

        fig_canvas = plt_weekview.canvas

        tooltip = plt_weekview.add_tooltip(0,0,"",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.8),
            visible=False)
        def on_mouse_move(e: backend_bases.Event):
            e = cast(backend_bases.MouseEvent, e)
            if e.inaxes != plt_weekview.ax:
                tooltip.set_visible(False)
                fig_canvas.draw()
                return
            hover_patch = None
            for patch in patch_map:
                if patch.contains(e)[0]:
                    hover_patch = patch
                    break
            if hover_patch is not None:
                name, cur_val = patch_map[hover_patch]
                # 格式：第一行项目名，第二行时间
                tip_content = f"{name}\n{cur_val}min"
                tooltip.set_text(tip_content)
                tooltip.set_position((e.xdata if e.xdata else 0, e.ydata if e.ydata else 0))
                tooltip.set_visible(True)
            else:
                tooltip.set_visible(False)
            fig_canvas.draw()
        plt_weekview.event_callback('motion_notify_event', on_mouse_move)

        # detail bar
        chart_total_w = 346
        progress_canvas = cast(CanvasCtrl, self.get_control("cvsDetailEveryDayHour"))
        _ = cast(tk.Canvas, progress_canvas.control).config(width=chart_total_w,background='white')

        # Fixed layout constants for progress item styling
        ICON_WIDTH: int = 32
        BAR_TOTAL_LENGTH: int = 70
        BAR_HEIGHT: int = 11  # Progress bar height set to half of original size
        ITEM_FIXED_WIDTH: int = BAR_TOTAL_LENGTH + ICON_WIDTH + 50
        ROW_GAP: int = 40
        COL_GAP: int = 20
        NAME_TEXT_HEIGHT: int = 18
        GRAY_BG_COLOR: str = "#cccccc"

        # Calculate max items per single row, auto wrap to new line when over width limit
        per_row_max: int = int(chart_total_w / ITEM_FIXED_WIDTH)
        per_row_max = max(1, per_row_max)

        all_items = list(zip(name_labels, color_list, actual_data, aim_data, icon_path_list))

        for col_idx, (lab, col, act_list, aim_list, icon_path) in enumerate(all_items):
            cur_row = col_idx // per_row_max
            cur_col = col_idx % per_row_max

            # Calculate left margin for horizontal even distribution in one row
            row_total_used_width = per_row_max * ITEM_FIXED_WIDTH + (per_row_max - 1) * COL_GAP
            row_left_margin = (chart_total_w - row_total_used_width) / 2 if per_row_max > 1 else 15
            base_x = row_left_margin + cur_col * (ITEM_FIXED_WIDTH + COL_GAP)
            base_y = 15 + cur_row * ROW_GAP

            sum_act = sum(act_list)
            sum_aim = sum(aim_list)
            ratio: float = sum_act / sum_aim if sum_aim != 0 else 0.0
            fill_len: float = BAR_TOTAL_LENGTH * ratio

            # Calculate vertical bound of left side full-height subject icon (covers name + progress bar area)
            icon_top = base_y
            icon_bottom = base_y + NAME_TEXT_HEIGHT + BAR_HEIGHT + 6
            icon_h = int(icon_bottom - icon_top)
            icon_center_x = base_x + ICON_WIDTH / 2
            icon_center_y = (icon_top + icon_bottom) / 2

            # Draw tall left sidebar icon (covers both name area and progress bar vertically)
            icon_top = base_y
            icon_bottom = base_y + NAME_TEXT_HEIGHT + BAR_HEIGHT + 3
            icon_h = icon_bottom - icon_top
            _ = progress_canvas.create_image(
                icon_center_x, icon_center_y,
                file_path=icon_path,
                target_w=ICON_WIDTH,
                target_h=icon_h,
                fallback_fill=col,
                anchor="center"
            )

            bar_start_x = base_x + ICON_WIDTH + 12
            name_y_center = base_y + NAME_TEXT_HEIGHT / 2
            right_text_x = bar_start_x + BAR_TOTAL_LENGTH + 12
            bar_top = base_y + NAME_TEXT_HEIGHT + 4
            bar_bottom = bar_top + BAR_HEIGHT
            bar_center_y = (bar_top + bar_bottom) / 2

            # Draw subject name above progress bar, left aligned
            _ = progress_canvas.create_text(
                bar_start_x, name_y_center, text=lab, anchor="w", font=("Microsoft YaHei", 10, "bold")
            )

            # Draw total consumed time text on same horizontal level as subject name
            right_text_x = bar_start_x + BAR_TOTAL_LENGTH + 12
            _ = progress_canvas.create_text(
                right_text_x, name_y_center, text=f"{sum_act}min", anchor="w", font=("Microsoft YaHei", 9)
            )

            # Draw gray background base bar + colored progress fill bar
            _ = progress_canvas.create_rectangle(
                bar_start_x, bar_top, bar_start_x + BAR_TOTAL_LENGTH, bar_bottom, fill=GRAY_BG_COLOR, outline="#888888"
            )
            _ = progress_canvas.create_rectangle(
                bar_start_x, bar_top, bar_start_x + fill_len, bar_bottom, fill=col, outline="black"
            )

            # Draw completion rate text aligned vertically with progress bar center
            _ = progress_canvas.create_text(
                right_text_x, bar_center_y, text=f"{ratio:.0%}", anchor="w", font=("Microsoft YaHei", 9)
            )

    def _get_hours_last7days(self, hid: int):
        assert self._db is not None
        today = datetime.datetime.today()
        last7day = today + datetime.timedelta(days=-7)
        records = self._db.get_records(last7day, hid, today)
        total_minutes = 0
        for record in records.values():
            total_minutes += record["duration"]
        return total_minutes / 60.0

    # TODO:
    def _get_hours_milestone(self, hid: int):
        return "∞"

    @override
    def _beforego(self, **kwargs: object):
        po(f"_hourdetaildlg_beforego: {kwargs}")
        self._hid = cast(int, kwargs["id"])
        self._db = cast(TimeDatabase, kwargs["db"])

        self._detail = self._get_hourdetail(self._db, self._hid)
        # po(f"{iid}: {detail}")
        # owner = cast(Container, self._owner)

        lbl_father = cast(LabelCtrl, self.get_control("lblFatherItemDetail"))
        fid = self._detail["fid"]
        if fid != -1:
            detail_father = self._get_hourdetail(self._db, fid)
            name_father = detail_father["name"]
            pv(name_father)
            lbl_father['text'] = name_father
        else:
            lbl_father.hide()

        icon = cast(IconTuple, self._detail["iid"])
        imagepath = self._get_imagepath(icon.grpidx, icon.eleidx)
        img_item = cast(ImageBtttonCtrl, self.get_control("btnImageHourDetail"))
        img_item.change_image(imagepath)

        # TODO: children?
        firstday = datetime.datetime.fromisoformat("2025-01-01T16:34:00")
        end_date = firstday.date()
        today = datetime.datetime.today().date()
        total_days = 0
        strt_date = today
        records = self._db.get_records(firstday, self._hid, today)
        for record in records.values():
            bgn_dtime = cast(datetime.datetime, record['bgn_dtime'])
            if bgn_dtime.date() != firstday.date():
                total_days += 1
            strt_date = min(strt_date, bgn_dtime.date())
            end_date = max(end_date, bgn_dtime.date())

        lbl_item = cast(LabelCtrl, self.get_control("lblInfoHourDetail"))
        lbl_item.set_text(f"{self._detail["name"]}\n从{strt_date}开始")
        self._update_hourdetailctrl("sum", f"{self._detail["sums"]/ 60:.1f}")
        self._update_hourdetailctrl("TotalDays", total_days)

        total_weeks = math.ceil(((end_date - strt_date).days + 1)/7)
        pv(total_weeks)
        hours_everyweek = self._detail["sums"] / total_weeks /60
        self._update_hourdetailctrl("HoursEveryWeek", f"{hours_everyweek:.1f}")
        hours_last7days = self._get_hours_last7days(self._hid)
        self._update_hourdetailctrl("HoursLast7Days", f"{hours_last7days:.1f}")
        hours_2milestone = self._get_hours_milestone(self._hid)
        self._update_hourdetailctrl("RestHours2Milestone", hours_2milestone)

        clk_str = ""
        schedule_str = ""
        for reminder in self._detail["reminders"].values():
            if reminder["clk_time"]:
                clkstr, _ = reminder2str(reminder)
                clk_str = clk_str + "\t" + clkstr
            else:
                pv(reminder)
                _, schedule_str = reminder2str(reminder)
                pv(schedule_str)

        lbl_selclock = cast(LabelCtrl, self.get_control("lblSelClockItemDetail"))
        lbl_selclock['text'] = clk_str
        lbl_selschedule = cast(LabelCtrl, self.get_control("lblSelScheduleItemDetail"))
        lbl_selschedule['text'] = schedule_str

        parent = cast(FrameCtrl, self.get_control("frmSubItmes"))
        children = self._db.get_children(self._hid)
        idx = 0
        for cid, child in children.items():
            icon = cast(IconTuple, child.data["iid"])
            self._children[idx] = HourTuple(hid=cid, name=child.data["name"],
                iid=icon, fid=child.data["fid"],
                reminders=child.data["reminders"], sums=child.data["sums"])
            self._create_childctrl(parent, idx, child.data["name"],
                icon, f"{child.data["sums"] / 60: .1f}")
            idx += 1
        pv(self._children)
        self._last_cid = len(self._children) - 1
        lbl_totalsubitems = cast(LabelCtrl, self.get_control("lblTotalChildren"))
        lbl_totalsubitems["text"] = f"共{idx}个子项目"

        self._firstday = today + datetime.timedelta(days=-today.weekday())
        self._plot_weekview(self._hid, self._detail, self._db, self._firstday)

        """
        thismonth = today.month
        for i in range(6):
            month = thismonth - i
            hours = self._db.get_hoursbymonth(self._iid, month)
            po(f"hours of month {month} is {hours}")

        thisyear = today.year
        for i in range(6):
            year = thisyear - i
            hours = self._db.get_hoursbyyear(self._iid, year)
            po(f"hours of year {year} is {hours}")
        """

    @override
    def _cancel(self, **kwargs: object):
        po(f"_hourdetaildlg_cancel: {kwargs}")
        for idx in self._children:
            self._delete_childctrl(idx)
        self._children.clear()
        return True, ""

    @override
    def _confirm(self, **kwargs: object):
        owner = cast(Dialog, self.owner)
        for idx, child in self._children.items():
            if idx > self._last_cid:
                name =      child.name
                iid =       child.iid
                reminders = child.reminders
                fid = cast(int, kwargs["id"])
                _ = owner.process_message("NewHour",
                    name=name, fid=fid, iid=iid, reminders=reminders)
            self._delete_childctrl(idx)
        self._children.clear()
        return True, ""

    def _get_imagepath(self, group: int, index: int):
        """_summary_

        Args:
            group (int): _description_
            index (int): _description_

        Returns:
            _type_: _description_
        """
        owner = cast(Container, self._owner)
        imagepath = cast(str, owner.process_message("getImagePath", group=group, index=index))
        return imagepath

    def show_recordhourdlg(self, owner: Container | None = None, x: int = 0, y: int = 0,
            **kwargs: object):
        """_summary_
        Args:
            owner (type): _description_
            x (type): _description_
            y (type): _description_
        """
        dlg_id = "dlgRecordHour"
        dlg_cfg = self._app.get_customctrlcfg(dlg_id)
        app = cast(tkWin, self._app)
        recordhour_dlg = RecordHourDlg(app, dlg_cfg)
        # self._gui.register_customctrl(dlg_id, recordhour_dlg)
        recordhour_dlg.do_show(owner, x, y, **kwargs)

    def _show_edithourdlg(self, owner: Container | None = None, x: int = 0, y: int = 0,
            **kwargs: object):
        """_summary_
        Args:
            owner (type): _description_
            x (type): _description_
            y (type): _description_
        """
        dlg_id = "dlgEditHour"
        dlg_cfg = self._app.get_customctrlcfg(dlg_id)
        app = cast(tkWin, self._app)
        dlg = EditHourDlg(app, dlg_cfg)
        dlg.do_show(owner, x, y, **kwargs)

    def _update_hour(self, uid: int, attrib: str, val: str | float):
        """_summary_

        Args:
            uid (int): _description_
            attrib (str): _description_
            val (str | float): _description_
        """
        owner = cast(Container, self._owner)
        _ = owner.process_message("updateHour", id=uid, attrib=attrib, val=val)

    def _create_childctrl(self, parent: Widget, uid: int, sub_item: str,
            iid: IconTuple, sums: str):
        """_summary_

        Args:
            parent (Widget): _description_
            uid (int): _description_
            sub_item (str): _description_
            iid (tuple[int, int]): _description_
            sums (str): _description_
        """
        imagepath = self._get_imagepath(iid.grpidx, iid.eleidx)

        level = 2
        frm_child_xml = self._app.create_xml("Frame", {"id": f"frmSub{uid}"})
        _, frm_child = self._app.create_control(parent, frm_child_xml, level)

        level = 3

        pnlitem_xml = self._app.create_xml("ImagePanel", {"id": f"pnlChild{uid}",
            "image": imagepath, 
            "options": "{'height':20, 'width':20}"}, frm_child_xml)
        _, pnl_item = self._app.create_control(frm_child, pnlitem_xml, level)
        self._app.assemble_control(pnl_item, {"layout":"pack",
            "pack":"{'side':'left','anchor':'w'}"}, '  '*level)

        lblitem_xml = self._app.create_xml("Label", {"id": f"lblChild{uid}", 
            "text": sub_item, "options": "{'width':40}"}, frm_child_xml)
        _, lbl_subitem = self._app.create_control(frm_child, lblitem_xml, level)
        self._app.assemble_control(lbl_subitem, {"layout":"pack",
            "pack":"{'side':'left','anchor':'w'}"}, f"{'  '*level}")

        lblsum_xml = self._app.create_xml("Label", {"text": f"{sums}h",
            "id": f"lblSubSum{uid}"}, frm_child_xml)
        _, lbl_sum = self._app.create_control(frm_child, lblsum_xml, level)
        self._app.assemble_control(lbl_sum, {"layout":"pack",
            "pack":"{'side':'left','anchor':'e'}"}, f"{'  '*level}")

        self._app.assemble_control(frm_child, {"layout": "grid",
            "grid": f"{{'row':{uid},'column':0,'pady':4}}"}, f"{'  '*(level-1)}")

    def _delete_childctrl(self, sid: int):
        """_summary_

        Args:
            sid (int): _description_
        """
        self._app.delete_control(f"frmSub{sid}")
        self._app.delete_control(f"pnlChild{sid}")
        self._app.delete_control(f"lblChild{sid}")
        self._app.delete_control(f"lblSubSum{sid}")

    @override
    def process_message(self, idmsg: str, **kwargs: object):
        if self.alive:
            kwargs.update(self._extral_msg)
            hid = cast(int, kwargs["id"])
            db = cast(TimeDatabase, kwargs["db"])
            owner = cast(Dialog, self.owner)
            match idmsg:
                case "btnImageHourDetail":
                    detail = self._get_hourdetail(db, hid)
                    fid = detail["fid"]
                    x, y = cast(tuple[int, int], kwargs["mousepos"])
                    self._show_edithourdlg(self, x+20, y+20,
                        fid=fid, id=hid, db=db)
                case "changeItemImage": # come from `EditHourDlg`
                    grp = cast(int, kwargs["group"])
                    idx = cast(int, kwargs["index"])
                    imagebutton = cast(ImageBtttonCtrl, self.get_control("btnImageHourDetail"))
                    imagepath = self._get_imagepath(grp, idx)
                    # pv(imagepath)
                    imagebutton.change_image(imagepath)
                    _ = owner.process_message("changeItemImage",
                        id=hid, group=grp, index=idx)
                case "changeClock": # come from `EditHourDlg`
                    clk_str = cast(str, kwargs["clk_str"])
                    lbl_selclock = cast(LabelCtrl,
                        self.get_control("lblSelClockItemDetail"))
                    lbl_selclock['text'] = clk_str
                    _ = owner.process_message("changeClock", **kwargs)
                case "ModifySchedule":  # come from `EditHourDlg`
                    reminder = cast(ReminderDataDict, kwargs["reminder"])
                    _, schedule_str = reminder2str(reminder) 
                    lbl_selschedule = cast(LabelCtrl,
                        self.get_control("lblSelScheduleItemDetail"))
                    lbl_selschedule.set_text(schedule_str)
                    _ = owner.process_message("ModifySchedule", **kwargs)
                case "NewSchedule": # come from `EditHourDlg`
                    reminder = cast(ReminderDataDict, kwargs["reminder"])
                    _, schedule_str = reminder2str(reminder) 
                    lbl_selschedule = cast(LabelCtrl,
                        self.get_control("lblSelScheduleItemDetail"))
                    lbl_selschedule.set_text(schedule_str)
                    _ = owner.process_message("NewSchedule", **kwargs)
                case "DelSchedule": # come from `EditHourDlg`
                    lbl_selschedule = cast(LabelCtrl,
                        self.get_control("lblSelScheduleItemDetail"))
                    lbl_selschedule.set_text("")
                    _ = owner.process_message("DelSchedule", **kwargs)
                case "NewClock": # come from `EditHourDlg`
                    reminder = cast(ReminderDataDict, kwargs["reminder"])
                    clk_str, schedule_str = reminder2str(reminder)
                    lbl_selclock = cast(LabelCtrl,
                        self.get_control("lblSelClockItemDetail"))
                    lbl_selclock['text'] = clk_str
                    lbl_selschedule = cast(LabelCtrl,
                        self.get_control("lblSelScheduleItemDetail"))
                    lbl_selschedule['text'] = schedule_str
                    _ = owner.process_message("NewClock", **kwargs)
                case "DelClock": # come from `EditHourDlg`
                    reminder = cast(ReminderDataDict, kwargs["reminder"])
                    eid = cast(int, kwargs["eid"])
                    pv(eid)
                    clk_str, schedule_str = reminder2str(reminder)
                    lbl_selclock = cast(LabelCtrl,
                        self.get_control("lblSelClockItemDetail"))
                    lbl_selclock['text'] = ""
                    _ = owner.process_message("DelClock", **kwargs)
                case "deleteItem":  # come from `EditHourDlg`
                    _ = owner.process_message("deleteItem", id=hid)
                    self.destroy()
                case "btnAddChild":
                    x, y = cast(tuple[int, int], kwargs["mousepos"])
                    self._show_edithourdlg(self, x+20, y+20,
                        fid=hid, id=0, db=db)
                case "CreateChild":  # come from `EditHourDlg`
                    parent = cast(FrameCtrl, self.get_control("frmSubItmes"))
                    cid = len(self._children)
                    name = cast(str, kwargs["name"])
                    iid = cast(IconTuple, kwargs["iid"])
                    self._create_childctrl(parent, cid, name, iid, "0.0")

                    reminders = cast(dict[int, ReminderDataDict],  kwargs["reminders"])
                    fid = cast(int, kwargs["fid"])
                    self._children[cid] = HourTuple(0, name, iid, fid,
                        reminders, 0)
                    lbl_totalsubitems = cast(LabelCtrl, self.get_control("lblTotalChildren"))
                    lbl_totalsubitems["text"] = f"共{len(self._children)}个子项目"
                case "btnRecordHourDetail":
                    detail = self._get_hourdetail(db, hid)
                    fid = detail["fid"]
                    x, y = cast(tuple[int, int], kwargs["mousepos"])
                    self.show_recordhourdlg(self, x+20, y+20,
                        fid=fid, id=hid, db=db)
                case "ChangeSum":   # come from `RecordHourDlg`
                    sum_minutes= cast(float, kwargs["sum"])
                    lbl_sum = cast(LabelCtrl, self.get_control("lblSumHourDetail"))
                    lbl_sum.set_text(f"{float(sum_minutes)/60:.1f}\nhours")
                    self._update_hour(hid, "sum", sum_minutes)
                case "btnPrevDayHour":
                    self._firstday -= datetime.timedelta(days=1)
                    self._plot_weekview(self._hid, self._detail, db, self._firstday)
                case "btnPrevWeekHour":
                    self._firstday -= datetime.timedelta(days=7)
                    self._plot_weekview(self._hid, self._detail, db, self._firstday)
                case "btnNextDayHour":
                    self._firstday += datetime.timedelta(days=1)
                    self._plot_weekview(self._hid, self._detail, db, self._firstday)
                case "btnNextWeekHour":
                    self._firstday += datetime.timedelta(days=7)
                    self._plot_weekview(self._hid, self._detail, db, self._firstday)
                case _:
                    return super().process_message(idmsg, **kwargs)
            return True 
        return super().process_message(idmsg, **kwargs)


class HourTab(Container):
    """_summary_

    Attributes:
        _gui (_type_): _description_
        _schedule (_type_): _description_
        _images_dict (_type_): _description_
        _selclock_dlg (_type_): _description_
        _selschedule_dlg (_type_): _description_
        _hoursdb (_type_): _description_
    """
    def __init__(self, owner: Container, schedule: Schedule):
        """_summary_

        Args:
            owner (tkWin): _description_
        """
        super().__init__()
        self._gui: tkWin = cast(tkWin, owner)
        self._gui.filter_message(self.process_message)
        self._schedule: Schedule = schedule
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

        self._selclock_dlg: DialogCtrl = cast(DialogCtrl, self.get_control("dlgSelClock"))
        self._selclock_dlg.register_eventhandler("confirm", self._selclockdlg_confirm)
        self._selclock_dlg.register_eventhandler("beforego", self._selclockdlg_beforego)
        self._selclock_dlg.register_eventhandler("cancel", self._selclockdlg_cancel)

        self._clkstr: str = ""
        self._old_clkstr: str = ""

        self._selschedule_dlg: DialogCtrl = cast(DialogCtrl, self.get_control("dlgSelSchedule"))
        self._selschedule_dlg.register_eventhandler("confirm", self._selscheduledlg_confirm)
        self._selschedule_dlg.register_eventhandler("beforego", self._selscheduledlg_beforego)
        self._selschedule_dlg.register_eventhandler("cancel", self._selscheduledlg_cancel)

        self._schedulestr: str = ""
        self._old_schedulestr: str = ""

        self._hoursdb: TimeDatabase = TimeDatabase()

    def _open(self, dbpath: str):
        """_summary_
        Args:
            dbpath (type): _description_
        """
        return self._hoursdb.open(dbpath)

    def new_hours(self, dbpath: str):
        """_summary_
        Args:
            dbpath (type): _description_
        """
        _ = self._open(dbpath)

    def open_hours(self, dbpath: str):
        """_summary_
        Args:
            dbpath (type): _description_
        """
        _ = self._open(dbpath)
        plans = self._hoursdb.read_plans()
        for pid, plandata in plans.items():
            name = plandata["name"]
            iid = cast(IconTuple, plandata["iid"])
            self.create_hourctrl(pid,
                name, iid,
                plandata["reminders"], plandata["sums"], plandata['fid'])
            for eid, reminderdata in plandata["reminders"].items():
                if clock_time := reminderdata["clk_time"]:
                    self._schedule.add_event(eid, name, clock_time, reminderdata["every"], reminderdata["unit"],
                        reminderdata["custom"],
                        reminderdata["cycbgn_dtime"], reminderdata["cycend_dtime"],
                        ActTyp.LOCK_SCREEN)

    def update_hourctrl_attrib(self, uid: int, attrib: str, val: str | int, eid: int = 0):
        """_summary_

        Args:
            uid (int): _description_
            attrib (str): _description_
            val (str | float): _description_

        Raises:
            KeyError: _description_
        """
        match attrib:
            case "name":
                ctrl_item1 = cast(LabelCtrl, self.get_control(f"lblItem{uid}"))
                # ctrl_item1['text'] = val
                _ = ctrl_item1.configure(text=val, anchor='w')
            case "image":
                ctrl_item2 = cast(ImageBtttonCtrl, self.get_control(f"btnItem{uid}"))
                ctrl_item2.change_image(cast(str, val))
            case "clock":   # lblClock{hid}_{eid}
                if val in ["", "选择定时提醒"]:
                    return
                ctrl_item3 = cast(LabelCtrl, self.get_control(f"lblClock{uid}_{eid}"))
                ctrl_item3.set_text(cast(str, val))
            case "sum":
                ctrl_item4 = cast(LabelCtrl, self.get_control(f"lblSumHour{uid}"))
                _ = ctrl_item4.configure(text=f"{float(val)/60:.1f}\nhours")
            case _:
                raise KeyError(f"Unkonw arrtrib: {attrib}")

    def get_hourctrl_attrib(self, uid: int, attrib: str, eid: int = 0) -> str:
        """_summary_

        Args:
            uid (int): _description_
            attrib (str): _description_

        Returns:
            str: _description_
        """
        val: str = ""
        match attrib:
            case "name":
                ctrl_item1 = cast(LabelCtrl, self.get_control(f"lblItem{uid}"))
                val = cast(str, ctrl_item1['text'])
            # case "image":
                # ctrl_item2 = cast(ImageBtttonCtrl, self.get_control(f"btnItem{id_}")
                # raise NotImplementedError("")
            case "clock":
                ctrl_item3 = cast(LabelCtrl, self.get_control(f"lblClock{uid}_{eid}"))
                val = ctrl_item3.get_text()
            case "sum":
                ctrl_item4 = cast(LabelCtrl, self.get_control(f"lblSumHour{uid}"))
                val = cast(str, ctrl_item4['text'])
            case _:
                val = ""
        return val

    def delete_fatherctrl(self, father: int):
        """_summary_

        Args:
            father (int): _description_
        """
        children =self._hoursdb.get_children(father)
        for sid in children.keys():
            self.delete_hourctrl(father, sid)
        self.delete_hourctrl(-1, father)

    def delete_hourctrl(self, father: int, iid: int):
        """_summary_

        Args:
            father (int): _description_
            iid (int): _description_
        """
        self._gui.delete_control(f"frmItem{iid}")
        self._gui.delete_control(f"btnItem{iid}")
        self._gui.delete_control(f"lblItem{iid}")
        self._gui.delete_control(f"pnlClock{iid}")
        plan = self._hoursdb.get_plandata(iid)
        for eid in plan["reminders"]:
            self._gui.delete_control(f"lblClock{iid}_{eid}")
        self._gui.delete_control(f"lblSumHour{iid}")
        self._gui.delete_control(f"frmClock{iid}")
        if father == -1:
            self._gui.delete_control(f"frmGroup{iid}")

    def add_clock_ctrl(self, hid: int, eid: int, reminder: ReminderDataDict):
        clk_str, _ = reminder2str(reminder)
        pv(clk_str)

        level = 4

        pnl_clock = cast(ImagePanelCtrl, self._gui.get_control(f"pnlClock{hid}"))
        pnl_clock.show()

        frm_clock = cast(FrameCtrl, self._gui.get_control(f"frmClock{hid}"))

        lblclock_xml = self._gui.create_xml("Label", {"id": f"lblClock{hid}_{eid}",
            "text": clk_str, "clickable": "true",
            "options":"{'justify':'center'}"})
        _, lbl_clock = self._gui.create_control(frm_clock, lblclock_xml, level)
        self._gui.assemble_control(lbl_clock, {"layout":"pack",
            "pack":"{'side':'left'}"}, f"{'  '*level}")

    def del_clock_ctrl(self, hid: int, eid: int):
        pnl_clock = cast(ImagePanelCtrl, self._gui.get_control(f"pnlClock{hid}"))

        # lbl_clock = cast(LabelCtrl, self._gui.get_control(f"lblClock{hid}_{eid}"))
        self._gui.delete_control(f"lblClock{hid}_{eid}")
        pnl_clock.hide()

    def create_hourctrl(self, hid: int, item: str, iid: IconTuple,
            reminders: dict[int, ReminderDataDict], sums: int, fid: int = -1):
        """_summary_

        Args:
            hid (int): _description_
            item (str): _description_
            iid (IconTuple): _description_
            clock (str): _description_
            sums (int): _description_, in minutes
            fid (int, optional): _description_. Defaults to -1.
        """
        imagepath = self._get_imagepath(iid.grpidx, iid.eleidx)

        frmain = cast(Widget, self.get_control("frmHourMain"))
        is_subitem = (fid != -1)
        if is_subitem:
            frmgroup = cast(Widget, self.get_control(f"frmGroup{fid}"))
            item_padx1 = 15
            item_padx2 = 5
        else:
            xml = self._gui.create_xml("Frame", {"id":f"frmGroup{hid}"})
                 # "options":"{'borderwidth':1,'relief':'ridge'}"})
            _, frmgroup = self._gui.create_control(frmain, xml, 2)
            item_padx1 = 0
            item_padx2 = 5

        level = 3
        frmitem_xml = self._gui.create_xml("Frame", {"id": f"frmItem{hid}"})
        _, frm_item = self._gui.create_control(frmgroup, frmitem_xml, level)

        level = 4

        radio = 0.8 if is_subitem else 1.0

        btnitem_xml = self._gui.create_xml("ImageButton", {"id": f"btnItem{hid}",
            "image": imagepath,
            "options": f"{{'height': {int(60 * radio)}, 'width': {int(60 * radio)}}}"}, frmitem_xml)
        _, btn_item = self._gui.create_control(frm_item, btnitem_xml, level)
        self._gui.assemble_control(btn_item, {"layout":"grid",
            "grid":"{'row':0,'column':0,'rowspan':2}"}, '  '*level)

        lblitem_xml = self._gui.create_xml("Label", {"text": item,
            "id": f"lblItem{hid}", "options": "{'width':48}"}, frmitem_xml)
        # pv(lbl_item_xml)
        _, lbl_item = self._gui.create_control(frm_item, lblitem_xml, level)
        self._gui.assemble_control(lbl_item, {"layout":"grid",
            "grid":"{'row':0,'column':1,'sticky':'w'}"},
            f"{'  '*level}")

        frmclock_xml = self._gui.create_xml("Frame", {"id": f"frmClock{hid}"}, frmitem_xml)
        _, frm_clock = self._gui.create_control(frm_item, frmclock_xml, level)
        self._gui.assemble_control(frm_clock, {"layout":"grid",
            "grid": "{'row':1,'column':1,'sticky':'w'}"}, f"{'  '*level}")

        pnlclock_xml = self._gui.create_xml("ImagePanel", {"id": f"pnlClock{hid}",
            "image": "VaadinAlarm.png",
             "options": "{'height':20, 'width':20}"}, frmclock_xml)
        _, pnl_clock = self._gui.create_control(frm_clock, pnlclock_xml, level)
        self._gui.assemble_control(pnl_clock, {"layout":"pack",
            "pack":"{'side':'left'}"}, f"{'  '*level}")

        i = 0
        for eid, data in reminders.items():
            clk_str, _ = reminder2str(data)
            if clk_str:
                lblclock_xml = self._gui.create_xml("Label", {"id": f"lblClock{hid}_{eid}",
                    "text": clk_str, "clickable": "true",
                    "options":"{'justify':'center'}"}, frmclock_xml)
                _, lbl_clock = self._gui.create_control(frm_clock, lblclock_xml, level)
                self._gui.assemble_control(lbl_clock, {"layout":"pack",
                    "pack":"{'side':'left'}"}, f"{'  '*level}")
                i += 1

        if i <= 0:
            cast(ImagePanelCtrl, pnl_clock).hide()

        lblsum_xml = self._gui.create_xml("Label", {"id": f"lblSumHour{hid}",
            "text": f"{sums/60:.1f}\nhours", "clickable": "true",
            "options":"{'justify':'center'}"}, frmitem_xml)
        _, lbl_sum = self._gui.create_control(frm_item, lblsum_xml, level)
        self._gui.assemble_control(lbl_sum, {"layout":"grid",
            "grid":"{'row':0,'column':2,'rowspan':2,'sticky':'w'}"}, f"{'  '*level}")

        self._gui.assemble_control(frm_item, {"layout": "pack",
            "pack": f"{{'side':'top','pady':1,'padx':({item_padx1},{item_padx2})}}"},
            f"{'  '*(level-1)}")

        if not is_subitem:
            if hid == 1:
                pady1 = 10
            else:
                pady1 = 5
            self._gui.assemble_control(frmgroup, {"layout": "pack",
                "pack":f"{{'side':'top','pady':({pady1},5),'fill':'x'}}"}, f"{'  '*(2-1)}")

    def _get_imagepath(self, group: int, index: int):
        """_summary_

        Args:
            group (int): _description_
            index (int): _description_

        Returns:
            _type_: _description_
        """
        return self._images_dict[group].get(index, "CircleFlagsUsBetsyRoss.png")

    def get_control(self, idctrl: str) -> object:
        """_summary_

        Args:
            idctrl (str): _description_

        Returns:
            object: _description_
        """
        return self._gui.get_control(idctrl)

    def show_selclockdlg(self, owner: Container | None = None,
            x: int = 0, y: int = 0, **kwargs: object):
        """_summary_
        Args:
            owner (type): _description_
            x (type): _description_
            y (type): _description_
            kwargs (type): _description_
        """
        self._selclock_dlg.do_show(owner, x, y, **kwargs)
        return self._clkstr

    def _selclockdlg_beforego(self, **kwargs: object):
        po(f"_selclockdlg_beforego: {kwargs}")
        clkstr = cast(str, kwargs['clkstr'])
        self._old_clkstr = clkstr
        clkstr_list = clkstr.split()
        cmb_selday = cast(ComboboxCtrl, self._selclock_dlg.get_control("cmbSelDay"))
        cmb_selday.set_val(clkstr_list[0])
        time_list = clkstr_list[1].split(":")
        cmb_selhour = cast(ComboboxCtrl, self._selclock_dlg.get_control("cmbSelHour"))
        cmb_selhour.set_val(time_list[0])
        cmb_selminute = cast(ComboboxCtrl, self._selclock_dlg.get_control("cmbSelMinute"))
        cmb_selminute.set_val(time_list[1])

    def _selclockdlg_cancel(self, **_: object):
        self._clkstr = self._old_clkstr

    def _selclockdlg_confirm(self, **kwargs: object) -> tuple[bool, str]:
        """_summary_
        Args:
            kwargs (type): _description_
        """
        po(f"_selclockdlg_confirm: {kwargs}")
        # owner = cast(Container, self._selclock_dlg.owner)
        cmb_selday = cast(ComboboxCtrl, self._selclock_dlg.get_control("cmbSelDay"))
        sel_day = cmb_selday.get_val()
        pv(sel_day)
        cmb_selhour = cast(ComboboxCtrl, self._selclock_dlg.get_control("cmbSelHour"))
        sel_hour = cmb_selhour.get_val()
        pv(sel_hour)
        cmb_selminute = cast(ComboboxCtrl, self._selclock_dlg.get_control("cmbSelMinute"))
        sel_minute = cmb_selminute.get_val()
        pv(sel_minute)
        hour = int(sel_hour[:-1])
        minute = int(sel_minute[:-1])
        # clk_time = str2time(f"{hour:02}:{minute:02}")
        # day = str_to_intenum(DayType, sel_day)
        clk_str = f"{sel_day} {hour:02}:{minute:02}"
        # _ = owner.process_message("changeClock", clk_time=clk_time,
        #     custom=day, clk_str=clk_str, **kwargs)
        self._clkstr = clk_str
        return True, ""

    def show_selscheduledlg(self, owner: Container | None = None, x: int = 0, y: int = 0, **kwargs: object):
        """_summary_
        Args:
            owner (type): _description_
            x (type): _description_
            y (type): _description_
        """
        self._selschedule_dlg.do_show(owner, x, y, **kwargs)
        return self._schedulestr

    def _str2duration(self, duration_str: str):
        PATTERN = re.compile(
            r"""
            ^               # Start of string (ensure we match the entire duration string)
            (?:(\d+)h)?     # Optional hours group: (\d+) = 1+ digits, h = literal "h" (non-capturing group for optional)
            \s*             # Optional whitespace (handles "1h 30m" or "1h30m")
            (?:(\d+)m)?     # Optional minutes group: (\d+) = 1+ digits, m = literal "m" (non-capturing group for optional)
            $               # End of string (avoid partial matches like "1h30mxyz")
            """,
            re.VERBOSE | re.IGNORECASE  # VERBOSE = readable regex; IGNORECASE = match H/M or h/m
        )

        match = PATTERN.match(duration_str.strip())
        if not match:
            raise ValueError(f"Invalid duration string: '{duration_str}' (expected format like 15m, 1h30m, 3h)")

        # Extract groups: group 1 = hours, group 2 = minutes (default to 0 if None)
        hours_str = match.group(1)
        minutes_str = match.group(2)

        # Convert to integers (0 if missing)
        hours = int(hours_str) if hours_str else 0
        minutes = int(minutes_str) if minutes_str else 0
        return hours * 60 + minutes

    def _selscheduledlg_beforego(self, **kwargs: object):
        po(f"_selscheduledlg_beforego: {kwargs}")
        schedulestr = cast(str, kwargs['schedulestr'])
        self._old_schedulestr = schedulestr

        cmb_selunit = cast(ComboboxCtrl, self._selschedule_dlg.get_control("cmbSelUnit"))
        cmb_selval = cast(ComboboxCtrl, self._selschedule_dlg.get_control("cmbSelVal"))

        schedule_list = schedulestr.split()
        if len(schedule_list) == 3:
            cmb_selunit.set_val(schedule_list[0] + " " + schedule_list[1])
            cmb_selval.set_val(schedule_list[2])

    def _selscheduledlg_cancel(self, **_: object):
        self._schedulestr = self._old_schedulestr

    def _selscheduledlg_confirm(self, **kwargs: object) -> tuple[bool, str]:
        """_summary_
        Args:
            kwargs (type): _description_
        """
        po(f"_selscheduledlg_confirm: {kwargs}")
        cmb_selunit = cast(ComboboxCtrl, self._selschedule_dlg.get_control("cmbSelUnit"))
        unit_str = cmb_selunit.get_val()
        cmb_selval = cast(ComboboxCtrl, self._selschedule_dlg.get_control("cmbSelVal"))
        duration_str = cmb_selval.get_val()

        self._schedulestr = f"{unit_str} {duration_str}"

        return True, ""

    def show_recordhourdlg(self, owner: Container | None = None, x: int = 0, y: int = 0,
            **kwargs: object):
        """_summary_
        Args:
            owner (type): _description_
            x (type): _description_
            y (type): _description_
            kwargs (type): _description_
        """
        dlg_id = "dlgRecordHour"
        dlg_cfg = self._gui.get_customctrlcfg(dlg_id)
        dlg = RecordHourDlg(self._gui, dlg_cfg)
        dlg.do_show(owner, x, y, **kwargs)

    def show_hourdetaildlg(self, owner: Container | None = None, x: int = 0, y: int = 0,
            **kwargs: object):
        """_summary_
        Args:
            owner (type): _description_
            x (type): _description_
            y (type): _description_
            kwargs (type): _description_
        """
        dlg_id = "dlgHourDetail"
        dlg_cfg = self._gui.get_customctrlcfg(dlg_id)
        dlg = HourDetailDlg(self._gui, dlg_cfg)
        dlg.do_show(owner, x, y, **kwargs)

    def show_edithourdlg(self, owner: Container | None = None, x: int = 0, y: int = 0,
            **kwargs: object):
        """_summary_
        Args:
            owner (type): _description_
            x (type): _description_
            y (type): _description_
            kwargs (type): _description_
        """
        dlg_id = "dlgEditHour"
        dlg_cfg = self._gui.get_customctrlcfg(dlg_id)
        dlg = EditHourDlg(self._gui, dlg_cfg)
        dlg.do_show(owner, x, y, **kwargs)

    def modify_clock(self, hid: int, eid: int, clk_time: datetime.time, custom: DayType):
        cycbgn_dtime = datetime.datetime.now()
        reminder = self._hoursdb.modify_reminder(hid, eid,
            clk_time=clk_time,
            every=1,
            unit=TimeUnit.WEEK,
            custom=custom,
            cycbgn_dtime=cycbgn_dtime,
            cycend_dtime=None,
        )
        clk_str, _ = reminder2str(reminder)
        pv(clk_str)
        self.update_hourctrl_attrib(hid, "clock", clk_str, eid)

        self._schedule.modify_event(eid, clk_time, cycbgn_dtime, custom=reminder["custom"])

    @override
    def process_message(self, idmsg: str, **kwargs: object):
        if idmsg.startswith("btnItem"):
            hid = int(idmsg[7:])
            x, y = cast(tuple[int, int], kwargs["mousepos"])
            self.show_hourdetaildlg(self, x+20, y+20, id=hid, db=self._hoursdb)
            return True
        elif idmsg.startswith("lblSumHour"):
            hid = int(idmsg[10:])
            x, y = cast(tuple[int, int], kwargs["mousepos"])
            self.show_recordhourdlg(self, x+20, y+20, id=hid, db=self._hoursdb)
            return True
        elif idmsg.startswith("lblClock"):  # lblClock{hid}_{eid}
            msglist = idmsg.split("_")
            # pv(idmsg)
            len_eid = len(msglist[1])
            # pv(len_eid)
            hid = int(idmsg[8: -(len_eid + 1)])
            # pv(hid)
            eid = int(idmsg[-len_eid: ])
            # pv(eid)
            x, y = cast(tuple[int, int], kwargs["mousepos"])
            lbl_clock = cast(LabelCtrl, self._gui.get_control(idmsg))
            oldclkstr = lbl_clock.get_text()
            kwargs.update({"clkstr": oldclkstr})
            clkstr = self.show_selclockdlg(self, x+20, y+20, id=hid, eid=eid, **kwargs)
            reminder = str2reminder(clkstr, "")
            clk_time = reminder["clk_time"]
            assert clk_time is not None
            if clkstr != oldclkstr:
                self.modify_clock(hid, eid, clk_time, cast(DayType, reminder["custom"]))
            return True
        elif idmsg == "btnNewHour":
            x, y = cast(tuple[int, int], kwargs["mousepos"])
            self.show_edithourdlg(self, x+20, y+20, fid=-1, id=0, db=self._hoursdb)
            return True
        else:
            match idmsg:
                case "showSelClockDlg": # come from `EditHourDlg` or <-`HourDetailDlg`<-`EditHourDlg`
                    owner = cast(Dialog, kwargs["owner"])
                    x, y = cast(tuple[int, int], kwargs["pos"])
                    options = cast(dict[str, object], kwargs["options"])
                    return self.show_selclockdlg(owner, x, y, **options)
                case "showSelScheduleDlg": # come from `EditHourDlg` or <-`HourDetailDlg`<-`EditHourDlg`
                    owner = cast(Dialog, kwargs["owner"])
                    x, y = cast(tuple[int, int], kwargs["pos"])
                    options = cast(dict[str, object], kwargs["options"])
                    return self.show_selscheduledlg(owner, x, y, **options)
                case "RecordHour":  # come from `RecordHourDlg`
                    hid = cast(int, kwargs["id"])
                    strt_dtime = cast(datetime.datetime, kwargs["strt_dtime"])
                    duration = cast(int, kwargs["duration"])
                    # po(kwargs)
                    name = self._hoursdb.get_plandata(hid)["name"]
                    _ = self._hoursdb.add_record(pid=hid, name=name,
                        bgn_dtime=strt_dtime, duration=duration)
                case "ChangeSum":   # come from RecordHourDlg
                    hid = cast(int, kwargs["id"])
                    sum_minutes= cast(int, kwargs["sum"])
                    self.update_hourctrl_attrib(hid, "sum", sum_minutes)
                    _ = self._hoursdb.modify_plan(hid, sums=sum_minutes)
                case "changeItemImage": # come from <-`HourDetailDlg`<-`EditHourDlg`
                    hid = cast(int, kwargs["id"])
                    grp = cast(int, kwargs["group"])
                    idx = cast(int, kwargs["index"])
                    imagepath = self._get_imagepath(grp, idx)
                    self.update_hourctrl_attrib(hid, "image", imagepath)
                    icon = IconTuple(grp, idx)
                    _ = self._hoursdb.modify_plan(hid, iid=icon)
                case "changeClock": # come from <-`HourDetailDlg`<-`EditHourDlg`
                    hid = cast(int, kwargs["id"])
                    eid = cast(int, kwargs["eid"])
                    clk_time = cast(datetime.time, kwargs["clk_time"])
                    custom = cast(DayType, kwargs["custom"])

                    self.modify_clock(hid, eid, clk_time, custom)
                case "NewClock": # come from `HourDetailDlg`<-`EditHourDlg`
                    hid = cast(int, kwargs["hid"])
                    name = cast(str, kwargs["name"])
                    reminder = cast(ReminderDataDict, kwargs["reminder"])
                    eid = self._hoursdb.add_reminder(hid, **reminder)
                    if clk_time := reminder['clk_time']:
                        self._schedule.add_event(eid, name, clk_time, reminder['every'],
                            reminder['unit'], reminder['custom'],
                            reminder['cycbgn_dtime'], reminder['cycend_dtime']
                        )
                        self.add_clock_ctrl(hid, eid, reminder)
                case "DelClock": # come from `HourDetailDlg`<-`EditHourDlg`
                    hid = cast(int, kwargs["hid"])
                    eid = cast(int, kwargs["eid"])
                    reminder = cast(ReminderDataDict, kwargs["reminder"])
                    self._hoursdb.del_reminder(hid, eid)
                    self._schedule.del_event(eid)
                    self.del_clock_ctrl(hid, eid)
                case "NewSchedule":  # come from <-`HourDetailDlg`<-`EditHourDlg`<-`SelScheduleDlg`
                    hid = cast(int, kwargs["id"])
                    reminder = cast(ReminderDataDict, kwargs["reminder"])
                    eid = self._hoursdb.add_reminder(hid, **reminder)
                case "DelSchedule":  # come from <-`HourDetailDlg`<-`EditHourDlg`<-`SelScheduleDlg`
                    hid = cast(int, kwargs["id"])
                    eid = cast(int, kwargs["eid"])
                    self._hoursdb.del_reminder(hid, eid)
                case "ModifySchedule":  # come from <-`HourDetailDlg`<-`EditHourDlg`<-`SelScheduleDlg`
                    hid: int = cast(int, kwargs["id"])
                    eid = cast(int, kwargs["eid"])
                    reminder = cast(ReminderDataDict, kwargs["reminder"])
                    _ = self._hoursdb.modify_reminder(hid, eid,
                        every=reminder["every"],
                        unit=reminder["unit"],
                        custom=reminder["custom"],
                        duration=reminder["duration"],
                        cycbgn_dtime=datetime.datetime.now(),
                    )
                case "deleteItem":  # come from <-`HourDetailDlg`<-`EditHourDlg`
                    hid = cast(int, kwargs["id"])
                    detail = self._hoursdb.get_plandata(hid)

                    children = self._hoursdb.get_children(hid)
                    if len(children) > 0:
                        return False, f"Couldn't delete {detail['name']} wtih children"

                    self._gui.delete_control(f"frmItem{hid}")
                    self._gui.delete_control(f"btnItem{hid}")
                    self._gui.delete_control(f"lblItem{hid}")
                    self._gui.delete_control(f"btnClock{hid}")
                    self._gui.delete_control(f"lblSum{hid}")
                    fid = detail["fid"]
                    if fid == -1:
                        self._gui.delete_control(f"frmGroup{hid}")

                    self._hoursdb.del_plan(hid)

                    return True, f"Success to delete {detail['name']}"
                case "updateHour":  # come from `HourDetailDlg`
                    hid = cast(int, kwargs["id"])
                    attr = cast(str, kwargs["attrib"])
                    val = cast(str | int, kwargs["val"])
                    self.update_hourctrl_attrib(hid, attr, val)
                case "NewHour": # come from `EditHourDlg` or <-`HourDetailDlg`<-`EditHourDlg`
                    name =cast(str, kwargs["name"])
                    fid = cast(int, kwargs["fid"])
                    iid = cast(IconTuple, kwargs["iid"])
                    reminders = cast(dict[int, ReminderDataDict], kwargs["reminders"])

                    plandata = default_plan_data()
                    plandata["fid"] = fid
                    plandata["iid"] = iid
                    plandata["name"] = name
                    hid = self._hoursdb.add_plan(**plandata)
                    self.create_hourctrl(hid, name, iid, reminders, 0, fid)
                case "getImagePath": # come from `HourDetailDlg`
                    group = cast(int, kwargs["group"])
                    index = cast(int, kwargs["index"])
                    return self._get_imagepath(group, index)
                case "getImagesDict":   # come from `EditHourDlg`
                    return self._images_dict
                case "DeleteFatherCtrl":    # come from `TimeDatabase`
                    hid = cast(int, kwargs["id"])
                    self.delete_fatherctrl(hid)
                case _:
                    return None
            return True

    @override
    def destroy(self, **kwargs: object):
        """ _summary_
        """
        _ = self._hoursdb.close()
