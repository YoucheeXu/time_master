#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import datetime
import uuid
import xml.etree.ElementTree as et
# from functools import partial
from typing import Literal
from typing import TypeAlias, TypedDict, Callable, cast, override
import tkinter as tk
from tkinter import ttk, messagebox

from pyutilities.logit import po, pv, pe
from pygui.winbasic import Widget, Container, Dialog, WinBasic
from pygui.tkcontrol import tkControl
from pygui.tkwin import LabelCtrl, EntryCtrl, ButtonCtrl, ComboboxCtrl, ImageBtttonCtrl
from pygui.tkwin import FrameCtrl
from pygui.tkwin import DialogCtrl, tkWin
from pygui.tkcalendar import CalendarCtrl
from pygui.tkscrollpicker import TimeScrollPickerCtrl

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

# class TodoDict(TypedDict):
    # iid: str
    # text: str
    # completed: bool
    # created_at: float
    # note: str
    # reminder_time: float
    # repeat_cycle: str

class TodoDict(PlanDataDict):
    tid: int
    reminder_id: int
    reminder: ReminderDataDict | None

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
        self, parent: tk.Frame, todo_dict: TodoDict, app: "TodoTab",
            show_divider: bool = True) -> None:
        self._parent: tk.Frame = parent
        self._app: TodoTab = app
        self._show_divider: bool = show_divider
        self._todo_dict: TodoDict = todo_dict

        # Core UI containers
        self._wrapper: tk.Frame = tk.Frame(
            parent, bg=COLORS["background"], height=SWIPE_CONFIG["placeholder_height"], width=400
        )
        self._wrapper.pack(fill="x", pady=0)
        self._wrapper.todo_id = todo_dict["tid"]

        self._content_frame: tk.Frame = tk.Frame(
            self._wrapper, bg=COLORS["background"], height=SWIPE_CONFIG["placeholder_height"], width=400
        )
        self._content_frame.place(x=0, y=0, relwidth=1.0)

        # State variables
        self._is_delete_btn_visible: bool = False
        self._editing: bool = False
        self._edit_entry: tk.Entry | None = None

        # Create UI components
        self._create_left_area()
        self._create_right_buttons()
        self._create_delete_button()
        self._create_divider()
        self._bind_events()
        self._update_text_display()

    def _create_left_area(self) -> None:
        self._left_area: tk.Frame = tk.Frame(
            self._content_frame, bg=COLORS["background"], height=SWIPE_CONFIG["placeholder_height"]
        )
        self._left_area.pack(side="left", fill="both", expand=True)
        _ = self._left_area.pack_propagate(False)

        self._checkbox: RoundCheckbutton = RoundCheckbutton(
            self._left_area, callback=self.toggle_completed,
            is_checked=self._todo_dict["status"] == StatusEnum.COMPLETED
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
        _ = self._more_btn.configure(command=lambda: self.open_detail(self._more_btn.winfo_rootx(),
            self._more_btn.winfo_rooty()))
        self._more_btn.pack(side="top", padx=2, pady=5)

        # Edit-mode delete button
        self._edit_delete_btn: tk.Button = tk.Button(
            self._btn_container, text="Delete", font=FONT_CONFIG["small"], bg=COLORS["background"],
            fg=COLORS["danger"], borderwidth=0, width=4, command=self.delete
        )
        if self._app._edit_mode:
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
        if self._app._edit_mode or self._app._editing_todo_id:
            return
        if event.widget in [self._text_container, self._more_btn] or isinstance(event.widget, tk.Canvas):
            return

        self._app._dragging = True
        self._app._drag_start_x = event.x_root
        self._app._drag_start_y = event.y_root
        self._app._current_dragged_item = self._wrapper
        self._app._original_todo_id = self._todo_dict["tid"]
        self._app._current_offset_x = 0
        self._app._current_offset_y = 0
        self._wrapper.lift()
        self._app._drag_type = None

    def _on_drag(self, event: tk.Event) -> None:
        if not self._app._dragging or self._app._current_dragged_item != self._wrapper:
            return

        dx: int = event.x_root - self._app._drag_start_x
        dy: int = event.y_root - self._app._drag_start_y

        # Determine drag type (delete/sort)
        if self._app._drag_type is None:
            if abs(dx) > SWIPE_CONFIG["drag_threshold"]:
                self._app._drag_type = "delete"
                _ = self._wrapper.config(bg=COLORS["danger_bg"])
            elif abs(dy) > SWIPE_CONFIG["drag_threshold"]:
                self._app._drag_type = "sort"
                _ = self._content_frame.config(
                    bg=COLORS["drag_active"], relief="solid", bd=1,
                    highlightbackground=COLORS["drag_border"], highlightthickness=1
                )
                self._app._create_drag_placeholder(self._wrapper)

        # Handle swipe delete
        if self._app._drag_type == "delete":
            self._handle_swipe_delete(dx)
        # Handle drag sort
        elif self._app._drag_type == "sort":
            self._handle_drag_sort(dy)

    def _on_release(self, event: tk.Event) -> None:
        if not self._app._dragging or self._app._current_dragged_item != self._wrapper:
            self._app._reset_drag_state()
            return

        if self._app._drag_type == "delete":
            if self._app._current_offset_x <= SWIPE_CONFIG["delete_threshold"]:
                self.delete()
            else:
                self._animate_swipe_back()
        elif self._app._drag_type == "sort":
            _ = self._content_frame.config(
                bg=COLORS["background"], relief="flat", bd=0, highlightthickness=0
            )
            self._app._finalize_drag_sort()

        self._app._reset_drag_state()

    def _on_leave(self, event: tk.Event) -> None:
        if self._app._dragging and self._app._current_dragged_item == self._wrapper:
            if self._app._drag_type == "sort":
                _ = self._content_frame.config(
                    bg=COLORS["background"], relief="flat", bd=0, highlightthickness=0
                )
            self._app._reset_drag_state()
            if self._app._drag_type == "delete" and self._app._current_offset_x > SWIPE_CONFIG["delete_threshold"]:
                self._animate_swipe_back()

    def _on_text_click(self, event: tk.Event) -> str:
        if self._app._edit_mode or self._app._editing_todo_id:
            return "break"

        self._app._reset_drag_state()
        self._switch_to_edit_mode()
        return "break"

    def _handle_swipe_delete(self, dx: int) -> None:
        offset_x: int = dx
        if offset_x > 0:
            offset_x = 0
        elif offset_x < SWIPE_CONFIG["max_swipe_distance"]:
            self.delete()
            self._app._reset_drag_state()
            return

        self._app._current_offset_x = offset_x
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

    def _handle_drag_sort(self, dy: int) -> None:
        self._app._current_offset_y = dy
        self._wrapper.place(y=self._wrapper.winfo_y() + dy)

        # Find nearest todo item
        todo_items: list[tk.Frame] = [w for w in self._app._todo_container.winfo_children() if hasattr(w, "todo_id")]
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

        if nearest_index != -1 and nearest_index != self._app._last_nearest_index:
            self._app._move_drag_placeholder(nearest_index)
            self._app._last_nearest_index = nearest_index

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
        if self._app._editing_todo_id and self._app._editing_todo_id != self._todo_dict["iid"]:
            self._app.cancel_edit()

        if self._app._editing_todo_id == self._todo_dict["iid"]:
            return

        # Clear text container
        for widget in self._text_container.winfo_children():
            widget.destroy()

        self._app._editing_todo_id = self._todo_dict["tid"]

        # Create edit entry
        original_width: int = int((400 - 100) / 8)
        new_width: int = int(original_width * (2/3))

        self._edit_entry = tk.Entry(
            self._text_container, font=(FONT_CONFIG["body"][0], FONT_CONFIG["body"][1], "bold"),
            bg="white", fg=COLORS["primary_text"], relief="solid", bd=1,
            highlightthickness=1, highlightcolor=COLORS["accent"], width=new_width
        )
        self._edit_entry.pack(side="left", fill="x", expand=False, padx=5, pady=10)
        self._edit_entry.insert(0, self._todo_dict["name"])
        self._edit_entry.select_range(0, tk.END)
        self._edit_entry.focus_force()
        self._app._current_edit_entry = self._edit_entry

        # Bind save/cancel
        _ = self._edit_entry.bind("<Return>", lambda e: self._save_edit())
        _ = self._edit_entry.bind("<FocusOut>", lambda e: self._save_edit())
        _ = self._edit_entry.bind("<Escape>", lambda e: self.cancel_edit())

    def _save_edit(self) -> None:
        if not self._edit_entry:
            return

        new_text: str = self._edit_entry.get().strip()
        if not new_text:
            new_text = "Unnamed todo"

        # Update data
        self._todo_dict["name"] = new_text
        # self._app.save_todos()

        # Exit edit mode
        self._app._editing_todo_id = None
        self._app._current_edit_entry = None

        # Refresh display
        self._update_text_display()
        self._app.update_stats()

    def cancel_edit(self) -> None:
        self._app._editing_todo_id = None
        self._app._current_edit_entry = None
        self._update_text_display()

    def _update_text_display(self) -> None:
        # Clear text container
        for widget in self._text_container.winfo_children():
            widget.destroy()

        # Text styling
        text_color = COLORS["secondary_text"] \
            if self._todo_dict["status"] == StatusEnum.COMPLETED else COLORS["primary_text"]
        strike: str = "overstrike" if self._todo_dict["status"] == StatusEnum.COMPLETED else "normal"

        # Main text frame
        text_frame: tk.Frame = tk.Frame(self._text_container, bg=COLORS["background"])
        text_frame.pack(side="left", fill="both", expand=True, padx=5, pady=2)

        # Todo title
        name_label: tk.Label = tk.Label(
            text_frame, text=self._todo_dict["name"],
            font=(FONT_CONFIG["body"][0], FONT_CONFIG["body"][1], "bold", strike),
            bg=COLORS["background"], fg=text_color, anchor="w", wraplength=280, justify="left"
        )
        name_label.pack(side="top", fill="x", anchor="w")

        # Note text
        note_label: tk.Label = tk.Label(
            text_frame, text=self._todo_dict.get("note", ""),
            font=(FONT_CONFIG["small"][0], FONT_CONFIG["small"][1], strike),
            bg=COLORS["background"], fg=COLORS["secondary_text"], anchor="w", wraplength=280, justify="left"
        )
        if self._todo_dict.get("note", "").strip():
            note_label.pack(side="top", fill="x", anchor="w", pady=(0, 1))
        else:
            note_label.pack_forget()

        # Reminder info
        reminder_info: str = self._app.format_reminder_info(self._todo_dict)
        is_expired: bool = self._app.is_reminder_expired(self._todo_dict)
        reminder_color: str = COLORS["danger"] if is_expired else COLORS["secondary_text"]

        reminder_label: tk.Label = tk.Label(
            text_frame, text=reminder_info,
            font=(FONT_CONFIG["small"][0], FONT_CONFIG["small"][1], strike),
            bg=COLORS["background"], fg=reminder_color, anchor="w", wraplength=280, justify="left"
        )
        reminder_label.pack(side="top", fill="x", anchor="w")

        # Bind edit events
        for widget in [text_frame, name_label, note_label, reminder_label]:
            _ = widget.bind("<Button-1>", self._on_text_click)
            _ = widget.bind("<B1-Motion>", lambda e: "break")

    # Public Methods
    def toggle_completed(self) -> None:
        if self._app._editing_todo_id == self._todo_dict["tid"]:
            self.cancel_edit()
        if self._todo_dict["status"] == StatusEnum.COMPLETED:
           self._todo_dict["status"] = StatusEnum.ONGOING
        else:
            self._todo_dict["status"] = StatusEnum.COMPLETED
        self._checkbox.set_checked(self._todo_dict["status"] == StatusEnum.COMPLETED)
        # self._app.save_todos()
        self._update_text_display()
        self._app.update_stats()

    def delete(self) -> None:
        if self._app._editing_todo_id == self._todo_dict["tid"]:
            self._app._editing_todo_id = None
            self._app._current_edit_entry = None

        # Confirm deletion in edit mode
        if self._app._edit_mode and not messagebox.askyesno("Confirmation", "Are you sure to delete this todo?"):
            return

        self._app.delete_todo_by_id(self._todo_dict["tid"])

    def open_detail(self, x: int, y: int) -> None:
        if self._app._editing_todo_id:
            self._app.cancel_edit()
        self._app.open_todo_detail_dlg(x, y, todo_dict=self._todo_dict)

    def update_edit_mode(self) -> None:
        if self._app._edit_mode:
            self._edit_delete_btn.pack(side="top", padx=2, pady=2)
        else:
            self._edit_delete_btn.pack_forget()

    def update_data(self, updated_data: TodoDict) -> None:
        self._todo_dict = updated_data
        self._checkbox.set_checked(updated_data["status"] == StatusEnum.COMPLETED)
        self._update_text_display()


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
        plandata = default_plan_data()
        self._todo_dict: TodoDict = {
            **plandata,
            "tid": -1,
            "reminder_id": -1,
            "reminder": None,
        }
        super().__init__(app, dlg_cfg)

    @override
    def _beforego(self, **kwargs: object):
        self._todo_dict = cast(TodoDict, kwargs["todo_dict"])
        entry_name = cast(EntryCtrl, self._app.get_control("txtNameEditTodo"))
        entry_name.set_val(self._todo_dict["name"])
        entry_note = cast(EntryCtrl, self._app.get_control("txtNoteEditTodo"))
        entry_note.set_val(self._todo_dict["note"])

        if self._todo_dict["reminder_id"] > 0:
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
        entry_name = cast(EntryCtrl, self._app.get_control("txtNameEditTodo"))
        name = entry_name.get_val()
        self._todo_dict["name"] = name
        entry_note = cast(EntryCtrl, self._app.get_control("txtNoteEditTodo"))
        note = entry_note.get_val()
        self._todo_dict["note"] = note

        date: datetime.date | None = None
        lbl_date = cast(LabelCtrl, self.get_control("lblSelDateEditTodo"))
        date_str = lbl_date.get_text()
        if date_str:
            date = datetime.datetime.strptime(date_str, "%B %d, %Y\t%A").date()

        time: datetime.time | None = None
        lbl_time = cast(LabelCtrl, self.get_control("lblSelTimeEditTodo"))
        time_str = lbl_time.get_text()
        if time_str:
            time = datetime.datetime.strptime(time_str, "%H:%M").time()

        if date or time:
            if self._todo_dict["reminder_id"] <= 0:
                self._todo_dict["reminder_id"] = uuid.uuid4().int
            reminder = default_reminder_data()
            reminder["clk_time"] = time
            date = date if date else datetime.datetime.now().date()
            time = time if time else datetime.time(0, 0)
            reminder["cycbgn_dtime"] = datetime.datetime.combine(date, time)
            self._todo_dict["reminder"] = reminder

        pv(self._todo_dict["reminder"])
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
                    lbl_time = cast(LabelCtrl, self.get_control("lblSelTimeEditTodo"))
                    time = cast(datetime.time, kwargs['val'])
                    # date_text = f"{date.year}年{date.month:02d}月{date.day:02d}日"
                    time_text = time.strftime("%H:%M")
                    # print(f"select date: {date_text}")
                    lbl_time.set_text(time_text)
                case _:
                    return super().process_message(idmsg, **kwargs)
            return True
        return super().process_message(idmsg, **kwargs)


class BaseTodoPage(Container):
    """Base class for all Todo pages (shared UI structure).

    This class provides a reusable UI template for all four todo pages, including
    a title bar with a back button to TodoTab and a content frame for page-specific
    widgets. All concrete pages inherit from this class.

    Args:
        parent: Parent widget (root window or container frame)
        controller: Main application instance for frame navigation
        page_title: Display title for the page's title bar
    """
    def __init__(self, parent: tk.Frame, owner: Container, page_title: str) -> None:
        self._page_title: str = page_title
        super().__init__()
        self._owner = owner

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

    @property
    def frame(self):
        return self._main_frame

    def _back_to_todo_tab(self) -> None:
        """Navigate back to the main TodoTab frame.

        Triggers the main app's frame switching method to display TodoTab.
        """
        assert self._owner is not None
        _ = self._owner.process_message("ShowPage", page="MainTodo")

    def _toggle_edit_mode(self):
        pass


class TodayTodoPage(BaseTodoPage):
    def __init__(self, parent: tk.Frame, owner: Container):
        super().__init__(parent, owner, "Today")

        self._todos: list[TodoDict] = []
        self._edit_mode: bool = False
        self._editing_todo_id: int | None = None
        self._current_edit_entry: tk.Entry | None = None

        self._dragging: bool = False
        self._drag_type: Literal["delete", "sort"] | None = None
        self._drag_start_x: int = 0
        self._drag_start_y: int = 0
        self._current_dragged_item: tk.Frame | None = None
        self._current_offset_x: int = 0
        self._current_offset_y: int = 0
        self._drag_placeholder: tk.Frame | None = None
        self._original_todo_id: int | None = None
        self._last_nearest_index: int = -1

        self._stats_label: tk.Label | None = None
        self._canvas: tk.Canvas | None = None
        self._todo_container: tk.Frame | None = None
        self._todo_entry: tk.Entry | None = None
        self._placeholder_text: str = "Add new todo..."
        self._todo_items: list[TodoItem] = []

        # Load data
        # self._todos = self.load_todos()

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

    # def load_todos(self) -> list[TodoDict]:
        # todos: list[TodoDict] = []
        # if os.path.exists(self._data_file):
            # try:
                # with open(self._data_file, "r", encoding="utf-8") as f:
                    # raw_todos = cast(list[TodoDict], json.load(f))
                    # for todo in raw_todos:
                        # Ensure all fields exist
                        # todo_dict: TodoDict = {
                            # "iid": todo.get("iid", str(uuid.uuid4())),
                            # "text": todo.get("text", ""),
                            # "completed": todo.get("completed", False),
                            # "created_at": todo.get("created_at", datetime.now().timestamp()),
                            # "note": todo.get("note", ""),
                            # "reminder_time": todo.get("reminder_time"),
                            # "repeat_cycle": todo.get("repeat_cycle", "No repeat")
                        # }
                        # todos.append(todo_dict)
            # except Exception as e:
                # print(f"Error loading todos: {e}")
                # todos = []
        # return todos

    # def save_todos(self) -> None:
        # try:
            # with open(self._data_file, "w", encoding="utf-8") as f:
                # json.dump(self._todos, f, ensure_ascii=False, indent=2)
        # except Exception as e:
            # print(f"Error saving todos: {e}")
            # _ = messagebox.showerror("Error", "Failed to save todo data!")

    def get_todo_time_group(self, todo_dict: TodoDict) -> Literal["morning", "afternoon", "evening", "no_reminder"]:
        if todo_dict["reminder_id"] <= 0:
            return "no_reminder"

        reminder = todo_dict["reminder"]
        assert reminder and reminder["clk_time"]
        # reminder_dt = datetime.fromtimestamp(todo_dict["reminder_time"])
        reminder_time = reminder["clk_time"]

        if TIME_GROUPS["morning"]["start"] <= reminder_time < TIME_GROUPS["morning"]["end"]:
            return "morning"
        elif TIME_GROUPS["afternoon"]["start"] <= reminder_time < TIME_GROUPS["afternoon"]["end"]:
            return "afternoon"
        else:
            return "evening"

    def group_todos_by_time(self) -> dict[str, list[TodoDict]]:
        grouped_todos: dict[str, list[TodoDict]] = {
            "morning": [], "afternoon": [], "evening": [], "no_reminder": []
        }

        # Sort by creation time (newest first)
        # sorted_todos = sorted(self._todos, key=lambda x: x["created_at"], reverse=True)
        sorted_todos = self._todos

        for todo in sorted_todos:
            group_key = self.get_todo_time_group(todo)
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
        total = len(self._todos)
        completed = sum(1 for todo in self._todos if todo["status"] == StatusEnum.COMPLETED)
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
        self._editing_todo_id = None
        self._current_edit_entry = None

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

    def is_reminder_expired(self, todo_dict: TodoDict) -> bool:
        if todo_dict["reminder_id"] <= 0:
            return False

        current_ts: float = datetime.datetime.now().timestamp()
        if todo_dict.get("repeat_cycle", "No repeat") != "No repeat":
            return False
        return todo_dict["reminder_time"] < current_ts

    def format_reminder_info(self, todo_dict: TodoDict) -> str:
        repeat_icon: str = "🔄"
        reminder_str: str = ""

        if todo_dict["reminder_id"] > 0:
            dt = datetime.datetime.fromtimestamp(todo_dict["reminder_time"])
            reminder_str = dt.strftime("%Y-%m-%d %H:%M")
        else:
            reminder_str = ""

        repeat_cycle = todo_dict.get("repeat_cycle", "No repeat")

        if reminder_str:
            if repeat_cycle != "No repeat":
                return f"Reminder: {reminder_str} {repeat_icon} {repeat_cycle}"
            else:
                return f"Reminder: {reminder_str}"
        else:
            if repeat_cycle != "No repeat":
                return f"{repeat_icon} {repeat_cycle}"
            else:
                return "No reminder"

    def toggle_edit_mode(self) -> None:
        self._edit_mode = not self._edit_mode

        # Update edit button text
        if self._edit_btn:
            _ = self._edit_btn.config(text="Done" if self._edit_mode else "Edit")

        # Cancel active edits
        if self._editing_todo_id:
            self.cancel_edit()

        # Update todo items
        for todo_item in self._todo_items:
            todo_item.update_edit_mode()

        # Refresh scroll region
        assert self._todo_container is not None
        self._todo_container.update_idletasks()
        if self._canvas:
            _ = self._canvas.configure(scrollregion=self._canvas.bbox("all"))

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
        # hid = self._todos_db.add_plan(**plandata)
        hid = int(uuid.uuid4())
        new_todo: TodoDict = {
            **plandata,
            # "iid": str(uuid.uuid4()),
            "tid": hid,
            "reminder_id": -1,
            "reminder": None,
            # "created_at": datetime.now().timestamp(),
        }

        # Save and refresh
        self._todos.append(new_todo)
        # self.save_todos()
        self.render_todo_list()
        self.update_stats()

        # Reset input
        self._todo_entry.delete(0, tk.END)
        self._todo_entry.insert(0, self._placeholder_text)
        _ = self._todo_entry.config(fg=COLORS["placeholder"])

    def delete_todo_by_id(self, todo_id: int) -> None:
        # Remove from list
        for idx, todo in enumerate(self._todos):
            if todo["iid"] == todo_id:
                del self._todos[idx]
                break

        # Save and refresh
        # self.save_todos()
        self.render_todo_list()
        self.update_stats()

    def update_todo_detail(self, updated_data: TodoDict) -> None:
        # Update todo in list
        for idx, todo in enumerate(self._todos):
            if todo["iid"] == updated_data["iid"]:
                self._todos[idx] = updated_data
                break

        # Save and refresh UI
        # self.save_todos()
        for todo_item in self._todo_items:
            if todo_item._todo_dict["tid"] == updated_data["tid"]:
                todo_item.update_data(updated_data)
                break
        self.update_stats()

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
            if todo_item._todo_dict["tid"] == todo_id:
                todo_item._save_edit()
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

    def _finalize_drag_sort(self) -> None:
        """Complete drag sorting and update todo order"""
        if not self._drag_placeholder or not self._original_todo_id:
            return

        # Get current order of todo items
        todo_items: list[tk.Frame] = [w for w in self._todo_container.winfo_children() if hasattr(w, "todo_id")]
        placeholder_index: int = todo_items.index(self._drag_placeholder) if self._drag_placeholder in todo_items else -1

        if placeholder_index == -1:
            return

        # Find original todo
        original_todo = next((t for t in self._todos if t["iid"] == self._original_todo_id), None)
        if not original_todo:
            return

        # Remove original todo from list
        self._todos = [t for t in self._todos if t["iid"] != self._original_todo_id]

        # Insert at new position
        self._todos.insert(placeholder_index, original_todo)

        # Save and re-render
        # self.save_todos()
        self.render_todo_list()

    def _reset_drag_state(self) -> None:
        """Reset all drag-related state variables"""
        self._dragging = False
        self._drag_type = None
        self._current_dragged_item = None
        self._current_offset_x = 0
        self._current_offset_y = 0
        self._original_todo_id = None
        self._last_nearest_index = -1

        # Destroy drag placeholder
        if self._drag_placeholder:
            self._drag_placeholder.destroy()
            self._drag_placeholder = None


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
        # self._parent: tk.Misc = parent
        self._gui: tkWin = cast(tkWin, owner)
        self._gui.filter_message(self.process_message)
        self._schedule: Schedule = schedule

        self._todos_db: TimeDatabase = TimeDatabase()
        self._todos: list[TodoDict] = []

        self._pages: dict[str, tk.Frame] = {}

        parent = cast(tk.Frame, cast(tkControl, self._gui.get_control("tabTodo")).control)
        self._pages["TodayTodo"] = TodayTodoPage(parent, self).frame
        # self._pages["PlannedTodo"] = PlannedTodoPage(parent, self)

        for _, frame in self._pages.items():
            frame.grid(row=0, column=0, sticky="nsew")
        _ = parent.grid_rowconfigure(0, weight=1)
        _ = parent.grid_columnconfigure(0, weight=1)

        self._pages["MainTodo"] = cast(tk.Frame, cast(tkControl, self._gui.get_control("frmMainTodo")).control)

        frame = cast(tk.Frame, cast(tkControl, self._gui.get_control("frmTodayTodo")).control)
        _ = frame.bind("<Button-1>", lambda e: self._show_page("TodayTodo"))

        self._pages["MainTodo"].tkraise()

    def _open(self, db_path: str):
        """_summary_
        Args:
            db_path (type): _description_
        """
        return self._todos_db.open(db_path)

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
        for pid, plandata in plans.items():
            eid = 0
            reminderdata = None
            if len(plandata["reminders"].keys()) > 0:
                eid = list(plandata["reminders"].keys())[0]
                reminderdata = plandata["reminders"][eid]
                if clock_time := reminderdata["clk_time"]:
                    self._schedule.add_event(eid, plandata["name"], clock_time, reminderdata["every"],
                        reminderdata["unit"], reminderdata["custom"], reminderdata["cycend_dtime"],
                        ActTyp.LOCK_SCREEN)
            todo: TodoDict = {
                **plandata,
                "tid": pid,
                "reminder_id": eid,
                "reminder": reminderdata
            }
            self._todos.append(todo)

    def open_todo_detail_dlg(self, x: int, y: int, **kwargs: object) -> None:
        dlg_id = "dlgEditTodo"
        dlg_cfg = self._gui.get_customctrlcfg(dlg_id)
        editodo_dlg = EditTodoDialog(self._gui, dlg_cfg)
        editodo_dlg.do_show(self, x, y, **kwargs)

    def _show_page(self, page_name: str):
        page = self._pages[page_name]
        page.tkraise()

    @override
    def process_message(self, idmsg: str, **kwargs: object):
        match idmsg:
            case "ShowPage":
                page_name = cast(str, kwargs["page"])
                self._show_page(page_name)
            case "lblTitleToday":
                self._show_page("TodayTodo")
            case "lblNumberToday":
                self._show_page("TodayTodo")
            case _:
                print(f"undeal message {idmsg}")
        return True
