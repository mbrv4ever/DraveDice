#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DraveDice - dobbelsteen-roller voor D&D en andere tafelspellen.
Dravenlock-huisstijl. Lokaal, offline, toegankelijk (grote tekst, hoog contrast).
Klik een dobbelsteen om te gooien, of typ een eigen worp (bijv. 2d6+3).
"""
import os
import sys
import json
import random
import re

from PyQt6.QtCore import Qt, QLocale, QUrl, pyqtSignal
from PyQt6.QtGui import (QPixmap, QImage, QPainter, QColor, QBrush, QPen,
                         QIcon, QDesktopServices, QFont)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QGridLayout, QLineEdit, QSpinBox, QComboBox, QFrame,
    QMessageBox, QDialog, QToolButton, QStatusBar, QPlainTextEdit,
    QListWidget, QListWidgetItem, QSizePolicy)

APP_NAME = "DraveDice"
APP_VERSION = "0.2.1"
DONATE_URL = "https://paypal.me/roger076"
SUPPORT_MAIL = "service@dravenlock.nl"

# ---- Dravenlock-huisstijl ----
BG = "#0e0e11"
PANEL = "#16161b"
SILVER = "#d4d4d4"
MUTE = "#8a8a94"
ACCENT = "#6fa3d6"
GOOD = "#4fb477"
WARN = "#e0a23a"
BAD = "#d6645f"

DICE = [4, 6, 8, 10, 12, 20, 100]
HISTORY_MAX = 20


# ---------------------------------------------------------------------------
# Pad-helpers (frozen-bewust)
# ---------------------------------------------------------------------------
def _app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def _config_path():
    return os.path.join(_app_dir(), "dravedice_config.json")


DEFAULT_CONFIG = {"lang": ""}


def load_config():
    cfg = dict(DEFAULT_CONFIG)
    try:
        with open(_config_path(), "r", encoding="utf-8") as f:
            cfg.update(json.load(f))
    except Exception:
        pass
    return cfg


def save_config(cfg):
    try:
        with open(_config_path(), "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Taal (NL basis + OS-detectie + handmatige keuze)
# ---------------------------------------------------------------------------
_LANG = "nl"

TRANSLATIONS = {
    "en": {
        "Instellingen\u2026": "Settings\u2026", "Snelgids": "Quick guide",
        "Over": "About", "Sluiten": "Close", "Taal:": "Language:",
        "Automatisch (OS)": "Automatic (OS)", "Nederlands": "Dutch",
        "Engels": "English", "Donatie": "Donate",
        "Sommige instellingen gaan pas in na herstarten.":
            "Some settings apply after a restart.",
        "Dobbelstenen": "Dice",
        "Klik een dobbelsteen om te gooien": "Click a die to roll",
        "Modifier": "Modifier", "Worp": "Roll", "Gooi": "Roll",
        "Minder": "Less", "Meer": "More",
        "Eigen worp": "Custom roll",
        "bijv. 2d6+3": "e.g. 2d6+3",
        "Normaal": "Normal", "Voordeel": "Advantage", "Nadeel": "Disadvantage",
        "voordeel": "advantage", "nadeel": "disadvantage",
        "Modus (alleen d20):": "Mode (d20 only):",
        "Totaal": "Total", "Geschiedenis": "History", "Wissen": "Clear",
        "Gooi iets om te beginnen": "Roll something to get started",
        "KRITIEK!": "CRITICAL!", "Misser!": "Critical miss!",
        "Ongeldige worp. Probeer bijv. 2d6+3 of 1d20.":
            "Invalid roll. Try e.g. 2d6+3 or 1d20.",
        "snelgids_titel": "DraveDice - quick guide",
    }
}


def detect_lang(cfg):
    forced = (cfg.get("lang") or "").strip().lower()
    if forced in ("nl", "en"):
        return forced
    try:
        loc = QLocale.system().name().lower()
        if loc.startswith("nl"):
            return "nl"
        return "en"
    except Exception:
        return "nl"


def t(s, lang=None):
    lg = lang or _LANG
    if lg == "nl":
        return s
    return TRANSLATIONS.get(lg, {}).get(s, s)


# ---------------------------------------------------------------------------
# Logo / icoon
# ---------------------------------------------------------------------------
def make_logo(size=32):
    """Eenvoudig d20-achtig icoon als val-terug (normaal gebruiken we logo.png)."""
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    s = size
    from PyQt6.QtCore import QPointF
    from PyQt6.QtGui import QPolygonF
    cx, cy, r = s * 0.5, s * 0.52, s * 0.42
    pts = []
    import math
    for i in range(6):
        ang = math.radians(60 * i - 90)
        pts.append(QPointF(cx + r * math.cos(ang), cy + r * math.sin(ang)))
    p.setBrush(QBrush(QColor(ACCENT)))
    p.setPen(QPen(QColor(BG), max(1, int(s * 0.04))))
    p.drawPolygon(QPolygonF(pts))
    p.setPen(QPen(QColor(BG), max(1, int(s * 0.03))))
    p.drawLine(int(cx), int(cy - r), int(cx), int(cy))
    p.drawLine(int(cx), int(cy), int(cx - r * 0.85), int(cy + r * 0.5))
    p.drawLine(int(cx), int(cy), int(cx + r * 0.85), int(cy + r * 0.5))
    p.end()
    return pm


def _logo_path():
    dirs = [_app_dir()]
    mp = getattr(sys, "_MEIPASS", None)
    if mp:
        dirs.append(mp)
    dirs.append(os.path.join(_app_dir(), "_internal"))
    for d in dirs:
        for name in ("logo.ico", "logo.png"):
            p = os.path.join(d, name)
            if os.path.exists(p):
                return p
    return None


def app_icon():
    p = _logo_path()
    if p:
        ic = QIcon(p)
        if not ic.isNull():
            return ic
    return QIcon(make_logo(64))


def logo_pixmap(size=32):
    p = _logo_path()
    if p:
        pm = QPixmap(p)
        if not pm.isNull():
            return pm.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio,
                             Qt.TransformationMode.SmoothTransformation)
    return make_logo(size)


# ---------------------------------------------------------------------------
# Dobbel-logica
# ---------------------------------------------------------------------------
def roll_die(sides):
    return random.randint(1, sides)


def roll_single(sides, modifier=0, mode="normal"):
    """Eén dobbelsteen gooien. Voor d20 kan voordeel/nadeel (twee keer)."""
    if sides == 20 and mode in ("adv", "dis"):
        a, b = roll_die(20), roll_die(20)
        chosen = max(a, b) if mode == "adv" else min(a, b)
        return {
            "kind": "single", "sides": sides, "mode": mode,
            "rolls": [a, b], "chosen": chosen,
            "modifier": modifier, "total": chosen + modifier,
        }
    r = roll_die(sides)
    return {
        "kind": "single", "sides": sides, "mode": "normal",
        "rolls": [r], "chosen": r,
        "modifier": modifier, "total": r + modifier,
    }


def parse_and_roll(expr):
    """Worp-notatie gooien, bijv. '2d6+3', '1d20-1', 'd8+1d4+2'.
    Geeft (total, parts, mod). Gooit ValueError bij onzin."""
    s = (expr or "").lower().replace(" ", "")
    if not s:
        raise ValueError("leeg")
    if not re.fullmatch(r'[0-9d+\-]+', s):
        raise ValueError("ongeldige tekens")
    tokens = re.findall(r'[+\-]?[^+\-]+', s)
    if not tokens:
        raise ValueError("geen termen")
    total = 0
    mod = 0
    parts = []
    for tk in tokens:
        sign = 1
        if tk.startswith('+'):
            tk = tk[1:]
        elif tk.startswith('-'):
            sign = -1
            tk = tk[1:]
        if not tk:
            raise ValueError("losse +/-")
        if 'd' in tk:
            a, _, b = tk.partition('d')
            count = int(a) if a else 1
            if not b:
                raise ValueError("geen zijden")
            sides = int(b)
            if count < 1 or count > 100 or sides < 1 or sides > 1000:
                raise ValueError("buiten bereik")
            rolls = [roll_die(sides) for _ in range(count)]
            for r in rolls:
                total += sign * r
            parts.append({"sign": sign, "count": count, "sides": sides,
                          "rolls": rolls})
        else:
            v = int(tk)
            total += sign * v
            mod += sign * v
            parts.append({"sign": sign, "count": None, "sides": None,
                          "value": v})
    return total, parts, mod


# ---------------------------------------------------------------------------
# Snelgids
# ---------------------------------------------------------------------------
GUIDE_NL = """DraveDice - Snelgids

