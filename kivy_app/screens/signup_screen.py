"""Signup screen."""

import threading

from kivy.clock import Clock
from kivy.app import App
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget

from screens.widgets import C_BTN_GREEN, C_LOGIN_TOP, C_WHITE, StyledButton, StyledInput, label, show_toast, spacer


def _humanise(raw: str) -> str:
    lowered = raw.lower()
    if "email" in lowered and ("valid" in lowered or "value" in lowered):
        return "Please enter a valid email address"
    if "already registered" in lowered:
        return "That email is already registered"
    if "username already" in lowered:
        return "That username is already taken"
    if "connection" in lowered or "refused" in lowered:
        return "Cannot reach the server. Is the backend running?"
    return "Signup failed. Please try again"


class SignupScreen(Screen):
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

        card.add_widget(label(t("createAccount"), bold=True, color=(0.13, 0.10, 0.07, 1), halign="center", height=dp(26), font_size=sp(17)))
        card.add_widget(label(t("enterEmailSignup"), color=(0.28, 0.44, 0.28, 1), halign="center", height=dp(20), font_size=sp(12)))

        self._user_inp = StyledInput(hint_text="Username", size_hint_y=None, height=dp(50))
        self._email_inp = StyledInput(hint_text="Email address", size_hint_y=None, height=dp(50))
        self._pass_inp = StyledInput(hint_text="Password", password=True, size_hint_y=None, height=dp(50))
        for widget in (self._user_inp, self._email_inp, self._pass_inp):
            card.add_widget(widget)

        self._submit_btn = StyledButton(text=t("startGrowing"), bg=C_BTN_GREEN, size_hint_y=None, height=dp(52))
        self._submit_btn.bind(on_release=self._do_signup)
        card.add_widget(self._submit_btn)
        inner.add_widget(card)

        inner.add_widget(spacer(dp(14)))

        row = BoxLayout(size_hint_y=None, height=dp(30), spacing=dp(4))
        row.add_widget(Widget())
        row.add_widget(Label(
            text=t("alreadyHaveAccount"),
            font_size=sp(13),
            color=(0.76, 0.92, 0.70, 1),
            size_hint=(None, 1),
            width=dp(178),
        ))
        li_btn = Button(
            text=t("logIn"),
            font_size=sp(13),
            bold=True,
            color=C_WHITE,
            size_hint=(None, 1),
            width=dp(52),
            background_normal="",
            background_color=(0, 0, 0, 0),
        )
        li_btn.bind(on_release=lambda *_: setattr(self.sm, "current", "login"))
        row.add_widget(li_btn)
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

    def _do_signup(self, *_):
        username = self._user_inp.text.strip()
        email = self._email_inp.text.strip()
        password = self._pass_inp.text.strip()
        if not username or not email or not password:
            show_toast("Please fill in all fields", success=False)
            return
        self._submit_btn.text = self.lang.t("saving")
        threading.Thread(target=self._thread, args=(username, email, password), daemon=True).start()

    def _thread(self, username, email, password):
        try:
            self.auth.signup(username, email, password)
            Clock.schedule_once(self._success)
        except Exception as exc:
            msg = str(exc)
            Clock.schedule_once(lambda dt: self._fail(msg))

    def _success(self, _dt):
        self._submit_btn.text = self.lang.t("startGrowing")
        show_toast(self.lang.t("welcomeToApp"))
        self.sm.current = "garden"
        self.sm.get_screen("garden").refresh_language()

    def _fail(self, msg):
        self._submit_btn.text = self.lang.t("startGrowing")
        show_toast(_humanise(msg), success=False)
