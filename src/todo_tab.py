#!/usr/bin/python3
# -*- coding: UTF-8 -*-
from __future__ import annotations
from copy import deepcopy
import datetime
import uuid
import abc
from functools import partial
import xml.etree.ElementTree as et
# from functools import partial
from typing import Literal
from typing import TypeAlias, TypedDict, Callable, cast, override
import tkinter as tk
from tkinter import ttk, messagebox

from pyutilities.logit import po, pv, pe
from pygui_simple.winbasic import Widget, Container, Dialog, WinBasic
from pygui_simple.tkcontrol import tkControl
from pygui_simple.tkwin import T, LabelCtrl, EntryCtrl, ButtonCtrl, ComboboxCtrl, ImageBtttonCtrl
from pygui_simple.tkwin import FrameCtrl
from pygui_simple.tkwin import DialogCtrl, tkWin
from pygui_simple.tkcalendar import CalendarCtrl
from pygui_simple.tkscrollpicker import ScrollPickerCtrl, TimeScrollPickerCtrl

from src.action_sys import ActTyp
from src.schedule import Schedule
from src.time_database_type import StatusEnum, str2reminder
from src.time_database_type import TimeUnit, DayType, str_to_intenum
from src.time_database_type import reminder2str, time2str, str2time
from src.time_database_type import PlanDataDict, default_plan_data
from src.time_database_type import ReminderDataDict, default_reminder_data
from src.time_database import TimeDatabase

# --------------------------
# Type Definitions & Config
# --------------------------
COLORS: dict[str, str] = {
    "background": "#F5F5F7",      # iOS light mode background
    "card": "#F5F5F7",            # Same as overall background
    "primary_text": "#1D1D1F",    # Primary text color
    "secondary_text": "#86868B",  # Secondary text color
    "accent": "#007AFF",          # iOS theme blue
    "success": "#34C759",         # Completed state green
    "border": "#E6E6E8",          # Divider color (light gray)
    "danger": "#FF3B30",          # Delete red
    "danger_bg": "#FFEEEE",       # Swipe-to-delete background color
    "placeholder": "#C7C7CC",     # Placeholder text color
    "drag_placeholder": "#EFEFF4",# Drag placeholder background color
    "drag_active": "#E8F4FF",     # Dragging item background color
    "drag_border": "#007AFF",     # Dragging border color
    "group_title": "#636366"      # Group title text color
}

FONT_CONFIG: dict[str, tuple[str, int, str]] = {
    "title": ("Microsoft YaHei", 20, "bold"),
    "subtitle": ("Microsoft YaHei", 16, "normal"),
    "body": ("Microsoft YaHei", 14, "normal"),
    "small": ("Microsoft YaHei", 12, "normal"),
    "group_title": ("Microsoft YaHei", 14, "bold")
}

SWIPE_CONFIG: dict[str, int] = {
    "delete_threshold": -80,      # Left swipe delete threshold (pixels)
    "max_swipe_distance": -80,    # Maximum left swipe distance (pixels)
    "delete_btn_width": 80,       # Delete button width (pixels)
    "animation_duration": 100,    # Rebound animation duration (milliseconds)
    "show_btn_threshold": -20,    # Threshold to show delete button (pixels)
    "drag_threshold": 10,         # Minimum distance to trigger drag sorting (pixels)
    "placeholder_height": 80      # Todo item height (pixels)
}

REPEAT_OPTIONS: list[str] = [
    "No repeat", "Every day", "Every week", "Every month", "Every year"
]

class TimeGroup(TypedDict):
    name: str
    start: datetime.time
    end: datetime.time

TIME_GROUPS: dict[str, TimeGroup] = {
    "morning": {"name": "Morning", "start": datetime.time(6, 0), "end": datetime.time(12, 0)},
    "afternoon": {"name": "Afternoon", "start": datetime.time(12, 0), "end": datetime.time(18, 0)},
    "evening": {"name": "Evening", "start": datetime.time(18, 0), "end": datetime.time(6, 0)},
    # "no_reminder": {"name": "No reminder", "start": None, "end": None}
}

class ReminderGroups(TypedDict):
    morning: ReminderDataDict
    afternoon: ReminderDataDict
    evening: ReminderDataDict

class ReminderInfo(TypedDict):
    clock_time: datetime.time
    completed: bool

class TodoData(TypedDict):
    name: str
    note: str
    tags: list[str]
    fid: int
    status: StatusEnum
    reminder_id: int
    reminder: ReminderDataDict
    reminder_infos: list[ReminderInfo]

type TodosDict = dict[int, TodoData]

class Todo(TypedDict):
    tid: int
    data: TodoData
    day: datetime.date
    reminder_idx: int


