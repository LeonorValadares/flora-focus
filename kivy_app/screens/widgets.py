"""
Flora Focus shared widgets, palette, flower engine, and utilities.
"""

import math
from datetime import datetime, timezone

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.graphics import Color, Ellipse, Line, Rectangle, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget

# Palette
C_CREAM = (0.98, 0.96, 0.90, 1)
C_CREAM_DARK = (0.94, 0.91, 0.83, 1)
C_WHITE = (1.00, 1.00, 1.00, 1)
C_BORDER = (0.87, 0.82, 0.72, 1)
C_INK = (0.13, 0.10, 0.07, 1)
C_INK_SOFT = (0.42, 0.37, 0.28, 1)
C_FOREST = (0.15, 0.35, 0.15, 1)
C_LEAF = (0.27, 0.56, 0.20, 1)
C_MINT = (0.72, 0.93, 0.68, 1)
C_SAGE = (0.60, 0.78, 0.52, 1)
C_PETAL_PINK = (0.98, 0.55, 0.67, 1)
C_PETAL_YELLOW = (0.99, 0.87, 0.26, 1)
C_PETAL_ORANGE = (0.99, 0.65, 0.30, 1)
C_PETAL_PURPLE = (0.72, 0.45, 0.90, 1)
C_PETAL_RED = (0.95, 0.28, 0.35, 1)
C_PETAL_WHITE = (0.98, 0.97, 0.96, 1)
C_CENTER_GOLD = (0.99, 0.80, 0.10, 1)
C_CENTER_BROWN = (0.52, 0.28, 0.10, 1)
C_WILT_PETAL = (0.62, 0.55, 0.42, 1)
C_WILT_STEM = (0.55, 0.50, 0.38, 1)
C_BLUSH = (1.00, 0.93, 0.90, 1)
C_BLUSH_BORDER = (0.95, 0.72, 0.62, 1)
C_CORAL = (0.88, 0.32, 0.24, 1)
C_SKY = (0.53, 0.81, 0.98, 1)
C_SKY_DARK = (0.14, 0.52, 0.78, 1)
C_LAVENDER = (0.82, 0.74, 0.98, 1)
C_LAVENDER_DARK = (0.44, 0.28, 0.78, 1)
C_LOGIN_TOP = (0.10, 0.24, 0.14, 1)
C_LOGIN_BOT = (0.16, 0.38, 0.22, 1)
C_BTN_GREEN = (0.20, 0.52, 0.25, 1)
C_AMBER100 = (0.99, 0.95, 0.76, 1)
C_AMBER800 = (0.55, 0.32, 0.04, 1)

C_PRI_HIGH = (0.95, 0.28, 0.35, 1)
C_PRI_MEDIUM = (0.99, 0.65, 0.30, 1)
C_PRI_LOW = (0.27, 0.56, 0.20, 1)

PETAL_PALETTES = [
    (C_PETAL_PINK, C_CENTER_GOLD),
    (C_PETAL_YELLOW, C_CENTER_BROWN),
    (C_PETAL_ORANGE, C_CENTER_GOLD),
    (C_PETAL_PURPLE, C_CENTER_GOLD),
    (C_PETAL_RED, C_CENTER_BROWN),
    (C_PETAL_WHITE, C_CENTER_GOLD),
]

FLOWER_POSITIONS = [
    (0.12, 0.10), (0.32, 0.30), (0.55, 0.08),
    (0.75, 0.25), (0.88, 0.55), (0.20, 0.60),
    (0.50, 0.50), (0.68, 0.70),
]


def calculate_time_remaining(deadline_iso: str) -> int:
    try:
        deadline = datetime.fromisoformat(deadline_iso.replace("Z", "+00:00"))
        return max(0, int((deadline - datetime.now(timezone.utc)).total_seconds()))
    except Exception:
        return 0


def format_time_remaining(seconds: int) -> str:
    if seconds <= 0:
        return "Expired"
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    mins = (seconds % 3600) // 60
    if days > 0:
        return f"{days}d {hours}h"
    if hours > 0:
        return f"{hours}h {mins}m"
    return f"{mins}m"


