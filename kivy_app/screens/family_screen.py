"""Family screen."""

import threading
from datetime import datetime, timedelta, timezone

from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

from screens.widgets import (
    BottomNav,
    C_AMBER100,
    C_AMBER800,
    C_CREAM,
    C_INK,
    C_INK_SOFT,
    C_LEAF,
    C_WHITE,
    DropdownSpinner,
    HeaderBar,
    LoadingSpinner,
    OutlineButton,
    RoundedBox,
    StyledButton,
    StyledInput,
    StyledTextArea,
    label,
    show_toast,
)

CAT_OPTIONS = [
    ("general", "General"), ("work", "Work"), ("personal", "Personal"),
    ("health", "Health"), ("study", "Study"),
]
PRI_OPTIONS = [("low", "Low"), ("medium", "Medium"), ("high", "High")]


class FamilyScreen(Screen):
    def __init__(self, auth, lang, sm, **kwargs):
        super().__init__(**kwargs)
        self.auth = auth
        self.lang = lang
        self.sm = sm
        self.groups = []
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
        left = BoxLayout(orientation="vertical")
        left.add_widget(Label(text=t("familyGroups"), font_size=sp(22), bold=True, color=C_INK, halign="left"))
        self._grp_lbl = Label(text=f"0 {t('groups')}", font_size=sp(11), color=C_INK_SOFT, halign="left")
        left.add_widget(self._grp_lbl)
        hdr.add_widget(left)
        create_btn = StyledButton(text="+ Group", size_hint=(None, 1), width=dp(90))
        create_btn.bind(on_release=self._show_create)
        hdr.add_widget(create_btn)
        root.add_widget(hdr)

        scroll = ScrollView(do_scroll_x=False)
        self._body = BoxLayout(orientation="vertical", padding=[dp(14), dp(12), dp(14), dp(80)], spacing=dp(12), size_hint_y=None)
        self._body.bind(minimum_height=self._body.setter("height"))

        self._spinner = LoadingSpinner()
        self._body.add_widget(self._spinner)
        self._spinner.start()

        scroll.add_widget(self._body)
        root.add_widget(scroll)
        root.add_widget(BottomNav(current="family", on_navigate=self._navigate, lang=self.lang))
        self.add_widget(root)

    def on_enter(self, *_):
        if self.groups:
            self._render(self.groups)
        self._spinner.start()
        threading.Thread(target=self._fetch, daemon=True).start()

    def _fetch(self):
        try:
            groups = self.auth.get_family_groups()
            Clock.schedule_once(lambda _dt: self._render(groups))
        except Exception:
            Clock.schedule_once(lambda _dt: show_toast("Failed to load groups", success=False))

    def _render(self, groups):
        self._spinner.stop()
        self._spinner.text = ""
        self.groups = groups
        t = self.lang.t
        self._grp_lbl.text = f"{len(groups)} {t('groups')}"
        self._body.clear_widgets()

        if not groups:
            empty = RoundedBox(size_hint_y=None, height=dp(104), orientation="vertical", padding=[dp(16), dp(16)])
            empty.add_widget(label("Family", halign="center", font_size=sp(22), height=dp(38)))
            empty.add_widget(label(t("noFamilyGroups"), color=C_INK_SOFT, halign="center"))
            empty.add_widget(label(t("createGroupToManage"), color=C_INK_SOFT, font_size=sp(11), halign="center"))
            self._body.add_widget(empty)
            return

        for group in groups:
            self._body.add_widget(self._group_card(group))

    def _group_card(self, group):
        t = self.lang.t
        user_email = (self.auth.user or {}).get("email", "")
        user_member = next((m for m in group["members"] if m["email"] == user_email), None)
        is_admin = bool(user_member and user_member["role"] == "admin")
        count = len(group["members"])
        card_h = dp(52) + dp(28) + count * dp(54) + dp(20)

        card = RoundedBox(orientation="vertical", size_hint_y=None, height=card_h, padding=[dp(14), dp(12)], spacing=dp(8))
        top = BoxLayout(size_hint_y=None, height=dp(40))
        name_lbl = Label(text="Group  " + group["name"], font_size=sp(17), bold=True, color=C_INK, halign="left")
        name_lbl.bind(size=lambda i, v: setattr(i, "text_size", (v[0], None)))
        top.add_widget(name_lbl)
        if is_admin:
            btn = StyledButton(text=t("assignTask"), size_hint=(None, 1), width=dp(120))
            btn.bind(on_release=lambda *_args, g=group: self._show_assign(g))
            top.add_widget(btn)
        card.add_widget(top)
        card.add_widget(label(f"{t('members')} ({count}/8)", bold=True, font_size=sp(12), color=C_INK_SOFT, height=dp(22)))

        for member in group["members"]:
            row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
            row.add_widget(Label(text="Admin" if member["role"] == "admin" else "User", font_size=sp(10), size_hint=(None, 1), width=dp(40), color=C_INK))
            info = BoxLayout(orientation="vertical")
            info.add_widget(label(member["username"], bold=True, font_size=sp(12), height=dp(20)))
            info.add_widget(label(member["email"], color=C_INK_SOFT, font_size=sp(10), height=dp(16)))
            row.add_widget(info)

            badge_bg = C_AMBER100 if member["role"] == "admin" else (0.91, 0.90, 0.87, 1)
            badge_clr = C_AMBER800 if member["role"] == "admin" else C_INK_SOFT
            badge = BoxLayout(size_hint=(None, 1), width=dp(54))
            with badge.canvas.before:
                Color(*badge_bg)
                brr = RoundedRectangle(pos=badge.pos, size=badge.size, radius=[dp(10)])
            badge.bind(pos=lambda _i, v: setattr(brr, "pos", v), size=lambda _i, v: setattr(brr, "size", v))
            badge.add_widget(Label(text=t(member["role"]), font_size=sp(10), color=badge_clr))
            row.add_widget(badge)
            card.add_widget(row)

        return card

    def _show_create(self, *_):
        t = self.lang.t
        box = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(14))
        box.add_widget(label(t("groupName"), bold=True, height=dp(22)))
        name_inp = StyledInput(hint_text=t("groupNamePlaceholder"), size_hint_y=None, height=dp(50))
        box.add_widget(name_inp)
        box.add_widget(label(t("memberEmails"), bold=True, height=dp(22)))
        emails_inp = StyledTextArea(
            hint_text="email1@example.com, email2@example.com",
            size_hint_y=None,
            height=dp(70),
        )
        box.add_widget(emails_inp)
        box.add_widget(label(t("maxMembers"), color=C_INK_SOFT, font_size=sp(11), height=dp(18)))
        btns = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10))
        cancel = OutlineButton(text=t("cancel"))
        create = StyledButton(text=t("createGroup"))
        btns.add_widget(cancel)
        btns.add_widget(create)
        box.add_widget(btns)

        pop = Popup(title=t("createFamilyGroup"), content=box, size_hint=(0.92, None), height=dp(360), background="", background_color=(0, 0, 0, 0), overlay_color=(0, 0, 0, 0.50), title_color=C_INK)
        with pop.canvas.before:
            Color(*C_CREAM)
            rr = RoundedRectangle(pos=pop.pos, size=pop.size, radius=[dp(20)])
        pop.bind(pos=lambda _i, v: setattr(rr, "pos", v), size=lambda _i, v: setattr(rr, "size", v))
        cancel.bind(on_release=pop.dismiss)
        create.bind(on_release=lambda *_args: self._create_group(name_inp.text.strip(), emails_inp.text.strip(), pop))
        pop.open()

    def _create_group(self, name, emails_str, pop):
        emails = [email.strip() for email in emails_str.split(",") if email.strip()]
        if not name or not emails:
            show_toast("Please fill in all fields", success=False)
            return
        if len(emails) > 7:
            show_toast("Maximum 7 members (8 including you)", success=False)
            return
        pop.dismiss()
        threading.Thread(target=self._do_create, args=(name, emails), daemon=True).start()

    def _do_create(self, name, emails):
        try:
            self.auth.create_family_group({"name": name, "member_emails": emails})
            Clock.schedule_once(lambda _dt: (show_toast("Group created"), self.on_enter()))
        except Exception as exc:
            msg = str(exc)
            Clock.schedule_once(lambda _dt: show_toast(msg, success=False))

    def _show_assign(self, group):
        t = self.lang.t
        user_email = (self.auth.user or {}).get("email", "")
        others = [m for m in group["members"] if m["email"] != user_email]
        if not others:
            show_toast("No other members to assign to", success=False)
            return

        scroll = ScrollView(do_scroll_x=False)
        box = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(12), size_hint_y=None)
        box.bind(minimum_height=box.setter("height"))

        box.add_widget(label(t("assignTo"), bold=True, height=dp(22)))
        member_opts = [(m["email"], f"{m['username']} ({m['email']})") for m in others]
        assign_sp = DropdownSpinner(member_opts, size_hint_y=None, height=dp(48))
        box.add_widget(assign_sp)

        box.add_widget(label(t("taskTitle"), bold=True, height=dp(22)))
        title_inp = StyledInput(hint_text="Clean the garden", size_hint_y=None, height=dp(48))
        box.add_widget(title_inp)

        box.add_widget(label(t("description"), bold=True, height=dp(22)))
        desc_inp = StyledTextArea(
            hint_text="Task details...",
            size_hint_y=None,
            height=dp(64),
        )
        box.add_widget(desc_inp)

        cp_row = BoxLayout(size_hint_y=None, height=dp(72), spacing=dp(10))
        for lbl_text, opts, default, attr in [("Category", CAT_OPTIONS, "general", "_ac"), ("Priority", PRI_OPTIONS, "medium", "_ap")]:
            col = BoxLayout(orientation="vertical", spacing=dp(4))
            col.add_widget(label(lbl_text, bold=True, height=dp(20), font_size=sp(12), color=C_INK_SOFT))
            spinner = DropdownSpinner(opts, value=default, size_hint_y=None, height=dp(46))
            setattr(self, attr, spinner)
            col.add_widget(spinner)
            cp_row.add_widget(col)
        box.add_widget(cp_row)

        box.add_widget(label(t("timeLimit"), bold=True, height=dp(22)))
        time_row = BoxLayout(size_hint_y=None, height=dp(72), spacing=dp(8))
        d_inp = StyledInput(hint_text=t("days"), text="0", input_filter="int", size_hint_y=None, height=dp(48))
        h_inp = StyledInput(hint_text=t("hours"), text="1", input_filter="int", size_hint_y=None, height=dp(48))
        m_inp = StyledInput(hint_text=t("minutes"), text="0", input_filter="int", size_hint_y=None, height=dp(48))
        for inp, lbl_text in [(d_inp, t("days")), (h_inp, t("hours")), (m_inp, t("minutes"))]:
            col = BoxLayout(orientation="vertical", spacing=dp(4))
            col.add_widget(inp)
            col.add_widget(label(lbl_text, color=C_INK_SOFT, font_size=sp(10), height=dp(16), halign="center"))
            time_row.add_widget(col)
        box.add_widget(time_row)

        btns = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        cancel = OutlineButton(text=t("cancel"))
        assign = StyledButton(text=t("assignTask"))
        btns.add_widget(cancel)
        btns.add_widget(assign)
        box.add_widget(btns)
        scroll.add_widget(box)

        pop = Popup(title=t("assignTask"), content=scroll, size_hint=(0.93, None), height=dp(560), background="", background_color=(0, 0, 0, 0), overlay_color=(0, 0, 0, 0.50), title_color=C_INK)
        with pop.canvas.before:
            Color(*C_CREAM)
            rr = RoundedRectangle(pos=pop.pos, size=pop.size, radius=[dp(20)])
        pop.bind(pos=lambda _i, v: setattr(rr, "pos", v), size=lambda _i, v: setattr(rr, "size", v))
        cancel.bind(on_release=pop.dismiss)
        assign.bind(on_release=lambda *_args: self._do_assign_task(group, assign_sp.value, title_inp.text.strip(), desc_inp.text.strip(), self._ac.value, self._ap.value, d_inp.text, h_inp.text, m_inp.text, pop))
        pop.open()

    def _do_assign_task(self, group, email, title, desc, cat, pri, d, h, m, pop):
        if not email or not title:
            show_toast("Please fill in required fields", success=False)
            return
        try:
            secs = int(d or 0) * 86400 + int(h or 0) * 3600 + int(m or 0) * 60
        except ValueError:
            show_toast("Invalid time values", success=False)
            return
        if secs <= 0:
            show_toast("Please set a time limit", success=False)
            return
        deadline = (datetime.now(timezone.utc) + timedelta(seconds=secs)).isoformat()
        data = {
            "group_id": group["id"],
            "assigned_to_email": email,
            "title": title,
            "description": desc or None,
            "category": cat,
            "priority": pri,
            "deadline": deadline,
            "time_remaining_seconds": secs,
        }
        pop.dismiss()
        threading.Thread(target=self._do_assign, args=(group["id"], data), daemon=True).start()

    def _do_assign(self, gid, data):
        try:
            self.auth.assign_group_task(gid, data)
            Clock.schedule_once(lambda _dt: show_toast(self.lang.t("taskAssignedSuccess")))
        except Exception as exc:
            msg = str(exc)
            Clock.schedule_once(lambda _dt: show_toast(msg, success=False))

    def _navigate(self, screen):
        self.sm.current = screen

    def refresh_language(self):
        self._build()
        self._render(self.groups)