class RepeatCycleDlg(DialogCtrl):
    def __init__(self, app: tkWin, dlg_cfg: et.Element):
        super().__init__(app, dlg_cfg)

        # Weekday list
        self.weekdays: list[str] = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        self.selected_weekdays: set[int] = {0}  # Default: select Monday
        self.checkmark_labels: list[ttk.Label] = []  # Store references for dynamic updates

        # Date grid (1-31)
        self.date_labels: dict [int, ttk.Label] = {}  # Store references to date labels for updates
        self.selected_dates: set[int] = set()  # 存储所有选中的日期，支持多选
        self.selected_dates.add(19)  # 默认选中19号（与截图一致）

    def _configure_styles(self):
        """ Configure iOS-inspired ttk styles for the interface"""
        style = ttk.Style()
        # style.theme_use("default")

        # Card container style (white background, no border)
        # style.configure(
        #     "Card.TFrame",
        #     background="white",
        #     relief=tk.FLAT,
        #     borderwidth=0
        # )

        style.configure(
            "CardLabel.TLabel",
            background="white",
            font=("Helvetica", 16)  # Fallback cross-platform font
        )

        style.configure(
            "WeekdayLabel.TLabel",
            background="white",
            font=("Helvetica", 16)
        )
        style.configure(
            "CheckmarkLabel.TLabel",
            background="white",
            font=("Helvetica", 16),
            foreground="#007aff"
        )

        # Date number styles
        style.configure(
            "DateNormal.TLabel",
            background="white",
            foreground="black",
            font=("Helvetica", 18),
            anchor=tk.CENTER
        )
        style.configure(
            "DateSelected.TLabel",
            background="#007aff",
            foreground="white",
            font=("Helvetica", 18),
            anchor=tk.CENTER
        )

    def _create_weekday_selection_card(self, parent: FrameCtrl):
        """ Create multi-select weekday toggle card"""
        # weekday_card = ttk.Frame(parent.control, style="Card.TFrame", padding=(16, 12, 16, 12))
        # weekday_card.pack(fill=tk.X, padx=16, pady=8)
        weekday_card = parent.control
        # _ = weekday_card.grid_columnconfigure(0, weight=1)

        for i, day in enumerate(self.weekdays):
            # Clickable row frame
            row = ttk.Frame(weekday_card, style="Card.TFrame", cursor="hand2")
            row.pack(fill=tk.X, pady=4)

            # Weekday label (left-aligned)
            day_label = ttk.Label(row, text=day, style="WeekdayLabel.TLabel")
            day_label.pack(side=tk.LEFT)

            # Checkmark (right-aligned, only visible when selected)
            checkmark_text = "✓" if i in self.selected_weekdays else ""
            checkmark_label = ttk.Label(row, text=checkmark_text, style="CheckmarkLabel.TLabel")
            checkmark_label.pack(side=tk.RIGHT)
            self.checkmark_labels.append(checkmark_label)

            # Bind click events to all elements in the row
            toggle_callback = partial(self._toggle_weekday, i)
            _ = row.bind("<Button-1>", toggle_callback)
            _ = day_label.bind("<Button-1>", toggle_callback)
            _ = checkmark_label.bind("<Button-1>", toggle_callback)

            # Add divider line (except after last row)
            if i < len(self.weekdays) - 1:
                ttk.Separator(weekday_card, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=8)

    def _toggle_weekday(self, idx: int, _: tk.Event[tk.Widget] | None = None):
        """ Toggle selected state of a weekday when clicked"""
        if idx in self.selected_weekdays:
            # Deselect the weekday
            self.selected_weekdays.remove(idx)
            __ = self.checkmark_labels[idx].config(text="")
        else:
            # Select the weekday
            self.selected_weekdays.add(idx)
            __ = self.checkmark_labels[idx].config(text="✓")

    def _create_date_selection_card(self, parent: FrameCtrl):
        """ Create multi-select date selection card with grid view"""
        date_card = ttk.Frame(parent.control, style="Card.TFrame", padding=(16, 12, 16, 12))
        date_card.pack(fill=tk.X, padx=16, pady=8)
        # date_card = parent.control

        # "日期" option with checkmark (selected)
        date_option_frame = ttk.Frame(date_card, style="Card.TFrame")
        date_option_frame.pack(fill=tk.X, pady=4)
        ttk.Label(date_option_frame, text="日期", style="CardLabel.TLabel").pack(side=tk.LEFT)
        ttk.Label(date_option_frame, text="✓", style="CheckmarkLabel.TLabel").pack(side=tk.RIGHT)

        # Divider line
        ttk.Separator(date_card, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=8)

        # "在..." option (placeholder for future use)
        ttk.Label(date_card, text="在...", style="CardLabel.TLabel").pack(anchor=tk.W, pady=4)

        # Divider line before date grid
        ttk.Separator(date_card, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=8)

        # Create grid frame for dates
        date_grid_frame = ttk.Frame(date_card, style="Card.TFrame")
        date_grid_frame.pack(fill=tk.X, pady=4)

        # Populate dates 1-31 in a 7-column grid
        for day in range(1, 32):
            row = (day - 1) // 7
            col = (day - 1) % 7

            # 根据初始选中状态设置样式
            if day in self.selected_dates:
                label = ttk.Label(
                    date_grid_frame,
                    text=str(day),
                    style="DateSelected.TLabel",
                    width=4,
                    padding=(0, 12),
                    cursor="hand2"  # 保持可点击状态，支持取消选择
                )
            else:
                label = ttk.Label(
                    date_grid_frame,
                    text=str(day),
                    style="DateNormal.TLabel",
                    width=4,
                    padding=(0, 12),
                    cursor="hand2"
                )

            label.grid(row=row, column=col, sticky="nsew")
            self.date_labels[day] = label

            # 绑定点击事件，支持切换选中状态
            _ = label.bind("<Button-1>", lambda e, d=day: self._toggle_date_selection(d))

        # Configure grid weights to make cells equal width
        for col in range(7):
            _ = date_grid_frame.grid_columnconfigure(col, weight=1)

    def _toggle_date_selection(self, day: int):
        """ Toggle selected state of a date (supports multi-select)"""
        label = self.date_labels[day]

        if day in self.selected_dates:
            # 取消选中：从集合中移除，切换为普通样式
            self.selected_dates.remove(day)
            _ = label.config(style="DateNormal.TLabel")
        else:
            # 选中日期：添加到集合中，切换为高亮样式
            self.selected_dates.add(day)
            _ = label.config(style="DateSelected.TLabel")

    @override
    def _beforego(self, **kwargs: object):
        spr_ctrl = cast(ScrollPickerCtrl[int], self.get_control("sprEveryRepeatCycle"))
        spr_ctrl.hide()
        spr_ctrl = cast(ScrollPickerCtrl[str], self.get_control("sprFrqRepeatCycle"))
        spr_ctrl.hide()

        # Configure custom styles
        self._configure_styles()

        cycle_info = cast(str, kwargs["cycle_info"])
        lbl = cast(LabelCtrl, self.get_control(idctrl="lblInfoRepeatCycle"))
        lbl.set_text(cycle_info)

        frm_week = cast(FrameCtrl, self.get_control("frmWeekCustomRepeatCycle"))
        self._create_weekday_selection_card(frm_week)
        frm_week.hide()

        frm_month = cast(FrameCtrl, self.get_control("frmMonthCustomRepeatCycle"))
        self._create_date_selection_card(frm_month)
        frm_month.hide()

    @override
    def process_message(self, idmsg: str, **kwargs: object):
        # kwargs.update(self._extral_msg)
        if self.alive:
            match idmsg:
                case "lblSelEveryRepeatCycle":
                    spr_ctrl = cast(ScrollPickerCtrl[int], self.get_control("sprEveryRepeatCycle"))
                    spr_ctrl.hide(spr_ctrl.visible)
                case "sprEveryRepeatCycle":
                    val = cast(int, kwargs["val"])
                    lbl_every = cast(LabelCtrl, self.get_control("lblSelEveryRepeatCycle"))
                    lbl_every.set_text(str(val))
                    lbl_info = cast(LabelCtrl, self.get_control(idctrl="lblInfoRepeatCycle"))
                    if val == 0:
                        lbl_info.set_text("Never")
                    else:
                        lbl_frq = cast(LabelCtrl, self.get_control("lblSelFrqRepeatCycle"))
                        frq = lbl_frq.get_text()

                        lbl_info.set_text(f"Every {val} {frq}")
                case "lblSelFrqRepeatCycle":
                    spr_ctrl = cast(ScrollPickerCtrl[str], self.get_control("sprFrqRepeatCycle"))
                    spr_ctrl.hide(spr_ctrl.visible)
                case "sprFrqRepeatCycle":
                    val = cast(str, kwargs["val"])
                    lbl_every = cast(LabelCtrl, self.get_control("lblSelFrqRepeatCycle"))
                    lbl_every.set_text(val)
                    
                    frm_week = cast(FrameCtrl, self.get_control("frmWeekCustomRepeatCycle"))
                    frm_month = cast(FrameCtrl, self.get_control("frmMonthCustomRepeatCycle"))
                    if val == "Week":
                        frm_month.hide()
                        frm_week.show()
                    elif val == "Month":
                        frm_week.hide()
                        frm_month.show()
                    else:
                        frm_week.hide()
                        frm_month.hide()
                case _:
                    return super().process_message(idmsg, **kwargs)
            return True
        return super().process_message(idmsg, **kwargs)                    

    @override
    def _confirm(self, **kwargs: object):
        # po(f"{self._idself} confirm")
        lbl_info = cast(LabelCtrl, self.get_control(idctrl="lblInfoRepeatCycle"))
        cycle_info = lbl_info.get_text()
        lbl_every = cast(LabelCtrl, self.get_control("lblSelEveryRepeatCycle"))
        every = int(lbl_every.get_text())
        lbl_frq = cast(LabelCtrl, self.get_control("lblSelFrqRepeatCycle"))
        frq = TimeUnit[lbl_frq.get_text().upper()]

        assert self._owner is not None
        _ = self._owner.process_message("ModifyCycle", cycle_info=cycle_info, every=every, frq=frq)
        return True, ""

    @override
    def _cancel(self, **kwargs: object):
        # po(f"{self._idself} cancel")
        return True, ""