def get_task_status(task: dict) -> str:
    time_left = calculate_time_remaining(task["deadline"])
    if task["status"] == "completed":
        return "completed"
    if task["status"] == "expired" or time_left <= 0:
        return "expired"
    return "active"


def growth_stage(task: dict) -> str:
    status = get_task_status(task)
    if status == "expired":
        return "wilted"
    if status == "completed":
        return "blooming"
    total = task.get("time_remaining_seconds", 86400)
    left = calculate_time_remaining(task["deadline"])
    if total <= 0:
        return "blooming"
    ratio = left / total
    if ratio > 0.75:
        return "seed"
    if ratio > 0.50:
        return "sprout"
    if ratio > 0.20:
        return "growing"
    return "blooming"


def palette_for(task_id: str) -> tuple:
    return PETAL_PALETTES[abs(hash(task_id)) % len(PETAL_PALETTES)]


def priority_color(priority: str) -> tuple:
    return {"high": C_PRI_HIGH, "medium": C_PRI_MEDIUM}.get(priority, C_PRI_LOW)


class FlowerWidget(Widget):
    STAGE_SCALE = {
        "seed": 0.18,
        "sprout": 0.42,
        "growing": 0.68,
        "blooming": 1.0,
        "wilted": 0.78,
    }

    def __init__(self, stage="seed", petal_color=None, center_color=None,
                 petal_count=6, **kwargs):
        kwargs.setdefault("size_hint", (None, None))
        kwargs.setdefault("size", (dp(72), dp(72)))
        super().__init__(**kwargs)
        self.stage = stage
        self.petal_color = petal_color or C_PETAL_PINK
        self.center_color = center_color or C_CENTER_GOLD
        self.petal_count = petal_count
        self._s = self.STAGE_SCALE[stage]
        self.bind(pos=self._redraw, size=self._redraw)

    def set_stage(self, stage, animate=True):
        self.stage = stage
        target = self.STAGE_SCALE[stage]
        if animate:
            anim = Animation(_s=target, duration=0.75, t="out_elastic")
            anim.bind(on_progress=lambda *_: self._redraw())
            anim.start(self)
        else:
            self._s = target
            self._redraw()

    def _redraw(self, *_):
        self.canvas.clear()
        cx = self.x + self.width / 2
        cy = self.y + self.height / 2
        with self.canvas:
            getattr(self, f"_draw_{self.stage}")(cx, cy, self._s)

    def _draw_seed(self, cx, cy, s):
        Color(0.52, 0.36, 0.16, 1)
        Ellipse(pos=(cx - dp(10), cy - dp(6)), size=(dp(20), dp(9)))
        Color(0.64, 0.46, 0.22, 1)
        r = dp(7) * max(s, 0.14)
        Ellipse(pos=(cx - r, cy - r * 0.55), size=(r * 2, r * 1.25))

    def _draw_sprout(self, cx, cy, s):
        h = dp(22) * s
        base = cy - dp(5)
        Color(0.30, 0.60, 0.20, 1)
        Line(points=[cx, base, cx, base + h], width=dp(2.5))
        lw = dp(11) * s
        Color(0.38, 0.70, 0.26, 1)
        Ellipse(pos=(cx - lw - dp(2), base + h * 0.42), size=(lw, lw * 0.52))
        Ellipse(pos=(cx + dp(2), base + h * 0.42), size=(lw, lw * 0.52))
        Color(0.52, 0.36, 0.16, 1)
        Ellipse(pos=(cx - dp(11), base - dp(6)), size=(dp(22), dp(9)))

    def _draw_growing(self, cx, cy, s):
        h = dp(30) * s
        base = cy - dp(7)
        Color(0.28, 0.57, 0.18, 1)
        Line(points=[cx, base, cx - dp(3) * s, base + h * 0.5, cx, base + h], width=dp(2.5))
        lw = dp(14) * s
        Color(0.36, 0.68, 0.24, 1)
        Ellipse(pos=(cx - lw - dp(1), base + h * 0.33), size=(lw, lw * 0.50))
        Ellipse(pos=(cx + dp(1), base + h * 0.54), size=(lw, lw * 0.50))
        br = dp(7.5) * s
        Color(*self.petal_color[:3], 0.78)
        Ellipse(pos=(cx - br, base + h - br), size=(br * 2, br * 2.3))
        Color(0.52, 0.36, 0.16, 1)
        Ellipse(pos=(cx - dp(12), base - dp(6)), size=(dp(24), dp(9)))

    def _draw_blooming(self, cx, cy, s):
        h = dp(32) * s
        base = cy - dp(8)
        flower_y = base + h
        pr = dp(11.5) * s
        cr = dp(7.5) * s
        Color(0.26, 0.54, 0.17, 1)
        Line(points=[cx, base, cx, flower_y], width=dp(2.5))
        lw = dp(15) * s
        Color(0.34, 0.67, 0.23, 1)
        Ellipse(pos=(cx - lw - dp(1), base + h * 0.28), size=(lw, lw * 0.46))
        Ellipse(pos=(cx + dp(1), base + h * 0.50), size=(lw, lw * 0.46))
        Color(*self.petal_color)
        for i in range(self.petal_count):
            angle = math.radians(i * 360 / self.petal_count)
            ox = math.cos(angle) * pr
            oy = math.sin(angle) * pr
            Ellipse(pos=(cx + ox - pr * 0.62, flower_y + oy - pr * 0.62),
                    size=(pr * 1.25, pr * 1.25))
        Color(*self.center_color)
        Ellipse(pos=(cx - cr, flower_y - cr), size=(cr * 2, cr * 2))
        Color(1, 1, 1, 0.42)
        Ellipse(pos=(cx - cr * 0.36, flower_y - cr * 0.14), size=(cr * 0.58, cr * 0.58))
        Color(0.50, 0.34, 0.13, 1)
        Ellipse(pos=(cx - dp(13), base - dp(6)), size=(dp(26), dp(9)))

    def _draw_wilted(self, cx, cy, s):
        h = dp(24) * s
        base = cy - dp(5)
        tx = cx + dp(11) * s
        ty = base + h * 0.68
        Color(*C_WILT_STEM)
        Line(points=[cx, base, cx + dp(4) * s, base + h * 0.48, tx, ty], width=dp(2))
        pr = dp(8.5) * s
        Color(*C_WILT_PETAL)
        for i in range(5):
            angle = math.radians(i * 72 + 25)
            ox = math.cos(angle) * pr * 0.78
            oy = math.sin(angle) * pr * 0.52 - pr * 0.42
            Ellipse(pos=(tx + ox - pr * 0.52, ty + oy - pr * 0.52),
                    size=(pr * 1.05, pr * 1.05))
        Color(0.47, 0.41, 0.31, 1)
        Ellipse(pos=(tx - dp(4.5) * s, ty - dp(4.5) * s), size=(dp(9) * s, dp(9) * s))
        Color(0.48, 0.33, 0.12, 1)
        Ellipse(pos=(cx - dp(11), base - dp(5)), size=(dp(22), dp(9)))