DraveDice gooit dobbelstenen voor D&D en andere tafelspellen. Lokaal en
offline, met grote, goed leesbare cijfers.

Snel gooien
- Klik op een dobbelsteen (d4 t/m d100) om er meteen een te gooien.
- De modifier (- / +) wordt bij die worp opgeteld.
- Modus 'Voordeel' of 'Nadeel' geldt voor de d20: hij gooit dan twee keer
  en neemt de hoogste (voordeel) of laagste (nadeel).

Eigen worp
- Typ een worp in het vak, bijvoorbeeld:
    2d6+3   (twee zesvlakken plus drie)
    1d20-1  (een twintigvlak min een)
    1d8+1d4+2  (combineren mag)
- Klik 'Gooi' of druk op Enter.

Resultaat
- Het grote getal is het totaal. Daaronder zie je elke worp apart.
- Een natuurlijke 20 op een losse d20 = KRITIEK; een natuurlijke 1 = misser.
- Onder 'Geschiedenis' staan je laatste worpen. 'Wissen' maakt 'm leeg.

Vragen of een tip? service@dravenlock.nl
"""

GUIDE_EN = """DraveDice - Quick guide

DraveDice rolls dice for D&D and other tabletop games. Local and offline,
with large, easy-to-read numbers.

Quick roll
- Click a die (d4 to d100) to roll one immediately.
- The modifier (- / +) is added to that roll.
- Mode 'Advantage' or 'Disadvantage' applies to the d20: it rolls twice and
  takes the highest (advantage) or lowest (disadvantage).