class EditTodoDialog(DialogCtrl):
    """_summary_

    Attributes:
        _variable_ (_type_): _description_
    """
    def __init__(self, app: tkWin, dlg_cfg: et.Element):
        """_summary_

        Args:
            app (tkWin): _description_
            dlg_cfg (et.Element): _description_
        """
        self._todo: Todo | None = None
        self._todo_old: Todo | None = None
        super().__init__(app, dlg_cfg)

    @override
    def _beforego(self, **kwargs: object):
        self._todo = cast(Todo, kwargs["todo"])
        self._todo_old = deepcopy(self._todo)

        tododata = self._todo["data"]
        entry_name = cast(EntryCtrl, self._app.get_control("txtNameEditTodo"))
        entry_name.set_val(tododata["name"])
        entry_note = cast(EntryCtrl, self._app.get_control("txtNoteEditTodo"))
        entry_note.set_val(tododata["note"])

        if tododata["reminder_id"] > 0:
            pass

        calendar = cast(CalendarCtrl, self.get_control("cadDateEditTodo"))
        calendar.cancel_select()
        calendar.hide()
        time_scrollerpicker_ctrl = cast(TimeScrollPickerCtrl, self.get_control("tspTimeEditTodo"))
        time_scrollerpicker_ctrl.hide()

        # frm = cast(FrameCtrl, self.get_control(idctrl="frmEndEditTodo"))
        # frm.hide()

    @override
    def _confirm(self, **kwargs: object):
        assert self._todo is not None
        assert self._todo_old is not None

        tododata = self._todo["data"]
        entry_name = cast(EntryCtrl, self._app.get_control("txtNameEditTodo"))
        tododata["name"] = entry_name.get_val()
        entry_note = cast(EntryCtrl, self._app.get_control("txtNoteEditTodo"))
        tododata["note"] = entry_note.get_val()

        # date: datetime.date | None = None
        # lbl_date = cast(LabelCtrl, self.get_control("lblSelDateEditTodo"))
        # date_str = lbl_date.get_text()
        # if date_str:
        #     date = datetime.datetime.strptime(date_str, "%B %d, %Y\t%A").date()

        # pv(date)

        # time: datetime.time | None = None
        # lbl_time = cast(LabelCtrl, self.get_control("lblSelTimeEditTodo"))
        # time_str = lbl_time.get_text()
        # if time_str:
        #     time = datetime.datetime.strptime(time_str, "%H:%M").time()

        # pv(time)

        # if date or time:
        #     if self._todo_dict["reminder_id"] <= 0:
        #         self._todo_dict["reminder_id"] = uuid.uuid4().int
        #     reminder = self._todo_dict["reminder"]
        #     assert reminder is not None
        #     reminder["clk_time"] = time
        #     date = date if date else datetime.datetime.now().date()
        #     time = time if time else datetime.time(0, 0)
        #     reminder["cycbgn_dtime"] = datetime.datetime.combine(date, time)

        # pv(self._todo_dict["reminder"])

        # TODO: compare self._todo_dict with self._todo_old


        if tododata["reminder"]["every"] !=0 and tododata["reminder_id"] == 0:
            tododata["reminder_id"] = uuid.uuid4().int

        assert self._owner is not None
        _ = self._owner.process_message("ModifyTodo", todo=self._todo)
        # pv(self._owner)

        return True, ""

    @override
    def process_message(self, idmsg: str, **kwargs: object):
        if self.alive:
            kwargs.update(self._extral_msg)
            match idmsg:
                case "lblSelDateEditTodo":
                    lbl_date = cast(LabelCtrl, self.get_control("lblSelDateEditTodo"))
                    calendar = cast(CalendarCtrl, self.get_control("cadDateEditTodo"))
                    if lbl_date.get_text():
                        calendar.hide(calendar.visible)
                        # slideswitch = cast(SlideSwitchCtrl, self.get_control("slsDateEditTodo"))
                        # slideswitch.set_state(calendar.visible)
                case "slsDateEditTodo":
                    val = cast(bool, kwargs['val'])
                    calendar = cast(CalendarCtrl, self.get_control("cadDateEditTodo"))
                    if not val:
                        calendar.cancel_select()
                        lbl = cast(LabelCtrl, self.get_control("lblSelDateEditTodo"))
                        lbl.set_text("")
                    calendar.hide(not val)
                case "cadDateEditTodo":
                    lbl_date = cast(LabelCtrl, self.get_control("lblSelDateEditTodo"))
                    date = cast(datetime.date, kwargs['val'])
                    # date_text = f"{date.year}年{date.month:02d}月{date.day:02d}日"
                    date_text = date.strftime("%B %d, %Y\t%A")
                    # print(f"select date: {date_text}")
                    lbl_date.set_text(date_text)
                case "lblSelTimeEditTodo":
                    lbl_time = cast(LabelCtrl, self.get_control("lblSelTimeEditTodo"))
                    time_scrollerpicker_ctrl = cast(TimeScrollPickerCtrl, self.get_control("tspTimeEditTodo"))
                    if lbl_time.get_text():
                        time_scrollerpicker_ctrl.hide(time_scrollerpicker_ctrl.visible)
                        # slideswitch = cast(SlideSwitchCtrl, self.get_control("slsDateEditTodo"))
                        # slideswitch.set_state(calendar.visible)
                case "slsTimeEditTodo":
                    val = cast(bool, kwargs['val'])
                    time_scrollerpicker_ctrl = cast(TimeScrollPickerCtrl, self.get_control("tspTimeEditTodo"))
                    if not val:
                        lbl_time = cast(LabelCtrl, self.get_control("lblSelTimeEditTodo"))
                        lbl_time.set_text("")
                    time_scrollerpicker_ctrl.hide(not val)
                case "tspTimeEditTodo":
                    assert self._todo is not None
                    lbl_time = cast(LabelCtrl, self.get_control("lblSelTimeEditTodo"))
                    time = cast(datetime.time, kwargs['val'])
                    # date_text = f"{date.year}年{date.month:02d}月{date.day:02d}日"
                    time_text = time.strftime("%H:%M")
                    # print(f"select date: {date_text}")
                    lbl_time.set_text(time_text)

                    reminder = self._todo["data"]["reminder"]
                    assert reminder is not None
                    reminder["clk_time"] = datetime.datetime.strptime(lbl_time.get_text(), "%H:%M").time()
                    # pv(self._todo_dict)
                case "lblSelCycleEditTodo":
                    lbl = cast(LabelCtrl, self.get_control(idctrl="lblSelCycleEditTodo"))
                    cycle_info = lbl.get_text()
                    x, y = cast(tuple[int, int], kwargs["mousepos"])
                    dlg_id = "dlgRepeatCycle"
                    dlg_cfg = self._app.get_customctrlcfg(dlg_id)
                    dlg = RepeatCycleDlg(self._app, dlg_cfg)
                    dlg.do_show(self, x+20, y+20, cycle_info=cycle_info)
                case "ModifyCycle":
                    assert self._todo is not None
                    cycle_info = cast(str, kwargs["cycle_info"])
                    lbl = cast(LabelCtrl, self.get_control(idctrl="lblSelCycleEditTodo"))
                    lbl.set_text(cycle_info)

                    reminder = self._todo["data"]["reminder"]
                    assert reminder is not None
                    reminder["every"] = cast(int, kwargs["every"])
                    reminder["unit"] = cast(TimeUnit, kwargs["frq"])
                    # pv(self._todo_dict)
                case _:
                    return super().process_message(idmsg, **kwargs)
            return True
        return super().process_message(idmsg, **kwargs)


# --------------------------
# Custom Round Checkbutton
# --------------------------
class RoundCheckbutton:
    def __init__(self, parent: tk.Frame, callback: Callable[[], None] | None = None, is_checked: bool = False) -> None:
        self._parent: tk.Frame = parent
        self._callback: Callable[[], None] | None = callback
        self.checked: bool = is_checked

        self._canvas: tk.Canvas = tk.Canvas(
            parent, width=20, height=20, bg=COLORS["background"], highlightthickness=0
        )
        self._canvas.pack(side="left", padx=(5, 10), pady=5)
        self.draw_checkbox()

        _ = self._canvas.bind("<Button-1>", self.on_click)
        _ = self._canvas.bind("<B1-Motion>", lambda e: "break")

    def draw_checkbox(self) -> None:
        self._canvas.delete("all")
        if self.checked:
            _ = self._canvas.create_oval(2, 2, 18, 18, fill=COLORS["accent"], outline="")
            _ = self._canvas.create_polygon(5, 10, 8, 13, 15, 6, fill="white", outline="")
        else:
            _ = self._canvas.create_oval(2, 2, 18, 18, fill="", outline=COLORS["secondary_text"], width=1)

    def on_click(self, event: tk.Event) -> str:
        self.checked = not self.checked
        self.draw_checkbox()
        if self._callback:
            self._callback()
        return "break"

    def set_checked(self, checked: bool) -> None:
        self.checked = checked
        self.draw_checkbox()

