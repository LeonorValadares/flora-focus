"""Friends screen."""

import threading

from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView

from screens.widgets import (
    BottomNav,
    C_CREAM,
    C_INK,
    C_INK_SOFT,
    C_MINT,
    FLOWER_POSITIONS,
    FlowerWidget,
    GardenPanel,
    HeaderBar,
    LoadingSpinner,
    OutlineButton,
    RoundedBox,
    StyledButton,
    StyledInput,
    label,
    palette_for,
    section_heading,
    show_toast,
    spacer,
)


class FriendsScreen(Screen):
    def __init__(self, auth, lang, sm, **kwargs):
        super().__init__(**kwargs)
        self.auth = auth
        self.lang = lang
        self.sm = sm
        self.friends = []
        self.reqs = []
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
        left.add_widget(Label(text=t("friends"), font_size=sp(22), bold=True, color=C_INK, halign="left"))
        self._buddy_lbl = Label(text=f"0 {t('gardenBuddies')}", font_size=sp(11), color=C_INK_SOFT, halign="left")
        left.add_widget(self._buddy_lbl)
        hdr.add_widget(left)
        add_btn = StyledButton(text="+ Add", size_hint=(None, 1), width=dp(72))
        add_btn.bind(on_release=self._show_add)
        hdr.add_widget(add_btn)
        root.add_widget(hdr)

        scroll = ScrollView(do_scroll_x=False)
        self._body = BoxLayout(orientation="vertical", padding=[dp(14), dp(12), dp(14), dp(80)], spacing=dp(10), size_hint_y=None)
        self._body.bind(minimum_height=self._body.setter("height"))

        self._spinner = LoadingSpinner()
        self._body.add_widget(self._spinner)
        self._spinner.start()

        scroll.add_widget(self._body)
        root.add_widget(scroll)
        root.add_widget(BottomNav(current="friends", on_navigate=self._navigate, lang=self.lang))
        self.add_widget(root)

    def on_enter(self, *_):
        if self.friends or self.reqs:
            self._render(self.friends, self.reqs)
        self._spinner.start()
        threading.Thread(target=self._fetch, daemon=True).start()

    def _fetch(self):
        try:
            friends = self.auth.get_friends()
            reqs = self.auth.get_friend_requests()
            Clock.schedule_once(lambda _dt: self._render(friends, reqs))
        except Exception:
            Clock.schedule_once(lambda _dt: show_toast("Failed to load friends", success=False))

    def _render(self, friends, reqs):
        self._spinner.stop()
        self._spinner.text = ""
        self.friends = friends
        self.reqs = reqs
        t = self.lang.t
        self._buddy_lbl.text = f"{len(friends)} {t('gardenBuddies')}"
        self._body.clear_widgets()

        if reqs:
            self._body.add_widget(section_heading(t("friendRequests")))
            for req in reqs:
                self._body.add_widget(self._req_card(req))
            self._body.add_widget(spacer(dp(6)))

        self._body.add_widget(section_heading(t("yourFriends")))
        if not friends:
            empty = RoundedBox(size_hint_y=None, height=dp(88), orientation="vertical", padding=[dp(16), dp(16)])
            empty.add_widget(label("Friends", halign="center", font_size=sp(20), height=dp(36)))
            empty.add_widget(label(t("noFriends"), color=C_INK_SOFT, halign="center"))
            self._body.add_widget(empty)

        for friend in friends:
            self._body.add_widget(self._friend_card(friend))

    def _req_card(self, req):
        card = RoundedBox(
            orientation="horizontal",
            bg_color=C_MINT,
            border_color=C_MINT,
            size_hint_y=None,
            height=dp(66),
            padding=[dp(12), dp(8)],
            spacing=dp(10),
        )
        card.add_widget(Label(text="User", font_size=sp(12), size_hint=(None, 1), width=dp(34), color=C_INK))
        info = BoxLayout(orientation="vertical")
        info.add_widget(label(req["user"]["username"], bold=True, font_size=sp(13), height=dp(22)))
        info.add_widget(label(req["user"]["email"], color=C_INK_SOFT, font_size=sp(11), height=dp(18)))
        card.add_widget(info)
        accept = StyledButton(text="Accept", size_hint=(None, 1), width=dp(86))
        accept.bind(on_release=lambda *_args, fid=req["friendship_id"]: self._accept(fid))
        card.add_widget(accept)
        return card

    def _friend_card(self, friend):
        t = self.lang.t
        card = RoundedBox(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(66),
            padding=[dp(12), dp(8)],
            spacing=dp(10),
        )
        card.add_widget(Label(text="Pal", font_size=sp(12), size_hint=(None, 1), width=dp(34), color=C_INK))
        info = BoxLayout(orientation="vertical")
        name_btn = Button(
            text=friend["user"]["username"],
            background_normal="",
            background_color=(0, 0, 0, 0),
            color=C_INK,
            bold=True,
            size_hint_y=None,
            height=dp(22),
        )
        name_btn.bind(on_release=lambda *_args, em=friend["user"]["email"]: self._view_garden(em))
        info.add_widget(name_btn)
        info.add_widget(label(friend["user"]["email"], color=C_INK_SOFT, font_size=sp(11), height=dp(18)))
        card.add_widget(info)
        view = OutlineButton(text=t("viewGarden"), size_hint=(None, 1), width=dp(110))
        view.bind(on_release=lambda *_args, em=friend["user"]["email"]: self._view_garden(em))
        card.add_widget(view)
        return card

    def _accept(self, fid):
        threading.Thread(target=self._do_accept, args=(fid,), daemon=True).start()

    def _do_accept(self, fid):
        try:
            self.auth.accept_friend_request(fid)
            Clock.schedule_once(lambda _dt: (show_toast(self.lang.t("friendRequestAccepted")), self.on_enter()))
        except Exception:
            Clock.schedule_once(lambda _dt: show_toast("Failed to accept request", success=False))

    def _show_add(self, *_):
        t = self.lang.t
        box = BoxLayout(orientation="vertical", spacing=dp(12), padding=dp(14))
        box.add_widget(label(t("friendEmail"), bold=True, height=dp(22)))
        inp = StyledInput(hint_text="friend@email.com", size_hint_y=None, height=dp(50))
        box.add_widget(inp)
        btns = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10))
        cancel = OutlineButton(text=t("cancel"))
        send = StyledButton(text=t("sendRequest"))
        btns.add_widget(cancel)
        btns.add_widget(send)
        box.add_widget(btns)
        pop = Popup(title=t("addFriend"), content=box, size_hint=(0.88, None), height=dp(230), background="", background_color=(0, 0, 0, 0), overlay_color=(0, 0, 0, 0.50), title_color=C_INK)
        with pop.canvas.before:
            Color(*C_CREAM)
            rr = RoundedRectangle(pos=pop.pos, size=pop.size, radius=[dp(20)])
        pop.bind(pos=lambda _i, v: setattr(rr, "pos", v), size=lambda _i, v: setattr(rr, "size", v))
        cancel.bind(on_release=pop.dismiss)
        send.bind(on_release=lambda *_args: self._send_req(inp.text.strip(), pop))
        pop.open()

    def _send_req(self, email, pop):
        if not email:
            show_toast("Please enter an email address", success=False)
            return
        pop.dismiss()
        threading.Thread(target=self._do_send, args=(email,), daemon=True).start()

    def _do_send(self, email):
        try:
            self.auth.send_friend_request(email)
            Clock.schedule_once(lambda _dt: show_toast(self.lang.t("friendRequestSent")))
        except Exception as exc:
            msg = str(exc)
            Clock.schedule_once(lambda _dt: show_toast(msg, success=False))

    def _view_garden(self, email):
        threading.Thread(target=self._fetch_garden, args=(email,), daemon=True).start()

    def _fetch_garden(self, email):
        try:
            data = self.auth.get_friend_garden(email)
            Clock.schedule_once(lambda _dt: self._garden_popup(data))
        except Exception:
            Clock.schedule_once(lambda _dt: show_toast("Failed to load garden", success=False))

    def _garden_popup(self, data):
        uname = (data.get("user") or {}).get("username", "Friend")
        completed = [task for task in (data.get("tasks") or []) if task["status"] == "completed"]

        panel = GardenPanel(size_hint_y=None, height=dp(200))
        if not completed:
            panel.add_widget(Label(text=self.lang.t("noFlowers"), color=C_INK_SOFT, size_hint=(1, 1)))
        else:
            for idx, task in enumerate(completed[:8]):
                petal, center = palette_for(task["id"])
                flower = FlowerWidget(stage="blooming", petal_color=petal, center_color=center, size=(dp(58), dp(58)))
                panel.add_widget(flower)
                rx, ry = FLOWER_POSITIONS[idx % len(FLOWER_POSITIONS)]
                Clock.schedule_once(
                    lambda _dt, w=flower, x=rx, y=ry: setattr(w, "pos", (panel.x + x * panel.width - w.width / 2, panel.y + y * panel.height - w.height / 2)),
                    0,
                )

        box = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(10))
        box.add_widget(panel)
        box.add_widget(label(f"{len(completed)} {self.lang.t('flowersBloomin')}", halign="center", color=C_INK_SOFT))
        pop = Popup(title=f"{uname}{self.lang.t('yourGarden')}", content=box, size_hint=(0.92, None), height=dp(320), background="", background_color=(0, 0, 0, 0), overlay_color=(0, 0, 0, 0.50), title_color=C_INK)
        with pop.canvas.before:
            Color(*C_CREAM)
            rr = RoundedRectangle(pos=pop.pos, size=pop.size, radius=[dp(20)])
        pop.bind(pos=lambda _i, v: setattr(rr, "pos", v), size=lambda _i, v: setattr(rr, "size", v))
        pop.open()

    def _navigate(self, screen):
        self.sm.current = screen

    def refresh_language(self):
        self._build()
        self._render(self.friends, self.reqs)
