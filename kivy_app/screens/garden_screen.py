"""
Garden screen.
"""

import threading

from kivy.clock import Clock
from kivy.app import App
from kivy.graphics import Color, Ellipse, Rectangle, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import AsyncImage
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget

from screens.task_modal import TaskModal
from screens.settings_modal import SettingsModal
from screens.widgets import (
    BottomNav,
    C_BLUSH,
    C_BLUSH_BORDER,
    C_BORDER,
    C_CORAL,
    C_CREAM,
    C_FOREST,
    C_INK,
    C_INK_SOFT,
    C_LEAF,
    C_MINT,
    C_WHITE,
    FLOWER_POSITIONS,
    FlowerWidget,
    GardenPanel,
    HeaderBar,
    LoadingSpinner,
    OutlineButton,
    Pill,
    RoundedBox,
    StyledButton,
    calculate_time_remaining,
    format_time_remaining,
    get_task_status,
    growth_stage,
    label,
    palette_for,
    priority_color,
    section_heading,
    show_toast,
    spacer,
)


class GardenScreen(Screen):
    def __init__(self, auth, lang, sm, **kwargs):
        super().__init__(**kwargs)
        self.auth = auth
        self.lang = lang
        self.sm = sm
        self.tasks = []
        self._flower_widgets = {}
        self._timer_event = None
        self._notif_event = None
        self._notified_tasks = set()
        self._build()

    def _build(self):
        self.clear_widgets()
        t = self.lang.t

        root = BoxLayout(orientation="vertical")
        with root.canvas.before:
            Color(*C_CREAM)
            self._bg = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=lambda _i, v: setattr(self._bg, "pos", v))
        root.bind(size=lambda _i, v: setattr(self._bg, "size", v))

        header = HeaderBar()

        left = BoxLayout(spacing=dp(10))
        icon_wrap = BoxLayout(size_hint=(None, 1), width=dp(44))
        icon_inner = FloatLayout(size_hint=(None, 1), width=dp(44))
        with icon_inner.canvas.before:
            Color(*C_MINT)
            self._icon_ellipse = Ellipse(size=(dp(38), dp(38)))

        def _upd_icon(inst, _val):
            self._icon_ellipse.pos = (
                inst.x + (inst.width - dp(38)) / 2,
                inst.y + (inst.height - dp(38)) / 2,
            )
            self._icon_ellipse.size = (dp(38), dp(38))

        icon_inner.bind(pos=_upd_icon, size=_upd_icon)
        avatar_url = (self.auth.user or {}).get("avatar_url")
        if avatar_url:
            avatar_view = AsyncImage(source=avatar_url, size_hint=(1, 1), allow_stretch=True, keep_ratio=False)
        else:
            avatar_view = Label(text=self._avatar_text(), font_size=sp(14), bold=True, color=C_INK, size_hint=(1, 1))
        avatar_btn = Button(
            text="",
            background_normal="",
            background_color=(0, 0, 0, 0),
            size_hint=(1, 1),
        )
        avatar_btn.bind(on_release=self._open_settings)
        icon_inner.add_widget(avatar_view)
        icon_inner.add_widget(avatar_btn)
        icon_wrap.add_widget(icon_inner)
        left.add_widget(icon_wrap)

        name_col = BoxLayout(orientation="vertical")
        username = self.auth.user.get("username", "") if self.auth.user else ""
        self._title_lbl = Label(text=self.lang.garden_title(username), font_size=sp(15), bold=True, color=C_INK, halign="left")
        self._title_lbl.bind(size=lambda i, v: setattr(i, "text_size", (v[0], None)))
        self._count_lbl = Label(text=f"0 {t('flowersBloomin')}", font_size=sp(11), color=C_INK_SOFT, halign="left")
        self._count_lbl.bind(size=lambda i, v: setattr(i, "text_size", (v[0], None)))
        name_col.add_widget(self._title_lbl)
        name_col.add_widget(self._count_lbl)
        left.add_widget(name_col)
        header.add_widget(left)

        right = BoxLayout(size_hint=(None, 1), width=dp(120), spacing=dp(4))
        self._lang_btn = Button(
            text="PT" if self.lang.language == "en" else "EN",
            size_hint=(None, 1),
            width=dp(38),
            background_normal="",
            background_color=(0, 0, 0, 0),
            color=C_INK_SOFT,
            font_size=sp(12),
        )
        self._lang_btn.bind(on_release=self._toggle_lang)
        right.add_widget(self._lang_btn)
        logout_btn = Button(
            text=t("logout"),
            size_hint=(None, 1),
            width=dp(74),
            background_normal="",
            background_color=(0, 0, 0, 0),
            color=C_INK_SOFT,
            font_size=sp(12),
        )
        logout_btn.bind(on_release=self._logout)
        right.add_widget(logout_btn)
        header.add_widget(right)
        root.add_widget(header)

        scroll = ScrollView(do_scroll_x=False)
        self._body = BoxLayout(orientation="vertical", padding=[dp(14), dp(10), dp(14), dp(80)], spacing=dp(12), size_hint_y=None)
        self._body.bind(minimum_height=self._body.setter("height"))

        self._garden_panel = GardenPanel()
        self._body.add_widget(self._garden_panel)

        tasks_row = BoxLayout(size_hint_y=None, height=dp(44))
        self._active_lbl = Label(text=t("activeTasks"), font_size=sp(17), bold=True, color=C_INK, halign="left")
        self._active_lbl.bind(size=lambda i, v: setattr(i, "text_size", (v[0], None)))
        tasks_row.add_widget(self._active_lbl)
        add_btn = StyledButton(text=f"+ {t('addTask')}", size_hint=(None, 1), width=dp(120))
        add_btn.bind(on_release=lambda *_: self._open_modal(None))
        tasks_row.add_widget(add_btn)
        self._body.add_widget(tasks_row)

        self._spinner = LoadingSpinner()
        self._body.add_widget(self._spinner)
        self._spinner.start()

        self._tasks_box = BoxLayout(orientation="vertical", spacing=dp(10), size_hint_y=None)
        self._tasks_box.bind(minimum_height=self._tasks_box.setter("height"))
        self._body.add_widget(self._tasks_box)

        scroll.add_widget(self._body)
        root.add_widget(scroll)
        root.add_widget(BottomNav(current="garden", on_navigate=self._navigate, lang=self.lang))
        self.add_widget(root)

    def on_enter(self, *_):
        if self.tasks:
            self._render(self.tasks)
        self._load_tasks()
        if self._timer_event:
            self._timer_event.cancel()
        if self._notif_event:
            self._notif_event.cancel()
        self._timer_event = Clock.schedule_interval(self._tick, 60)
        self._notif_event = Clock.schedule_interval(self._check_notifs, 60)

    def on_leave(self, *_):
        for ev in (self._timer_event, self._notif_event):
            if ev:
                ev.cancel()
        self._timer_event = None
        self._notif_event = None

    def _load_tasks(self):
        self._spinner.start()
        threading.Thread(target=self._fetch, daemon=True).start()

    def _fetch(self):
        try:
            tasks = self.auth.get_tasks()
            Clock.schedule_once(lambda _dt: self._render(tasks))
        except Exception:
            Clock.schedule_once(lambda _dt: show_toast("Could not load tasks", success=False))

    def _render(self, tasks):
        self._spinner.stop()
        self._spinner.text = ""
        self.tasks = tasks
        active = [task for task in tasks if get_task_status(task) == "active"]
        completed = [task for task in tasks if task["status"] == "completed"]
        expired = [task for task in tasks if get_task_status(task) == "expired"]

        self._count_lbl.text = f"{len(completed)} {self.lang.t('flowersBloomin')}"
        self._rebuild_garden(active, completed, expired)
        self._rebuild_cards(active, completed)

    def _rebuild_garden(self, active, completed, expired):
        self._garden_panel.clear_widgets()
        self._flower_widgets.clear()

        all_shown = active[:5] + completed[:5] + expired[:2]
        if not all_shown:
            lbl = Label(
                text=f"Garden\n{self.lang.t('gardenWaiting')}\n{self.lang.t('addTasksToGrow')}",
                font_size=sp(13),
                color=C_INK_SOFT,
                halign="center",
                valign="middle",
                size_hint=(1, 1),
            )
            lbl.bind(size=lambda i, v: setattr(i, "text_size", v))
            self._garden_panel.add_widget(lbl)
            return

        for idx, task in enumerate(all_shown[:8]):
            status = get_task_status(task)
            stage = "wilted" if status == "expired" else "blooming" if status == "completed" else growth_stage(task)
            petal, center = palette_for(task["id"])
            flower = FlowerWidget(stage=stage, petal_color=petal, center_color=center, petal_count=6)
            self._garden_panel.add_widget(flower)
            rx, ry = FLOWER_POSITIONS[idx % len(FLOWER_POSITIONS)]
            Clock.schedule_once(lambda _dt, w=flower, x=rx, y=ry: self._place(w, x, y), 0)
            self._flower_widgets[task["id"]] = flower

    def _place(self, widget, rx, ry):
        panel = self._garden_panel
        grass_top = panel.y + panel.height * 0.42
        grass_bot = panel.y
        plant_y = grass_bot + ry * (grass_top - grass_bot)
        widget.pos = (panel.x + rx * panel.width - widget.width / 2, plant_y)

    def _rebuild_cards(self, active, completed):
        self._tasks_box.clear_widgets()
        if not active:
            empty = RoundedBox(size_hint_y=None, height=dp(72), orientation="vertical", padding=[dp(16), dp(16)])
            empty.add_widget(label(self.lang.t("noActiveTasks"), color=C_INK_SOFT, halign="center"))
            self._tasks_box.add_widget(empty)

        for task in active:
            self._tasks_box.add_widget(self._task_card(task))

        if completed:
            self._tasks_box.add_widget(spacer(dp(4)))
            self._tasks_box.add_widget(section_heading(self.lang.t("completedTasks")))
            for task in completed[:5]:
                self._tasks_box.add_widget(self._completed_card(task))

    def _task_card(self, task):
        time_left = calculate_time_remaining(task["deadline"])
        urgent = time_left < 3600
        stage = growth_stage(task)
        has_desc = bool(task.get("description"))
        card_h = dp(116) + (dp(18) if has_desc else 0)

        card = RoundedBox(
            orientation="horizontal",
            bg_color=C_BLUSH if urgent else C_WHITE,
            border_color=C_BLUSH_BORDER if urgent else C_BORDER,
            size_hint_y=None,
            height=card_h,
            padding=[dp(10), dp(10)],
            spacing=dp(10),
        )

        petal, center = palette_for(task["id"])
        card.add_widget(FlowerWidget(stage=stage, petal_color=petal, center_color=center, size=(dp(62), dp(62))))

        info = BoxLayout(orientation="vertical", spacing=dp(3))
        title_lbl = Label(text=task["title"], font_size=sp(14), bold=True, color=C_INK, halign="left", valign="middle", size_hint_y=None, height=dp(26))
        title_lbl.bind(size=lambda i, v: setattr(i, "text_size", (v[0], None)))
        info.add_widget(title_lbl)

        if has_desc:
            info.add_widget(label(task["description"], font_size=sp(11), color=C_INK_SOFT, height=dp(18)))

        meta = BoxLayout(size_hint_y=None, height=dp(26), spacing=dp(6))
        meta.add_widget(Label(
            text=f"Time: {format_time_remaining(time_left)}",
            font_size=sp(11),
            color=C_CORAL if urgent else C_INK_SOFT,
            size_hint=(None, 1),
            width=dp(98),
            halign="left",
        ))
        meta.add_widget(Pill(text=task.get("category", "general").capitalize(), bg_color=C_MINT, text_color=C_FOREST))
        priority = task.get("priority", "medium")
        meta.add_widget(Label(
            text=priority.capitalize(),
            font_size=sp(10),
            color=priority_color(priority),
            size_hint=(None, 1),
            width=dp(64),
            halign="left",
        ))
        meta.add_widget(Widget())
        info.add_widget(meta)

        btns = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(6))
        btns.add_widget(Widget())
        done_btn = StyledButton(text="Done", bg=C_LEAF, size_hint=(None, 1), width=dp(80))
        done_btn.bind(on_release=lambda *_args, tid=task["id"]: self._complete_task(tid))
        btns.add_widget(done_btn)

        edit_btn = OutlineButton(text="Edit", size_hint=(None, 1), width=dp(68))
        edit_btn.bind(on_release=lambda *_args, tk=task: self._open_modal(tk))
        btns.add_widget(edit_btn)

        del_btn = Button(
            text="Del",
            font_size=sp(12),
            size_hint=(None, 1),
            width=dp(40),
            background_normal="",
            background_color=(0, 0, 0, 0),
            color=(0.70, 0.30, 0.25, 1),
        )
        del_btn.bind(on_release=lambda *_args, tid=task["id"], ttl=task["title"]: self._confirm_delete(tid, ttl))
        btns.add_widget(del_btn)
        info.add_widget(btns)

        card.add_widget(info)
        return card

    def _completed_card(self, task):
        row = BoxLayout(size_hint_y=None, height=dp(46), padding=[dp(14), dp(6)], spacing=dp(10))
        with row.canvas.before:
            Color(*C_MINT)
            rr = RoundedRectangle(pos=row.pos, size=row.size, radius=[dp(14)])
        row.bind(pos=lambda _i, v: setattr(rr, "pos", v), size=lambda _i, v: setattr(rr, "size", v))
        row.add_widget(Label(text="Done", font_size=sp(11), size_hint=(None, 1), width=dp(38)))
        lbl = Label(text=task["title"], font_size=sp(13), color=C_FOREST, halign="left", strikethrough=True)
        lbl.bind(size=lambda i, v: setattr(i, "text_size", (v[0], None)))
        row.add_widget(lbl)
        return row

    def _confirm_delete(self, task_id, title):
        content = BoxLayout(orientation="vertical", spacing=dp(16), padding=dp(16))
        content.add_widget(label(f'Delete "{title}"?', bold=True, halign="center", height=dp(28), font_size=sp(15)))
        content.add_widget(label("This will remove the task and its flower.", color=C_INK_SOFT, halign="center", height=dp(22), font_size=sp(12)))
        btns = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(10))
        cancel = OutlineButton(text="Cancel")
        confirm = StyledButton(text="Delete", bg=C_CORAL)
        btns.add_widget(cancel)
        btns.add_widget(confirm)
        content.add_widget(btns)

        pop = Popup(title="", content=content, size_hint=(0.82, None), height=dp(200), background="", background_color=(*C_WHITE[:3], 0.97), separator_height=0)
        with pop.canvas.before:
            Color(*C_BORDER)
            rr = RoundedRectangle(pos=pop.pos, size=pop.size, radius=[dp(20)])
        pop.bind(pos=lambda _i, v: setattr(rr, "pos", v), size=lambda _i, v: setattr(rr, "size", v))
        cancel.bind(on_release=pop.dismiss)
        confirm.bind(on_release=lambda *_args: (pop.dismiss(), self._delete_task(task_id)))
        pop.open()

    def _check_notifs(self, _dt=None):
        for task in self.tasks:
            if get_task_status(task) != "active":
                continue
            secs = calculate_time_remaining(task["deadline"])
            tid = task["id"]
            if secs <= 0:
                continue
            if secs <= 3600 and f"1h_{tid}" not in self._notified_tasks:
                self._notified_tasks.add(f"1h_{tid}")
                show_toast(f"Task '{task['title']}' due in {format_time_remaining(secs)}!", success=False)
            elif secs <= 86400 and f"24h_{tid}" not in self._notified_tasks:
                self._notified_tasks.add(f"24h_{tid}")
                show_toast(f"Task '{task['title']}' due in {format_time_remaining(secs)}")

    def _complete_task(self, task_id):
        flower = self._flower_widgets.get(task_id)
        if flower:
            flower.set_stage("blooming", animate=True)
        threading.Thread(target=self._do_complete, args=(task_id,), daemon=True).start()

    def _do_complete(self, task_id):
        try:
            self.auth.complete_task(task_id)
            Clock.schedule_once(lambda _dt: (show_toast(self.lang.t("taskCompleted")), self._load_tasks()))
        except Exception:
            Clock.schedule_once(lambda _dt: show_toast("Failed to complete task", success=False))

    def _delete_task(self, task_id):
        threading.Thread(target=self._do_delete, args=(task_id,), daemon=True).start()

    def _do_delete(self, task_id):
        try:
            self.auth.delete_task(task_id)
            Clock.schedule_once(lambda _dt: (show_toast(self.lang.t("taskDeleted")), self._load_tasks()))
        except Exception:
            Clock.schedule_once(lambda _dt: show_toast("Failed to delete task", success=False))

    def _open_modal(self, task):
        TaskModal(auth=self.auth, on_success=self._load_tasks, task=task, lang=self.lang).open()

    def _avatar_text(self):
        username = (self.auth.user or {}).get("username", "FF")
        parts = [part for part in username.split() if part]
        if len(parts) >= 2:
            return (parts[0][0] + parts[1][0]).upper()
        return username[:2].upper() if username else "FF"

    def _open_settings(self, *_):
        SettingsModal(auth=self.auth, lang=self.lang, on_success=self._settings_done).open()

    def _settings_done(self, account_deleted=False):
        if account_deleted:
            self.sm.current = "login"
            return
        self._build()
        if self.tasks:
            self._render(self.tasks)

    def _tick(self, _dt):
        self._render(self.tasks)
        self._check_notifs()

    def _toggle_lang(self, *_):
        self.lang.toggle_language()
        App.get_running_app().refresh_language()

    def _logout(self, *_):
        self.auth.logout()
        self.sm.current = "login"

    def _navigate(self, screen):
        self.sm.current = screen

    def refresh_language(self):
        self._build()
        if self.tasks:
            self._render(self.tasks)