# --------------------------
# TodoItem Class
# --------------------------
class TodoItem:
    def __init__(
        self, parent: tk.Frame, todo: Todo, owner: Container,
            show_divider: bool = True) -> None:
        self._parent: tk.Frame = parent
        self._owner: Container = owner
        self._show_divider: bool = show_divider

        self._todo: Todo = todo

        self._reminder_str: str = ""
        self._expired: bool = False

        # Core UI containers
        self._wrapper: tk.Frame = tk.Frame(
            parent, bg=COLORS["background"], height=SWIPE_CONFIG["placeholder_height"], width=400
        )
        self._wrapper.pack(fill="x", pady=0)
        # self._wrapper.todo_id = todo_dict["tid"]

        self._content_frame: tk.Frame = tk.Frame(
            self._wrapper, bg=COLORS["background"], height=SWIPE_CONFIG["placeholder_height"], width=400
        )
        self._content_frame.place(x=0, y=0, relwidth=1.0)

        # State variables
        self._is_delete_btn_visible: bool = False

        self._dragging: bool = False
        self._drag_type: Literal["delete", "sort"] | None = None
        self._drag_start_x: int = 0
        self._drag_start_y: int = 0

        self._current_dragged_item: tk.Frame | None = None
        self._current_offset_x: int = 0

        self._last_nearest_index: int = -1

        self._edit_mode: bool = False
        self._editing_todo_id: int | None = None
        self._current_edit_entry: tk.Entry | None = None
        self._edit_entry: tk.Entry | None = None
        self._editing: bool = False

        # Create UI components
        self._create_left_area()
        self._create_right_buttons()
        self._create_delete_button()
        self._create_divider()
        self._bind_events()

        self._expired = self._is_reminder_expired(self._todo)
        self._reminder_str = self._get_reminder_str(self._todo)
        self._update_text_display(self._reminder_str, self._expired)

    @property
    def todo(self):
        return self._todo

    @todo.setter
    def todo(self, val: Todo):
        self._todo = val
        pv(self._todo)

    def _create_left_area(self) -> None:
        self._left_area: tk.Frame = tk.Frame(
            self._content_frame, bg=COLORS["background"], height=SWIPE_CONFIG["placeholder_height"]
        )
        self._left_area.pack(side="left", fill="both", expand=True)
        _ = self._left_area.pack_propagate(False)

        self._checkbox: RoundCheckbutton = RoundCheckbutton(
            self._left_area, callback=self._on_toggle_completed
        )

        self._text_container: tk.Frame = tk.Frame(self._left_area, bg=COLORS["background"])
        self._text_container.pack(side="left", fill="both", expand=True)

    def _create_right_buttons(self) -> None:
        self._btn_container: tk.Frame = tk.Frame(
            self._content_frame, bg=COLORS["background"], width=80, height=SWIPE_CONFIG["placeholder_height"]
        )
        self._btn_container.pack(side="right", padx=5, pady=0, fill="y")
        _ = self._btn_container.pack_propagate(False)

        # More options button
        self._more_btn: tk.Button = tk.Button(
            self._btn_container, text="⋮", font=("Arial", 14, "bold"), bg=COLORS["background"],
            fg=COLORS["accent"], borderwidth=0, relief="flat", width=2, height=2)
        _ = self._more_btn.configure(command=lambda: self._on_open_detail(self._more_btn.winfo_rootx(),
            self._more_btn.winfo_rooty()))
        self._more_btn.pack(side="top", padx=2, pady=5)

        # Edit-mode delete button
        self._edit_delete_btn: tk.Button = tk.Button(
            self._btn_container, text="Delete", font=FONT_CONFIG["small"], bg=COLORS["background"],
            fg=COLORS["danger"], borderwidth=0, width=4, command=self.delete
        )
        if self._edit_mode:
            self._edit_delete_btn.pack(side="top", padx=2, pady=2)
        else:
            self._edit_delete_btn.pack_forget()

    def _create_delete_button(self) -> None:
        self._delete_btn: tk.Button = tk.Button(
            self._wrapper, text="Delete", font=FONT_CONFIG["small"], bg=COLORS["danger"],
            fg="white", borderwidth=0, command=self.delete, width=10, state="disabled"
        )
        self._delete_btn.place(
            x=400, y=0, width=SWIPE_CONFIG["delete_btn_width"], height=SWIPE_CONFIG["placeholder_height"]
        )

    def _create_divider(self) -> None:
        if self._show_divider:
            self._divider: tk.Frame = tk.Frame(
                self._wrapper, bg=COLORS["border"], height=1, width=400 - 30
            )
            self._divider.place(x=30, y=SWIPE_CONFIG["placeholder_height"]-1)

    def _bind_events(self) -> None:
        # Drag/swipe events
        for widget in [self._wrapper, self._content_frame]:
            _ = widget.bind("<ButtonPress-1>", self._on_press)
            _ = widget.bind("<B1-Motion>", self._on_drag)
            _ = widget.bind("<ButtonRelease-1>", self._on_release)
            _ = widget.bind("<Leave>", self._on_leave)

        # Text edit event
        _ = self._text_container.bind("<Button-1>", self._on_text_click)

    def _on_press(self, event: tk.Event) -> None:
        if self._edit_mode or self._editing_todo_id:
            return
        if event.widget in [self._text_container, self._more_btn] or isinstance(event.widget, tk.Canvas):
            return

        self._dragging = True
        self._drag_start_x = event.x_root
        self._drag_start_y = event.y_root
        self._current_dragged_item = self._wrapper
        # self._owner._original_todo_id = self._todo_dict["tid"]
        self._current_offset_x = 0
        # self._current_offset_y = 0
        self._wrapper.lift()
        self._drag_type = None

    def _reset_drag_state(self) -> None:
        """Reset all drag-related state variables"""
        self._dragging = False
        self._drag_type = None
        self._current_dragged_item = None
        self._current_offset_x = 0
        # self._current_offset_y = 0
        # self._original_todo_id = None
        self._last_nearest_index = -1

        # Destroy drag placeholder
        # if self._drag_placeholder:
        #     self._drag_placeholder.destroy()
        #     self._drag_placeholder = None

    def _on_drag(self, event: tk.Event) -> None:
        if not self._dragging or self._current_dragged_item != self._wrapper:
            return

        dx: int = event.x_root - self._drag_start_x
        dy: int = event.y_root - self._drag_start_y

        # Determine drag type (delete/sort)
        if self._drag_type is None:
            if abs(dx) > SWIPE_CONFIG["drag_threshold"]:
                self._drag_type = "delete"
                _ = self._wrapper.config(bg=COLORS["danger_bg"])
            elif abs(dy) > SWIPE_CONFIG["drag_threshold"]:
                # self._drag_type = "sort"
                # _ = self._content_frame.config(
                #     bg=COLORS["drag_active"], relief="solid", bd=1,
                #     highlightbackground=COLORS["drag_border"], highlightthickness=1
                # )
                # self._owner._create_drag_placeholder(self._wrapper)
                pass

        # Handle swipe delete
        if self._drag_type == "delete":
            self._handle_swipe_delete(dx)
        # Handle drag sort
        elif self._drag_type == "sort":
            # self._owner._handle_drag_sort(dy)
            pass

    def _on_release(self, event: tk.Event) -> None:
        if not self._dragging or self._current_dragged_item != self._wrapper:
            self._reset_drag_state()
            return

        if self._drag_type == "delete":
            if self._current_offset_x <= SWIPE_CONFIG["delete_threshold"]:
                self.delete()
            else:
                self._animate_swipe_back()
        elif self._drag_type == "sort":
            # _ = self._content_frame.config(
            #     bg=COLORS["background"], relief="flat", bd=0, highlightthickness=0
            # )
            # self._owner._finalize_drag_sort()
            pass

        self._reset_drag_state()

    def _on_leave(self, event: tk.Event) -> None:
        if self._dragging and self._current_dragged_item == self._wrapper:
            if self._drag_type == "sort":
                _ = self._content_frame.config(
                    bg=COLORS["background"], relief="flat", bd=0, highlightthickness=0
                )
            self._reset_drag_state()
            if self._drag_type == "delete" and self._current_offset_x > SWIPE_CONFIG["delete_threshold"]:
                self._animate_swipe_back()

    def _on_text_click(self, event: tk.Event) -> str:
        if self._edit_mode or self._editing_todo_id:
            return "break"

        self._reset_drag_state()
        self._switch_to_edit_mode()
        return "break"

    def _handle_swipe_delete(self, dx: int) -> None:
        offset_x: int = dx
        if offset_x > 0:
            offset_x = 0
        elif offset_x < SWIPE_CONFIG["max_swipe_distance"]:
            self.delete()
            self._reset_drag_state()
            return

        self._current_offset_x = offset_x
        self._content_frame.place(x=offset_x, y=0, width=400)

        # Show/hide delete button
        if offset_x <= SWIPE_CONFIG["show_btn_threshold"] and not self._is_delete_btn_visible:
            _ = self._delete_btn.config(state="normal")
            delete_btn_x: int = 400 + offset_x
            self._delete_btn.place(
                x=delete_btn_x, y=0, width=SWIPE_CONFIG["delete_btn_width"],
                height=SWIPE_CONFIG["placeholder_height"]
            )
            self._is_delete_btn_visible = True
        elif offset_x > SWIPE_CONFIG["show_btn_threshold"] and self._is_delete_btn_visible:
            _ = self._delete_btn.config(state="disabled")
            self._delete_btn.place(x=400, y=0)
            self._is_delete_btn_visible = False

    def _animate_swipe_back(self) -> None:
        current_x: int = int(float(self._content_frame.place_info()["x"]))
        if current_x >= 0:
            self._reset_state()
            return

        steps: int = 10
        step_x: float = abs(current_x) / steps

        def animate_step(step: int) -> None:
            if step >= steps:
                self._reset_state()
                return

            new_x: float = current_x + (step + 1) * step_x
            if new_x > 0:
                new_x = 0

            self._content_frame.place(x=new_x, y=0, width=400)

            if self._is_delete_btn_visible:
                delete_btn_x: float = 400 + new_x
                self._delete_btn.place(
                    x=delete_btn_x, y=0, width=SWIPE_CONFIG["delete_btn_width"],
                    height=SWIPE_CONFIG["placeholder_height"]
                )

            _ = self._wrapper.after(int(SWIPE_CONFIG["animation_duration"] / steps),
                animate_step, step + 1)

        animate_step(0)

    def _reset_state(self) -> None:
        self._content_frame.place(x=0, y=0, width=400)
        _ = self._wrapper.config(bg=COLORS["background"])
        _ = self._content_frame.config(
            bg=COLORS["background"], relief="flat", bd=0, highlightthickness=0
        )

        if self._is_delete_btn_visible:
            _ = self._delete_btn.config(state="disabled")
            self._delete_btn.place(x=400, y=0)
            self._is_delete_btn_visible = False

    def _switch_to_edit_mode(self) -> None:
        # Cancel other edits
        if self._editing_todo_id and self._editing_todo_id != self._todo["iid"]:
            self.cancel_edit()

        if self._editing_todo_id == self._todo["iid"]:
            return

        # Clear text container
        for widget in self._text_container.winfo_children():
            widget.destroy()

        self._editing_todo_id = self._todo["tid"]

        # Create edit entry
        original_width: int = int((400 - 100) / 8)
        new_width: int = int(original_width * (2/3))

        self._edit_entry = tk.Entry(
            self._text_container, font=(FONT_CONFIG["body"][0], FONT_CONFIG["body"][1], "bold"),
            bg="white", fg=COLORS["primary_text"], relief="solid", bd=1,
            highlightthickness=1, highlightcolor=COLORS["accent"], width=new_width
        )
        self._edit_entry.pack(side="left", fill="x", expand=False, padx=5, pady=10)
        self._edit_entry.insert(0, self._todo["name"])
        self._edit_entry.select_range(0, tk.END)
        self._edit_entry.focus_force()
        self._current_edit_entry = self._edit_entry

        # Bind save/cancel
        _ = self._edit_entry.bind("<Return>", lambda e: self.save_edit())
        _ = self._edit_entry.bind("<FocusOut>", lambda e: self.save_edit())
        _ = self._edit_entry.bind("<Escape>", lambda e: self.cancel_edit())

    def save_edit(self) -> None:
        if not self._edit_entry:
            return

        new_text: str = self._edit_entry.get().strip()
        if not new_text:
            new_text = "Unnamed todo"

        # Update data
        self._todo["name"] = new_text
        # self._app.save_todos()

        # Exit edit mode
        # self._owner._editing_todo_id = None
        # self._owner._current_edit_entry = None

        # Refresh display
        self._update_text_display()
        # self._owner.update_stats()

    def cancel_edit(self) -> None:
        # self._owner._editing_todo_id = None
        # self._owner._current_edit_entry = None
        self._update_text_display()

    def _is_reminder_expired(self, todo: Todo) -> bool:
        tododata = todo["data"]
        if tododata["reminder_id"] <= 0:
            return False

        reminder_info = tododata["reminder_infos"][todo["reminder_idx"]]
        reminder_time = reminder_info["clock_time"]
        reminder_dtime = datetime.datetime.combine(todo["day"], reminder_time)

        return reminder_dtime < datetime.datetime.now()

    def _update_text_display(self, reminder_str: str, is_expired: bool = False, is_completed: bool = False):
        # Clear text container
        for widget in self._text_container.winfo_children():
            widget.destroy()

        # Text styling
        text_color = COLORS["secondary_text"] \
            if is_completed else COLORS["primary_text"]
        strike: str = "overstrike" if is_completed else "normal"

        # Main text frame
        text_frame: tk.Frame = tk.Frame(self._text_container, bg=COLORS["background"])
        text_frame.pack(side="left", fill="both", expand=True, padx=5, pady=2)

        # Todo title
        name_label: tk.Label = tk.Label(
            text_frame, text=self._todo["data"]["name"],
            font=(FONT_CONFIG["body"][0], FONT_CONFIG["body"][1], "bold", strike),
            bg=COLORS["background"], fg=text_color, anchor="w", wraplength=280, justify="left"
        )
        name_label.pack(side="top", fill="x", anchor="w")

        # Note text
        note_label: tk.Label = tk.Label(
            text_frame, text=self._todo.get("note", ""),
            font=(FONT_CONFIG["small"][0], FONT_CONFIG["small"][1], strike),
            bg=COLORS["background"], fg=COLORS["secondary_text"], anchor="w", wraplength=280, justify="left"
        )
        if self._todo.get("note", "").strip():
            note_label.pack(side="top", fill="x", anchor="w", pady=(0, 1))
        else:
            note_label.pack_forget()

        reminder_color: str = COLORS["danger"] if is_expired else COLORS["secondary_text"]

        reminder_label: tk.Label = tk.Label(
            text_frame, text=reminder_str,
            font=(FONT_CONFIG["small"][0], FONT_CONFIG["small"][1], strike),
            bg=COLORS["background"], fg=reminder_color, anchor="w", wraplength=280, justify="left"
        )
        reminder_label.pack(side="top", fill="x", anchor="w")

        # Bind edit events
        for widget in [text_frame, name_label, note_label, reminder_label]:
            _ = widget.bind("<Button-1>", self._on_text_click)
            _ = widget.bind("<B1-Motion>", lambda e: "break")

    def _get_reminder_str(self, todo: Todo):
        if todo["data"]["reminder_id"] !=0 :
            reminder_info = todo["data"]["reminder_infos"][todo["reminder_idx"]]
            reminder_time = reminder_info["clock_time"]
            clock_str= time2str(reminder_time)
            cyc_str, _ = reminder2str(todo["data"]["reminder"])
            reminder_str = f"Remind: {clock_str} 🔁 {cyc_str[:-5]}"
        else:
            reminder_str = "No reminder"
        return reminder_str

    def _on_toggle_completed(self) -> None:
        # if self._owner._editing_todo_id == self._todo_dict["tid"]:
        #     self.cancel_edit()

        reminder_idx = self._todo["reminder_idx"]
        tododata = self._todo["data"]
        tododata["reminder_infos"][reminder_idx]["completed"] = True

        self._update_text_display(self._reminder_str, self._expired, True)

        # Notify to owner
        _ = self._owner.process_message("CompleteTodo", todo=self._todo)

        # if self._todo["reminder_idx"] == -1:
        #     # _ = self._owner.process_message("CompleteTodo", todo=self._todo)
        #     pass
        # else:
        #     self._expired = self._is_reminder_expired(self._todo)
        #     self._reminder_str = self._get_reminder_str(self._todo)
        #     self._update_text_display(self._reminder_str, self._expired)

    def delete(self) -> None:
        if self._editing_todo_id == self._todo["tid"]:
            self._editing_todo_id = None
            self._current_edit_entry = None

        # Confirm deletion in edit mode
        if self._edit_mode and not messagebox.askyesno("Confirmation", "Are you sure to delete this todo?"):
            return

        # Notify to owner
        # self._owner.delete_todo_by_id(self._todo_dict["tid"])

    def _on_open_detail(self, x: int, y: int) -> None:
        if self._editing_todo_id:
            self.cancel_edit()
        _ = self._owner.process_message("OpenEditTodoDlg", mousepos=[x,y], todo=self._todo)
        # pv(self._todo_dict)

    def update_edit_mode(self) -> None:
        if self._edit_mode:
            self._edit_delete_btn.pack(side="top", padx=2, pady=2)
        else:
            self._edit_delete_btn.pack_forget()

    # TODO
    def tick(self) -> None:
        # calc status
        pass
        # self._checkbox.set_checked(updated_data["status"] == StatusEnum.COMPLETED)
        # self._update_text_display()

