#!/usr/bin/python3
# -*- coding: UTF-8 -*-
from __future__ import annotations
import datetime
import xml.etree.ElementTree as et
from typing import cast, override

from pyutilities.logit import po, pv, pe
from pyutilities.winbasic import Widget, Container, Dialog
from pyutilities.tkwin import tkWin
from pyutilities.tkwin import LabelCtrl, EntryCtrl, ButtonCtrl, ComboboxCtrl, ImageBtttonCtrl
from pyutilities.tkwin import PicsListviewCtrl, DialogCtrl, FrameCtrl
from pyutilities.matplot import MatPlotCtrl, LineData
# from pyutilities.calendarctrl import CalendarCtrl
from pyutilities.scrollpickerctrl import DateScrollPickerCtrl, TimeScrollPickerCtrl

from src.schedule import Schedule
from src.hour_type import HourTuple, HourDict
from src.time_database_type import IconTuple
from src.time_database_type import TimeUnit, DayType, str_to_intenum
from src.time_database_type import reminder2clkstr, time2str, str2time

from src.time_database import TimeDatabase


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

        Args:
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
        scrollpicker = DateScrollPickerCtrl((x, y+20), "选择日期")
        date = scrollpicker.get_datestr()
        pv(date)
        lbl_day = cast(LabelCtrl, self.get_control("lblSelDayRecordHour"))
        lbl_day.set_text(date)

    def _select_strtime(self, **kwargs: object):
        """_summary_
        """
        lbl_strtime = cast(LabelCtrl, self.get_control("lblSelStrtRecordHour"))
        x, y = cast(tuple[int, int], kwargs["mousepos"])
        scrollpicker = TimeScrollPickerCtrl((x, y+20), "选择时间", lbl_strtime.get_text())
        strt_time = scrollpicker.get_datestr()
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
        scrollpicker = TimeScrollPickerCtrl((x, y+20), "持续时间", lastime)
        lastime = scrollpicker.get_datestr()
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
        self._old_clock: str = ""
        self._old_schedule: str = ""
        self._old_rid: tuple[int, int] = (0, 0)

    @override
    def _beforego(self, **kwargs: object):
        po(f"_edithourdlg_beforego: {kwargs}")
        fid = cast(int, kwargs["father"])
        self._old_fid = fid
        iid = cast(int, kwargs["id"])
        db = cast(TimeDatabase, kwargs["db"])
        owner = cast(Dialog, self.owner)

        if fid != -1:
            lbl_father = cast(LabelCtrl, self.get_control("lblSelFatherEditHour"))
            detail_father = self._get_hourdetail(db, fid)
            name_father = detail_father["name"]
            pv(name_father)
            lbl_father['text'] = name_father

        if iid == 0:
            self.set_title("新建项目")
            btn_delhour = cast(ButtonCtrl, self.get_control("btnDelItemEditHour"))
            btn_delhour.hide()
            grp, idx = 0, 0
        else:
            self.set_title("编辑项目")
            detail = self._get_hourdetail(db, iid)
            pv(detail)

            ent_name = cast(EntryCtrl, self.get_control("txtItemEditHour"))
            ent_name.set_val(detail["name"])
            ent_name.disable()
            lbl_selclock = cast(LabelCtrl, self.get_control("lblSelClockEditHour"))
            lbl_selclock['text'] = detail["clock"] if detail["clock"] else "选择定时提醒"
            lbl_selschedule = cast(LabelCtrl, self.get_control("lblSelScheduleEditHour"))
            lbl_selschedule['text'] = detail["schedule"] if detail["schedule"] else "选择时间投入计划"
            grp, idx = detail["rid"]

            self._old_clock = lbl_selclock['text']
            self._old_schedule = lbl_selschedule['text']
            self._old_rid = detail["rid"]

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
        father = cast(int, kwargs["father"])
        iid = cast(int, kwargs["id"])
        if iid != 0:    # edit item
            lbl_selclock = cast(LabelCtrl, self.get_control("lblSelClockEditHour"))
            clock = cast(str, lbl_selclock['text'])
            pv(clock)
            if clock != self._old_clock:
                _ = owner.process_message("changeClock", id=iid, clock=clock)

            lbl_selschedule = cast(LabelCtrl, self.get_control("lblSelScheduleEditHour"))
            schedule = cast(str, lbl_selschedule['text'])
            pv(schedule)
            if schedule != self._old_schedule:
                _ = owner.process_message("changeSchedule", id=iid, schedule=schedule)

            lst_itemimage = cast(PicsListviewCtrl,
                self.get_control("lstImageEditHour"))
            grp, idx = lst_itemimage.get_selected()
            if (grp, idx) != self._old_rid:
                _ = owner.process_message("changeItemImage",
                    id=iid, group=grp, index=idx)
        else:   # New item
            ent_name = cast(EntryCtrl, self.get_control("txtItemEditHour"))
            name = ent_name.get_val()
            # pv(name)
            if len(name) == 0:
                return False, "Name should not be empty"
            lbl_selclock = cast(LabelCtrl, self.get_control("lblSelClockEditHour"))
            clock  = cast(str, lbl_selclock['text'])
            clock_val = "" if clock == "选择定时提醒" else clock
            lbl_selschedule = cast(LabelCtrl, self.get_control("lblSelScheduleEditHour"))
            schedule = cast(str, lbl_selschedule['text'])
            schedule_val = "" if schedule == "选择时间投入计划" else schedule
            lst_itemimage = cast(PicsListviewCtrl,
                self.get_control("lstImageEditHour"))
            rid = lst_itemimage.get_selected()
            if father == -1:
                _ = owner.process_message("newHour",
                    name=name, father=father, rid=rid, clock=clock, schedule=schedule)
            else:
                _ = owner.process_message("createChild", name=name, rid=rid,
                    clock=clock_val, schedule=schedule_val, father=father)
        return True, ""

    def _get_hourdetail(self, db: TimeDatabase, iid: int):
        """_summary_

        Args:
            iid (int): _description_

        Returns:
            _type_: _description_
        """
        detail: HourDict = {"name": "", "rid": (0, 0), "clock": "", "schedule": "",
            "sums": 0, "father": -1}
        # owner = cast(Container, self._owner)
        _ = db.get_hourdetail(iid, detail)
        return detail

    @override
    def process_message(self, idmsg: str, **kwargs: object):
        if self.alive:
            kwargs.update(self._extral_msg)
            owner = cast(Dialog, self.owner)
            match idmsg:
                case "lblSelClockEditHour":
                    pv(kwargs)
                    x, y = cast(tuple[int, int], kwargs["mousepos"])
                    return owner.process_message("showSelClockDlg", owner=self,
                        pos=(x+20,y+20), options=kwargs)
                case "changeClock": # come from `SelClockDlg`
                    clock = cast(str, kwargs["clock"])
                    lbl_selclock = cast(LabelCtrl, self.get_control("lblSelClockEditHour"))
                    lbl_selclock['text'] = clock
                case "lblSelScheduleEditHour":
                    pv(kwargs)
                    x, y = cast(tuple[int, int], kwargs["mousepos"])
                    return owner.process_message("showSelScheduleDlg", owner=self,
                        pos=(x+20,y+20), options=kwargs)
                case "changeSchedule":  # come from `SelScheduleDlg`
                    schedule = cast(str, kwargs["schedule"])
                    lbl_selschedule = cast(LabelCtrl, self.get_control("lblSelScheduleEditHour"))
                    lbl_selschedule['text'] = schedule
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

        self._iid: int = 0
        self._detail: HourDict = {"name": "", "rid": (0, 0), "clock": "",
            "schedule": "", "sums": 0, "father": -1}
        self._db: TimeDatabase | None = None
        self._firstday: datetime.date = datetime.date(2025,12,25)
        

    def _update_hourdetail(self, attrib: str, val: str | float):
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

    def _get_hourdetail(self, db: TimeDatabase, iid: int):
        """_summary_

        Args:
            iid (int): _description_

        Returns:
            _type_: _description_
        """
        detail: HourDict = {"name": "", "rid": (0, 0), "clock": "", "schedule": "",
            "sums": 0, "father": -1}
        # owner = cast(Container, self._owner)
        _ = db.get_hourdetail(iid, detail)
        return detail

    def _plot_weekview(self, iid: int, detail: HourDict, db: TimeDatabase,
            firstday: datetime.date):
        children = db.get_children(iid)
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

        plt_weekview = cast(MatPlotCtrl, self.get_control("pltEveryDayHour"))
        plt_weekview.clear_canvas()
        xdata: list[int] = []
        father_ydata: list[float] = []
        children_ydata: dict[int, list[float]] = {}
        labels: list[str] = []
        for i in range(7):
            day = firstday + datetime.timedelta(days=i)
            weekday = day.weekday()
            labels.append(f"{week_day[weekday]}\n{day.day}")
            xdata.append(i)
            minutes = db.get_hoursbyday(iid, day) * 60
            father_ydata.append(minutes)
            po(f"minutes of day {day} is {minutes}")
            for sid in children.keys():
                minutes = db.get_hoursbyday(sid, day) * 60
                if children_ydata.get(sid) is None:
                    children_ydata[sid] = [minutes]
                else:
                    children_ydata[sid].append(minutes)
        plt_weekview.xdata = xdata
        father_yline = LineData(father_ydata,
            {"tick_label":labels,"width":0.4,"facecolor":"green"}, "bar")
        _ = plt_weekview.add_line(father_yline)
        bottom = father_ydata
        for sid, child_ydata in children_ydata.items():
            child_yline = LineData(child_ydata, {"width":0.4,"bottom":bottom}, "bar")
            bottom = child_ydata
            _ = plt_weekview.add_line(child_yline)
        limit_yline = LineData(limit_ydata, {"linestyle":"dotted","color":"red"})
        _ = plt_weekview.add_line(limit_yline)
        plt_weekview.draw()

    @override
    def _beforego(self, **kwargs: object):
        po(f"_hourdetaildlg_beforego: {kwargs}")
        self._iid = cast(int, kwargs["id"])
        self._db = cast(TimeDatabase, kwargs["db"])

        self._detail = self._get_hourdetail(self._db, self._iid)
        # po(f"{iid}: {detail}")
        # owner = cast(Container, self._owner)

        lbl_father = cast(LabelCtrl, self.get_control("lblFatherItemDetail"))
        fid = self._detail["father"]
        if fid != -1:
            detail_father = self._get_hourdetail(self._db, fid)
            name_father = detail_father["name"]
            pv(name_father)
            lbl_father['text'] = name_father
        else:
            lbl_father.hide()

        rid = self._detail["rid"]
        imagepath = self._get_imagepath(rid[0], rid[1])
        img_item = cast(ImageBtttonCtrl, self.get_control("btnImageHourDetail"))
        img_item.change_image(imagepath)

        strt_date = self._db.get_hourstartdate(self._iid)
        lbl_item = cast(LabelCtrl, self.get_control("lblInfoHourDetail"))
        lbl_item.set_text(f"{self._detail["name"]}\n从{strt_date}开始")
        self._update_hourdetail("sum", f"{self._detail["sums"]/ 60:.1f}")
        total_days = self._db.get_hourtotaldays(self._iid)
        self._update_hourdetail("TotalDays", total_days)
        hours_everyweek = self._db.get_hourseveryweek(self._iid)
        self._update_hourdetail("HoursEveryWeek", f"{hours_everyweek:.1f}")
        hours_last7days = self._db.get_hourslast7days(self._iid)
        self._update_hourdetail("HoursLast7Days", f"{hours_last7days:.1f}")
        hours_2milestone = self._db.get_hours2milestone(self._iid)
        self._update_hourdetail("RestHours2Milestone", hours_2milestone)

        lbl_selclock = cast(LabelCtrl, self.get_control("lblSelClockItemDetail"))
        lbl_selclock['text'] = self._detail["clock"]
        lbl_selschedule = cast(LabelCtrl, self.get_control("lblSelScheduleItemDetail"))
        lbl_selschedule['text'] = self._detail["schedule"]

        parent = cast(FrameCtrl, self.get_control("frmSubItmes"))
        children = self._db.get_children(self._iid)
        idx = 0
        for sid, child in children.items():
            self._children[idx] = HourTuple(iid=sid, name=child["name"], rid=child["rid"],
                clock=child["clock"], schedule=child["schedule"], sums=child["sums"],
                father=child["father"])
            self._create_childctrl(parent, idx, child["name"],
                child["rid"], f"{child["sums"] / 60: .1f}")
            idx += 1
        pv(self._children)
        self._last_cid = len(self._children) - 1
        lbl_totalsubitems = cast(LabelCtrl, self.get_control("lblTotalChildren"))
        lbl_totalsubitems["text"] = f"共{idx}个子项目"

        btn_prev = cast(ImageBtttonCtrl, self.get_control("btnPrevDayHour"))

        today = datetime.datetime.today().date()

        self._firstday = today + datetime.timedelta(days=-today.weekday())
        self._plot_weekview(self._iid, self._detail, self._db, self._firstday)

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

    @override
    def _cancel(self, **kwargs: object):
        po(f"_hourdetaildlg_cancel: {kwargs}")
        for idx, _ in self._children.items():
            self._delete_childctrl(idx)
        self._children.clear()
        return True, ""

    @override
    def _confirm(self, **kwargs: object):
        owner = cast(Dialog, self.owner)
        for idx, child in self._children.items():
            if idx > self._last_cid:
                name =      child.name
                rid =       child.rid
                clock =     child.clock
                schedule =  child.schedule
                father = cast(int, kwargs["id"])
                _ = owner.process_message("newHour",
                    name=name, father=father, rid=rid, clock=clock, schedule=schedule)
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
        recordhour_dlg = RecordHourDlg(self._app, dlg_cfg)
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
        dlg = EditHourDlg(self._app, dlg_cfg)
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
            rid: tuple[int, int], sums: str):
        """_summary_

        Args:
            parent (Widget): _description_
            uid (int): _description_
            sub_item (str): _description_
            rid (tuple[int, int]): _description_
            sums (str): _description_
        """
        imagepath = self._get_imagepath(rid[0], rid[1])

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
            iid = cast(int, kwargs["id"])
            db = cast(TimeDatabase, kwargs["db"])
            owner = cast(Dialog, self.owner)
            match idmsg:
                case "btnImageHourDetail":
                    detail = self._get_hourdetail(db, iid)
                    father = detail["father"]
                    x, y = cast(tuple[int, int], kwargs["mousepos"])
                    self._show_edithourdlg(self, x+20, y+20,
                        father=father, id=iid, db=db)
                case "changeItemImage": # come from `EditHourDlg`
                    grp = cast(int, kwargs["group"])
                    idx = cast(int, kwargs["index"])
                    imagebutton = cast(ImageBtttonCtrl, self.get_control("btnImageHourDetail"))
                    imagepath = self._get_imagepath(grp, idx)
                    # pv(imagepath)
                    imagebutton.change_image(imagepath)
                    _ = owner.process_message("changeItemImage",
                        id=iid, group=grp, index=idx)
                case "changeClock": # come from `EditHourDlg`
                    clock = cast(str, kwargs["clock"])
                    lbl_selclock = cast(LabelCtrl,
                        self.get_control("lblSelClockItemDetail"))
                    lbl_selclock['text'] = clock
                    self._update_hour(iid, "clock", clock)
                    _ = owner.process_message("changeClock", id=iid, clock=clock)
                case "changeSchedule":  # come from `EditHourDlg`
                    schedule = cast(str, kwargs["schedule"])
                    lbl_selschedule = cast(LabelCtrl,
                        self.get_control("lblSelScheduleItemDetail"))
                    lbl_selschedule['text'] = schedule
                    _ = owner.process_message("changeSchedule",
                        id=iid, schedule=schedule)
                case "deleteItem":  # come from `EditHourDlg`
                    _ = owner.process_message("deleteItem", id=iid)
                    self.destroy()
                case "btnAddChild":
                    x, y = cast(tuple[int, int], kwargs["mousepos"])
                    self._show_edithourdlg(self, x+20, y+20,
                        father=iid, id=0, db=db)
                case "createChild":  # come from `EditHourDlg`
                    parent = cast(FrameCtrl, self.get_control("frmSubItmes"))
                    cid = len(self._children)
                    name =cast(str, kwargs["name"])
                    rid =cast(tuple[int, int], kwargs["rid"])
                    self._create_childctrl(parent, cid, name, rid, "0.0")

                    clock_val = cast(str, kwargs["clock"]) 
                    schedule_val = cast(str, kwargs["schedule"])
                    father = cast(int, kwargs["father"])
                    self._children[cid] = HourTuple(iid=0, name=name, rid=rid,
                        clock=clock_val, schedule=schedule_val, sums=0, father=father)
                    lbl_totalsubitems = cast(LabelCtrl, self.get_control("lblTotalChildren"))
                    lbl_totalsubitems["text"] = f"共{len(self._children)}个子项目"
                case "btnRecordHourDetail":
                    detail = self._get_hourdetail(db, iid)
                    father = detail["father"]
                    x, y = cast(tuple[int, int], kwargs["mousepos"])
                    self.show_recordhourdlg(self, x+20, y+20,
                        father=father, id=iid, db=db)
                case "ChangeSum":   # come from `RecordHourDlg`
                    sum_minutes= cast(float, kwargs["sum"])
                    lbl_sum = cast(LabelCtrl, self.get_control("lblSumHourDetail"))
                    lbl_sum.set_text(f"{float(sum_minutes)/60:.1f}\nhours")
                    self._update_hour(iid, "sum", sum_minutes)
                case "btnPrevDayHour":
                    self._firstday -= datetime.timedelta(days=1)
                    self._plot_weekview(self._iid, self._detail, db, self._firstday)
                case "btnNextDayHour":
                    self._firstday += datetime.timedelta(days=1)
                    self._plot_weekview(self._iid, self._detail, db, self._firstday)
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

        self._selschedule_dlg: DialogCtrl = cast(DialogCtrl, self.get_control("dlgSelSchedule"))
        self._selschedule_dlg.register_eventhandler("confirm", self._selscheduledlg_confirm)

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
            reminder = list(plandata["reminders"].values())[0]
            clkstr = reminder2clkstr(reminder)
            iid = cast(IconTuple, plandata["iid"])
            self.create_hourctrl(pid,
                plandata["name"], iid,
                clkstr, plandata["sums"], plandata['fid'])

    def update_hourctrl_attrib(self, uid: int, attrib: str, val: str | int):
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
            case "clock":
                if val in ["", "选择定时提醒"]:
                    return
                ctrl_item3 = cast(ImageBtttonCtrl, self.get_control(f"btnClock{uid}"))
                if not ctrl_item3.visible:
                    ctrl_item3.show()
                # ctrl_item3['text'] = val
                _ = ctrl_item3.configure(text=val)
            case "sum":
                ctrl_item4 = cast(LabelCtrl, self.get_control(f"lblSumHour{uid}"))
                _ = ctrl_item4.configure(text=f"{float(val)/60:.1f}\nhours")
            case _:
                raise KeyError(f"Unkonw arrtrib: {attrib}")

    def get_hourctrl_attrib(self, uid: int, attrib: str) -> str:
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
                ctrl_item3 = cast(ImageBtttonCtrl, self.get_control(f"btnClock{uid}"))
                val = cast(str, ctrl_item3['text'])
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
        self._gui.delete_control(f"btnClock{iid}")
        self._gui.delete_control(f"lblSumHour{iid}")
        if father == -1:
            self._gui.delete_control(f"frmGroup{iid}")

    def create_hourctrl(self, hid: int, item: str, iid: IconTuple,
            clock: str, sums: int, fid: int = -1):
        """_summary_

        Args:
            hid (int): _description_
            item (str): _description_
            iid (IconTuple): _description_
            clock (str): _description_
            sums (int): _description_
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

        btnclock_xml = self._gui.create_xml("ImageButton", {"id": f"btnClock{hid}",
            "text": clock, "image": "VaadinAlarm.png",
             "options": "{'height':20, 'width':20}"}, frmitem_xml)
        _, btn_clock = self._gui.create_control(frm_item, btnclock_xml, level)
        self._gui.assemble_control(btn_clock, {"layout":"grid",
            "grid":"{'row':1,'column':1,'sticky':'w'}"}, f"{'  '*level}")

        if clock in ["", "选择定时提醒"]:
            cast(ImageBtttonCtrl, btn_clock).hide()

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

    def _selclockdlg_confirm(self, **kwargs: object) -> tuple[bool, str]:
        """_summary_
        Args:
            kwargs (type): _description_
        """
        po(f"_selclockdlg_confirm: {kwargs}")
        owner = cast(Container, self._selclock_dlg.owner)
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
        # clk_time = datetime.time.fromisoformat(f"{hour:02}:{minute:02}:00")
        clk_time = str2time(f"{hour:02}:{minute:02}")
        day = str_to_intenum(DayType, sel_day)
        _ = owner.process_message("changeClock", clk_time=clk_time,
            custom=day, **kwargs)
        return True, ""

    def show_selscheduledlg(self, owner: Container | None = None, x: int = 0, y: int = 0, **kwargs: object):
        """_summary_
        Args:
            owner (type): _description_
            x (type): _description_
            y (type): _description_
        """
        self._selschedule_dlg.do_show(owner, x, y, **kwargs)

    def _selscheduledlg_confirm(self, **kwargs: object) -> tuple[bool, str]:
        """_summary_
        Args:
            kwargs (type): _description_
        """
        po(f"_selscheduledlg_confirm: {kwargs}")
        owner = cast(Container, self._selclock_dlg.owner)
        cmb_selunit = cast(ComboboxCtrl, self._selclock_dlg.get_control("cmbSelUnit"))
        sel_unit = cmb_selunit.get_val()
        pv(sel_unit)
        cmb_selval = cast(ComboboxCtrl, self._selclock_dlg.get_control("cmbSelVal"))
        sel_val = cmb_selval.get_val()
        pv(sel_val)
        schedule = f"计划{sel_unit}{sel_val}"
        _ = owner.process_message("changeSchedule", schedule=schedule, **kwargs)
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

    def _get_hourdetail(self, iid: int):
        """_summary_

        Args:
            iid (int): _description_

        Returns:
            _type_: _description_
        """
        detail: HourDict = {"name": "", "rid": (0, 0), "clock": "", "schedule": "",
            "sums": 0, "father": -1}
        self._hoursdb.get_hourdetail(iid, detail)
        return detail

    def modify_hour(self, hid: int, attrib: str, val: str | int | tuple[int, int]):
        """_summary_
        Args:
            hid (type): _description_
            attrib (type): _description_
            val (type): _description_
        """
        match attrib:
            case "schedule":
                val = cast(str, val)
                sqlval = self._hoursdb.schedule_app2sql(val)
            case "rid":
                grp, idx = cast(tuple[int, int], val)
                sqlval = f"{grp}_{idx}"
                imagepath = self._get_imagepath(grp, idx)
                self.update_hourctrl_attrib(hid, "image", imagepath)
            case _:
                raise ValueError(f"unsupport to modify {attrib}")
        po(f"modify {hid}'s {attrib} to {sqlval}")
        self._hoursdb.modify_hourattr(hid, attrib, sqlval)

    @override
    def process_message(self, idmsg: str, **kwargs: object):
        if idmsg.startswith("btnItem"):
            hid = int(idmsg[7:])
            x, y = cast(tuple[int, int], kwargs["mousepos"])
            self.show_hourdetaildlg(self, x+20, y+20, id=hid, db=self._hoursdb)
        elif idmsg.startswith("lblSumHour"):
            hid = int(idmsg[10:])
            x, y = cast(tuple[int, int], kwargs["mousepos"])
            self.show_recordhourdlg(self, x+20, y+20, id=hid, db=self._hoursdb)
        elif idmsg.startswith("btnClock"):
            hid = int(idmsg[8:])
            x, y = cast(tuple[int, int], kwargs["mousepos"])
            # TODO: extactly eid
            plandata = self._hoursdb.get_plandata(hid)
            reminders = plandata["reminders"]
            eid = next(iter(reminders.keys()))
            self.show_selclockdlg(self, x+20, y+20, hid=hid, eid=eid)
        elif idmsg == "btnNewHour":
            x, y = cast(tuple[int, int], kwargs["mousepos"])
            self.show_edithourdlg(self, x+20, y+20, father=-1, id=0, db=self._hoursdb)
        else:
            match idmsg:
                case "showSelClockDlg": # come from `EditHourDlg` or <-`HourDetailDlg`<-`EditHourDlg`
                    owner = cast(Dialog, kwargs["owner"])
                    x, y = cast(tuple[int, int], kwargs["pos"])
                    options = cast(dict[str, object], kwargs["options"])
                    self.show_selclockdlg(owner, x, y, **options)
                case "showSelScheduleDlg": # come from `EditHourDlg` or <-`HourDetailDlg`<-`EditHourDlg`
                    owner = cast(Dialog, kwargs["owner"])
                    x, y = cast(tuple[int, int], kwargs["pos"])
                    options = cast(dict[str, object], kwargs["options"])
                    self.show_selscheduledlg(owner, x, y, **options)
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
                    self.modify_hour(hid, "rid", f"{grp}_{idx}")
                case "changeClock":
                    # come from `SelClockDlg` or <-`HourDetailDlg`<-`EditHourDlg`<-`SelClockDlg`
                    hid = cast(int, kwargs["hid"])
                    eid = cast(int, kwargs["eid"])
                    clk_time = cast(datetime.time, kwargs["clk_time"])
                    custom = cast(DayType, kwargs["custom"])
                    ## TODO: come from ?
                    # clockstr = "" if clockstr=="选择定时提醒" else clockstr
                    # TODO: add event
                    # if clock:
                        # name = self._hoursdb.get_plandata(hid)["name"]
                        # self._schedule.add_event(sqlval, name)
                        # self._schedule.event_to_schedule()
                    reminder = self._hoursdb.modify_reminder(hid, eid,
                        clk_time=clk_time,
                        every=1,
                        unit=TimeUnit.WEEK,
                        custom=custom,
                        cycbgn_dtime=datetime.datetime.now(),
                        cycend_dtime=None,
                    )
                    clockstr = reminder2clkstr(reminder)
                    pv(clockstr)
                    self.update_hourctrl_attrib(hid, "clock", clockstr)
                case "changeSchedule":
                    # come from `SelScheduleDlg` or <-`HourDetailDlg`<-`EditHourDlg`<-`SelScheduleDlg`
                    hid = cast(int, kwargs["id"])
                    schedule = cast(str, kwargs["schedule"])
                    schedule = "" if schedule=="选择时间投入计划" else schedule
                    self.modify_hour(hid, "schedule", schedule)
                case "deleteItem":  # come from <-`HourDetailDlg`<-`EditHourDlg`
                    hid = cast(int, kwargs["id"])
                    detail = self._get_hourdetail(hid)
                    id_father = detail["father"]
                    if id_father == -1:
                        self._gui.delete_control(f"frmGroup{hid}")
                    else:
                        self._gui.delete_control(f"frmItem{hid}")
                        self._gui.delete_control(f"btnItem{hid}")
                        self._gui.delete_control(f"lblItem{hid}")
                        self._gui.delete_control(f"btnClock{hid}")
                        self._gui.delete_control(f"lblSum{hid}")

                        self._hoursdb.del_hour(hid)
                case "createHourCtrl":  # come from `TimeDatabase`<-`TimeMasterApp`
                    hid = cast(int, kwargs["id"])
                    name =cast(str, kwargs["name"])
                    rid = cast(tuple[int, int], kwargs["rid"])
                    clockstr = cast(str, kwargs["clock"])
                    sums = cast(str, kwargs["sum"])
                    fid = cast(int, kwargs["fid"])
                    self.create_hourctrl(hid, name, rid, clockstr, sums, fid)
                case "updateHour":  # come from `HourDetailDlg`
                    hid = cast(int, kwargs["id"])
                    attr = cast(str, kwargs["attrib"])
                    val = cast(str | int, kwargs["val"])
                    self.update_hourctrl_attrib(hid, attr, val)
                case "newHour": # come from `EditHourDlg` or <-`EditHourDlg`<-`HourDetailDlg`
                    name =cast(str, kwargs["name"])
                    fid = cast(int, kwargs["father"])
                    rid = cast(tuple[int, int], kwargs["rid"])
                    clockstr = cast(str, kwargs["clock"])
                    schedule = cast(str, kwargs["schedule"])

                    clock_val = "" if clockstr == "选择定时提醒" else clockstr
                    schedule_val = "" if schedule == "选择时间投入计划" else schedule
                    hid = self._hoursdb.add_hour(name, rid, clock_val, schedule_val, fid)
                    self.create_hourctrl(hid, name, rid, clockstr, "0.0h", fid)
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
                    pass
            return True

    def close(self):
        """_summary_
        """
        return self._hoursdb.close()
