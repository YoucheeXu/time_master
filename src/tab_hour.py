#!/usr/bin/python3
# -*- coding: UTF-8 -*-
from __future__ import annotations
import datetime
from typing import cast, Any
import tkinter as tk

from pyutilities.logit import po, pv, pe
from pyutilities.winbasic import Dialog
from pyutilities.tkwin import tkWin
from pyutilities.tkwin import LabelCtrl, EntryCtrl, ButtonCtrl, ComboboxCtrl, ImageBtttonCtrl
from pyutilities.tkwin import PicsListviewCtrl, DialogCtrl
from pyutilities.calendarctrl import CalendarCtrl

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

        self._recordhour_dlg: DialogCtrl = cast(DialogCtrl, self._gui.get_control("dlgRecord"))
        self._recordhour_dlg.register_eventhandler("beforego", self._recorddlg_beforego)
        self._recordhour_dlg.register_eventhandler("lblDay", self._recorddlg_selday)
        self._recordhour_dlg.register_eventhandler("confirm", self._recorddlg_confirm)

        self._hourdetail_dlg: DialogCtrl = cast(DialogCtrl, self._gui.get_control("dlgItemDetail"))
        self._hourdetail_dlg.filter_message(self._hourdetaildlg_processmessage)

        self._edithour_dlg: DialogCtrl = cast(DialogCtrl, self._gui.get_control("dlgEditItem"))
        self._edithour_dlg.filter_message(self._edithourdlg_processmessage)

        msglst = ["btnNewHour", "changeClock", "changeSchedule", "changeItemImage", "deleteItem"]
        self._gui.filter_message(self._process_message, 1, msglst)

    def update_hour(self, uid: int, attrib: str, val: str):
        match attrib:
            case "name":
                ctrl_item1 = cast(LabelCtrl, self._gui.get_control(f"lblItem{uid}"))
                # ctrl_item1['text'] = val
                _ = ctrl_item1.configure(text=val, anchor='w')
            case "image":
                ctrl_item2 = cast(ImageBtttonCtrl, self._gui.get_control(f"btnItem{uid}"))
                ctrl_item2.change_image(val)
            case "clock":
                if val in ["", "选择定时提醒"]:
                    return
                ctrl_item3 = cast(ImageBtttonCtrl, self._gui.get_control(f"btnClock{uid}"))
                if not ctrl_item3.visible:
                    ctrl_item3.grid()
                # ctrl_item3['text'] = val
                _ = ctrl_item3.configure(text=val)
            case "sums":
                ctrl_item4 = cast(LabelCtrl, self._gui.get_control(f"lblSumHour{uid}"))
                _ = ctrl_item4.configure(text=f"{val}\nhours")
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

        master = self._gui.get_control("frmHourMain")
        if is_subitem:
            detail = cast(HourDict, self._gui.process_message("GetHourDetail", id=iid))
            idfather = detail["father"]
            parent = self._gui.get_control(f"frmGroup{idfather}")
            item_padx1 = 15
            item_padx2 = 5
        else:
            xml = self._gui.create_xml("Frame", {"id":f"frmGroup{iid}"})
                 # "options":"{'borderwidth':1,'relief':'ridge'}"})
            _, parent = self._gui.create_control(master, xml, 2)
            item_padx1 = 0
            item_padx2 = 5

        level = 3
        frmitem_xml = self._gui.create_xml("Frame", {"id": f"frmItem{iid}"})
        _, frm_item = self._gui.create_control(parent, frmitem_xml, level)

        level = 4

        radio = 0.8 if is_subitem else 1

        btnitem_xml = self._gui.create_xml("ImageButton", {"id": f"btnItem{iid}",
            "img": imagepath,
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
            "text": clock, "img": "VaadinAlarm.png",
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
            self._gui.assemble_control(parent, {"layout": "pack",
                "pack":f"{{'side':'top','pady':({pady1},5),'fill':'x'}}"}, f"{'  '*(2-1)}")

    def get_childattrib(self, uid: int, attrib: str) -> str:
        val: str = ""
        match attrib:
            case "name":
                ctrl_item1 = cast(LabelCtrl, self._gui.get_control(f"lblChild{uid}"))
                val = cast(str, ctrl_item1['text'])
            # case "img":
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

    def _create_child(self, parent: object, uid: int, sub_item: str,
            rid: tuple[int, int], sums: str):
        imagepath = self._get_imagepath(rid[0], rid[1])

        level = 2
        frm_child_xml = self._gui.create_xml("Frame", {"id": f"frmSub{uid}"})
        _, frm_child = self._gui.create_control(parent, frm_child_xml, level)

        level = 3

        pnlitem_xml = self._gui.create_xml("ImagePanel", {"id": f"pnlChild{uid}",
            "img": imagepath, 
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

    def show_selclockdlg(self, owner: Dialog | None = None, x: int = 0, y: int = 0, **kwargs: Any):
        self._selclock_dlg.do_show(owner, x+20, y+20, **kwargs)

    def _selclockdlg_confirm(self, **kwargs: Any) -> tuple[bool, str]:
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
        self._selclock_dlg.owner.process_message("changeClock", clock=clock, **kwargs)
        return True, ""

    def _selscheduledlg_confirm(self, **kwargs: Any) -> tuple[bool, str]:
        po(f"_selscheduledlg_confirm: {kwargs}")
        cmb_selunit = cast(ComboboxCtrl, self._selclock_dlg.get_control("cmbSelUnit"))
        sel_unit = cmb_selunit.get_val()
        pv(sel_unit)
        cmb_selval = cast(ComboboxCtrl, self._selclock_dlg.get_control("cmbSelVal"))
        sel_val = cmb_selval.get_val()
        pv(sel_val)
        schedule = f"计划{sel_unit}{sel_val}"
        self._selschedule_dlg.owner.process_message("changeSchedule", schedule=schedule, **kwargs)
        return True, ""

    def show_recordhourdlg(self, owner: Dialog | None = None, x: int = 0, y: int = 0, **kwargs: Any):
        self._recordhour_dlg.do_show(owner, x+20, y+20, **kwargs)

    def _recorddlg_beforego(self, **kwargs: Any):
        po(f"_recorddlg_beforego: {kwargs}")
        iid = cast(int, kwargs["id"])
        detail = cast(HourDict, self._gui.process_message("GetHourDetail", id=iid))
        lbl_item = cast(LabelCtrl, self._gui.get_control("lblItem"))
        lbl_item["text"] = detail["name"]
        today = datetime.date.today()
        lbl_day = cast(LabelCtrl, self._gui.get_control("lblDay"))
        lbl_day["text"] = today

    def _recorddlg_selday(self, **kwargs: Any):
        x, y = cast(tuple[int, int], kwargs["mousepos"])
        # self._selclock_dlg
        calendar = CalendarCtrl((x, y+20))
        date = calendar.get_datestr()
        pv(date)
        lbl_day = cast(LabelCtrl, self._gui.get_control("lblDay"))
        lbl_day["text"] = date

    # TODO: wait to test
    def _recorddlg_confirm(self, **kwargs: Any) -> tuple[bool, str]:
        po(f"_recorddlg_confirm: {kwargs}")
        iid = cast(int, kwargs["id"])
        cmb_selhour = cast(ComboboxCtrl, self._gui.get_control("cmbSelHour"))
        hour = int(cmb_selhour.get_val()[:-1])
        cmb_selminute = cast(ComboboxCtrl, self._gui.get_control("cmbSelMinute"))
        minute = int(cmb_selminute.get_val()[:-1])
        delta = datetime.timedelta(hours=hour, minutes=minute)
        pv(delta)
        _ = self._gui.process_message("record", id=iid, timecost=delta)
        # sums_str = self.get_item(iid, "sums")
        detail = cast(HourDict, self._gui.process_message("GetHourDetail", id=iid))
        # sums = datetime.timedelta(hours=float(sums_str[:-1]))
        sums = datetime.timedelta(minutes=detail["sums"])
        sums += delta
        pv(sums)
        sums_hours = sums.days * 24.0 + sums.seconds / 3600.0
        self.update_hour(iid, "sums", f"{sums_hours}")
        _ = self._gui.process_message("modify", id=iid, attrib="sums", val=int(sums_hours*60))
        return True, ""

    def show_hourdetaildlg(self, owner: Dialog | None = None, x: int = 0, y: int = 0, **kwargs: Any):
        self._hourdetail_dlg.do_show(owner, x+20, y+20, **kwargs)

    def _hourdetaildlg_beforego(self, **kwargs: Any):
        po(f"_hourdetaildlg_beforego: {kwargs}")
        iid = cast(int, kwargs["id"])
        # data = ItemDict()
        # data = {}
        # self._gui.process_message("GetHourDetail", id=iid, detail=data)
        detail = cast(HourDict, self._gui.process_message("GetHourDetail", id=iid))
        # po(f"{iid}: {detail}")

        lbl_father = cast(LabelCtrl, self._gui.get_control("lblFatherItemDetail"))
        id_father = detail["father"]
        if id_father != -1:
            detail_father = cast(HourDict, self._gui.process_message("GetHourDetail", id=id_father))
            name_father = detail_father["name"]
            pv(name_father)
            lbl_father['text'] = name_father
        else:
            lbl_father.hide()

        rid = detail["rid"]
        imagepath = self._get_imagepath(rid[0], rid[1])
        img_item = cast(ImageBtttonCtrl, self._gui.get_control(f"imgItemDetail"))
        img_item.change_image(imagepath)

        lbl_item = cast(LabelCtrl, self._gui.get_control("lblItemItemDetail"))
        lbl_item['text'] = detail["name"]
        lbl_sum = cast(LabelCtrl, self._gui.get_control("lblSumItemDetail"))
        lbl_sum['text'] = f"{detail['sums'] / 60}"

        lbl_selclock = cast(LabelCtrl, self._gui.get_control("lblSelClockItemDetail"))
        # clock = data["clock"]
        lbl_selclock['text'] = detail["clock"]
        lbl_selschedule = cast(LabelCtrl, self._gui.get_control("lblSelScheduleItemDetail"))
        lbl_selschedule['text'] = detail["schedule"]

        parent: tk.Frame = cast(tk.Frame, self._gui.get_control("frmSubItmes"))
        # get subitem info(rid, name, sums) of id
        children = cast(dict[int, HourDict], self._gui.process_message("getChildren", father=iid))
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
        lbl_totalsubitems = cast(LabelCtrl, self._gui.get_control("lblTotalChildren"))
        lbl_totalsubitems["text"] = f"共{idx}个子项目"
        # ...

    def _hourdetaildlg_confirm(self, **kwargs: Any) -> tuple[bool, str]:
        po(f"_hourdetaildlg_confirm: {kwargs}")
        for idx, child in self._children.items():
            if idx > self._old_subid:
                name =      child.name
                sums =      child.sums
                rid =       child.rid
                clock =     child.clock
                schedule =  child.schedule
                father = cast(int, kwargs["id"])
                iid = cast(int, self._gui.process_message("addItem", father=father, name=name,
                    rid=rid, clock=clock, schedule=schedule, sums=sums))
                self.create_hour(iid, name, rid, clock, f"{sums / 60:.1f}", True)
            self._delete_child(idx)
        self._children.clear()
        return True, ""

    def _hourdetaildlg_cancel(self, **kwargs: Any) -> tuple[bool, str]:
        po(f"_hourdetaildlg_cancel: {kwargs}")
        for idx, _ in self._children.items():
            self._delete_child(idx)
        self._children.clear()
        return True, ""

    def _hourdetaildlg_processmessage(self, idmsg: str, **kwargs: Any):
        if self._hourdetail_dlg.alive:
            iid = cast(int, kwargs["id"])
            match idmsg:
                case "beforego":
                    self._hourdetaildlg_beforego(**kwargs)
                case "changeItemImage":
                    grp = cast(int, kwargs["group"])
                    idx = cast(int, kwargs["index"])
                    imagebutton = cast(ImageBtttonCtrl, self._gui.get_control("imgItemDetail"))
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
                    self._hourdetail_dlg.owner.process_message("changeClock", id=iid, clock=clock)
                case "changeSchedule":
                    schedule = cast(str, kwargs["schedule"])
                    lbl_selschedule = cast(LabelCtrl,
                        self._gui.get_control("lblSelScheduleItemDetail"))
                    lbl_selschedule['text'] = schedule
                    self._hourdetail_dlg.owner.process_message("changeSchedule",
                        id=iid, schedule=schedule)
                case "imgItemDetail":
                    detail = cast(HourDict, self._gui.process_message("GetHourDetail", id=iid))
                    father = detail["father"]
                    x, y = cast(tuple[int, int], kwargs["mousepos"])
                    self._edithour_dlg.do_show(self._hourdetail_dlg, x+20, y+20,
                        father=father, id=iid)
                case "btnAddChild":
                    x, y = cast(tuple[int, int], kwargs["mousepos"])
                    self._edithour_dlg.do_show(self._hourdetail_dlg, x+20, y+20,
                        father=iid, id=0)
                case "btnRecordItemDetail":
                    detail = cast(HourDict, self._gui.process_message("GetHourDetail", id=iid))
                    father = detail["father"]
                    x, y = cast(tuple[int, int], kwargs["mousepos"])
                    self._recordhour_dlg.do_show(self._hourdetail_dlg, x+20, y+20,
                        father=father, id=iid)
                case "deleteItem":
                    self._hourdetail_dlg.destroy()
                    self._hourdetail_dlg.owner.process_message("deleteItem", id=iid)
                case "confirm":
                    return self._hourdetaildlg_confirm(**kwargs)
                case "cancel":
                    return self._hourdetaildlg_cancel(**kwargs)
                case _:
                    return None
            return True
        return None

    def _edithourdlg_beforego(self, **kwargs: Any):
        po(f"_edithourdlg_beforego: {kwargs}")
        father = cast(int, kwargs["father"])
        iid = cast(int, kwargs["id"])

        if father != -1:
            lbl_father = cast(LabelCtrl, self._gui.get_control("lblSelFatherEditItem"))
            detail_father = cast(HourDict, self._gui.process_message("GetHourDetail", id=father))
            name_father = detail_father["name"]
            pv(name_father)
            lbl_father['text'] = name_father

        if iid == 0:
            self._edithour_dlg.set_title("新建项目")
            btn_delitem = cast(ButtonCtrl, self._gui.get_control("btnDelItemEditItem"))
            btn_delitem.hide()
            grp, idx = 0, 0
        else:
            self._edithour_dlg.set_title("编辑项目")
            detail = cast(HourDict, self._gui.process_message("GetHourDetail", id=iid))
            pv(detail)

            ent_name = cast(EntryCtrl, self._gui.get_control("txtItemEditItem"))
            ent_name.set_val(detail["name"])
            ent_name.disable()
            lbl_selclock = cast(LabelCtrl, self._gui.get_control("lblSelClockEditItem"))
            lbl_selclock['text'] = detail["clock"] if detail["clock"] else "选择定时提醒"
            lbl_selschedule = cast(LabelCtrl, self._gui.get_control("lblSelScheduleEditItem"))
            lbl_selschedule['text'] = detail["schedule"] if detail["schedule"] else "选择时间投入计划"
            grp, idx = detail["rid"]

        list_itemimage = cast(PicsListviewCtrl, self._gui.get_control("lstItemImageEditItem"))
        # list_itemimage.display_images(list(self._images_dict.values()))
        list_itemimage.add_imagegroup("一般", list(self._images_dict[0].values()))
        list_itemimage.add_imagegroup("课程", list(self._images_dict[1].values()))
        list_itemimage.add_imagegroup("锻炼", list(self._images_dict[2].values()))
        list_itemimage.add_imagegroup("语言", list(self._images_dict[3].values()))
        list_itemimage.add_imagegroup("考试", list(self._images_dict[4].values()))

        list_itemimage.select(grp, idx)

    # TODO: only change those which are modified
    def _edithourdlg_confirm(self, **kwargs: Any):
        po(f"_edithourdlg_confirm: {kwargs}")
        father = cast(int, kwargs["father"])
        iid = cast(int, kwargs["id"])
        if iid != 0:    # edit item
            lbl_selclock = cast(LabelCtrl, self._gui.get_control("lblSelClockEditItem"))
            clock = cast(str, lbl_selclock['text'])
            pv(clock)
            _ = self._edithour_dlg.owner.process_message("changeClock", id=iid, clock=clock)

            lbl_selschedule = cast(LabelCtrl, self._gui.get_control("lblSelScheduleEditItem"))
            schedule = cast(str, lbl_selschedule['text'])
            pv(schedule)
            _ = self._edithour_dlg.owner.process_message("changeSchedule", id=iid, schedule=schedule)

            lst_itemimage = cast(PicsListviewCtrl,
                self._gui.get_control("lstItemImageEditItem"))
            grp, idx = lst_itemimage.get_selected()
            _ = self._edithour_dlg.owner.process_message("changeItemImage",
                id=iid, group=grp, index=idx)
        else:   # New item
            ent_name = cast(EntryCtrl, self._gui.get_control("txtItemEditItem"))
            name = ent_name.get_val()
            # pv(name)
            if len(name) == 0:
                return False, "Name should not be empty"
            lbl_selclock = cast(LabelCtrl, self._gui.get_control("lblSelClockEditItem"))
            clock  = cast(str, lbl_selclock['text'])
            clock_val = "" if clock == "选择定时提醒" else clock
            lbl_selschedule = cast(LabelCtrl, self._gui.get_control("lblSelScheduleEditItem"))
            schedule = cast(str, lbl_selschedule['text'])
            schedule_val = "" if schedule == "选择时间投入计划" else schedule
            lst_itemimage = cast(PicsListviewCtrl,
                self._gui.get_control("lstItemImageEditItem"))
            rid = lst_itemimage.get_selected()
            if father == -1:
                iid = cast(int, self._gui.process_message("addItem",
                    name=name, rid=rid, clock=clock_val, schedule=schedule_val, father=father))
                self.create_hour(iid, name, rid, clock, '0.0')
            else:
                idx = len(self._children)
                parent = cast(tk.Frame, self._gui.get_control("frmSubItmes"))
                self._create_child(parent, idx, name, rid, '0.0')
                self._children[idx] = HourTuple(iid=0, name=name, rid=rid,
                    clock=clock_val, schedule=schedule_val, sums=0, father=father)
                lbl_totalsubitems = cast(LabelCtrl, self._gui.get_control("lblTotalChildren"))
                lbl_totalsubitems["text"] = f"共{len(self._children)}个子项目"
                # self._old_subid += 1
        return True, ""

    def _edithourdlg_processmessage(self, idmsg: str, **kwargs: Any):
        if self._edithour_dlg.alive:
            iid = cast(int, kwargs["id"])
            match idmsg:
                case "beforego":
                    self._edithourdlg_beforego(**kwargs)
                case "changeClock":
                    clock = cast(str, kwargs["clock"])
                    lbl_selclock = cast(LabelCtrl, self._gui.get_control("lblSelClockEditItem"))
                    lbl_selclock['text'] = clock
                case "changeSchedule":
                    schedule = cast(str, kwargs["schedule"])
                    lbl_selschedule = cast(LabelCtrl, self._gui.get_control("lblSelScheduleEditItem"))
                    lbl_selschedule['text'] = schedule
                case "lblSelClockEditItem":
                    pv(kwargs)
                    x, y = cast(tuple[int, int], kwargs["mousepos"])
                    self._selclock_dlg.do_show(self._edithour_dlg, x+20, y+20, **kwargs)
                case "lblSelScheduleEditItem":
                    pv(kwargs)
                    x, y = cast(tuple[int, int], kwargs["mousepos"])
                    self._selschedule_dlg.do_show(self._edithour_dlg, x+20, y+20, **kwargs)
                case "btnDelItemEditItem":
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

    def _process_message(self, idmsg: str, **kwargs: Any):
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
                _ = self._gui.process_message("ModifyHourAttr", id=iid, attrib="clock", val=clock)
                self.update_hour(iid, "clock", clock)
            case "changeSchedule":
                iid = cast(int, kwargs["id"])
                schedule = cast(str, kwargs["schedule"])
                schedule = "" if schedule=="选择时间投入计划" else schedule
                _ = self._gui.process_message("ModifyHourAttr", id=iid, attrib="schedule", val=schedule)
            case "deleteItem":
                iid = cast(int, kwargs["id"])
                detail = cast(HourDict, self._gui.process_message("GetHourDetail", id=iid))
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