class BaseTodoPage(Container, metaclass=abc.ABCMeta):
    """Base class for all Todo pages (shared UI structure).

    This class provides a reusable UI template for all four todo pages, including
    a title bar with a back button to TodoTab and a content frame for page-specific
    widgets. All concrete pages inherit from this class.

    Args:
        parent: Parent widget (root window or container frame)
        controller: Main application instance for frame navigation
        page_title: Display title for the page's title bar
    """
    def __init__(self, parent: tk.Frame, owner: Container, name: str, page_title: str) -> None:
        self._page_title: str = page_title
        super().__init__(owner)

        self._main_frame: tk.Frame = tk.Frame(parent)

        # -------------------------- Grid Layout (Key to Fill Remaining Space) -------------------------
        # Row 0: Fixed nav bar (weight=0)
        # Row 0: Fixed title bar (weight=0)
        # Row 1: Content frame fills ALL remaining space (weight=1)
        # Column 0: Full width fill (weight=1)
        _ = self._main_frame.grid_rowconfigure(0, weight=0)
        _ = self._main_frame.grid_rowconfigure(1, weight=0)
        _ = self._main_frame.grid_rowconfigure(2, weight=1)
        _ = self._main_frame.grid_columnconfigure(0, weight=1)

        # -------------------------- Title Bar (Consistent for All Pages, Fixed Height) -------------------------
        # Create title bar frame with background color
        nav_bar = tk.Frame(self._main_frame, bg="#2c3e50", height=50)
        # Place title bar in row 0, full width
        nav_bar.grid(row=0, column=0, sticky="nsew", padx=2)
        _ = nav_bar.pack_propagate(False)  # Fix height

        # Back Button (returns to TodoTab)
        back_btn = ttk.Button(
            nav_bar,
            text="< List",
            command=self._back_to_todo_tab
        )
        back_btn.pack(side=tk.LEFT, padx=10, pady=8)

        title_bar = tk.Frame(self._main_frame, bg="white", height=50)
        title_bar.grid(row=1, column=0, sticky="nsew", padx=2)
        _ = title_bar.pack_propagate(False)  # Fix height

        # Page Title Label
        title_label: tk.Label = tk.Label(
            title_bar,
            text=self._page_title,
            fg=COLORS["accent"],
            bg="white",
            font=("Arial", 14, "bold")
        )
        title_label.pack(side=tk.LEFT, padx=20)

        # Edit button
        self._edit_btn: tk.Button = tk.Button(
            title_bar, text="Edit", font=FONT_CONFIG["small"],
            bg="white", fg=COLORS["accent"], borderwidth=0,
            command=self._toggle_edit_mode
        )
        self._edit_btn.place(relx=0.9, rely=0.5, anchor="center")

        # -------------------------- Page Content Frame (FILLS ALL REMAINING SPACE) -----------
        self.content_frame: tk.Frame = tk.Frame(self._main_frame, bg="#ecf0f1")
        self.content_frame.grid(row=2, column=0, sticky="nsew", padx=2, pady=2)

        self._name: str = name

        self._todos_data: TodosDict = {}

    @property
    def frame(self):
        return self._main_frame

    def _back_to_todo_tab(self) -> None:
        """Navigate back to the main TodoTab frame.

        Triggers the main app's frame switching method to display TodoTab.
        """
        assert self._owner is not None
        _ = self._owner.process_message("ShowMainPage")

    @property
    def name(self):
        return self._name

    @property
    def todos(self):
        return self._todos_data

    @todos.setter
    def todos(self, val: TodosDict):
        self._todos_data = val
        pv(self._todos_data)

    def show_page(self):
        self._alive = True
        self.refresh_todos()

    def hide_page(self):
        self._alive = False

    @abc.abstractmethod
    def refresh_todos(self):
        pass

    def _toggle_edit_mode(self):
        pass


