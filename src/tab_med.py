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

from item_type import MedDict


class MedTab:
    def __init__(self, gui: tkWin):
        self._gui: tkWin = gui

        self._images_dict: dict[int, dict[int, str]] = {
            0: {0: "Items\\CircleFlagsUsBetsyRoss.png", 1: "Items\\FlatUiNews.png", 
                2: "Items\\gift.png", 3: "Items\\VaadinAlarm.png"},
            1: {0: "Items\\Course\\cpp.png", 1: "Items\\Course\\MPC.png",
                2: "Items\\Course\\Vehicle Engineering.png", 3: "Items\\Course\\PMSM.png",
                4: "Items\\Course\\Handwrite.png", 5: "Items\\Course\\股票.png",
                6: "Items\\Course\\管理.png", 7: "Items\\Course\\绘画.png",
                8: "Items\\Course\\机器视觉.png", 9: "Items\\Course\\Calligraphy.png",
                10: "Items\\Course\\语文.png", 11: "Items\\Course\\自动化.png"},
            2: {0: "Items\\Exercise\\锻炼.png", 1: "Items\\Exercise\\俯卧撑.png",
                2: "Items\\Exercise\\跑步.png", 3: "Items\\Exercise\\平板支撑.png",
                4: "Items\\Exercise\\足球.png"},
            3: {0: "Items\\Language\\German.png", 1: "Items\\Language\\Korean.png",
                2: "Items\\Language\\Japanese.png", 3: "Items\\Language\\English.png",
                4: "Items\\Language\\Oral.png", 5: "Items\\Language\\Listen.png",
                6: "Items\\Language\\Read.png", 7: "Items\\Language\\Write.png"},
            4: {0: "Items\\Test\\CET-4.png", 1: "Items\\Test\\CET-6.png",
                2: "Items\\Test\\CFA.png", 3: "Items\\Test\\CPA.png",
                4: "Items\\Test\\GRE.png", 5: "Items\\Test\\IELTS.png",
                6: "Items\\Test\\TOEFL.png"}
        }

        self._seldue_dlg: DialogCtrl = cast(DialogCtrl, self._gui.get_control("dlgSelMedDue"))
        self._seldue_dlg.filter_message(self._selduedlg_processmessage)

        self._recordmed_dlg: DialogCtrl = cast(DialogCtrl, self._gui.get_control("dlgRecordMed"))
        self._recordmed_dlg.filter_message(self._recordmeddlg_processmessage)

        self._meddetail_dlg: DialogCtrl = cast(DialogCtrl, self._gui.get_control("dlgMedDetail"))
        self._meddetail_dlg.filter_message(self._meddetaildlg_processmessage)

        self._editmed_dlg: DialogCtrl = cast(DialogCtrl, self._gui.get_control("dlgEditMed"))
        self._editmed_dlg.filter_message(self._editmeddlg_processmessage)

        msglst = ["btnAddMed", "ChangeMedImage", "ChangeMedDue",
            "DeleteMed"]
        self._gui.filter_message(self._process_message, 1, msglst)

    # TODO:
    def update_medstor(self, uid: int, attrib: str, val: str):
        match attrib:
            # case "name":
                # ctrl_Med1 = cast(LabelCtrl, self._gui.get_control(f"lblNameMedStor{uid}"))
                # # ctrl_Med1['text'] = val
                # _ = ctrl_Med1.configure(text=val, anchor='w')
            case "image":
                ctrl_Med2 = cast(ImageBtttonCtrl, self._gui.get_control(f"btnImageMedStor{uid}"))
                ctrl_Med2.change_image(val)
            case "due":
                if val in ["", "选择定时提醒"]:
                    return
                ctrl_Med3 = cast(ImageBtttonCtrl, self._gui.get_control(f"btnDueMedStor{uid}"))
                if not ctrl_Med3.visible:
                    ctrl_Med3.grid()
                # ctrl_Med3['text'] = val
                _ = ctrl_Med3.configure(text=val)
            case "sums":
                ctrl_Med4 = cast(LabelCtrl, self._gui.get_control(f"lblSumMedStor{uid}"))
                _ = ctrl_Med4.configure(text=val)
            case _:
                raise KeyError(f"Unkonw arrtrib: {attrib}")

    def get_medstorattr(self, iid: int, attrib: str) -> str:
        val: str = ""
        match attrib:
            case "name":
                ctrl_Med1 = cast(LabelCtrl, self._gui.get_control(f"lblNameMedStor{iid}"))
                # val = cast(str, ctrl_Med1['text'])
                val = ctrl_Med1.get_text()
            # case "image":
                # ctrl_Med2 = cast(ImageBtttonCtrl, self._gui.get_control(f"btnImageMedStor{id_}")
                # raise NotImplementedError("")
            case "due":
                ctrl_Med3 = cast(ImageBtttonCtrl, self._gui.get_control(f"btnDueMedStor{iid}"))
                val = cast(str, ctrl_Med3['text'])
            case "sums":
                ctrl_Med4 = cast(LabelCtrl, self._gui.get_control(f"lblSumMedStor{iid}"))
                val = cast(str, ctrl_Med4['text'])
            case _:
                val = ""
        return val

    def delete_medstor(self, iid: int):
        self._gui.delete_control(f"btnImageMedStor{iid}")
        self._gui.delete_control(f"lblNameMedStor{iid}")
        self._gui.delete_control(f"btnDueMedStor{iid}")
        self._gui.delete_control(f"lblSumMedStor{iid}")

    def create_medstor(self, iid: int, Med: str, rid: tuple[int, int],
            due: str, sums: str, unit: str):
        imagepath = self._get_imagepath(rid[0], rid[1])

        master = self._gui.get_control("frmMedStorMain")

        level = 3
        frmed_xml = self._gui.create_xml("Frame", {"id": f"frmMedStor{iid}"})
        _, frm_med = self._gui.create_control(master, frmed_xml, 2)

        level = 3

        btnimg_xml = self._gui.create_xml("ImageButton", {"id":f"btnImageMedStor{iid}",
            "image": imagepath,
           "options": "{'width':60, 'height':60}"}, frmed_xml)
        _, btn_img = self._gui.create_control(frm_med, btnimg_xml, level)
        self._gui.assemble_control(btn_img, {"layout":"grid",
            "grid":"{'row':0,'column':0,'rowspan':2}"}, '  '*level)

        lblname_xml = self._gui.create_xml("Label", {"text":Med, "id":f"lblNameMedStor{iid}",
            "options": "{'width':48}"}, frmed_xml)
        # pv(lbl_Med_xml)
        _, lbl_name = self._gui.create_control(frm_med, lblname_xml, level)
        self._gui.assemble_control(lbl_name, {"layout":"grid",
            "grid":"{'row':0,'column':1,'sticky':'w'}"},
            f"{'  '*level}")

        btndue_xml = self._gui.create_xml("ImageButton", {"id": f"btnDueMedStor{iid}",
            "text": due, "image": "VaadinAlarm.png",
             "options": "{'width':20, 'height':20}"}, frmed_xml)
        _, btn_due = self._gui.create_control(frm_med, btndue_xml, level)
        self._gui.assemble_control(btn_due, {"layout":"grid",
            "grid":"{'row':1,'column':1,'sticky':'w'}"}, f"{'  '*level}")

        lblsum_xml = self._gui.create_xml("Label", {"id": f"lblSumMedStor{iid}",
            "text":f"{sums}\n{unit}", "clickable":"true",
            "options":"{'width':100,'justify':'center'}"}, frmed_xml)
        _, lbl_sum = self._gui.create_control(frm_med, lblsum_xml, level)
        self._gui.assemble_control(lbl_sum, {"layout":"grid",
            "grid":"{'row':0,'column':2,'rowspan':2,'sticky':'w'}"}, f"{'  '*level}")

        self._gui.assemble_control(frm_med, {"layout": "pack",
            # "pack": "{'side':'top','anchor':'e','pady':1,'padx':7}"}, f"{'  '*(level-1)}")
            "pack": "{'side':'top', 'expand':'yes', 'fill':'x'}"}, f"{'  '*(level-1)}")

    def _get_imagepath(self, group: int, index: int):
        return self._images_dict[group].get(index, "CircleFlagsUsBetsyRoss.png")

    def show_selduedlg(self, owner: Dialog | None = None, x: int = 0, y: int = 0, **kwargs: Any):
        self._seldue_dlg.do_show(owner, x+20, y+20, **kwargs)

    def _selduedlg_beforego(self, **kwargs: Any):
        po(f"_selduedlg_beforego: {kwargs}")
        name = cast(str, kwargs["name"])
        lbl_name = cast(LabelCtrl, self._seldue_dlg.get_control("lblNameSelMedDue"))
        # lbl_name["text"] = name
        lbl_name.set_text(name)
        lbl_seldue = cast(LabelCtrl, self._seldue_dlg.get_control("lblSelDaySelMedDue"))
        lbl_seldue = cast(LabelCtrl, self._seldue_dlg.get_control("lblSelDaySelMedDue"))
        today = datetime.date.today()
        lbl_seldue["text"] = today

    def _selduedlg_selday(self, **kwargs: Any):
        x, y = cast(tuple[int, int], kwargs["mousepos"])
        # self._selclock_dlg
        calendar = CalendarCtrl((x, y+20))
        date = calendar.get_datestr()
        pv(date)
        lbl_seldue = cast(LabelCtrl, self._gui.get_control("lblSelDaySelMedDue"))
        lbl_seldue["text"] = date

    def _selduedlg_confirm(self, **kwargs: Any) -> tuple[bool, str]:
        po(f"_selduedlg_confirm: {kwargs}")
        lbl_seldue = cast(LabelCtrl, self._seldue_dlg.get_control("lblSelDaySelMedDue"))
        due = cast(str, lbl_seldue["text"])
        self._seldue_dlg.owner.process_message("changeDue", due=due, **kwargs)
        return True, ""

    def _selduedlg_processmessage(self, idmsg: str, **kwargs: Any):
        if self._seldue_dlg.alive:
            match idmsg:
                case "beforego":
                    self._selduedlg_beforego(**kwargs)
                case "lblSelDaySelMedDue":
                    self._selduedlg_selday(**kwargs)
                case "confirm":
                    return self._selduedlg_confirm(**kwargs)
                case _:
                    return None
            return True
        return None 

    def show_recordmeddlg(self, owner: Dialog | None = None, x: int = 0, y: int = 0,
            **kwargs: Any):
        self._recordmed_dlg.do_show(owner, x+20, y+20, **kwargs)

    def _recordmeddlg_beforego(self, **kwargs: Any):
        po(f"_recordmeddlg_beforego: {kwargs}")
        iid = cast(int, kwargs["id"])
        detail = cast(MedDict, self._gui.process_message("GetMedDetail", id=iid))

        lbl_name = cast(LabelCtrl, self._gui.get_control("lblNameRecordMed"))
        lbl_name["text"] = detail["name"]
        today = datetime.date.today()
        lbl_day = cast(LabelCtrl, self._gui.get_control("lblSelDayRecordMed"))
        lbl_day["text"] = today

        # ent_dose = cast(EntryCtrl, self._gui.get_control("txtDoseRecordMed"))
        # ent_dose.set_val(detail["name"])

        lbl_unit = cast(LabelCtrl, self._gui.get_control("lblUnitRecordMed"))
        lbl_unit["text"] = detail["unit"]

        now = datetime.datetime.now()
        hour = now.hour
        cmb_hour = cast(ComboboxCtrl, self._gui.get_control("cmbSelHourRecordMed"))
        pv(hour)
        _ = cmb_hour.select(hour)
        minute = now.minute
        cmb_minute = cast(ComboboxCtrl, self._gui.get_control("cmbSelMinuteRecordMed"))
        _ = cmb_minute.select(minute // 5)
        pv(minute)

    def _recordmeddlg_selday(self, **kwargs: Any):
        x, y = cast(tuple[int, int], kwargs["mousepos"])
        # self._selclock_dlg
        calendar = CalendarCtrl((x, y+20))
        date = calendar.get_datestr()
        pv(date)
        lbl_day = cast(LabelCtrl, self._gui.get_control("lblSelDayRecordMed"))
        lbl_day["text"] = date

    # TODO: wait to test
    def _recordmeddlg_confirm(self, **kwargs: Any) -> tuple[bool, str]:
        po(f"_recordmeddlg_confirm: {kwargs}")
        iid = cast(int, kwargs["id"])

        lbl_day = cast(LabelCtrl, self._gui.get_control("lblSelDayRecordMed"))
        day = cast(str, lbl_day["text"])

        ent_dose = cast(EntryCtrl, self._gui.get_control("txtDoseRecordMed"))
        dose = float(ent_dose.get_val())

        # lbl_unit = cast(LabelCtrl, self._gui.get_control("lblUnitRecordMed"))
        # unit = lbl_unit["text"]

        detail = cast(MedDict, self._gui.process_message("GetMedDetail", id=iid))
        sums = detail["sums"] - dose

        cmb_hour = cast(ComboboxCtrl, self._gui.get_control("cmbSelHourRecordMed"))
        hour = int(cmb_hour.get_val()[:-1])

        cmb_minute = cast(ComboboxCtrl, self._gui.get_control("cmbSelMinuteRecordMed"))
        minute = int(cmb_minute.get_val()[:-1])

        time = datetime.datetime.strptime(f"{day} {hour:02d}:{minute:02d}", "%Y-%m-%d %H:%M")

        self.update_medstor(iid, "sums", str(sums))
        _ = self._gui.process_message("RecordMedUse", id=iid, time=time, dose=dose)
        return True, ""

    def _recordmeddlg_processmessage(self, idmsg: str, **kwargs: Any):
        if self._recordmed_dlg.alive:
            match idmsg:
                case "beforego":
                    self._recordmeddlg_beforego(**kwargs)
                case "lblSelDayRecordMed":
                    self._recordmeddlg_selday(**kwargs)
                case "confirm":
                    return self._recordmeddlg_confirm(**kwargs)
                case _:
                    return None
            return True
        return None 

    def show_meddetaildlg(self, owner: Dialog | None = None, x: int = 0, y: int = 0,
            **kwargs: Any):
        self._meddetail_dlg.do_show(owner, x+20, y+20, **kwargs)

    def _meddetaildlg_beforego(self, **kwargs: Any):
        po(f"_meddetaildlg_beforego: {kwargs}")
        iid = cast(int, kwargs["id"])
        # data = MedDict()
        # data = {}
        # self._gui.process_message("GetMedDetail", id=iid, detail=data)
        detail = cast(MedDict, self._gui.process_message("GetMedDetail", id=iid))
        # po(f"{iid}: {detail}")

        rid = detail["rid"]
        imagepath = self._get_imagepath(rid[0], rid[1])
        btn_Med = cast(ImageBtttonCtrl, self._gui.get_control("btnImageMedDetail"))
        btn_Med.change_image(imagepath)

        lbl_Med = cast(LabelCtrl, self._gui.get_control("lblNameMedDetail"))
        lbl_Med['text'] = detail["name"]
        lbl_sum = cast(LabelCtrl, self._gui.get_control("lblSumMedDetail"))
        lbl_sum['text'] = f"{detail['sums']}\n{detail['unit']}"

        lbl_seldue = cast(LabelCtrl, self._gui.get_control("lblSelDueMedDetail"))
        lbl_seldue['text'] = detail["due"]

    def _meddetaildlg_confirm(self, **kwargs: Any) -> tuple[bool, str]:
        po(f"_meddetaildlg_confirm: {kwargs}")
        return True, ""

    def _meddetaildlg_cancel(self, **kwargs: Any) -> tuple[bool, str]:
        po(f"_meddetaildlg_cancel: {kwargs}")
        return True, ""

    def _meddetaildlg_processmessage(self, idmsg: str, **kwargs: Any):
        if self._meddetail_dlg.alive:
            iid = cast(int, kwargs["id"])
            match idmsg:
                case "beforego":
                    self._meddetaildlg_beforego(**kwargs)
                case "changeMedImage":
                    grp = cast(int, kwargs["group"])
                    idx = cast(int, kwargs["index"])
                    imagebutton = cast(ImageBtttonCtrl, self._gui.get_control("imgMedDetail"))
                    imagepath = self._get_imagepath(grp, idx)
                    # pv(imagepath)
                    imagebutton.change_image(imagepath)
                    _ = self._meddetail_dlg.owner.process_message("changeMedImage",
                        id=iid, group=grp, index=idx)
                case "ChangeMedDue":
                    due = cast(str, kwargs["due"])
                    self.update_medstor(iid, "due", due)
                    self._meddetail_dlg.owner.process_message("ChangeMedDue", id=iid, due=due)
                case "btnImageMedDetail":
                    x, y = cast(tuple[int, int], kwargs["mousepos"])
                    self._editmed_dlg.do_show(self._meddetail_dlg, x+20, y+20,
                        id=iid)
                case "btnRecordMedDetail":
                    x, y = cast(tuple[int, int], kwargs["mousepos"])
                    self._recordmed_dlg.do_show(self._meddetail_dlg, x+20, y+20,
                        id=iid)
                case "DeleteMed":
                    self._meddetail_dlg.destroy()
                    self._meddetail_dlg.owner.process_message("DeleteMed", id=iid)
                case "confirm":
                    return self._meddetaildlg_confirm(**kwargs)
                case "cancel":
                    return self._meddetaildlg_cancel(**kwargs)
                case _:
                    return None
            return True
        return None

    def _edithourdlg_beforego(self, **kwargs: Any):
        po(f"_edithourdlg_beforego: {kwargs}")
        iid = cast(int, kwargs["id"])

        if iid == 0:
            self._editmed_dlg.set_title("新建药物")
            btn_delMed = cast(ButtonCtrl, self._gui.get_control("btnDelMedEditMed"))
            btn_delMed.hide()
            grp, idx = 0, 0
        else:
            self._editmed_dlg.set_title("编辑药物")
            detail = cast(MedDict, self._gui.process_message("GetMedDetail", id=iid))
            pv(detail)

            ent_name = cast(EntryCtrl, self._gui.get_control("txtMedEditMed"))
            ent_name.set_val(detail["name"])
            ent_name.disable()
            lbl_seldue = cast(LabelCtrl, self._gui.get_control("lblSelDueEditMed"))
            lbl_seldue['text'] = detail["due"] if detail["due"] else "选择到期时间"
            grp, idx = detail["rid"]

        list_Medimage = cast(PicsListviewCtrl, self._gui.get_control("lstMedImageEditMed"))
        list_Medimage.add_imagegroup("一般", list(self._images_dict[0].values()))
        list_Medimage.add_imagegroup("课程", list(self._images_dict[1].values()))
        list_Medimage.add_imagegroup("锻炼", list(self._images_dict[2].values()))
        list_Medimage.add_imagegroup("语言", list(self._images_dict[3].values()))
        list_Medimage.add_imagegroup("考试", list(self._images_dict[4].values()))

        list_Medimage.select(grp, idx)

    # TODO: only change those which are modified
    def _editmeddlg_confirm(self, **kwargs: Any):
        po(f"_editmeddlg_confirm: {kwargs}")
        iid = cast(int, kwargs["id"])
        if iid != 0:    # edit Med
            lbl_seldue = cast(LabelCtrl, self._gui.get_control("lblSelDueEditMed"))
            due = cast(str, lbl_seldue['text'])
            pv(due)
            _ = self._editmed_dlg.owner.process_message("ChangeMedDue", id=iid, due=due)

            lst_medimage = cast(PicsListviewCtrl,
                self._gui.get_control("lstMedImageEditMed"))
            grp, idx = lst_medimage.get_selected()
            _ = self._editmed_dlg.owner.process_message("ChangeMedImage",
                id=iid, group=grp, index=idx)
        else:   # New Med
            ent_name = cast(EntryCtrl, self._gui.get_control("txtMedEditMed"))
            name = ent_name.get_val()
            # pv(name)
            if len(name) == 0:
                return False, "Name should not be empty"
            lbl_seldue = cast(LabelCtrl, self._gui.get_control("lblSelDueEditMed"))
            due  = cast(str, lbl_seldue['text'])
            due_val = "" if due == "选择过期时间" else due
            lst_medimage = cast(PicsListviewCtrl,
                self._gui.get_control("lstMedImageEditMed"))
            rid = lst_medimage.get_selected()
            sums = ""
            unit = "ml"
            iid = cast(int, self._gui.process_message("AddMed",
                name=name, rid=rid, due=due_val, sums=sums, unit=unit))
            self.create_medstor(iid, name, rid, due, sums, unit)
        return True, ""

    def _editmeddlg_processmessage(self, idmsg: str, **kwargs: Any):
        if self._editmed_dlg.alive:
            iid = cast(int, kwargs["id"])
            match idmsg:
                case "beforego":
                    self._edithourdlg_beforego(**kwargs)
                case "btnDelMedEditMed":
                    pv(kwargs)
                    self._editmed_dlg.destroy()
                    _ = self._editmed_dlg.owner.process_message("DeleteMed", id=iid)
                case "lblSelDueEditMed":
                    pv(kwargs)
                    x, y = cast(tuple[int, int], kwargs["mousepos"])
                    ent_name = cast(EntryCtrl, self._gui.get_control("txtMedEditMed"))
                    name = ent_name.get_val()
                    self._seldue_dlg.do_show(self._editmed_dlg, x+20, y+20, name=name)
                case "changeDue":
                    due = cast(str, kwargs["due"])
                    lbl_selDue = cast(LabelCtrl, self._gui.get_control("lblSelDueEditMed"))
                    lbl_selDue['text'] = due
                case "confirm":
                    return self._editmeddlg_confirm(**kwargs)
                case _:
                    return None
            return True
        return None

    def _process_message(self, idmsg: str, **kwargs: Any):
        match idmsg:
            case "btnAddMed":
                x, y = cast(tuple[int, int], kwargs["mousepos"])
                self._editmed_dlg.do_show(self._gui, x+20, y+20, id=0)
            case "ChangeMedImage":
                iid = cast(int, kwargs["id"])
                grp = cast(int, kwargs["group"])
                idx = cast(int, kwargs["index"])
                imagepath = self._get_imagepath(grp, idx)
                _ = self._gui.process_message("ModifyMedAttr", id=iid, attrib="rid",
                    val=(grp, idx))
                self.update_medstor(iid, "image", imagepath)
            case "ChangeMedDue":
                iid = cast(int, kwargs["id"])
                due = cast(str, kwargs["due"])
                due = "" if due=="选择到期时间" else due
                _ = self._gui.process_message("ModifyMedAttr", id=iid, attrib="due",
                    val=due)
                self.update_medstor(iid, "due", due)
            case "DeleteMed":
                iid = cast(int, kwargs["id"])
                self.delete_medstor(iid)
                _ = self._gui.process_message("DelMed", id=iid)
            case _:
                return self._gui.process_message(idmsg, **kwargs)
        return True
