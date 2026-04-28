"""Login screen."""

import threading

from kivy.clock import Clock
from kivy.app import App
from kivy.graphics import Color, Ellipse, Rectangle, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget

from screens.widgets import (
    C_BTN_GREEN,
    C_LOGIN_TOP,
    C_WHITE,
    StyledButton,
    StyledInput,
    label,
    show_toast,
    spacer,
)


def _humanise(raw: str) -> str:
    lowered = raw.lower()
    if "email" in lowered and ("valid" in lowered or "value" in lowered):
        return "Please enter a valid email address"
    if "already registered" in lowered:
        return "That email is already registered"
    if "invalid credentials" in lowered or "401" in lowered:
        return "Wrong email or password"
    if "connection" in lowered or "refused" in lowered:
        return "Cannot reach the server. Is the backend running?"
    return "Login failed. Please try again"


class LoginScreen(Screen):
    def __init__(self, auth, lang, sm, **kwargs):
        super().__init__(**kwargs)
        self.auth = auth
        self.lang = lang
        self.sm = sm
        self._build()

    def _build(self):
        self.clear_widgets()
        t = self.lang.t

        root = BoxLayout(orientation="vertical")
        with root.canvas.before:
            Color(*C_LOGIN_TOP)
            self._bg = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=lambda i, v: setattr(self._bg, "pos", v), size=lambda i, v: setattr(self._bg, "size", v))

        with root.canvas:
            for cx, cy, r in [
                (0.12, 0.88, 2.5), (0.70, 0.93, 2), (0.35, 0.84, 3.5),
                (0.82, 0.78, 2), (0.55, 0.80, 1.8), (0.90, 0.62, 2.5),
                (0.04, 0.70, 2), (0.48, 0.91, 1.5),
            ]:
                Color(1, 1, 1, 0.22)
                Ellipse(pos=(cx * 400, cy * 750), size=(dp(r * 2), dp(r * 2)))

        scroll = ScrollView(do_scroll_x=False)
        inner = BoxLayout(
            orientation="vertical",
            padding=[dp(32), dp(52), dp(32), dp(32)],
            spacing=dp(14),
            size_hint_y=None,
        )
        inner.bind(minimum_height=inner.setter("height"))

        lang_row = BoxLayout(size_hint_y=None, height=dp(36))
        lang_row.add_widget(Widget())
        lang_btn = StyledButton(
            text="PT" if self.lang.language == "en" else "EN",
            bg=(1, 1, 1, 0.15),
            text_color=C_WHITE,
            size_hint=(None, 1),
            width=dp(54),
        )
        lang_btn.bind(on_release=self._toggle_lang)
        lang_row.add_widget(lang_btn)
        inner.add_widget(lang_row)

        inner.add_widget(spacer(dp(16)))

        decor = Label(
            text="FOCUS  PLAN  GROW",
            font_size=sp(18),
            size_hint_y=None,
            height=dp(38),
            halign="center",
            color=C_WHITE,
        )
        decor.bind(size=lambda i, v: setattr(i, "text_size", (v[0], None)))
        inner.add_widget(decor)

        for text, size, color, height in [
            (t("appName"), sp(42), C_WHITE, dp(58)),
            (t("tagline"), sp(14), (0.76, 0.94, 0.70, 1), dp(26)),
        ]:
            lbl = Label(text=text, font_size=size, bold=(size == sp(42)), color=color, size_hint_y=None, height=height, halign="center")
            lbl.bind(size=lambda i, v: setattr(i, "text_size", (v[0], None)))
            inner.add_widget(lbl)

        inner.add_widget(spacer(dp(16)))

        card = BoxLayout(
            orientation="vertical",
            spacing=dp(12),
            padding=[dp(22), dp(20), dp(22), dp(20)],
            size_hint_y=None,
        )
        card.bind(minimum_height=card.setter("height"))
        with card.canvas.before:
            Color(1, 1, 1, 0.97)
            self._card = RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(24)])
        card.bind(pos=lambda i, v: setattr(self._card, "pos", v), size=lambda i, v: setattr(self._card, "size", v))

        card.add_widget(label(t("enterEmailLogin"), color=(0.28, 0.44, 0.28, 1), halign="center", height=dp(22), font_size=sp(13)))

        self._email_inp = StyledInput(hint_text="Email address", size_hint_y=None, height=dp(50))
        self._pass_inp = StyledInput(hint_text="Password", password=True, size_hint_y=None, height=dp(50))
        card.add_widget(self._email_inp)
        card.add_widget(self._pass_inp)

        self._submit_btn = StyledButton(text=t("startGrowing"), bg=C_BTN_GREEN, size_hint_y=None, height=dp(52))
        self._submit_btn.bind(on_release=self._do_login)
        card.add_widget(self._submit_btn)
        inner.add_widget(card)

        inner.add_widget(spacer(dp(14)))

        row = BoxLayout(size_hint_y=None, height=dp(30), spacing=dp(4))
        row.add_widget(Widget())
        row.add_widget(Label(
            text=t("dontHaveAccount"),
            font_size=sp(13),
            color=(0.76, 0.92, 0.70, 1),
            size_hint=(None, 1),
            width=dp(165),
        ))
        su_btn = Button(
            text=t("signUp"),
            font_size=sp(13),
            bold=True,
            color=C_WHITE,
            size_hint=(None, 1),
            width=dp(64),
            background_normal="",
            background_color=(0, 0, 0, 0),
        )
        su_btn.bind(on_release=lambda *_: setattr(self.sm, "current", "signup"))
        row.add_widget(su_btn)
        row.add_widget(Widget())
        inner.add_widget(row)

        scroll.add_widget(inner)
        root.add_widget(scroll)
        self.add_widget(root)

    def _toggle_lang(self, *_):
        self.lang.toggle_language()
        App.get_running_app().refresh_language()

    def refresh_language(self):
        self._build()

    def _do_login(self, *_):
        email = self._email_inp.text.strip()
        password = self._pass_inp.text.strip()
        if not email or not password:
            show_toast("Please fill in all fields", success=False)
            return
        self._submit_btn.text = self.lang.t("saving")
        threading.Thread(target=self._thread, args=(email, password), daemon=True).start()

    def _thread(self, email, password):
        try:
            self.auth.login(email, password)
            Clock.schedule_once(self._success)
        except Exception as exc:
            msg = str(exc)
            Clock.schedule_once(lambda dt: self._fail(msg))

    def _success(self, _dt):
        self._submit_btn.text = self.lang.t("startGrowing")
        show_toast(self.lang.t("welcomeBack"))
        self.sm.current = "garden"
        self.sm.get_screen("garden").refresh_language()

    def _fail(self, msg):
        self._submit_btn.text = self.lang.t("startGrowing")
        show_toast(_humanise(msg), success=False)