class TodayTodoPage(BaseTodoPage):
    def __init__(self, parent: tk.Frame, owner: Container, name: str, page_title: str):
        super().__init__(parent, owner, name, page_title)

        self._stats_label: tk.Label | None = None
        self._canvas: tk.Canvas | None = None
        self._todo_container: tk.Frame | None = None
        self._todo_entry: tk.Entry | None = None
        self._placeholder_text: str = "Add new todo..."
        self._todo_items: list[TodoItem] = []

        # Load data
        # self._todos = self.load_todos()

        self._original_todo_id: int | None = None
        self._current_offset_y: int = 0
        self._drag_placeholder: tk.Frame | None = None

        # Setup UI
        self.setup_ui()

        # Render todo list (delayed)
        # _ = self._gui.win.after(100, self.render_todo_list)

        # Bind global events
        # _ = self._gui.win.bind("<Configure>", self.on_window_resize)
        # _ = self._gui.win.bind("<Button-1>", self.on_global_click)

    def on_window_resize(self, event: tk.Event) -> None:
        # if event.widget == self._parent:
        # if event.widget == self._gui.win:
            # self.render_todo_list()
        pass

    def _find_next_reminder(self, tododata: TodoData):
        last_fnshd_idx = -1
        for idx, reminder_info in enumerate(tododata['reminder_infos']):
            if reminder_info["completed"]:
                last_fnshd_idx = idx

        if last_fnshd_idx == -1:
            reminder_idx = 0
        else:
            reminder_idx = last_fnshd_idx + 1

        return reminder_idx

    def get_todo_time_group(self, reminder_time: datetime.time):
        if TIME_GROUPS["morning"]["start"] <= reminder_time < TIME_GROUPS["morning"]["end"]:
            return "morning"
        elif TIME_GROUPS["afternoon"]["start"] <= reminder_time < TIME_GROUPS["afternoon"]["end"]:
            return "afternoon"
        else:
            return "evening"

    def group_todos_by_time(self):
        grouped_todos: dict[str, list[Todo]] = {
            "morning": [], "afternoon": [], "evening": [], "no_reminder": []
        }

        # Sort by creation time (newest first)
        # sorted_todos = sorted(self._todos, key=lambda x: x["created_at"], reverse=True)
        sorted_todos = self._todos_data

        today =  datetime.date.today()
        for tid, tododata in sorted_todos.items():
            group_key = "no_reminder"
            if tododata["reminder_id"] !=0:
                for reminder_info in tododata["reminder_infos"]:
                    if not reminder_info["completed"]:
                        group_key = self.get_todo_time_group(reminder_info["clock_time"])
                        break
            reminder_idx = self._find_next_reminder(tododata)
            todo: Todo = {
                "tid": tid,
                "data": tododata,
                "day": today,
                "reminder_idx": reminder_idx
            }
            grouped_todos[group_key].append(todo)

        return grouped_todos

    def setup_ui(self) -> None:
        # self.setup_stats_bar()
        self.setup_todo_list()
        self.setup_add_todo()

    def setup_stats_bar(self) -> None:
        stats_frame = tk.Frame(self.content_frame, bg=COLORS["background"], height=40)
        stats_frame.pack(fill="x", padx=20, pady=10)

        self._stats_label = tk.Label(
            stats_frame, text=self.get_stats_text(), font=FONT_CONFIG["small"],
            bg=COLORS["background"], fg=COLORS["secondary_text"]
        )
        self._stats_label.pack(anchor="w")

    def get_stats_text(self) -> str:
        total = len(self._todos_data)
        completed = sum(1 for todo in self._todos_data if todo["status"] == StatusEnum.COMPLETED)
        return f"Completed {completed} / Total {total}"

    def setup_todo_list(self) -> None:
        # List container
        list_frame = tk.Frame(self.content_frame, bg=COLORS["background"])
        list_frame.pack(fill="both", expand=True, padx=0, pady=0)

        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical")
        scrollbar.pack(side="right", fill="y")

        # Canvas for scrollable content
        self._canvas = tk.Canvas(
            list_frame, bg=COLORS["background"], width=400,
            yscrollcommand=scrollbar.set, highlightthickness=0
        )
        self._canvas.pack(side="left", fill="both", expand=True)
        _ = scrollbar.config(command=self._canvas.yview)

        # Todo container (inside canvas)
        self._todo_container = tk.Frame(self._canvas, bg=COLORS["background"], width=400)
        _ = self._canvas.create_window((0, 0), window=self._todo_container, anchor="nw", width=400)

        # Update scroll region when content changes
        def update_scrollregion(event: tk.Event) -> None:
            if self._canvas:
                _ = self._canvas.configure(scrollregion=self._canvas.bbox("all"))
        _ = self._todo_container.bind("<Configure>", update_scrollregion)

    def create_group_title(self, group_key: str) -> tk.Frame:
        # group_info = TIME_GROUPS.get(group_key,
            # {"name": "No reminder", "start": None, "end": None})
        if group_key in TIME_GROUPS:
            title = TIME_GROUPS[group_key]["name"]
        else:
            title = "No reminder"

        title_frame = tk.Frame(self._todo_container, bg=COLORS["background"], height=30, width=400)
        title_frame.pack(fill="x", padx=20, pady=(15, 5))

        tk.Label(
            title_frame, text=title, font=FONT_CONFIG["group_title"],
            bg=COLORS["background"], fg=COLORS["group_title"]
        ).pack(anchor="w", padx=5)

        return title_frame

    def setup_add_todo(self) -> None:
        add_frame = tk.Frame(self.content_frame, bg=COLORS["background"], height=60)
        add_frame.pack(fill="x", padx=15, pady=10)

        # Input field
        self._todo_entry = tk.Entry(
            add_frame, font=FONT_CONFIG["body"], bg=COLORS["card"], fg=COLORS["primary_text"],
            insertbackground=COLORS["accent"], relief="flat", bd=0, highlightthickness=0
        )
        self._todo_entry.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        self._setup_entry_placeholder(self._todo_entry, self._placeholder_text)
        _ = self._todo_entry.bind("<Return>", self._on_add_todo)

        # Add button
        add_btn = tk.Button(
            add_frame, text="Add", font=FONT_CONFIG["small"],
            bg=COLORS["accent"], fg="white", borderwidth=0, relief="flat",
            command=self._on_add_todo, width=8
        )
        add_btn.pack(side="right", padx=5, pady=5)

    def render_todo_list(self) -> None:
        if not self._todo_container:
            return

        # Clear existing items
        for widget in self._todo_container.winfo_children():
            widget.destroy()
        self._todo_items.clear()

        # Cancel active edits
        # self._editing_todo_id = None
        # self._current_edit_entry = None

        # Group todos
        grouped_todos = self.group_todos_by_time()
        group_order = ["morning", "afternoon", "evening", "no_reminder"]
        # group_order = list(TIME_GROUPS.keys())

        # Check if empty
        has_any_todo = any(len(v) > 0 for v in grouped_todos.values())
        if not has_any_todo:
            empty_label = tk.Label(
                self._todo_container, text="No todos yet! Add one below.",
                font=FONT_CONFIG["body"], bg=COLORS["background"], fg=COLORS["secondary_text"]
            )
            empty_label.pack(pady=50)
            return

        # Render groups
        for group_key in group_order:
            todos_in_group = grouped_todos[group_key]
            if not todos_in_group:
                continue

            # Group title
            _ = self.create_group_title(group_key)

            # Todo items
            for idx, todo in enumerate(todos_in_group):
                show_divider = (idx < len(todos_in_group) - 1)
                todo_item = TodoItem(self._todo_container, todo, self, show_divider)
                self._todo_items.append(todo_item)

        # Update scroll region
        self._todo_container.update_idletasks()
        if self._canvas:
            _ = self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    @override
    def refresh_todos(self):
        self._todo_items.clear()
        self.render_todo_list()
        self.update_stats()

    def _on_add_todo(self, event: tk.Event | None = None) -> None:
        if not self._todo_entry:
            return

        text = self._todo_entry.get().strip()
        if text == self._placeholder_text or not text:
            _ = messagebox.showwarning("Warning", "Please enter todo content!")
            return

        # Create new todo
        plandata = default_plan_data()
        plandata['name'] = text
        # eid = uuid.uuid4().int
        eid = 0
        now = datetime.datetime.now()
        reminderdata: ReminderDataDict = {
            "clk_time": None,
            "bgn_time": None,  # Default
            "duration": 0,
            "every": 0,
            "unit": TimeUnit.WEEK,
            "custom": DayType.EVERYDAY,
            "cycbgn_dtime": now,  # Default
            "cycend_dtime": None   # Default
        }
        plandata["reminders"][eid] = reminderdata

        new_todo: TodoData = {
            "name": plandata['name'],
            "note": plandata['note'],
            "tags": plandata['tags'],
            "fid": plandata['fid'],
            "status": plandata["status"],
            "reminder_id": 0,
            "reminder": reminderdata,
            "reminder_infos": []
        }

        assert self._owner is not None
        tid = cast(int, self._owner.process_message("NewTodo", tododata=new_todo, plandata=plandata, reminderdata=reminderdata))

        self._todos_data[tid] = new_todo

        self.render_todo_list()
        self.update_stats()

        # Reset input
        self._todo_entry.delete(0, tk.END)
        self._todo_entry.insert(0, self._placeholder_text)
        _ = self._todo_entry.config(fg=COLORS["placeholder"])

    def delete_todo_by_id(self, todo_id: int) -> None:
        # Remove from list
        del self._todos_data[todo_id]

        # Save and refresh
        # self.save_todos()
        self.render_todo_list()
        self.update_stats()

    # TODO:
    def tick(self) -> None:
        # Update todo in list
        for todo_item in self._todo_items:
            todo_item.tick()

    def cancel_edit(self) -> None:
        self._editing_todo_id = None
        self._current_edit_entry = None
        for todo_item in self._todo_items:
            todo_item.cancel_edit()

    def on_global_click(self, event: tk.Event) -> None:
        if not self._editing_todo_id or not self._current_edit_entry:
            return

        # Check if click is outside edit field
        widget = event.widget
        if widget == self._current_edit_entry or widget in self._current_edit_entry.winfo_children():
            return

        # Save edit
        todo_id: int | None = self._editing_todo_id
        if not todo_id:
            return

        for todo_item in self._todo_items:
            if todo_item.todo["tid"] == todo_id:
                todo_item.save_edit()
                break

        self._editing_todo_id = None
        self._current_edit_entry = None

    def update_stats(self) -> None:
        if self._stats_label:
            _ = self._stats_label.config(text=self.get_stats_text())

    # Protected Methods
    def _setup_entry_placeholder(self, entry: tk.Entry, placeholder: str) -> None:
        def on_focus_in(event: tk.Event) -> None:
            if entry.get() == placeholder:
                entry.delete(0, tk.END)
                _ = entry.config(fg=COLORS["primary_text"])

        def on_focus_out(event: tk.Event) -> None:
            if not entry.get().strip():
                entry.insert(0, placeholder)
                _ = entry.config(fg=COLORS["placeholder"])

        # Initialize placeholder
        entry.insert(0, placeholder)
        _ = entry.config(fg=COLORS["placeholder"])
        _ = entry.bind("<FocusIn>", on_focus_in)
        _ = entry.bind("<FocusOut>", on_focus_out)

    def _create_drag_placeholder(self, reference_item: tk.Frame) -> None:
        if self._drag_placeholder:
            self._drag_placeholder.destroy()

        todo_items: list[tk.Frame] = [w for w in self._todo_container.winfo_children() if hasattr(w, "todo_id")]
        ref_index: int = todo_items.index(reference_item) if reference_item in todo_items else 0

        self._drag_placeholder = tk.Frame(
            self._todo_container, bg=COLORS["drag_placeholder"],
            height=SWIPE_CONFIG["placeholder_height"], width=400
        )
        if ref_index < len(todo_items):
            self._drag_placeholder.pack(fill="x", pady=0, before=todo_items[ref_index])

    def _move_drag_placeholder(self, target_index: int) -> None:
        if not self._drag_placeholder:
            return

        todo_items: list[tk.Frame] = [w for w in self._todo_container.winfo_children() if hasattr(w, "todo_id")]
        if 0 <= target_index < len(todo_items):
            self._drag_placeholder.pack_forget()
            self._drag_placeholder.pack(fill="x", pady=0, before=todo_items[target_index])

    def _handle_drag_sort(self, dy: int) -> None:
        self._current_offset_y = dy
        self._wrapper.place(y=self._wrapper.winfo_y() + dy)

        # Find nearest todo item
        todo_items: list[tk.Frame] = [w for w in self._todo_container.winfo_children() if hasattr(w, "todo_id")]
        current_y: int = self._wrapper.winfo_y() + SWIPE_CONFIG["placeholder_height"] // 2

        nearest_index: int = -1
        min_distance: float = float("inf")

        for idx, item in enumerate(todo_items):
            if item == self._wrapper:
                continue
            item_y: int = item.winfo_y() + SWIPE_CONFIG["placeholder_height"] // 2
            distance: float = abs(item_y - current_y)

            if distance < min_distance:
                min_distance = distance
                nearest_index = idx

        if nearest_index != -1 and nearest_index != self._last_nearest_index:
            self._move_drag_placeholder(nearest_index)
            self._last_nearest_index = nearest_index

    def _finalize_drag_sort(self) -> None:
        """ Complete drag sorting and update todo order"""
        if not self._drag_placeholder or not self._original_todo_id:
            return

        # Get current order of todo items
        todo_items: list[tk.Frame] = [w for w in self._todo_container.winfo_children() if hasattr(w, "todo_id")]
        placeholder_index: int = todo_items.index(self._drag_placeholder) if self._drag_placeholder in todo_items else -1

        if placeholder_index == -1:
            return

        # Find original todo
        original_todo = next((t for t in self._todos_data if t["iid"] == self._original_todo_id), None)
        if not original_todo:
            return

        # Remove original todo from list
        self._todos_data = [t for t in self._todos_data if t["iid"] != self._original_todo_id]

        # Insert at new position
        self._todos_data.insert(placeholder_index, original_todo)

        # Save and re-render
        # self.save_todos()
        self.render_todo_list()

    def _on_complete_todo(self, todo: Todo):
        assert self._owner is not None
        tododata = todo["data"]
        now = datetime.datetime.now()
        reminder_idx = todo["reminder_idx"]
        reminder_info = tododata["reminder_infos"][reminder_idx]

        # Mark complete
        tid = todo["tid"]
        self._todos_data[tid]["reminder_infos"][reminder_idx]["completed"] = True

        # Notify owner
        clock_time = reminder_info["clock_time"]
        reminder_dtime = datetime.datetime.combine(todo["day"], clock_time)
        duration = int(reminder_dtime.timestamp())
        _ = self._owner.process_message("RecordTodo", id=todo["tid"],
            strt_dtime=now, duration=duration)

        # Next reminder
        reminder_idx = -1
        now = datetime.datetime.now()
        reminder_infos = tododata["reminder_infos"]
        for idx in range(todo["reminder_idx"] + 1, len(reminder_infos)):
            if not reminder_infos[idx]["completed"]:
                clock_time = reminder_infos[idx]["clock_time"]
                reminder_dtime = datetime.datetime.combine(todo["day"], clock_time)
                if reminder_dtime >= now:
                    reminder_idx = idx
                    break

        if reminder_idx == -1:
            del self._todos_data[tid]

        self.refresh_todos()

    @override
    def process_message(self, idmsg: str, **kwargs: object):
        assert self._owner is not None
        match idmsg:
            # case "ModifyTodo":
            #     todo = cast(TodoDict, kwargs["todo_dict"])
            #     self.modify_todo(todo["tid"], todo)
                # assert self._owner is not None
                # _ = self._owner.process_message("ModifyTodo", todo_dict=todo)
            case "CompleteTodo":
                todo = cast(Todo, kwargs["todo"])
                self._on_complete_todo(todo)
            case _:
                return self._owner.process_message(idmsg, **kwargs)
        return True

    @override
    def destroy(self, **kwargs: object):
        """ _summary_
        """
        pass