Custom roll
- Type a roll in the box, for example:
    2d6+3   (two six-sided plus three)
    1d20-1  (one twenty-sided minus one)
    1d8+1d4+2  (combining is fine)
- Click 'Roll' or press Enter.

Result
- The big number is the total. Below it you see each roll separately.
- A natural 20 on a single d20 = CRITICAL; a natural 1 = critical miss.
- 'History' shows your recent rolls. 'Clear' empties it.

Questions or feedback? service@dravenlock.nl
"""


class GuideDialog(QDialog):
    def __init__(self, parent, lang):
        super().__init__(parent)
        self.setWindowTitle(t("snelgids_titel", lang))
        self.setWindowIcon(app_icon())
        self.resize(560, 520)
        lay = QVBoxLayout(self)
        box = QPlainTextEdit()
        box.setReadOnly(True)
        box.setObjectName("guide")
        box.setPlainText(GUIDE_NL if lang == "nl" else GUIDE_EN)
        lay.addWidget(box)
        row = QHBoxLayout()
        donate = QPushButton("\u2665 " + t("Donatie", lang))
        donate.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(DONATE_URL)))
        row.addWidget(donate)
        row.addStretch(1)
        close = QPushButton(t("Sluiten", lang))
        close.clicked.connect(self.accept)
        row.addWidget(close)
        lay.addLayout(row)


# ---------------------------------------------------------------------------
# Instellingen
# ---------------------------------------------------------------------------
class SettingsDialog(QDialog):
    def __init__(self, parent, cfg, lang):
        super().__init__(parent)
        self.cfg = cfg
        self.setWindowTitle(t("Instellingen\u2026", lang))
        self.setWindowIcon(app_icon())
        self.resize(360, 160)
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel(t("Taal:", lang)))
        self.langbox = QComboBox()
        self.langbox.addItem(t("Automatisch (OS)", lang), "")
        self.langbox.addItem(t("Nederlands", lang), "nl")
        self.langbox.addItem(t("Engels", lang), "en")
        self.langbox.setCurrentIndex(
            {"": 0, "nl": 1, "en": 2}.get(cfg.get("lang", ""), 0))
        lay.addWidget(self.langbox)
        hint = QLabel(t("Sommige instellingen gaan pas in na herstarten.", lang))
        hint.setObjectName("hint")
        hint.setWordWrap(True)
        lay.addWidget(hint)
        lay.addStretch(1)
        row = QHBoxLayout()
        row.addStretch(1)
        ok = QPushButton("OK")
        ok.clicked.connect(self.accept)
        row.addWidget(ok)
        lay.addLayout(row)

    def result_cfg(self):
        self.cfg["lang"] = self.langbox.currentData()
        return self.cfg


# ---------------------------------------------------------------------------
# Hoofdvenster
# ---------------------------------------------------------------------------
class DraveDice(QMainWindow):
    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        self.lang = _LANG
        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(app_icon())
        self.resize(720, 760)

        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(self._header())

        body = QWidget()
        bl = QVBoxLayout(body)
        bl.setContentsMargins(18, 16, 18, 16)
        bl.setSpacing(14)
        outer.addWidget(body, 1)

        # --- dobbelknoppen ---
        lbl_dice = QLabel(t("Dobbelstenen", self.lang))
        lbl_dice.setObjectName("section")
        bl.addWidget(lbl_dice)
        grid = QGridLayout()
        grid.setSpacing(10)
        for i, sides in enumerate(DICE):
            b = QPushButton("d%d" % sides)
            b.setObjectName("die")
            b.setMinimumHeight(64)
            b.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            b.clicked.connect(lambda _=False, s=sides: self.roll_die(s))
            grid.addWidget(b, i // 4, i % 4)
        bl.addLayout(grid)

        # --- modifier + modus ---
        opts = QHBoxLayout()
        opts.setSpacing(8)
        opts.addWidget(QLabel(t("Modifier", self.lang)))
        self._mod = 0
        self.b_modminus = QToolButton()
        self.b_modminus.setText("\u2212")
        self.b_modminus.setObjectName("step")
        self.b_modminus.setToolTip(t("Minder", self.lang))
        self.b_modminus.clicked.connect(lambda: self._bump_mod(-1))
        opts.addWidget(self.b_modminus)
        self.mod_lbl = QLabel()
        self.mod_lbl.setObjectName("modreadout")
        self.mod_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mod_lbl.setMinimumWidth(48)
        opts.addWidget(self.mod_lbl)
        self.b_modplus = QToolButton()
        self.b_modplus.setText("+")
        self.b_modplus.setObjectName("step")
        self.b_modplus.setToolTip(t("Meer", self.lang))
        self.b_modplus.clicked.connect(lambda: self._bump_mod(+1))
        opts.addWidget(self.b_modplus)
        self._update_mod_label()
        opts.addSpacing(16)
        opts.addWidget(QLabel(t("Modus (alleen d20):", self.lang)))
        self.mode = QComboBox()
        self.mode.addItem(t("Normaal", self.lang), "normal")
        self.mode.addItem(t("Voordeel", self.lang), "adv")
        self.mode.addItem(t("Nadeel", self.lang), "dis")
        opts.addWidget(self.mode)
        opts.addStretch(1)
        bl.addLayout(opts)

        # --- eigen worp ---
        custom = QHBoxLayout()
        custom.setSpacing(8)
        clabel = QLabel(t("Eigen worp", self.lang))
        custom.addWidget(clabel)
        self.expr = QLineEdit()
        self.expr.setObjectName("expr")
        self.expr.setPlaceholderText(t("bijv. 2d6+3", self.lang))
        self.expr.returnPressed.connect(self.roll_custom)
        custom.addWidget(self.expr, 1)
        self.b_roll = QPushButton(t("Gooi", self.lang))
        self.b_roll.setObjectName("primary")
        self.b_roll.clicked.connect(self.roll_custom)
        custom.addWidget(self.b_roll)
        bl.addLayout(custom)

        # --- resultaat ---
        res = QFrame()
        res.setObjectName("resultbox")
        rl = QVBoxLayout(res)
        rl.setContentsMargins(16, 14, 16, 14)
        rl.setSpacing(4)
        self.total_lbl = QLabel(t("Gooi iets om te beginnen", self.lang))
        self.total_lbl.setObjectName("total")
        self.total_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.total_lbl.setWordWrap(True)
        rl.addWidget(self.total_lbl)
        self.detail_lbl = QLabel("")
        self.detail_lbl.setObjectName("detail")
        self.detail_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.detail_lbl.setWordWrap(True)
        rl.addWidget(self.detail_lbl)
        self.crit_lbl = QLabel("")
        self.crit_lbl.setObjectName("crit")
        self.crit_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rl.addWidget(self.crit_lbl)
        bl.addWidget(res)

        # --- geschiedenis ---
        hrow = QHBoxLayout()
        hlabel = QLabel(t("Geschiedenis", self.lang))
        hlabel.setObjectName("section")
        hrow.addWidget(hlabel)
        hrow.addStretch(1)
        clear = QPushButton(t("Wissen", self.lang))
        clear.clicked.connect(self.clear_history)
        hrow.addWidget(clear)
        bl.addLayout(hrow)
        self.history = QListWidget()
        self.history.setObjectName("history")
        bl.addWidget(self.history, 1)

        # --- statusbalk ---
        sb = QStatusBar()
        self.setStatusBar(sb)
        sb.addPermanentWidget(QLabel("v" + APP_VERSION))
        donate = QToolButton()
        donate.setText("\u2665 " + t("Donatie", self.lang))
        donate.setObjectName("donate")
        donate.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(DONATE_URL)))
        sb.addPermanentWidget(donate)

    # ---- UI-opbouw ----
    def _header(self):
        w = QWidget()
        w.setObjectName("header")
        w.setFixedHeight(56)
        lay = QHBoxLayout(w)
        lay.setContentsMargins(14, 8, 14, 8)
        logo = QLabel()
        logo.setPixmap(logo_pixmap(30))
        lay.addWidget(logo)
        title = QLabel(APP_NAME)
        title.setObjectName("title")
        lay.addWidget(title)
        ver = QLabel("v" + APP_VERSION)
        ver.setObjectName("ver")
        lay.addWidget(ver)
        lay.addStretch(1)
        for label, slot in [(t("Instellingen\u2026", self.lang), self._settings),
                            (t("Snelgids", self.lang), self._guide),
                            (t("Over", self.lang), self._about)]:
            b = QPushButton(label)
            b.clicked.connect(lambda _=False, s=slot: s())
            lay.addWidget(b)
        return w

    # ---- modifier ----
    def _bump_mod(self, d):
        self._mod = max(-50, min(50, self._mod + d))
        self._update_mod_label()

    def _update_mod_label(self):
        if self._mod > 0:
            self.mod_lbl.setText("+%d" % self._mod)
        elif self._mod < 0:
            self.mod_lbl.setText("\u2212%d" % abs(self._mod))
        else:
            self.mod_lbl.setText("0")

    # ---- gooien ----
    def roll_die(self, sides):
        mode = self.mode.currentData() if sides == 20 else "normal"
        res = roll_single(sides, self._mod, mode)
        self._show_single(res)

    def roll_custom(self):
        expr = self.expr.text().strip()
        if not expr:
            return
        try:
            total, parts, mod = parse_and_roll(expr)
        except Exception:
            QMessageBox.information(
                self, APP_NAME,
                t("Ongeldige worp. Probeer bijv. 2d6+3 of 1d20.", self.lang))
            return
        self._show_custom(expr, total, parts)

    # ---- resultaat tonen ----
    def _show_single(self, res):
        sides = res["sides"]
        mod = res["modifier"]
        total = res["total"]
        self.total_lbl.setText(str(total))
        self.crit_lbl.setText("")
        self.crit_lbl.setProperty("kind", "")
        if res["mode"] in ("adv", "dis"):
            a, b = res["rolls"]
            modename = t("voordeel" if res["mode"] == "adv" else "nadeel", self.lang)
            detail = "d20 (%s): %d / %d \u2192 %d" % (modename, a, b, res["chosen"])
            if mod:
                detail += " %s%d = %d" % ("+" if mod >= 0 else "\u2212",
                                          abs(mod), total)
            self.detail_lbl.setText(detail)
            self._crit_check(res["chosen"], 20)
        else:
            r = res["chosen"]
            detail = "d%d: %d" % (sides, r)
            if mod:
                detail += " %s%d = %d" % ("+" if mod >= 0 else "\u2212",
                                          abs(mod), total)
            self.detail_lbl.setText(detail)
            if sides == 20:
                self._crit_check(r, 20)
        self._add_history(self._summary_single(res))
        self._restyle_crit()

    def _show_custom(self, expr, total, parts):
        self.total_lbl.setText(str(total))
        self.detail_lbl.setText(self._breakdown(parts))
        self.crit_lbl.setText("")
        self.crit_lbl.setProperty("kind", "")
        self._restyle_crit()
        self._add_history("%s = %d   (%s)" % (expr, total,
                                              self._breakdown(parts, short=True)))

    def _crit_check(self, value, sides):
        if value == sides:
            self.crit_lbl.setText("\u2605 " + t("KRITIEK!", self.lang))
            self.crit_lbl.setProperty("kind", "good")
        elif value == 1:
            self.crit_lbl.setText(t("Misser!", self.lang))
            self.crit_lbl.setProperty("kind", "bad")

    def _restyle_crit(self):
        self.crit_lbl.style().unpolish(self.crit_lbl)
        self.crit_lbl.style().polish(self.crit_lbl)

    def _breakdown(self, parts, short=False):
        bits = []
        for p in parts:
            sign = "\u2212" if p["sign"] < 0 else "+"
            if p["sides"] is None:
                bits.append("%s%d" % (sign, p["value"]))
            else:
                rolls = ",".join(str(r) for r in p["rolls"])
                tag = "%dd%d" % (p["count"], p["sides"])
                bits.append("%s%s[%s]" % (sign if bits else "", tag, rolls))
        text = " ".join(bits).strip()
        if text.startswith("+"):
            text = text[1:].strip()
        return text

    def _summary_single(self, res):
        sides = res["sides"]
        mod = res["modifier"]
        if res["mode"] in ("adv", "dis"):
            a, b = res["rolls"]
            tag = "d20 %s" % t("voordeel" if res["mode"] == "adv" else "nadeel",
                               self.lang)
            base = "%s: %d/%d\u2192%d" % (tag, a, b, res["chosen"])
        else:
            base = "d%d: %d" % (sides, res["chosen"])
        if mod:
            base += " %s%d" % ("+" if mod >= 0 else "\u2212", abs(mod))
        return "%s = %d" % (base, res["total"])

    def _add_history(self, line):
        item = QListWidgetItem(line)
        self.history.insertItem(0, item)
        while self.history.count() > HISTORY_MAX:
            self.history.takeItem(self.history.count() - 1)

    def clear_history(self):
        self.history.clear()

    # ---- menu's ----
    def _settings(self):
        dlg = SettingsDialog(self, dict(self.cfg), self.lang)
        if dlg.exec():
            self.cfg = dlg.result_cfg()
            save_config(self.cfg)

    def _guide(self):
        GuideDialog(self, self.lang).exec()

    def _about(self):
        QMessageBox.information(
            self, t("Over", self.lang),
            "%s v%s\n\n%s\nDravenlock\n%s\n%s"
            % (APP_NAME, APP_VERSION,
               "Dobbelsteen-roller voor D&D en tafelspellen."
               if self.lang == "nl" else
               "Dice roller for D&D and tabletop games.",
               SUPPORT_MAIL, DONATE_URL))


QSS = """
* { font-family: 'Segoe UI', sans-serif; font-size: 14px; color: %(silver)s; }
QMainWindow, QWidget { background: %(bg)s; }
#header { background: %(panel)s; border-bottom: 1px solid #23232b; }
#title { font-size: 19px; font-weight: 700; color: %(silver)s; }
#ver { color: %(mute)s; font-size: 12px; }
#section { color: %(mute)s; font-size: 13px; font-weight: 700;
           text-transform: uppercase; letter-spacing: 1px; }
