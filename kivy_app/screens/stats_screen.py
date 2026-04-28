"""Stats screen."""

import threading

from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView

from screens.widgets import (
    BottomNav,
    C_BLUSH,
    C_CORAL,
    C_CREAM,
    C_FOREST,
    C_INK,
    C_INK_SOFT,
    C_LAVENDER,
    C_LAVENDER_DARK,
    C_LEAF,
    C_MINT,
    C_SKY,
    C_SKY_DARK,
    C_WHITE,
    FlowerWidget,
    HeaderBar,
    LoadingSpinner,
    PETAL_PALETTES,
    RoundedBox,
    label,
    show_toast,
)


class BentoCard(BoxLayout):
    def __init__(self, title, value, subtitle, bg, text_color, **kwargs):
        kwargs.setdefault("orientation", "vertical")
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(110))
        kwargs.setdefault("padding", [dp(16), dp(12)])
        kwargs.setdefault("spacing", dp(2))
        super().__init__(**kwargs)
        self._bg = bg
        self.bind(pos=self._draw, size=self._draw)
        self.add_widget(Label(text=title, font_size=sp(14), bold=True, size_hint_y=None, height=dp(24), color=text_color))
        self.add_widget(Label(text=str(value), font_size=sp(30), bold=True, color=text_color, size_hint_y=None, height=dp(38)))
        sub = Label(text=subtitle, font_size=sp(11), color=text_color, size_hint_y=None, height=dp(18), halign="left")
        sub.bind(size=lambda i, v: setattr(i, "text_size", (v[0], None)))
        self.add_widget(sub)

    def _draw(self, *_):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self._bg)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(20)])
            Color(1, 1, 1, 0.12)
            RoundedRectangle(pos=(self.x + 2, self.y + 2), size=(self.width - 4, self.height - 4), radius=[dp(18)])


class StatsScreen(Screen):
    def __init__(self, auth, lang, sm, **kwargs):
        super().__init__(**kwargs)
        self.auth = auth
        self.lang = lang
        self.sm = sm
        self.stats = None
        self._build()

    def _build(self):
        self.clear_widgets()
        t = self.lang.t

        root = BoxLayout(orientation="vertical")
        with root.canvas.before:
            Color(*C_CREAM)
            bg = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=lambda _i, v: setattr(bg, "pos", v), size=lambda _i, v: setattr(bg, "size", v))

        hdr = HeaderBar()
        hdr.add_widget(Label(text=t("stats") + "  " + t("yourProgress"), font_size=sp(20), bold=True, color=C_INK, halign="left"))
        root.add_widget(hdr)

        scroll = ScrollView(do_scroll_x=False)
        self._body = BoxLayout(orientation="vertical", padding=[dp(14), dp(12), dp(14), dp(80)], spacing=dp(14), size_hint_y=None)
        self._body.bind(minimum_height=self._body.setter("height"))

        self._spinner = LoadingSpinner()
        self._body.add_widget(self._spinner)
        self._spinner.start()

        scroll.add_widget(self._body)
        root.add_widget(scroll)
        root.add_widget(BottomNav(current="stats", on_navigate=self._navigate, lang=self.lang))
        self.add_widget(root)

    def on_enter(self, *_):
        if self.stats is not None:
            self._render(self.stats)
        self._spinner.start()
        threading.Thread(target=self._fetch, daemon=True).start()

    def _fetch(self):
        try:
            stats = self.auth.get_stats()
            Clock.schedule_once(lambda _dt: self._render(stats))
        except Exception:
            Clock.schedule_once(lambda _dt: show_toast("Failed to load stats", success=False))

    def _render(self, stats):
        self.stats = stats
        self._spinner.stop()
        self._spinner.text = ""
        t = self.lang.t
        username = self.auth.user.get("username", "") if self.auth.user else ""
        self._body.clear_widgets()

        hero = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(130), padding=[dp(22), dp(16)], spacing=dp(12))
        with hero.canvas.before:
            Color(*C_FOREST)
            rr = RoundedRectangle(pos=hero.pos, size=hero.size, radius=[dp(22)])
        hero.bind(pos=lambda _i, v: setattr(rr, "pos", v), size=lambda _i, v: setattr(rr, "size", v))

        left_col = BoxLayout(orientation="vertical", spacing=dp(4))
        left_col.add_widget(label(t("completionRate"), color=C_MINT, font_size=sp(11), height=dp(18)))
        left_col.add_widget(Label(text=f"{stats['completion_rate']}%", font_size=sp(44), bold=True, color=C_WHITE, size_hint_y=None, height=dp(56)))
        left_col.add_widget(label(self.lang.tasks_progress(stats["completed_tasks"], stats["total_tasks"]), color=(0.70, 0.90, 0.65, 1), font_size=sp(11), height=dp(18)))
        hero.add_widget(left_col)

        petal, center = PETAL_PALETTES[0]
        hero.add_widget(FlowerWidget(stage="blooming", petal_color=petal, center_color=center, size=(dp(68), dp(68))))
        self._body.add_widget(hero)

        row1 = BoxLayout(size_hint_y=None, height=dp(110), spacing=dp(12))
        row1.add_widget(BentoCard("Active", stats["active_tasks"], t("active"), C_SKY, C_SKY_DARK))
        row1.add_widget(BentoCard("Done", stats["completed_tasks"], t("completed"), C_LEAF, C_WHITE))
        self._body.add_widget(row1)

        row2 = BoxLayout(size_hint_y=None, height=dp(110), spacing=dp(12))
        row2.add_widget(BentoCard("Flowers", stats["total_flowers"], t("flowers"), C_LAVENDER, C_LAVENDER_DARK))
        row2.add_widget(BentoCard("Expired", stats["expired_tasks"], t("expiredTasks"), C_BLUSH, (*C_CORAL[:3], 1)))
        self._body.add_widget(row2)

        if stats["total_tasks"] == 0:
            title = t("statsNoTasksTitle")
            msg = t("statsNoTasksMessage")
        elif stats["completion_rate"] >= 80:
            title = f"{t('keepItUp')}, {username}!"
            msg = t("gardenFlourishing")
        elif stats["completion_rate"] >= 50:
            title = f"{t('keepItUp')}, {username}!"
            msg = t("greatProgress")
        else:
            title = f"{t('keepItUp')}, {username}!"
            msg = t("everyTask")

        moti = RoundedBox(orientation="vertical", size_hint_y=None, height=dp(100), padding=[dp(18), dp(14)], spacing=dp(6))
        moti.add_widget(label(title, bold=True, font_size=sp(15), height=dp(26)))
        msg_lbl = Label(text=msg, font_size=sp(12), color=C_INK_SOFT, halign="left", valign="top")
        msg_lbl.bind(size=lambda i, v: setattr(i, "text_size", (v[0], None)))
        moti.add_widget(msg_lbl)
        self._body.add_widget(moti)

    def _navigate(self, screen):
        self.sm.current = screen

    def refresh_language(self):
        self._build()
        if self.stats is not None:
            self._render(self.stats)