class GardenPanel(FloatLayout):
    def __init__(self, **kwargs):
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(260))
        super().__init__(**kwargs)
        self.bind(pos=self._bg, size=self._bg)

    def _bg(self, *_):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(0.66, 0.87, 0.97, 1)
            Rectangle(pos=(self.x, self.y + self.height * 0.42), size=(self.width, self.height * 0.58))
            Color(0.82, 0.94, 0.99, 1)
            Rectangle(pos=(self.x, self.y + self.height * 0.36), size=(self.width, self.height * 0.10))
            Color(0.40, 0.74, 0.28, 1)
            RoundedRectangle(pos=(self.x, self.y), size=(self.width, self.height * 0.42),
                             radius=[0, 0, dp(20), dp(20)])
            Color(0.52, 0.84, 0.36, 1)
            RoundedRectangle(pos=(self.x, self.y + self.height * 0.34),
                             size=(self.width, self.height * 0.10), radius=[dp(8)])
            Color(0.99, 0.91, 0.28, 1)
            Ellipse(pos=(self.x + self.width * 0.78, self.y + self.height * 0.72),
                    size=(dp(38), dp(38)))
            Color(1.0, 0.96, 0.55, 0.28)
            Ellipse(pos=(self.x + self.width * 0.78 - dp(7), self.y + self.height * 0.72 - dp(7)),
                    size=(dp(52), dp(52)))
            Color(*C_BORDER)
            Line(rounded_rectangle=(self.x, self.y, self.width, self.height, dp(20)), width=1.5)