#hint { color: %(mute)s; font-size: 12px; }
QPushButton { background: %(panel)s; border: 1px solid #2c2c36; border-radius: 8px;
              padding: 7px 13px; color: %(silver)s; }
QPushButton:hover { border-color: %(accent)s; }
QPushButton#primary { background: %(accent)s; color: #08131f; font-weight: 700;
                      border: none; padding: 7px 18px; }
QPushButton#primary:hover { background: #87b6e3; }
QPushButton#die { font-size: 22px; font-weight: 700; color: %(accent)s;
                  background: #14141a; border: 1px solid #2c2c36; }
QPushButton#die:hover { border-color: %(accent)s; background: #1a1f29; }
QPushButton#die:pressed { background: %(accent)s; color: #08131f; }
QToolButton#step { background: #14141a; border: 1px solid #2c2c36;
    border-radius: 6px; padding: 4px 12px; color: %(silver)s;
    font-size: 18px; font-weight: 700; min-width: 30px; }
QToolButton#step:hover { border-color: %(accent)s; }
QToolButton#step:pressed { background: %(accent)s; color: #08131f; }
#modreadout { font-size: 18px; font-weight: 700; color: %(accent)s; }
QToolButton#donate { border: none; background: transparent; color: %(accent)s; }
QLineEdit#expr { background: #14141a; border: 1px solid #2c2c36; border-radius: 8px;
                 padding: 8px 10px; font-size: 16px; }