class TodoTab(Container):
    """_summary_

    Attributes:
        _gui (_type_): _description_
        _schedule (_type_): _description_
        _todo_db (_type_): _description_
    """
    def __init__(self, owner: Container, schedule: Schedule) -> None:
        """_summary_

        Args:
            owner (_type_): _description_
            schedule (_type_): _description_
        """
        super().__init__()

        self._gui: tkWin = cast(tkWin, owner)
        self._gui.filter_message(self.process_message)
        self._schedule: Schedule = schedule

        self._todos_db: TimeDatabase = TimeDatabase()
        self._todos: TodosDict = {}
        self._eids: list[int] = []

        self._active_page: BaseTodoPage | None = None

        self._pages: list[BaseTodoPage] = []
        # self._pages_frame: dict[str, tk.Frame] = {}

        parent = cast(tk.Frame, cast(tkControl, self._gui.get_control("tabTodo")).control)
        page = TodayTodoPage(parent, self, "TodayTodo", "Today")
        self._pages.append(page)

        for page in self._pages:
            page.frame.grid(row=0, column=0, sticky="nsew")
        _ = parent.grid_rowconfigure(0, weight=1)
        _ = parent.grid_columnconfigure(0, weight=1)

        self._main_pages_frame: tk.Frame = cast(tk.Frame, cast(tkControl, self._gui.get_control("frmMainTodo")).control)

        frame = cast(tk.Frame, cast(tkControl, self._gui.get_control("frmTodayTodo")).control)
        _ = frame.bind("<Button-1>", lambda e: self._show_page("TodayTodo"))

    def _open(self, db_path: str):
        """_summary_
        Args:
            db_path (type): _description_
        """
        _ =  self._todos_db.open(db_path)

    def new_todos(self, db_path: str):
        """_summary_
        Args:
            db_path (type): _description_
        """
        _ = self._open(db_path)

    def open_todos(self, db_path: str):
        """_summary_
        Args:
            db_path (type): _description_
        """
        _ = self._open(db_path)

        plans = self._todos_db.read_plans()
        for tid, plandata in plans.items():
            eids = list(plandata["reminders"].keys())
            if len(eids) > 0:
                eid = eids[0]
                reminderdata = plandata["reminders"][eid]
                if clock_time := reminderdata["clk_time"]:
                    self._schedule.add_event(eid, plandata["name"], clock_time, reminderdata["every"],
                        reminderdata["unit"], reminderdata["custom"],
                        reminderdata["cycbgn_dtime"], reminderdata["cycend_dtime"],
                        ActTyp.DRIPPING_WATER)
                todo: TodoData = {
                    "name": plandata["name"],
                    "note": plandata["note"],
                    "tags": plandata["tags"],
                    "fid": plandata["fid"],
                    "status": plandata["status"],
                    "reminder_id": eid,
                    "reminder": reminderdata,
                    "reminder_infos": []
                }
                self._todos[tid] = todo

        self._show_page("TodayTodo")

    def _get_todos_by_day(self, day: datetime.date):
        todos: TodosDict = {}

        for tid, todo in self._todos.items():
            eid = todo["reminder_id"] 
            if eid == 0:
                reminderdata = todo["reminder"]
                assert reminderdata is not None
                cycbgn_dtime = reminderdata["cycbgn_dtime"]
                assert cycbgn_dtime is not None
                if cycbgn_dtime.date() == day:
                    todos[tid] = todo
            else:
                day_agenda = self._schedule.agendas_on_date(day)
                if eid in day_agenda:
                    todos[tid] = todo
                    agendas = day_agenda[eid]
                    for agenda in agendas:
                        reminderinfo: ReminderInfo = {
                            "clock_time": agenda.clock,
                            "completed": False
                        }
                        todos[tid]["reminder_infos"].append(reminderinfo)

        return todos

    def open_todo_detail_dlg(self, x: int, y: int, **kwargs: object) -> None:
        dlg_id = "dlgEditTodo"
        dlg_cfg = self._gui.get_customctrlcfg(dlg_id)
        editodo_dlg = EditTodoDialog(self._gui, dlg_cfg)
        editodo_dlg.do_show(self, x, y, **kwargs)

    def _show_page(self, page_name: str):
        for page in self._pages:
            if page.name == page_name:
                self._active_page = page
                self._update_page()
                page.show_page()
            else:
                page.hide_page()

    def _update_page(self):
        assert self._active_page is not None
        page_name = self._active_page.name

        if page_name == "TodayTodo":
            today_todos: TodosDict = {}
            today = datetime.datetime.today()
            for tid, tododata in self._todos.items():
                cycbgn_dtime = tododata["reminder"]["cycbgn_dtime"]
                cycend_dtime = tododata["reminder"]["cycend_dtime"]
                assert cycbgn_dtime is not None
                if tododata["status"] == StatusEnum.ONGOING and cycbgn_dtime <= today:
                    if cycend_dtime is None or cycend_dtime >= today:
                        today_todos[tid] = tododata

            todos = self._get_todos_by_day(today.date())
            today_todos |= todos
            self._active_page.todos = today_todos

    @override
    def process_message(self, idmsg: str, **kwargs: object):
        match idmsg:
            case "ShowMainPage":
                self._main_pages_frame.tkraise()
                self._active_page = None
            case "ShowPage":
                page_name = cast(str, kwargs["page"])
                self._show_page(page_name)
            case "lblTitleToday":
                self._show_page("TodayTodo")
            case "lblNumberToday":
                self._show_page("TodayTodo")
            case "OpenEditTodoDlg":
                # todo_dict = cast(TodoDict, kwargs['todo_dict'])
                x, y = cast(tuple[int, int], kwargs['mousepos'])
                self.open_todo_detail_dlg(x, y, **kwargs)
            case "NewTodo":
                plandata: PlanDataDict = cast(PlanDataDict, kwargs["plandata"])
                reminderdata: ReminderDataDict = cast(ReminderDataDict, kwargs["reminderdata"])
                tid = self._todos_db.add_plan(**plandata)
                _ = self._todos_db.add_reminder(tid, 0, **reminderdata)
                todo = cast(TodoData, kwargs['tododata'])
                self._todos[tid] = todo
                return tid
            case "ModifyTodo":
                todo = cast(Todo, kwargs["todo"])
                
                tododata = todo["data"]
                plandata: PlanDataDict = {
                    "name": tododata["name"],
                    "note": tododata["note"],
                    "tags": tododata["tags"],
                    "iid": None,
                    "fid": tododata["fid"],
                    "reminders": {},
                    "action": ActTyp.NOACTION,
                    "status": tododata["status"],
                    "location": None,
                    "sums": 0
                }

                tid = todo["tid"]
                # _ = self._todos_db.modify_plan(tid, **plandata)
                if eid := tododata["reminder_id"]:
                    reminderdata = tododata["reminder"]
                    if self._todos[tid]["reminder_id"]:
                        _ = self._todos_db.del_reminder(tid, 0)
                        _ = self._todos_db.add_reminder(tid, eid, **reminderdata)
                    else:
                        _ = self._todos_db.modify_reminder(tid, eid, **reminderdata)
                    clock_time = reminderdata["clk_time"]
                    assert clock_time is not None
                    cycbgn_dtime = reminderdata["cycbgn_dtime"]
                    assert cycbgn_dtime is not None
                    if eid in self._schedule.events:
                        _ = self._schedule.modify_event(eid, clock_time, cycbgn_dtime, tododata["name"], 
                            reminderdata["every"], reminderdata["unit"], reminderdata["custom"], reminderdata["cycend_dtime"])
                    else:
                        self._schedule.add_event(eid, tododata["name"], clock_time, reminderdata["every"],
                        reminderdata["unit"], reminderdata["custom"],
                        cycbgn_dtime, reminderdata["cycend_dtime"],
                        ActTyp.DRIPPING_WATER)

                self._todos[tid] = todo["data"]
                self._update_page()

                if self._active_page:
                    self._active_page.refresh_todos()
            case _:
                print(f"TotoTab: undeal message {idmsg} with {kwargs}")
        return True

    @override
    def destroy(self, **kwargs: object):
        """ _summary_
        """
        pass