class RoundedBox(BoxLayout):
    def __init__(self, radius=dp(18), bg_color=C_WHITE,
                 border_color=C_BORDER, border_width=1.5, **kwargs):
        super().__init__(**kwargs)
        self._bg = bg_color
        self._bdr = border_color
        self._r = radius
        self._bw = border_width
        self.bind(pos=self._upd, size=self._upd)

    def _upd(self, *_):
        self.canvas.before.clear()
        with self.canvas.before:
            if self._bdr:
                Color(*self._bdr)
                RoundedRectangle(pos=self.pos, size=self.size, radius=[self._r])
            Color(*self._bg)
            bw = self._bw
            RoundedRectangle(pos=(self.x + bw, self.y + bw),
                             size=(self.width - bw * 2, self.height - bw * 2),
                             radius=[self._r])


class StyledButton(Button):
    def __init__(self, bg=C_LEAF, text_color=C_WHITE, radius=dp(26), **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_color = (0, 0, 0, 0)
        self._bg = bg
        self._r = radius
        self.color = text_color
        self.font_size = sp(14)
        self.bold = True
        self.bind(pos=self._draw, size=self._draw)

    def _draw(self, *_):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self._bg)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[self._r])


class OutlineButton(Button):
    def __init__(self, border_color=C_BORDER, text_color=C_INK,
                 radius=dp(26), **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_color = (0, 0, 0, 0)
        self._bdr = border_color
        self._r = radius
        self.color = text_color
        self.font_size = sp(14)
        self.bind(pos=self._draw, size=self._draw)

    def _draw(self, *_):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self._bdr)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[self._r])
            Color(*C_WHITE)
            RoundedRectangle(pos=(self.x + 1.5, self.y + 1.5),
                             size=(self.width - 3, self.height - 3), radius=[self._r])


class StyledInput(TextInput):
    def __init__(self, **kwargs):
        kwargs.setdefault("multiline", False)
        kwargs.setdefault("font_size", sp(14))
        kwargs.setdefault("padding", [dp(14), dp(12), dp(14), dp(12)])
        kwargs.setdefault("background_color", C_WHITE)
        kwargs.setdefault("background_normal", "")
        kwargs.setdefault("background_active", "")
        kwargs.setdefault("foreground_color", C_INK)
        kwargs.setdefault("cursor_color", C_LEAF)
        kwargs.setdefault("selection_color", (*C_MINT[:3], 0.45))
        kwargs.setdefault("hint_text_color", (0.60, 0.55, 0.46, 1))
        kwargs.setdefault("cursor_width", dp(1.5))
        kwargs.setdefault("write_tab", False)
        super().__init__(**kwargs)
        self.bind(pos=self._border, size=self._border)

    def _border(self, *_):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*C_BORDER)
            Line(rounded_rectangle=(self.x, self.y, self.width, self.height, dp(14)), width=1.5)


