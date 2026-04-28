"""Profile settings modal."""

import threading

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
    OutlineButton,
    StyledButton,
    StyledInput,
    StyledTextArea,
    label,
    show_toast,
    spacer,
)


class SettingsModal(Popup):
    def __init__(self, auth, lang, on_success, **kwargs):
        self.auth = auth
        self.lang = lang
        self.on_success = on_success
        super().__init__(
            title=lang.t("settings"),
            title_size=sp(17),
            title_color=C_INK,
            content=self._build_content(),
            size_hint=(0.93, None),
            height=dp(620),
            background="",
            background_color=(0, 0, 0, 0),
            separator_color=C_BORDER,
            overlay_color=(0, 0, 0, 0.55),
            auto_dismiss=True,
            **kwargs,
        )
        with self.canvas.before:
            Color(0.97, 0.95, 0.88, 1)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(22)])
        self.bind(pos=self._update_bg, size=self._update_bg)

    def _update_bg(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size

    def _build_content(self):
        scroll = ScrollView(do_scroll_x=False)
        box = BoxLayout(orientation="vertical", spacing=dp(10), padding=[dp(14), dp(8), dp(14), dp(12)], size_hint_y=None)
        box.bind(minimum_height=box.setter("height"))
        user = self.auth.user or {}

        box.add_widget(label(self.lang.t("profile"), bold=True, font_size=sp(16), height=dp(26)))

        box.add_widget(label(self.lang.t("username"), bold=True, font_size=sp(12), height=dp(20), color=(0.18, 0.15, 0.11, 1)))
        self._username = StyledInput(text=user.get("username", ""), size_hint_y=None, height=dp(46))
        box.add_widget(self._username)

        box.add_widget(label(self.lang.t("avatarUrl"), bold=True, font_size=sp(12), height=dp(20), color=(0.18, 0.15, 0.11, 1)))
        self._avatar = StyledInput(
            text=user.get("avatar_url") or "",
            hint_text=self.lang.t("avatarPlaceholder"),
            size_hint_y=None,
            height=dp(46),
        )
        box.add_widget(self._avatar)

        box.add_widget(label("Suggested future settings: change password, notification rules, weekly goals.", font_size=sp(11), height=dp(36), color=(0.33, 0.30, 0.24, 1)))

        box.add_widget(spacer(dp(8)))
        box.add_widget(label(self.lang.t("deleteAccount"), bold=True, font_size=sp(16), height=dp(26), color=(0.60, 0.22, 0.18, 1)))
        box.add_widget(label(self.lang.t("deleteAccountWarning"), font_size=sp(11), height=dp(36), color=(0.33, 0.30, 0.24, 1)))
        box.add_widget(label(self.lang.t("confirmPassword"), bold=True, font_size=sp(12), height=dp(20), color=(0.18, 0.15, 0.11, 1)))
        self._password = StyledInput(password=True, size_hint_y=None, height=dp(46))
        box.add_widget(self._password)

        btns = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10))
        close_btn = OutlineButton(text=self.lang.t("cancel"))
        close_btn.bind(on_release=lambda *_: self.dismiss())
        btns.add_widget(close_btn)
        self._save_btn = StyledButton(text=self.lang.t("saveChanges"))
        self._save_btn.bind(on_release=self._save_profile)
        btns.add_widget(self._save_btn)
        box.add_widget(btns)

        delete_btn = StyledButton(text=self.lang.t("deleteAccount"), bg=(0.75, 0.28, 0.22, 1), size_hint_y=None, height=dp(46))
        delete_btn.bind(on_release=self._delete_account)
        box.add_widget(delete_btn)

        scroll.add_widget(box)
        return scroll

    def _save_profile(self, *_):
        username = self._username.text.strip()
        avatar_url = self._avatar.text.strip()
        self._save_btn.text = self.lang.t("saving")
        threading.Thread(target=self._save_profile_thread, args=(username, avatar_url), daemon=True).start()

    def _save_profile_thread(self, username, avatar_url):
        try:
            self.auth.update_profile(username=username, avatar_url=avatar_url)
            Clock.schedule_once(lambda _dt: self._save_done())
        except Exception as exc:
            msg = str(exc)
            Clock.schedule_once(lambda _dt: self._save_error(msg))

    def _save_done(self):
        self._save_btn.text = self.lang.t("saveChanges")
        show_toast(self.lang.t("profileUpdated"))
        self.on_success()
        self.dismiss()

    def _save_error(self, msg):
        self._save_btn.text = self.lang.t("saveChanges")
        show_toast(msg or "Could not update profile", success=False)

    def _delete_account(self, *_):
        password = self._password.text.strip()
        if not password:
            show_toast(self.lang.t("confirmDelete"), success=False)
            return
        threading.Thread(target=self._delete_account_thread, args=(password,), daemon=True).start()

    def _delete_account_thread(self, password):
        try:
            self.auth.delete_account(password)
            Clock.schedule_once(lambda _dt: self._delete_done())
        except Exception as exc:
            msg = str(exc)
            Clock.schedule_once(lambda _dt: show_toast(msg or "Could not delete account", success=False))

    def _delete_done(self):
        show_toast(self.lang.t("accountDeleted"))
        self.on_success(account_deleted=True)
        self.dismiss()
