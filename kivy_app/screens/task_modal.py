"""Task modal for add/edit task."""

import threading
from datetime import datetime, timedelta, timezone

from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView

from screens.widgets import (
    C_BORDER,
    C_CREAM,
    C_INK,
    C_WHITE,
    DropdownSpinner,
    OutlineButton,
    StyledButton,
    StyledInput,
    StyledTextArea,
    label,
    show_toast,
    spacer,
)

CAT_OPTIONS = [
    ("general", "General"), ("work", "Work"), ("personal", "Personal"),
    ("health", "Health"), ("study", "Study"),
]
PRI_OPTIONS = [("low", "Low"), ("medium", "Medium"), ("high", "High")]


class TaskModal(Popup):
    def __init__(self, auth, on_success, task=None, lang=None, **kwargs):
        self.auth = auth
        self.on_success = on_success
        self.task = task
        self.lang = lang
        super().__init__(
            title=(lang.t("editTask") if task else lang.t("addNewTask")) if lang else ("Edit Task" if task else "New Task"),
            title_size=sp(17),
            title_color=C_INK,
            content=self._build_content(),
            size_hint=(0.93, None),
            height=dp(560),
            background="",
            background_color=(0.97, 0.95, 0.88, 1),
            separator_color=C_BORDER,
            overlay_color=(0, 0, 0, 0.55),
            auto_dismiss=True,
            **kwargs,
        )
        with self.canvas.before:
            Color(0, 0, 0, 0.18)
            RoundedRectangle(pos=(self.x + dp(4), self.y - dp(4)), size=self.size, radius=[dp(22)])
            Color(0.97, 0.95, 0.88, 1)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(22)])
        self.bind(pos=self._upd_bg, size=self._upd_bg)

    def _upd_bg(self, *_):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(0, 0, 0, 0.18)
            RoundedRectangle(pos=(self.x + dp(4), self.y - dp(4)), size=self.size, radius=[dp(22)])
            Color(0.97, 0.95, 0.88, 1)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(22)])

    def _t(self, key, fallback):
        return self.lang.t(key) if self.lang else fallback

    def _build_content(self):
        scroll = ScrollView(do_scroll_x=False)
        box = BoxLayout(orientation="vertical", spacing=dp(10), padding=[dp(12), dp(6), dp(12), dp(10)], size_hint_y=None)
        box.bind(minimum_height=box.setter("height"))
        with box.canvas.before:
            Color(*C_CREAM)
            bg = RoundedRectangle(pos=box.pos, size=box.size, radius=[dp(16)])
        box.bind(pos=lambda _i, v: setattr(bg, "pos", v), size=lambda _i, v: setattr(bg, "size", v))

        label_color = (0.18, 0.15, 0.11, 1)

        box.add_widget(label(self._t("taskTitle", "Task Title"), bold=True, height=dp(20), font_size=sp(12), color=label_color))
        self._title = StyledInput(hint_text=self._t("taskTitlePlaceholder", "Water the plants"), size_hint_y=None, height=dp(48))
        if self.task:
            self._title.text = self.task.get("title", "")
        box.add_widget(self._title)

        box.add_widget(label(self._t("descriptionOptional", "Description (optional)"), bold=True, height=dp(20), font_size=sp(12), color=label_color))
        self._desc = StyledTextArea(hint_text=self._t("descriptionPlaceholder", "Add any extra details here..."), size_hint_y=None, height=dp(72))
        if self.task:
            self._desc.text = self.task.get("description", "") or ""
        box.add_widget(self._desc)

        cp_row = BoxLayout(size_hint_y=None, height=dp(72), spacing=dp(10))
        for attr, label_text, options, default in [
            ("_cat", self._t("category", "Category"), CAT_OPTIONS, self.task.get("category", "general") if self.task else "general"),
            ("_pri", self._t("priority", "Priority"), PRI_OPTIONS, self.task.get("priority", "medium") if self.task else "medium"),
        ]:
            col = BoxLayout(orientation="vertical", spacing=dp(4))
            col.add_widget(label(label_text, bold=True, height=dp(20), font_size=sp(12), color=label_color))
            spinner = DropdownSpinner(options, value=default, size_hint_y=None, height=dp(46))
            setattr(self, attr, spinner)
            col.add_widget(spinner)
            cp_row.add_widget(col)
        box.add_widget(cp_row)

        box.add_widget(label(self._t("timeLimit", "Time Limit"), bold=True, height=dp(20), font_size=sp(12), color=label_color))

        d_def, h_def, m_def = 0, 1, 0
        if self.task:
            secs = self.task.get("time_remaining_seconds", 3600)
            d_def = secs // 86400
            h_def = (secs % 86400) // 3600
            m_def = (secs % 3600) // 60

        time_row = BoxLayout(size_hint_y=None, height=dp(72), spacing=dp(8))
        for attr, hint, default in [
            ("_days", self._t("days", "Days"), str(d_def)),
            ("_hrs", self._t("hours", "Hours"), str(h_def)),
            ("_mins", self._t("minutes", "Minutes"), str(m_def)),
        ]:
            col = BoxLayout(orientation="vertical", spacing=dp(4))
            inp = StyledInput(hint_text=hint, text=default, input_filter="int", size_hint_y=None, height=dp(46))
            setattr(self, attr, inp)
            col.add_widget(inp)
            col.add_widget(label(hint, color=label_color, font_size=sp(10), height=dp(16), halign="center"))
            time_row.add_widget(col)
        box.add_widget(time_row)

        box.add_widget(spacer(dp(4)))
        btns = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(12))
        cancel = OutlineButton(text=self._t("cancel", "Cancel"))
        cancel.bind(on_release=lambda *_: self.dismiss())
        btns.add_widget(cancel)
        self._ok = StyledButton(text=self._t("update", "Update") if self.task else self._t("create", "Create"))
        self._ok.bind(on_release=self._submit)
        btns.add_widget(self._ok)
        box.add_widget(btns)

        scroll.add_widget(box)
        return scroll

    def _submit(self, *_):
        title = self._title.text.strip()
        if not title:
            show_toast("Task title is required", success=False)
            return
        try:
            days = int(self._days.text or 0)
            hrs = int(self._hrs.text or 0)
            mins = int(self._mins.text or 0)
        except ValueError:
            show_toast("Please enter valid numbers for time", success=False)
            return

        secs = days * 86400 + hrs * 3600 + mins * 60
        if secs <= 0:
            show_toast("Please set a time limit", success=False)
            return

        deadline = (datetime.now(timezone.utc) + timedelta(seconds=secs)).isoformat()
        data = {
            "title": title,
            "description": self._desc.text.strip() or None,
            "category": self._cat.value,
            "priority": self._pri.value,
            "deadline": deadline,
            "time_remaining_seconds": secs,
        }
        self._ok.text = self._t("saving", "Saving...")
        threading.Thread(target=self._save, args=(data,), daemon=True).start()

    def _save(self, data):
        try:
            if self.task:
                self.auth.update_task(self.task["id"], data)
                msg = self._t("taskUpdated", "Task updated!")
            else:
                self.auth.create_task(data)
                msg = self._t("taskCreated", "Task created!")
            Clock.schedule_once(lambda _dt: self._done(msg))
        except Exception:
            Clock.schedule_once(lambda _dt: self._err())

    def _done(self, msg):
        show_toast(msg)
        self.dismiss()
        self.on_success()

    def _err(self):
        self._ok.text = self._t("update", "Update") if self.task else self._t("create", "Create")
        show_toast("Could not save task", success=False)