class StyledTextArea(TextInput):
    def __init__(self, **kwargs):
        kwargs.setdefault("multiline", True)
        kwargs.setdefault("font_size", sp(13))
        kwargs.setdefault("padding", [dp(12), dp(10), dp(12), dp(10)])
        kwargs.setdefault("background_color", C_WHITE)
        kwargs.setdefault("background_normal", "")
        kwargs.setdefault("background_active", "")
        kwargs.setdefault("foreground_color", C_INK)
        kwargs.setdefault("cursor_color", C_LEAF)
        kwargs.setdefault("cursor_width", dp(1.5))
        kwargs.setdefault("selection_color", (*C_MINT[:3], 0.45))
        kwargs.setdefault("hint_text_color", (0.60, 0.55, 0.46, 1))
        super().__init__(**kwargs)
        self.bind(pos=self._border, size=self._border)

    def _border(self, *_):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*C_BORDER)
            Line(rounded_rectangle=(self.x, self.y, self.width, self.height, dp(14)), width=1.5)


class Pill(BoxLayout):
    def __init__(self, text, bg_color, text_color=C_WHITE, **kwargs):
        kwargs.setdefault("size_hint", (None, None))
        kwargs.setdefault("size", (dp(72), dp(24)))
        kwargs.setdefault("padding", [dp(8), 0])
        super().__init__(**kwargs)
        self._bg = bg_color
        self.bind(pos=self._draw, size=self._draw)
        self.add_widget(Label(text=text, font_size=sp(10), bold=True,
                              color=text_color, halign="center"))

    def _draw(self, *_):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self._bg)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])


class HeaderBar(BoxLayout):
    def __init__(self, bg=C_CREAM, **kwargs):
        kwargs.setdefault("orientation", "horizontal")
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(66))
        kwargs.setdefault("padding", [dp(16), dp(8)])
        kwargs.setdefault("spacing", dp(8))
        super().__init__(**kwargs)
        self._bg = bg
        self.bind(pos=self._draw, size=self._draw)

    def _draw(self, *_):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self._bg)
            Rectangle(pos=self.pos, size=self.size)
            Color(*C_BORDER)
            Line(points=[self.x, self.y, self.x + self.width, self.y], width=1.2)


class BottomNav(BoxLayout):
    NAV_ITEMS = [
        ("garden", "garden"),
        ("stats", "stats"),
        ("friends", "friends"),
        ("family", "family"),
    ]

    def __init__(self, current, on_navigate, lang=None, **kwargs):
        kwargs.setdefault("orientation", "horizontal")
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(64))
        super().__init__(**kwargs)
        self._current = current
        self._lang = lang
        self.bind(pos=self._draw, size=self._draw)

        for key, label_key in self.NAV_ITEMS:
            active = current == key
            label_text = self._lang.t(label_key) if self._lang else label_key.title()
            btn = Button(
                text=label_text,
                background_normal="",
                background_color=(0, 0, 0, 0),
                color=C_MINT if active else (0.78, 0.85, 0.78, 1),
                bold=active,
                font_size=sp(12),
                on_release=lambda _btn, k=key: on_navigate(k),
            )
            self.add_widget(btn)

    def _draw(self, *_):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*C_FOREST)
            Rectangle(pos=self.pos, size=self.size)
            tab_w = self.width / 4
            keys = [k for k, _ in self.NAV_ITEMS]
            if self._current in keys:
                idx = keys.index(self._current)
                Color(*C_MINT)
                Line(points=[
                    self.x + tab_w * idx + tab_w * 0.2,
                    self.y + self.height - dp(3),
                    self.x + tab_w * idx + tab_w * 0.8,
                    self.y + self.height - dp(3),
                ], width=dp(3))