QLineEdit#expr:focus { border-color: %(accent)s; }
QSpinBox#mod { font-size: 16px; min-width: 64px; }
QSpinBox, QComboBox { background: %(panel)s; border: 1px solid #2c2c36;
                      border-radius: 6px; padding: 4px 8px; }
QComboBox QAbstractItemView { background: %(panel)s; color: %(silver)s;
    selection-background-color: %(accent)s; selection-color: #08131f; }
#resultbox { background: %(panel)s; border: 1px solid #2c2c36; border-radius: 12px; }
#total { font-size: 56px; font-weight: 800; color: %(silver)s; }
#detail { font-size: 18px; color: %(accent)s; }
#crit { font-size: 18px; font-weight: 700; color: %(mute)s; }
#crit[kind="good"] { color: %(good)s; }
#crit[kind="bad"] { color: %(bad)s; }
QListWidget#history { background: #14141a; border: 1px solid #2c2c36;
                      border-radius: 8px; font-size: 15px; padding: 4px; }
QListWidget#history::item { padding: 4px 6px; }
QStatusBar { background: %(panel)s; }
QDialog { background: %(bg)s; }
QPlainTextEdit#guide { background: %(panel)s; border: 1px solid #2c2c36;
                       border-radius: 8px; padding: 10px; font-size: 14px; }