class Toast(Popup):
    def __init__(self, message, success=True, **kwargs):
        icon = "OK" if success else "!"
        text = f"{icon}  {message}"
        pill_c = C_LEAF if success else (0.75, 0.28, 0.22, 1)

        inner = BoxLayout(orientation="horizontal", padding=[dp(14), dp(10)], spacing=dp(8))
        msg_label = Label(
            text=text,
            color=C_WHITE,
            font_size=sp(13),
            halign="center",
            valign="middle",
            bold=True,
        )
        msg_label.bind(size=lambda i, v: setattr(i, "text_size", v))
        inner.add_widget(msg_label)

        super().__init__(
            title="",
            content=inner,
            size_hint=(0.82, None),
            height=dp(54),
            auto_dismiss=True,
            background="",
            background_color=(0, 0, 0, 0),
            border=(0, 0, 0, 0),
            separator_height=0,
            overlay_color=(0, 0, 0, 0),
            **kwargs,
        )
        with self.canvas:
            pass
        with self.canvas.before:
            Color(*pill_c)
            self._rr = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(16)])
        self.bind(
            pos=lambda _i, v: setattr(self._rr, "pos", v),
            size=lambda _i, v: setattr(self._rr, "size", v),
        )
        self.open()
        Clock.schedule_once(lambda _dt: self.dismiss(), 3.0)


def show_toast(message, success=True):
    Toast(message, success)


class LoadingSpinner(Label):
    FRAMES = ["Loading", "Loading.", "Loading..", "Loading..."]

    def __init__(self, **kwargs):
        kwargs.setdefault("font_size", sp(18))
        kwargs.setdefault("color", C_LEAF)
        kwargs.setdefault("halign", "center")
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(48))
        super().__init__(**kwargs)
        self._fi = 0
        self._ev = None
        self.text = self.FRAMES[0]

    def start(self):
        self.stop()
        self._ev = Clock.schedule_interval(self._tick, 0.25)

    def stop(self):
        if self._ev:
            self._ev.cancel()
            self._ev = None

    def _tick(self, _dt):
        self._fi = (self._fi + 1) % len(self.FRAMES)
        self.text = self.FRAMES[self._fi]


class DropdownSpinner(BoxLayout):
    def __init__(self, options, value=None, on_change=None, **kwargs):
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(46))
        super().__init__(**kwargs)
        self.options = options
        self.on_change = on_change
        self._idx = 0
        if value:
            for i, (option_value, _) in enumerate(options):
                if option_value == value:
                    self._idx = i
                    break
        self.btn = Button(
            text=f"  {self.options[self._idx][1]}  v",
            background_normal="",
            background_color=(0, 0, 0, 0),
            color=C_INK,
            font_size=sp(13),
            halign="left",
            valign="middle",
        )
        self.btn.bind(on_release=self._cycle)
        self.add_widget(self.btn)
        self.bind(pos=self._draw, size=self._draw)

    @property
    def value(self):
        return self.options[self._idx][0]

    def _cycle(self, *_):
        self._idx = (self._idx + 1) % len(self.options)
        self.btn.text = f"  {self.options[self._idx][1]}  v"
        if self.on_change:
            self.on_change(self.value)

    def _draw(self, *_):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*C_BORDER)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(14)])
            Color(*C_WHITE)
            RoundedRectangle(pos=(self.x + 1.5, self.y + 1.5),
                             size=(self.width - 3, self.height - 3), radius=[dp(14)])


def label(text, font_size=sp(14), color=C_INK, bold=False,
          halign="left", size_hint_y=None, height=dp(22), **kwargs):
    lbl = Label(
        text=text,
        font_size=font_size,
        color=color,
        bold=bold,
        halign=halign,
        valign="middle",
        size_hint_y=size_hint_y,
        height=height,
        **kwargs,
    )
    lbl.bind(size=lambda i, v: setattr(i, "text_size", (v[0], None)))
    return lbl


def spacer(h=dp(8)):
    return Widget(size_hint_y=None, height=h)


def section_heading(text):
    box = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(36), spacing=0)
    box.add_widget(label(text, bold=True, font_size=sp(16), color=C_INK, height=dp(28)))
    line = Widget(size_hint_y=None, height=dp(2))
    with line.canvas:
        Color(*C_BORDER)
        Rectangle(pos=line.pos, size=line.size)
    line.bind(pos=lambda _i, v: setattr(line.canvas.children[-1], "pos", v))
    box.add_widget(line)
    return box