""" % {"bg": BG, "panel": PANEL, "silver": SILVER, "mute": MUTE,
       "accent": ACCENT, "good": GOOD, "bad": BAD}


def _install_excepthook():
    import traceback

    def hook(exctype, value, tb):
        msg = "".join(traceback.format_exception(exctype, value, tb))
        try:
            with open(os.path.join(_app_dir(), "dravedice-fout.txt"),
                      "w", encoding="utf-8") as f:
                f.write(msg)
        except Exception:
            pass
        try:
            if QApplication.instance():
                QMessageBox.critical(None, "DraveDice - fout",
                                     "Er ging iets mis bij het starten:\n\n"
                                     + msg[-1500:]
                                     + "\n\n(Ook opgeslagen in dravedice-fout.txt)")
        except Exception:
            pass
        sys.__excepthook__(exctype, value, tb)

    sys.excepthook = hook


def main():
    global _LANG
    _install_excepthook()
    app = QApplication(sys.argv)
    try:
        cfg = load_config()
        _LANG = detect_lang(cfg)
        app.setStyleSheet(QSS)
        win = DraveDice(cfg)
        win.show()
    except Exception:
        sys.excepthook(*sys.exc_info())
        return
    try:  # Dravenlock: stille update-check (uit te zetten; Ctrl+Shift+U = met de hand)
        import drave_update
        drave_update.start(win, 'DraveDice', APP_VERSION)
    except Exception:
        pass
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
