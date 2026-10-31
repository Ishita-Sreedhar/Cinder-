import sys
import os
import json
import shutil
import tempfile
import time
import random
from datetime import datetime
from math import sin, cos, sqrt, ceil, atan2, hypot, pi
from pathlib import Path

from PyQt6.QtCore import Qt, QPoint, QPointF, QRectF, QTimer, QObject
from PyQt6.QtWidgets import (
    QApplication, QGraphicsView, QWidget, QMenu, QGraphicsScene, QVBoxLayout,
    QLabel, QGraphicsTextItem, QGraphicsItemGroup, QGraphicsPolygonItem,
    QGraphicsRectItem, QGraphicsPathItem, QLineEdit, QGraphicsProxyWidget,
    QListWidget, QListWidgetItem, QGraphicsEllipseItem, QAbstractItemView,
    QGraphicsItem,
)
from PyQt6.QtGui import (
    QMouseEvent, QContextMenuEvent, QPainterPath, QBrush, QPen, QPolygonF,
    QColor, QCursor, QPainter, QPixmap, QFont, QTransform,
)
from pynput import keyboard, mouse


# ------------------------------------------------------ packaging helpers --
def resource_path(relative_path):
    """Path to a file that is BUNDLED with the app (like cind.jpg).
    Works from source and from the packaged exe (PyInstaller unpacks to sys._MEIPASS)."""
    if hasattr(sys, "_MEIPASS"):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative_path)


def get_data_dir():
    """Folder for files the app WRITES (to-dos, water settings, window sizes).
    It can't be next to the exe: a --onefile exe runs from a temp folder that is
    deleted on exit, which would wipe your data every time."""
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA") or Path.home())
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME") or (Path.home() / ".config"))
    folder = base / "Cinder"
    try:
        folder.mkdir(parents=True, exist_ok=True)
    except OSError:
        folder = Path.home()
    return folder


# ---------------------------------------------------------------- settings --
DATA_DIR = get_data_dir()
BG_PATH = resource_path("cind.jpg")       # bundled with the exe (see --add-data)
TODO_PATH = DATA_DIR / "todos.json"       # your to-do list is saved here
WATER_PATH = DATA_DIR / "water.json"      # water reminder settings are saved here
SIZES_PATH = DATA_DIR / "sizes.json"      # remembers how big you made each window


def migrate_old_data():
    """Running from source used to save next to the script. Copy that data to the
    new folder once, so your existing to-dos / settings don't disappear."""
    if getattr(sys, "frozen", False):
        return
    old_dir = Path(__file__).resolve().parent
    for path in (TODO_PATH, WATER_PATH, SIZES_PATH):
        old = old_dir / path.name
        if old.exists() and not path.exists():
            try:
                shutil.copy2(old, path)
            except OSError:
                pass


migrate_old_data()

WATER_BG_OPACITY = 0.35              # background image strength in the water reminder window
BG_IMAGE_OPACITY = 0.35               # 0 = invisible, 1 = full strength (lower = easier to read text)
WINDOW_RADIUS = 14                    # corner rounding of the timer / stopwatch / to-do windows

WORK_SECONDS = 1500        # 25 min
BREAK_SECONDS = 300        # 5 min
POMODORO_ROUNDS = 2        # number of work+break rounds before "Time's Up!"
SLEEP_AFTER_SECONDS = 600  # idle time before the cat falls asleep

# how far the big digits, label and play/pause button sit below the top of the
# timer and stopwatch windows (bigger = lower, 0 = the old position)
CLOCK_Y_OFFSET = 40

# pynput's keyboard listener can hard-crash Python on recent macOS ("Python quit
# unexpectedly"), so it is off there. The cat still wakes from mouse movement,
# clicks and scrolling. Set to True to try it anyway.
TRACK_KEYBOARD = sys.platform != "darwin"

TEXT_COLOR = QColor(176, 136, 123)
HOVER_COLOR = QColor(122, 86, 74)
TODO_TEXT_COLOR = QColor(110, 82, 72)
TODO_DONE_COLOR = QColor(190, 165, 155)

CONFETTI_COLORS = [
    QColor(255, 105, 150), QColor(255, 200, 70), QColor(110, 200, 190),
    QColor(170, 140, 230), QColor(255, 150, 90), QColor(240, 54, 116),
    QColor(120, 190, 255),
]
CHEERS = ["Yay!", "Well done!", "Nice one!", "You did it!", "Purrfect!", "Meow-velous!"]
WIN_FLAGS = Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint

# thin outline around the cat's silhouette
CAT_OUTLINE_COLOR = QColor(110, 92, 98)
CAT_OUTLINE_PEN_WIDTH = 6   # half of this is hidden under the white fill, so ~1.5px shows

# petting: circle the cursor around the cat PET_CIRCLES times
PET_CIRCLES = 1.5           # turns needed (try 1 for very easy, 2 for more deliberate)
PET_CENTER = (55, 80)       # roughly the middle of the cat, in scene coordinates
PET_MIN_RADIUS = 15         # px from the cat's centre (global screen pixels)
PET_MAX_RADIUS = 320
PET_MIN_STEP = 0.01         # radians; ignore tiny jitters
PET_MAX_STEP = 2.0          # radians; bigger jumps aren't a smooth circle
PET_RESET_GAP = 1.5         # seconds of no movement before the progress resets
PET_DURATION = 3.5          # seconds the cat stays happy
PET_COOLDOWN = 2.0          # seconds before it can be petted again

HEART_LIFETIME = 1.6        # seconds
HEART_RISE = 20             # px per second

ZZZ_PERIOD = 2.4            # seconds for one "z" to float up and fade while she sleeps

# window resizing (all tool windows scale together with their contents)
MIN_SCALE = 0.7
MAX_SCALE = 2.5
SIZE_PRESETS = (("Small", 0.8), ("Normal", 1.0), ("Large", 1.3), ("Extra large", 1.7))

# water reminder
WATER_MIN_MINUTES = 1
WATER_MAX_MINUTES = 240
WATER_MESSAGE_MS = 10000    # how long Cinder keeps the reminder bubble up
WATER_MESSAGES = [
    "Water break! \U0001F4A7",
    "Sip sip, stay hydrated! \U0001F4A7",
    "Drink some water, buddy \U0001F4A7",
    "Cinder says: water time! \U0001F4A7",
]
MESSAGE_STYLE = """background-color: rgb(250, 250, 238);
                   border: 2px solid rgb(176, 136, 123);
                   padding: 5px 10px;
                   border-radius: 10px;
                   color: rgb(110, 82, 72);
                   font-family: "Lucida Fax", "Georgia", serif;
                   font-size: 12px"""


# ------------------------------------------------------------ menu styling --
MENU_STYLE = """
QMenu {
    background-color: rgb(250, 250, 238);
    border: 2px solid rgb(176, 136, 123);
    border-radius: 10px;
    padding: 4px;
    font-family: "Lucida Fax", "Georgia", serif;
    font-size: 11px;
}
QMenu::item {
    padding: 5px 20px 5px 10px;
    margin: 1px;
    border-radius: 7px;
    color: rgb(110, 82, 72);
}
QMenu::item:selected {
    background-color: rgb(176, 136, 123);
    color: rgb(255, 250, 240);
}
QMenu::separator {
    height: 1px;
    background: rgba(176, 136, 123, 90);
    margin: 3px 8px;
}
"""


def make_menu():
    """A rounded, cream-and-brown context menu that matches the buddy's palette."""
    menu = QMenu()
    menu.setWindowFlags(
        menu.windowFlags()
        | Qt.WindowType.FramelessWindowHint
        | Qt.WindowType.NoDropShadowWindowHint
    )
    menu.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
    menu.setStyleSheet(MENU_STYLE)
    return menu


# ----------------------------------------------------------------- helpers --
def make_font(families, size):
    """Font with fallbacks, so a missing font doesn't give a random substitute."""
    font = QFont()
    font.setFamilies(families)
    font.setPointSize(size)
    return font


def add_window_background(scene, width=350, height=200, image=True, crop=False, opacity=None):
    """Rounded cream panel with a brown border, like the menus. The background image
    (if any) is clipped to the rounded corners and faded so the text stays readable.
    crop=True fills the window without stretching the picture (centre-cropped)."""
    rect = QRectF(2, 2, width - 4, height - 4)
    path = QPainterPath()
    path.addRoundedRect(rect, WINDOW_RADIUS, WINDOW_RADIUS)

    panel = scene.addPath(path, QPen(Qt.PenStyle.NoPen), QBrush(QColor(250, 250, 238)))
    panel.setZValue(-30)

    if image:
        pixmap = QPixmap(BG_PATH)
        if pixmap.isNull():
            print(f"[DesktopBuddy] Couldn't load background image: {BG_PATH}")
        else:
            target_w, target_h = int(rect.width()), int(rect.height())
            pixmap = pixmap.scaled(
                target_w, target_h,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding if crop
                else Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            if crop:
                pixmap = pixmap.copy((pixmap.width() - target_w) // 2,
                                     (pixmap.height() - target_h) // 2, target_w, target_h)
            rounded = QPixmap(pixmap.size())
            rounded.fill(Qt.GlobalColor.transparent)
            painter = QPainter(rounded)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            clip = QPainterPath()
            clip.addRoundedRect(QRectF(rounded.rect()), WINDOW_RADIUS, WINDOW_RADIUS)
            painter.setClipPath(clip)
            painter.drawPixmap(0, 0, pixmap)
            painter.end()
            picture = scene.addPixmap(rounded)
            picture.setPos(rect.topLeft())
            picture.setOpacity(BG_IMAGE_OPACITY if opacity is None else opacity)
            picture.setZValue(-20)

    border = scene.addPath(path, QPen(TEXT_COLOR, 2), QBrush())
    border.setZValue(-10)
    return panel


def shrink_polygon(points, factor):
    """Scales a polygon toward its centroid (used for the inner ears)."""
    cx = sum(p.x() for p in points) / len(points)
    cy = sum(p.y() for p in points) / len(points)
    return QPolygonF([
        QPointF(cx + (p.x() - cx) * factor, cy + (p.y() - cy) * factor)
        for p in points
    ])


def make_sparkle(radius):
    """A four-point star centred on (0, 0)."""
    points = []
    for i in range(8):
        r = radius if i % 2 == 0 else radius * 0.35
        angle = i * pi / 4 - pi / 2
        points.append(QPointF(cos(angle) * r, sin(angle) * r))
    return QPolygonF(points)


def make_heart_path():
    """A tiny heart, roughly 9px wide, centred near (0, 0)."""
    path = QPainterPath()
    path.moveTo(0, 4)
    path.cubicTo(-8, -2, -4, -7, 0, -3)
    path.cubicTo(4, -7, 8, -2, 0, 4)
    path.closeSubpath()
    return path


def center_x(item, width=350):
    """x position that horizontally centres a graphics item in a scene."""
    return (width - item.boundingRect().width()) / 2


_sizes = None


def _load_sizes():
    global _sizes
    if _sizes is None:
        _sizes = {}
        try:
            data = json.loads(SIZES_PATH.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            data = {}
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    _sizes[str(key)] = max(MIN_SCALE, min(MAX_SCALE, float(value)))
    return _sizes


def get_saved_scale(key):
    """Remembered window scale for a window kind ('timer', 'todo', ...), 1.0 if none."""
    return _load_sizes().get(key, 1.0)


def save_scale(key, scale):
    sizes = _load_sizes()
    sizes[key] = round(scale, 3)
    try:
        SIZES_PATH.write_text(json.dumps(sizes, indent=2), encoding="utf-8")
    except OSError as err:
        print(f"[DesktopBuddy] Couldn't save window sizes: {err}")


# ------------------------------------------------------------- main widget --
class DesktopBuddy(QWidget):
    # creates a widget for the desktop buddy

    def __init__(self):
        super().__init__()
        # the cat never grabs keyboard focus, so a reminder can't interrupt your typing
        self.setWindowFlags(WIN_FLAGS | Qt.WindowType.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.offset = QPoint()
        self.setFixedSize(600, 200)

        self.tool_open = False      # a tool window (timer / to-do / ...) is hiding the cat
        self.cat_peeking = False    # the cat was brought back briefly to deliver a reminder

        # creates the cat, lays it out and adds it into the widget
        self.sleep_message_active = False   # the "Zzz" bubble is up
        self.cat = BuddyCat()
        self.cat.on_sleep = self.show_sleep_message
        self.cat.on_wake = self.hide_sleep_message
        self.cat.on_pet = self.show_purr_message
        self.main_layout = QVBoxLayout()
        self.main_layout.addWidget(self.cat.view)
        self.setLayout(self.main_layout)

        # the speech bubble Cinder uses for the greeting and the water reminder
        self.message = QLabel(self)
        self.message.setStyleSheet(MESSAGE_STYLE)
        self.message.hide()
        self.message_timer = QTimer(self)
        self.message_timer.setSingleShot(True)
        self.message_timer.timeout.connect(self.hide_message)
        self.raise_timer = QTimer(self)          # keeps the cat above other windows while peeking
        self.raise_timer.timeout.connect(self.keep_cat_on_top)

        # water reminder state lives here because DesktopBuddy outlives every tool window
        self.water_enabled = False
        self.water_minutes = 60
        self.water_prioritize = False
        self.water_pending = False
        self.load_water_settings()

        self.water_timer = QTimer(self)
        self.water_timer.timeout.connect(self.on_water_due)
        self.water_check = QTimer(self)          # decides *when* a due reminder may appear
        self.water_check.timeout.connect(self.try_show_water)
        self.water_check.start(1000)
        self.apply_water_timer()

        self.show()

        # greeting
        hour = datetime.now().hour
        if hour < 4:
            self.text = "Buddy it's midnight. SLEEP!!!!"
        elif hour <= 8:
            self.text = "Wakey Wakey!"
        elif hour <= 12:
            self.text = "Good Morning!"
        elif hour <= 15:
            self.text = "Afternoon already?"
        elif hour <= 19:
            self.text = "Tea timeee"
        elif hour <= 22:
            self.text = "Chill mode? or hustle mode?"
        else:
            self.text = "Giving night owl vibes.."

        # first a quick hello, then the time-of-day greeting
        self.show_message("Hi, I'm Cinder!", 3000)
        QTimer.singleShot(3200, self.show_time_greeting)

    def show_time_greeting(self):
        if not self.tool_open:
            self.show_message(self.text)

    # lets us select the widget
    def mousePressEvent(self, event: QMouseEvent):
        self.offset = event.globalPosition().toPoint() - self.pos()

    # lets us move the widget
    def mouseMoveEvent(self, event: QMouseEvent):
        self.window_Position = event.globalPosition().toPoint() - self.offset
        self.move(self.window_Position)

    # ---- speech bubble ----
    def show_message(self, text, duration=6000):
        self.sleep_message_active = False
        self.message.setText(text)
        self.message.adjustSize()
        self.message.move(300, 3)
        self.message.show()
        self.message.raise_()
        self.message_timer.start(duration)

    def hide_message(self):
        self.message.hide()
        self.raise_timer.stop()
        if self.cat_peeking:             # reminder delivered: send the cat back behind the tool
            self.cat_peeking = False
            if self.tool_open:
                self.hide()

    # Cinder fell asleep: a "Zzz" bubble that stays up until she wakes
    def show_sleep_message(self):
        if self.tool_open:
            return
        self.show_message("Zzz...", 3600000)
        self.sleep_message_active = True

    def hide_sleep_message(self):
        if self.sleep_message_active:
            self.sleep_message_active = False
            self.message_timer.stop()
            self.message.hide()

    # being petted: Cinder purrs
    def show_purr_message(self):
        if not self.tool_open:
            self.show_message("Purrrr... \u2665", int(PET_DURATION * 1000))

    def keep_cat_on_top(self):
        if self.cat_peeking and self.isVisible():
            self.raise_()

    # shows a tool window (timer / stopwatch / to-do) where the cat is, and hides the cat
    def open_tool(self, tool):
        self.tool_open = True
        self.cat_peeking = False
        self.raise_timer.stop()
        self.message_timer.stop()
        self.message.hide()
        tool.view.setWindowFlags(WIN_FLAGS)
        w, h = tool.view.width(), tool.view.height()
        # centre the tool window on the cat, then keep it fully on screen
        cat_center = self.pos() + QPoint(self.width() // 2, self.height() // 2)
        x = cat_center.x() - w // 2
        y = cat_center.y() - h // 2
        screen = QApplication.screenAt(cat_center) or QApplication.primaryScreen()
        area = screen.availableGeometry()
        x = max(area.left(), min(x, area.right() - w + 1))
        y = max(area.top(), min(y, area.bottom() - h + 1))
        tool.view.move(x, y)
        tool.view.show()
        self.hide()

    # called when a tool window is closed: the cat comes back
    def cat_returned(self):
        self.tool_open = False
        self.cat_peeking = False
        self.raise_timer.stop()
        self.show()
        if self.cat.sleeping:            # still asleep when she comes back
            self.show_sleep_message()

    def OpenTimerMenu(self):
        self.menu_option = ChoiceSelection(self)
        self.open_tool(self.menu_option)

    def OpenStopwatch(self):
        self.stopwatch = StopwatchWidget(self)
        self.open_tool(self.stopwatch)

    def OpenTodo(self):
        self.todo = TodoWidget(self)
        self.open_tool(self.todo)

    def OpenWater(self):
        self.water_settings = WaterSettingsWidget(self)
        self.open_tool(self.water_settings)

    # ---- water reminder ----
    def apply_water_timer(self):
        self.water_timer.stop()
        if self.water_enabled:
            self.water_timer.start(self.water_minutes * 60000)

    def set_water_enabled(self, value):
        self.water_enabled = bool(value)
        self.water_pending = False
        self.apply_water_timer()
        if not self.water_enabled and self.cat_peeking:
            self.message_timer.stop()
            self.hide_message()
        self.save_water_settings()

    def set_water_minutes(self, minutes):
        self.water_minutes = max(WATER_MIN_MINUTES, min(WATER_MAX_MINUTES, int(minutes)))
        self.apply_water_timer()         # restarts the countdown with the new frequency
        self.save_water_settings()

    def set_water_prioritize(self, value):
        self.water_prioritize = bool(value)
        self.save_water_settings()

    def test_water(self):
        self.water_pending = True        # goes through the same rules as a real reminder

    def on_water_due(self):
        self.water_pending = True

    # runs every second. A due reminder is delivered by Cinder's speech bubble:
    #  - cat visible: straight away
    #  - a tool window is open and "prioritize" is on: the cat pops up over it for a moment
    #  - a tool window is open and "prioritize" is off: waits until the cat is back
    def try_show_water(self):
        if not self.water_pending:
            return
        if self.isVisible():
            self.deliver_water()
        elif self.water_prioritize and self.tool_open:
            self.cat_peeking = True
            self.show()
            self.raise_()
            self.raise_timer.start(400)
            self.deliver_water()

    def deliver_water(self):
        self.water_pending = False
        self.cat.poke()                  # wakes Cinder up if she was asleep
        self.show_message(random.choice(WATER_MESSAGES), WATER_MESSAGE_MS)

    def load_water_settings(self):
        try:
            data = json.loads(WATER_PATH.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return
        if not isinstance(data, dict):
            return
        try:
            minutes = int(data.get("minutes", 60))
        except (TypeError, ValueError):
            minutes = 60
        self.water_minutes = max(WATER_MIN_MINUTES, min(WATER_MAX_MINUTES, minutes))
        self.water_prioritize = bool(data.get("prioritize", False))
        self.water_enabled = bool(data.get("enabled", False))

    def save_water_settings(self):
        data = {
            "enabled": self.water_enabled,
            "minutes": self.water_minutes,
            "prioritize": self.water_prioritize,
        }
        try:
            WATER_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except OSError as err:
            print(f"[DesktopBuddy] Couldn't save water settings: {err}")

    # opens context menu on right click
    def contextMenuEvent(self, event: QContextMenuEvent):
        menu = make_menu()
        menu.addAction("⏰  Timer", self.OpenTimerMenu)
        menu.addAction("⏱  Stopwatch", self.OpenStopwatch)
        menu.addAction("📝  To-do list", self.OpenTodo)
        menu.addAction("💧  Water reminder", self.OpenWater)
        menu.addSeparator()
        menu.addAction("✖  Exit", QApplication.instance().quit)
        menu.exec(event.globalPos())


# --------------------------------------------------------------------- cat --
class BuddyCat(QObject):
    # centre of the sleeping muzzle (matches the awake muzzle's centre)
    SLEEP_CX = 56
    SLEEP_CY = 48

    def __init__(self):
        # creates transparent QGraphicScene displayed by QGraphicViews
        super().__init__()

        # state that the timers below rely on is set up first
        self.sleeping = False
        self.last_activity = time.time()
        self.sway_angle = 0
        self.last_mouse_pos = None

        # the main window sets these so Cinder's speech bubble can react
        self.on_sleep = None
        self.on_wake = None
        self.on_pet = None
        self.sleep_start = 0.0

        # petting state
        self.petting = False
        self.pet_until = 0.0
        self.pet_ticks = 0
        self.pet_cooldown_until = 0.0
        self.circle_total = 0.0
        self.last_angle = None
        self.last_angle_time = 0.0
        self.hearts = []
        self.heart_path = make_heart_path()

        self.graphic = QGraphicsScene()
        self.graphic.setBackgroundBrush(QBrush(Qt.GlobalColor.transparent))
        self.graphic.setSceneRect(0, 0, 120, 150)
        self.view = QGraphicsView(self.graphic)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.view.setStyleSheet("background: transparent; border: none;")
        # so this doesn't overshadow our mousepress events in the other class
        self.view.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        # setting the style of our pen and brush
        self.pen = QPen(Qt.GlobalColor.white, 3, Qt.PenStyle.SolidLine)
        self.white_brush = QBrush(Qt.GlobalColor.white, Qt.BrushStyle.SolidPattern)
        self.black_brush = QBrush(Qt.GlobalColor.black, Qt.BrushStyle.SolidPattern)
        pink_brush = QBrush(QColor(244, 172, 218))
        self.happy_blush_brush = QBrush(QColor(255, 130, 175))

        outline_pen = QPen(CAT_OUTLINE_COLOR, CAT_OUTLINE_PEN_WIDTH)
        outline_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        outline_pen.setCapStyle(Qt.PenCapStyle.RoundCap)

        left_ear_pts = [QPointF(38, 20), QPointF(48, 20), QPointF(41, 5)]
        right_ear_pts = [QPointF(62, 20), QPointF(72, 20), QPointF(70, 5)]

        # --- silhouette, pass 1: dark outline copies of body/head/tail/ears ---
        self.graphic.addEllipse(20, 50, 70, 90, outline_pen, self.white_brush)
        self.graphic.addEllipse(30, 15, 50, 50, outline_pen, self.white_brush)
        self.tail_outline = self.graphic.addPath(QPainterPath(), outline_pen)
        self.tail_outline.setBrush(self.white_brush)
        self.graphic.addPolygon(QPolygonF(left_ear_pts), outline_pen, self.white_brush)
        self.graphic.addPolygon(QPolygonF(right_ear_pts), outline_pen, self.white_brush)

        # --- silhouette, pass 2: white fills on top. They hide every outline
        # line where shapes overlap, so only the outer edge of the whole cat
        # keeps a thin outline (and the tail joins the body seamlessly) ---
        # body
        self.graphic.addEllipse(20, 50, 70, 90, self.pen, self.white_brush)
        # head
        self.graphic.addEllipse(30, 15, 50, 50, self.pen, self.white_brush)
        # tail
        self.tail_fill = self.graphic.addPath(QPainterPath(), self.pen)
        self.tail_fill.setBrush(self.white_brush)
        self.draw_tail()
        # ears
        self.graphic.addPolygon(QPolygonF(left_ear_pts), self.pen, self.white_brush)
        self.graphic.addPolygon(QPolygonF(right_ear_pts), self.pen, self.white_brush)

        # inner ears (smaller than the outer ears so the white rim shows)
        no_pen = QPen(Qt.PenStyle.NoPen)
        self.graphic.addPolygon(shrink_polygon(left_ear_pts, 0.5), no_pen, pink_brush)
        self.graphic.addPolygon(shrink_polygon(right_ear_pts, 0.5), no_pen, pink_brush)

        # facial features
        # blush
        self.blush_left = self.graphic.addEllipse(38, 38, 12, 8, self.pen, pink_brush)
        self.blush_right = self.graphic.addEllipse(62, 38, 12, 8, self.pen, pink_brush)
        self.pink_brush = pink_brush

        # nose
        self.graphic.addEllipse(51, 36, 10, 6, self.pen, self.black_brush)

        # eyes
        self.left_eye = self.graphic.addEllipse(41, 22, 13, 16, self.pen, self.black_brush)
        self.left_eye_inner = self.graphic.addEllipse(47, 28, 2, 4, self.pen, self.white_brush)
        self.right_eye = self.graphic.addEllipse(57, 22, 13, 16, self.pen, self.black_brush)
        self.right_eye_inner = self.graphic.addEllipse(63, 28, 2, 4, self.pen, self.white_brush)

        # closed (sleeping) eyes, centred under each open eye
        closed_eye_pen = QPen(Qt.GlobalColor.black, 1)
        closed_left_eye_path = QPainterPath()
        closed_left_eye_path.moveTo(43.5, 30)
        closed_left_eye_path.cubicTo(43.5, 36, 51.5, 36, 51.5, 30)
        self.closed_left_eye = self.graphic.addPath(closed_left_eye_path, closed_eye_pen)
        self.closed_left_eye.setVisible(False)
        closed_right_eye_path = QPainterPath()
        closed_right_eye_path.moveTo(59.5, 30)
        closed_right_eye_path.cubicTo(59.5, 36, 67.5, 36, 67.5, 30)
        self.closed_right_eye = self.graphic.addPath(closed_right_eye_path, closed_eye_pen)
        self.closed_right_eye.setVisible(False)

        # mouth
        mouth_pen = QPen(QColor(0, 0, 0, 200))
        muzzle_path = QPainterPath()
        muzzle_path.moveTo(48, 48)
        muzzle_path.cubicTo(50, 51, 52, 52, 56, 48)
        muzzle_path.cubicTo(60, 52, 62, 51, 64, 48)

        muzzle_path.moveTo(56, 48)
        muzzle_path.lineTo(56, 38)
        self.muzzle = self.graphic.addPath(muzzle_path, mouth_pen)
        self.sleep_muzzle = self.graphic.addEllipse(
            self.SLEEP_CX - 4, self.SLEEP_CY - 4, 8, 8, mouth_pen, self.black_brush)
        self.sleep_muzzle.setVisible(False)

        # whiskers
        whisker_pen = QPen(QColor(0, 0, 0, 128))
        whisker = QPainterPath()
        whisker.moveTo(44, 40)
        whisker.lineTo(34, 38)
        whisker.moveTo(44, 42)
        whisker.lineTo(34, 42)
        whisker.moveTo(44, 44)
        whisker.lineTo(34, 46)
        whisker.moveTo(68, 40)
        whisker.lineTo(78, 38)
        whisker.moveTo(68, 42)
        whisker.lineTo(78, 42)
        whisker.moveTo(68, 44)
        whisker.lineTo(78, 46)
        self.graphic.addPath(whisker, whisker_pen)

        # paws
        paw_pen = QPen(Qt.GlobalColor.black, 1.5, Qt.PenStyle.SolidLine)
        paws = QPainterPath()
        paws.moveTo(37, 120)
        paws.cubicTo(37, 146, 52, 146, 52, 120)
        paws.moveTo(63, 120)
        paws.cubicTo(63, 145, 78, 145, 78, 120)
        self.graphic.addPath(paws, paw_pen)

        # collar
        collar_path = QPainterPath()
        collar_path.addRoundedRect(QRectF(31, 57, 48, 6), 5, 5)
        self.graphic.addPath(collar_path, QPen(Qt.PenStyle.NoPen), QBrush(QColor(240, 54, 116, 200)))

        # bell
        self.graphic.addEllipse(48, 59, 12, 12, QPen(Qt.PenStyle.NoPen), QBrush(QColor(245, 215, 90)))

        # little "z z z" that float up from her head while she sleeps
        self.zzz = []
        for letter, size in ("z", 9), ("Z", 11), ("z", 13):
            font = make_font(["Lucida Fax", "Georgia", "serif"], size)
            font.setBold(True)
            item = self.graphic.addText(letter, font)
            item.setDefaultTextColor(QColor(240, 54, 116))
            item.setZValue(200)
            item.setVisible(False)
            self.zzz.append(item)

        # animation timers (started once every item exists)
        self.timer1 = QTimer(self)
        self.timer1.timeout.connect(self.animate_tail)
        self.timer1.timeout.connect(self.track_cursor)
        self.timer1.timeout.connect(self.update_state)
        self.timer1.timeout.connect(self.animate_pet)
        self.timer1.timeout.connect(self.animate_zzz)
        self.timer1.start(50)

        self.timer2 = QTimer(self)
        self.timer2.timeout.connect(self.animate_blink)
        self.timer2.start(4000)

        # sleep tracking (keyboard, scroll and clicks count as activity;
        # mouse movement is handled in track_cursor)
        self.keyboard_activity = None
        if TRACK_KEYBOARD:
            self.keyboard_activity = keyboard.Listener(on_press=self.key_press)
            self.keyboard_activity.start()
        self.mouse_listener = mouse.Listener(on_scroll=self.on_scroll, on_click=self.on_click)
        self.mouse_listener.start()

    def stop_listeners(self):
        if self.keyboard_activity is not None:
            self.keyboard_activity.stop()
        self.mouse_listener.stop()

    # counts as activity (wakes the cat up if it was asleep)
    def poke(self):
        self.last_activity = time.time()

    # tail drawing (updates both the outline copy and the white fill)
    def draw_tail(self, x_offset=0):
        self.path = QPainterPath()
        self.path.moveTo(65, 138)
        self.path.cubicTo(95 + x_offset, 135, 109 + x_offset, 120, 118 + x_offset, 85)
        self.path.cubicTo(115 + x_offset, 77, 110 + x_offset, 77, 107 + x_offset, 85)
        self.path.cubicTo(103 + x_offset, 88, 110 + x_offset, 118, 78 + x_offset, 118)
        self.path.closeSubpath()
        self.tail_outline.setPath(self.path)
        self.tail_fill.setPath(self.path)

    # animating the tail (and the sleeping muzzle's "breathing")
    def animate_tail(self):
        self.sway_angle += 0.35 if self.petting else 0.1   # happy wag when petted
        if self.sleeping:
            pulse = sin(self.sway_angle) * 2 + 4
            self.sleep_muzzle.setRect(
                self.SLEEP_CX - pulse / 2, self.SLEEP_CY - pulse / 2, pulse, pulse)
            return
        amplitude = 7 if self.petting else 4
        x_offset = sin(self.sway_angle) * amplitude
        self.draw_tail(x_offset)

    # blink
    def animate_blink(self):
        if self.sleeping:
            return
        self.left_eye.setRect(41, 22, 13, 0)   # close
        self.right_eye.setRect(57, 22, 13, 0)  # close
        QTimer.singleShot(200, self.reopen_eyes)

    # opening eyes after a blink
    def reopen_eyes(self):
        if self.sleeping:
            return
        self.left_eye.setRect(41, 22, 13, 16)
        self.right_eye.setRect(57, 22, 13, 16)

    # cursor tracking
    def track_cursor(self):
        current_pos = QCursor.pos()
        if current_pos == self.last_mouse_pos:
            return
        self.last_mouse_pos = current_pos
        self.last_activity = time.time()
        self.detect_circling(current_pos)
        mouse_scene = self.view.mapToScene(self.view.mapFromGlobal(current_pos))
        mouse_x = mouse_scene.x()
        mouse_y = mouse_scene.y()
        max_offset = 3
        dx_left = mouse_x - 47
        dx_right = mouse_x - 63
        dy_left = mouse_y - 28
        dy_right = mouse_y - 28
        distance_left = sqrt(dx_left * dx_left + dy_left * dy_left)
        distance_right = sqrt(dx_right * dx_right + dy_right * dy_right)
        # cursor exactly on an eye's reference point -> nothing to track (and no /0)
        if distance_left == 0 or distance_right == 0:
            return
        self.left_eye_inner.setPos(dx_left * (max_offset / distance_left),
                                   dy_left * (max_offset / distance_left))
        self.right_eye_inner.setPos(dx_right * (max_offset / distance_right),
                                    dy_right * (max_offset / distance_right))

    # key tracking
    def key_press(self, key):
        self.last_activity = time.time()

    # scroll tracking
    def on_scroll(self, x, y, dx, dy):
        self.last_activity = time.time()

    # click tracking
    def on_click(self, x, y, button, pressed):
        self.last_activity = time.time()

    # sleep and wake up trigger
    def update_state(self):
        if self.petting:
            return
        idle = time.time() - self.last_activity
        if idle > SLEEP_AFTER_SECONDS and not self.sleeping:
            self.fall_asleep()
        elif idle <= SLEEP_AFTER_SECONDS and self.sleeping:
            self.wake_up()

    # floating z z z: each letter drifts up and to the right, fading in and out
    def animate_zzz(self):
        if not self.sleeping:
            for item in self.zzz:
                if item.isVisible():
                    item.setVisible(False)
            return
        t = (time.time() - self.sleep_start) / ZZZ_PERIOD
        for i, item in enumerate(self.zzz):
            phase = (t + i / len(self.zzz)) % 1.0
            item.setPos(78 + phase * 16, 22 - phase * 24)
            item.setOpacity(sin(phase * pi))
            item.setScale(0.8 + 0.5 * phase)
            item.setVisible(True)

    def fall_asleep(self):
        self.sleeping = True
        self.sleep_start = time.time()
        self.closed_left_eye.setVisible(True)
        self.closed_right_eye.setVisible(True)
        self.sleep_muzzle.setVisible(True)
        self.left_eye.setVisible(False)
        self.right_eye.setVisible(False)
        self.muzzle.setVisible(False)
        self.left_eye.setRect(41, 22, 13, 0)
        self.right_eye.setRect(57, 22, 13, 0)
        if self.on_sleep:
            self.on_sleep()

    def wake_up(self):
        self.sleeping = False
        self.closed_left_eye.setVisible(False)
        self.closed_right_eye.setVisible(False)
        self.sleep_muzzle.setVisible(False)
        self.left_eye.setVisible(True)
        self.right_eye.setVisible(True)
        self.muzzle.setVisible(True)
        self.left_eye.setRect(41, 22, 13, 16)
        self.right_eye.setRect(57, 22, 13, 16)
        if self.on_wake:
            self.on_wake()

    # ------------------------------------------------------------ petting --
    def reset_circling(self):
        self.circle_total = 0.0
        self.last_angle = None

    # watches the cursor's angle around the cat; ~1.5 turns (either direction) = petting.
    # Jitter and small back-steps only subtract a little instead of wiping progress.
    def detect_circling(self, pos):
        now = time.time()
        if self.petting or self.sleeping or now < self.pet_cooldown_until or not self.view.isVisible():
            self.reset_circling()
            return

        center = self.view.mapToGlobal(self.view.mapFromScene(QPointF(*PET_CENTER)))
        dx = pos.x() - center.x()
        dy = pos.y() - center.y()
        if not (PET_MIN_RADIUS <= hypot(dx, dy) <= PET_MAX_RADIUS):
            self.reset_circling()
            return

        angle = atan2(dy, dx)
        if self.last_angle is None or now - self.last_angle_time > PET_RESET_GAP:
            self.circle_total = 0.0
            self.last_angle = angle
            self.last_angle_time = now
            return

        delta = angle - self.last_angle
        if delta > pi:
            delta -= 2 * pi
        elif delta < -pi:
            delta += 2 * pi
        if abs(delta) < PET_MIN_STEP:
            return                      # barely moved; keep waiting for a real step

        self.last_angle = angle
        self.last_angle_time = now
        if abs(delta) > PET_MAX_STEP:
            return                      # a jump: ignore this step but keep progress

        # only a sustained turn the other way undoes progress; a small wobble just dents it
        if self.circle_total * delta < 0:
            self.circle_total *= 0.5
        self.circle_total += delta

        if abs(self.circle_total) >= PET_CIRCLES * 2 * pi:
            self.reset_circling()
            self.start_pet()

    def start_pet(self):
        self.petting = True
        self.pet_until = time.time() + PET_DURATION
        self.pet_ticks = 0

        self.blush_left.setBrush(self.happy_blush_brush)
        self.blush_right.setBrush(self.happy_blush_brush)

        for _ in range(5):               # little burst of hearts to start
            self.spawn_heart()
        if self.on_pet:
            self.on_pet()

    def end_pet(self):
        self.petting = False
        self.pet_cooldown_until = time.time() + PET_COOLDOWN

        self.blush_left.setBrush(self.pink_brush)
        self.blush_right.setBrush(self.pink_brush)

    def spawn_heart(self):
        heart = QGraphicsPathItem(self.heart_path)
        heart.setBrush(QBrush(random.choice([
            QColor(255, 105, 150), QColor(255, 140, 180), QColor(240, 70, 120),
        ])))
        heart.setPen(QPen(Qt.PenStyle.NoPen))
        heart.setScale(random.uniform(0.8, 1.4))
        heart.setZValue(100)
        x0 = random.uniform(28, 88)
        y0 = random.uniform(10, 32)
        heart.setPos(x0, y0)
        self.graphic.addItem(heart)
        self.hearts.append({
            "item": heart,
            "born": time.time(),
            "x0": x0,
            "y0": y0,
            "vx": random.uniform(-22, 22),
            "phase": random.uniform(0, 2 * pi),
        })

    def update_hearts(self, now):
        alive = []
        for h in self.hearts:
            age = now - h["born"]
            if age >= HEART_LIFETIME:
                self.graphic.removeItem(h["item"])
                continue
            h["item"].setPos(
                h["x0"] + h["vx"] * age + sin(age * 5 + h["phase"]) * 3,
                h["y0"] - HEART_RISE * age,
            )
            h["item"].setOpacity(1 - (age / HEART_LIFETIME) ** 2)
            alive.append(h)
        self.hearts = alive

    # runs every tick: keeps spawning hearts while petted, ends the reaction, fades hearts
    def animate_pet(self):
        now = time.time()
        if self.petting:
            self.pet_ticks += 1
            if self.pet_ticks % 3 == 0:
                self.spawn_heart()
            if now >= self.pet_until:
                self.end_pet()
        self.update_hearts(now)


# ------------------------------------------------------------------- timer --
class TimerWidget(QObject):
    # initializing and setting up the timer widget
    def __init__(self, mode, duration, main_window):
        super().__init__()
        self.main_window = main_window
        self.mode = mode

        self.graphic = QGraphicsScene()
        self.graphic.setBackgroundBrush(QBrush(Qt.GlobalColor.transparent))
        self.graphic.setSceneRect(0, 0, 350, 200)
        # on_close makes sure the countdown stops when the window is closed
        self.view = DraggableView(self.graphic, self.main_window, on_close=self.stop_timer,
                                  size_key="timer")
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.view.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.view.setStyleSheet("background: transparent; border: none;")

        # setting background image
        add_window_background(self.graphic)
        add_close_button(self.graphic, self.view)
        add_resize_grip(self.graphic, self.view)

        # countdown state (end_time is a monotonic timestamp, so no drift)
        self.seconds_left = duration
        self.session_seconds = duration   # for the summary on the finish screen
        self.end_time = None
        self.phase = "Work"
        self.count = 0

        self.time_text = QGraphicsTextItem()
        self.time_text.setPos(20, 1 + CLOCK_Y_OFFSET)
        self.time_text.setFont(make_font(["Cooper Black", "Georgia", "serif"], 45))
        self.time_text.setDefaultTextColor(TEXT_COLOR)
        self.graphic.addItem(self.time_text)
        self.update_display()

        self.phase_text = QGraphicsTextItem("Work Time!")
        self.phase_text.setPos(140, 60 + CLOCK_Y_OFFSET)
        self.phase_text.setFont(make_font(["Pluma", "Georgia", "serif"], 10))
        self.phase_text.setDefaultTextColor(TEXT_COLOR)
        self.graphic.addItem(self.phase_text)

        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)

        # timer start button
        self.initial = StartButton(self)
        self.initial.setPos(170, 75 + CLOCK_Y_OFFSET)
        self.graphic.addItem(self.initial)

    # shows seconds_left as HH : MM : SS
    def update_display(self):
        total = max(0, self.seconds_left)
        hours = total // 3600
        minutes = (total % 3600) // 60
        seconds = total % 60
        self.time_text.setPlainText(f"{hours:02d} : {minutes:02d} : {seconds:02d}")

    # begins a new countdown phase
    def begin_phase(self, duration):
        self.seconds_left = duration
        self.end_time = time.monotonic() + duration
        self.update_display()

    # called by the QTimer; works out the time left from the real clock
    def tick(self):
        remaining = max(0, ceil(self.end_time - time.monotonic()))
        self.seconds_left = remaining
        self.update_display()
        if remaining == 0:
            self.phase_finished()

    def phase_finished(self):
        if self.mode == "Custom":
            self.finish()
            return

        if self.phase == "Work":
            QApplication.beep()
            self.phase = "Break"
            self.phase_text.setPlainText("Break Time!")
            self.begin_phase(BREAK_SECONDS)
        else:  # Break just ended
            self.count += 1
            if self.count >= POMODORO_ROUNDS:
                for _ in range(3):
                    QApplication.beep()
                self.finish()
            else:
                QApplication.beep()
                self.phase = "Work"
                self.phase_text.setPlainText("Work Time!")
                self.begin_phase(WORK_SECONDS)

    def finish(self):
        self.timer.stop()
        self.phase = ""
        self.initial.setVisible(False)
        self.phase_text.setVisible(False)
        self.time_text.setVisible(False)
        self.show_finished()

    # "Time's up!" screen: summary + "continue?" with Yes / No
    def show_finished(self):
        def add_text(text, size, color, y, families=("Lucida Fax", "Georgia", "serif")):
            item = QGraphicsTextItem(text)
            item.setFont(make_font(list(families), size))
            item.setDefaultTextColor(color)
            item.setPos(center_x(item), y)
            self.graphic.addItem(item)
            return item

        title = add_text("Time's up!", 24, TEXT_COLOR, 10, ("Cooper Black", "Georgia", "serif"))
        # a little yellow sparkle either side of the title
        rect = title.sceneBoundingRect()
        for x in (rect.left() - 14, rect.right() + 14):
            sparkle = QGraphicsPolygonItem(make_sparkle(7))
            sparkle.setBrush(QBrush(QColor(255, 200, 70)))
            sparkle.setPen(QPen(Qt.PenStyle.NoPen))
            sparkle.setPos(x, rect.center().y())
            self.graphic.addItem(sparkle)

        if self.mode == "Custom":
            summary = f"{max(1, self.session_seconds // 60)} min session complete"
        else:
            summary = f"{POMODORO_ROUNDS} focus rounds complete"
        add_text(summary, 10, TODO_TEXT_COLOR, 52)

        self.graphic.addRect(QRectF(40, 84, 270, 1), QPen(Qt.PenStyle.NoPen),
                             QBrush(QColor(176, 136, 123, 80)))
        add_text("Continue with another timer?", 11, TODO_TEXT_COLOR, 92)

        yes_w, no_w, gap = 130, 110, 14
        x0 = (350 - (yes_w + gap + no_w)) / 2
        self.yes_button = PillButton("Yes, continue", yes_w, 30, self.continue_session, font_size=10)
        self.yes_button.set_selected(True)           # the filled, primary choice
        self.yes_button.setPos(x0, 134)
        self.no_button = PillButton("No, I'm done", no_w, 30, self.view.close_timer, font_size=10)
        self.no_button.setPos(x0 + yes_w + gap, 134)
        self.graphic.addItem(self.yes_button)
        self.graphic.addItem(self.no_button)

    # Yes: back to the timer page (Pomodoro / Custom) in the same spot
    def continue_session(self):
        menu = ChoiceSelection(self.main_window)
        self.main_window.menu_option = menu
        menu.view.setWindowFlags(WIN_FLAGS)
        menu.view.move(self.view.pos())
        menu.view.show()
        self.view.hide()

    def start_timer(self):
        self.end_time = time.monotonic() + self.seconds_left
        self.timer.start(250)  # polled often; the display only changes each second

    def stop_timer(self):
        if self.timer.isActive() and self.end_time is not None:
            self.seconds_left = max(0, ceil(self.end_time - time.monotonic()))
        self.timer.stop()
        self.update_display()


# this entire class helps us to select, move and resize the widget
class DraggableView(QGraphicsView):
    def __init__(self, graphic, main_window, on_close=None, size_key=None):
        super().__init__(graphic)
        self.base_size = graphic.sceneRect().size().toSize()   # size at scale 1.0
        self.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.main_window = main_window
        self.on_close = on_close
        self.size_key = size_key        # windows with the same key share one remembered size
        self.scale_factor = 1.0
        self.offset = QPoint()
        self.dragging = False
        self.set_scale(get_saved_scale(size_key) if size_key else 1.0, save=False)

    # resizes the window and everything in it (the aspect ratio stays the same)
    def set_scale(self, scale, save=True):
        scale = max(MIN_SCALE, min(MAX_SCALE, scale))
        self.scale_factor = scale
        self.resetTransform()
        self.scale(scale, scale)
        self.setFixedSize(ceil(self.base_size.width() * scale),
                          ceil(self.base_size.height() * scale))
        if save and self.size_key:
            save_scale(self.size_key, scale)

    # pulls the window back onto the screen if resizing pushed it over an edge
    def keep_on_screen(self):
        screen = QApplication.screenAt(self.geometry().center()) or QApplication.primaryScreen()
        area = screen.availableGeometry()
        x = max(area.left(), min(self.x(), area.right() - self.width() + 1))
        y = max(area.top(), min(self.y(), area.bottom() - self.height() + 1))
        self.move(x, y)

    def finish_resize(self):
        if self.size_key:
            save_scale(self.size_key, self.scale_factor)
        if self.isVisible():
            self.keep_on_screen()

    def apply_preset(self, scale):
        self.set_scale(scale)
        if self.isVisible():
            self.keep_on_screen()

    # lets us select the widget
    def mousePressEvent(self, event: QMouseEvent):
        item = self.itemAt(event.position().toPoint())
        while item is not None:
            if isinstance(item, (StartButton, HoverText)) or getattr(item, "clickable", False):
                self.dragging = False
                super().mousePressEvent(event)
                return

            if isinstance(item, QGraphicsProxyWidget):
                self.dragging = False
                super().mousePressEvent(event)
                return

            item = item.parentItem()
        self.offset = event.globalPosition().toPoint() - self.mapToGlobal(QPoint(0, 0))
        self.dragging = True

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.dragging = False
        super().mouseReleaseEvent(event)

    # Ctrl + scroll wheel resizes
    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            step = 0.1 if event.angleDelta().y() > 0 else -0.1
            self.set_scale(self.scale_factor + step)
            if self.isVisible():
                self.keep_on_screen()
            event.accept()
            return
        super().wheelEvent(event)

    def contextMenuEvent(self, event: QContextMenuEvent):
        menu = make_menu()
        if self.size_key:
            sizes = make_menu()
            sizes.setTitle("↔  Size")
            for label, value in SIZE_PRESETS:
                sizes.addAction(label, lambda checked=False, v=value: self.apply_preset(v))
            menu.addMenu(sizes)
            menu.addSeparator()
        menu.addAction("✖  Exit", self.close_timer)
        menu.exec(event.globalPos())

    # lets us move the widget (and keeps hover / the resize grip working)
    def mouseMoveEvent(self, event: QMouseEvent):
        super().mouseMoveEvent(event)
        if self.dragging:
            self.window_Position = event.globalPosition().toPoint() - self.offset
            self.move(self.window_Position)

    def close_timer(self):
        if self.on_close:
            self.on_close()
        self.main_window.cat_returned()
        self.hide()


# clickable text that lights up and underlines when you hover over it
class HoverText(QGraphicsTextItem):
    UNDERLINE = True

    def __init__(self, text):
        super().__init__(text)
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def _set_underline(self, on):
        font = self.font()
        font.setUnderline(on)
        self.setFont(font)

    def hoverEnterEvent(self, event):
        self.setDefaultTextColor(HOVER_COLOR)
        if self.UNDERLINE:
            self._set_underline(True)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setDefaultTextColor(TEXT_COLOR)
        self._set_underline(False)
        super().hoverLeaveEvent(event)


# the little x in the top-right corner: closes the window and brings the cat back
class CloseButton(HoverText):
    UNDERLINE = False

    def __init__(self, view):
        super().__init__("✕")
        self.target_view = view
        self.setFont(make_font(["Segoe UI Symbol", "DejaVu Sans", "sans-serif"], 10))
        self.setDefaultTextColor(TEXT_COLOR)
        self.setToolTip("Close")

    def mousePressEvent(self, event):
        self.target_view.close_timer()


def add_close_button(scene, view, width=350):
    button = CloseButton(view)
    button.setPos(width - 10 - button.boundingRect().width(), 2)
    button.setZValue(500)
    scene.addItem(button)
    return button


# the little diagonal lines in the bottom-right corner: drag to resize the window
class ResizeGrip(QGraphicsItem):
    clickable = True    # DraggableView passes clicks on this item through instead of dragging
    SIZE = 14           # in screen pixels (the grip doesn't grow with the window)
    MARGIN = 6          # distance from the window corner

    def __init__(self, view):
        super().__init__()
        self.view = view
        self.start_pos = None
        self.start_scale = 1.0
        self.resizing = False
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIgnoresTransformations, True)
        self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        self.setToolTip("Drag to resize")
        self.setZValue(600)

    def boundingRect(self):
        s, m = self.SIZE, self.MARGIN
        return QRectF(-s - m, -s - m, s, s)

    def paint(self, painter, option, widget=None):
        m = self.MARGIN
        pen = QPen(TEXT_COLOR, 1.4)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(pen)
        for i in (4, 8, 12):
            painter.drawLine(QPointF(-m - i, -m), QPointF(-m, -m - i))

    def mousePressEvent(self, event):
        self.start_pos = event.screenPos()
        self.start_scale = self.view.scale_factor
        event.accept()

    def mouseMoveEvent(self, event):
        if self.start_pos is None:
            return
        d = event.screenPos() - self.start_pos
        bw, bh = self.view.base_size.width(), self.view.base_size.height()
        # project the drag onto the window's diagonal, so the corner follows the cursor
        delta = (d.x() * bw + d.y() * bh) / (bw * bw + bh * bh)
        target = max(MIN_SCALE, min(MAX_SCALE, self.start_scale + delta))
        # resizing makes the view replay the last mouse event, which would land back here:
        # skip it when nothing changed and never re-enter
        if self.resizing or abs(target - self.view.scale_factor) < 0.002:
            return
        self.resizing = True
        try:
            self.view.set_scale(target, save=False)
        finally:
            self.resizing = False

    def mouseReleaseEvent(self, event):
        self.start_pos = None
        self.view.finish_resize()


def add_resize_grip(scene, view, width=350, height=200):
    grip = ResizeGrip(view)
    grip.setPos(width, height)
    scene.addItem(grip)
    return grip


# choose pomodoro or your custom timer
class ChoiceSelection(QObject):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.graphic = QGraphicsScene()
        self.graphic.setBackgroundBrush(QBrush(Qt.GlobalColor.transparent))
        self.graphic.setSceneRect(0, 0, 350, 200)
        self.view = DraggableView(self.graphic, self.main_window, size_key="timer")
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.view.setStyleSheet("background: transparent; border: none;")
        self.view.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        add_window_background(self.graphic)
        add_close_button(self.graphic, self.view)
        add_resize_grip(self.graphic, self.view)

        choice_font = make_font(["Lucida Fax", "Georgia", "serif"], 18)

        self.pomodoro = PomodoroChoice(self)
        self.pomodoro.setFont(choice_font)
        self.pomodoro.setPos(center_x(self.pomodoro), 55)
        self.pomodoro.setDefaultTextColor(TEXT_COLOR)
        self.graphic.addItem(self.pomodoro)

        self.custom = CustomChoice(self)
        self.custom.setFont(choice_font)
        self.custom.setPos(center_x(self.custom), 100)
        self.custom.setDefaultTextColor(TEXT_COLOR)
        self.graphic.addItem(self.custom)

    def launchPomodoro(self):
        self.timer_widget = TimerWidget("Pomodoro", WORK_SECONDS, self.main_window)
        self.timer_widget.view.setWindowFlags(WIN_FLAGS)
        self.timer_widget.view.move(self.view.pos())
        self.timer_widget.view.show()
        self.view.hide()

    def launchCustom(self):
        self.custom.setVisible(False)
        self.pomodoro.setVisible(False)

        self.display_text = QLineEdit()
        self.display_text.setFixedWidth(190)
        self.display_text.setPlaceholderText("Enter the number of minutes")
        self.display_text.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                border-bottom: 2px solid rgb(176, 136, 123);
                color: rgb(110, 82, 72);
                font-family: "Lucida Fax", "Georgia", serif;
                font-size: 13px;
                padding: 5px;
                selection-background-color: rgb(176, 136, 123);
                selection-color: white;
            }
        """)
        proxy = self.graphic.addWidget(self.display_text)
        proxy.setPos((350 - 190) / 2, 50)

        self.confirm = ConfirmationButton(self)
        self.confirm.setPos(center_x(self.confirm), 85)
        self.graphic.addItem(self.confirm)


# contains the conditions on the time that you can enter in the field, then proceeds
class ConfirmationButton(HoverText):
    def __init__(self, parent_widget):
        super().__init__("Confirm")
        self.parent_widget = parent_widget
        self.setFont(make_font(["Lucida Fax", "Georgia", "serif"], 10))
        self.setDefaultTextColor(TEXT_COLOR)

    def mousePressEvent(self, event):
        self.ConfirmDuration()

    def ConfirmDuration(self):
        try:
            minutes = int(self.parent_widget.display_text.text())
        except ValueError:
            self.parent_widget.display_text.clear()
            self.parent_widget.display_text.setPlaceholderText("Enter a number greater than 0!")
            return
        if minutes <= 0:
            self.parent_widget.display_text.clear()
            self.parent_widget.display_text.setPlaceholderText("Enter a number greater than 0!")
            return
        self.parent_widget.timer_widget = TimerWidget(
            "Custom", minutes * 60, self.parent_widget.main_window)
        self.parent_widget.timer_widget.view.setWindowFlags(WIN_FLAGS)
        self.parent_widget.timer_widget.view.move(self.parent_widget.view.pos())
        self.parent_widget.timer_widget.view.show()
        self.parent_widget.view.hide()


# pomodoro
class PomodoroChoice(HoverText):
    def __init__(self, parent_widget):
        super().__init__("Pomodoro")
        self.parent_widget = parent_widget

    def mousePressEvent(self, event):
        self.parent_widget.launchPomodoro()


# custom timer
class CustomChoice(HoverText):
    def __init__(self, parent_widget):
        super().__init__("Custom")
        self.parent_widget = parent_widget

    def mousePressEvent(self, event):
        self.parent_widget.launchCustom()


# start and pause timer
class StartButton(QGraphicsItemGroup):
    def __init__(self, timer_widget):
        super().__init__()
        self.running = False
        self.timer_widget = timer_widget

        triangle = QPolygonF([QPointF(2, 4), QPointF(2, 14), QPointF(10, 9)])
        self.start = QGraphicsPolygonItem(triangle)
        self.start.setBrush(QBrush(TEXT_COLOR))
        self.start.setPen(QPen(TEXT_COLOR))
        self.addToGroup(self.start)

        self.pause_bar_1 = QGraphicsRectItem(4, 5, 2, 8)
        self.pause_bar_1.setBrush(QBrush(TEXT_COLOR))
        self.pause_bar_1.setPen(QPen(TEXT_COLOR))
        self.pause_bar_2 = QGraphicsRectItem(8, 5, 2, 8)
        self.pause_bar_2.setPen(QPen(TEXT_COLOR))
        self.pause_bar_2.setBrush(QBrush(TEXT_COLOR))
        self.addToGroup(self.pause_bar_1)
        self.addToGroup(self.pause_bar_2)
        self.pause_bar_1.setVisible(False)
        self.pause_bar_2.setVisible(False)

        self.setCursor(Qt.CursorShape.PointingHandCursor)

    # back to the "play" look without touching the timer (used by the stopwatch reset)
    def reset_visual(self):
        self.running = False
        self.pause_bar_1.setVisible(False)
        self.pause_bar_2.setVisible(False)
        self.start.setVisible(True)

    def mousePressEvent(self, event):
        if not self.running:
            self.timer_widget.start_timer()
            self.running = True
            self.pause_bar_1.setVisible(True)
            self.pause_bar_2.setVisible(True)
            self.start.setVisible(False)
        else:
            self.timer_widget.stop_timer()
            self.running = False
            self.pause_bar_1.setVisible(False)
            self.pause_bar_2.setVisible(False)
            self.start.setVisible(True)


# ---------------------------------------------------------------- stopwatch --
class ResetButton(HoverText):
    def __init__(self, parent_widget):
        super().__init__("Reset")
        self.parent_widget = parent_widget
        self.setFont(make_font(["Lucida Fax", "Georgia", "serif"], 10))
        self.setDefaultTextColor(TEXT_COLOR)

    def mousePressEvent(self, event):
        self.parent_widget.reset()


# counts up from zero; start/pause with the play button, reset with "Reset"
class StopwatchWidget(QObject):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window

        self.graphic = QGraphicsScene()
        self.graphic.setBackgroundBrush(QBrush(Qt.GlobalColor.transparent))
        self.graphic.setSceneRect(0, 0, 350, 200)
        # on_close pauses the stopwatch when the window is closed
        self.view = DraggableView(self.graphic, self.main_window, on_close=self.stop_timer,
                                  size_key="stopwatch")
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.view.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.view.setStyleSheet("background: transparent; border: none;")

        add_window_background(self.graphic)
        add_close_button(self.graphic, self.view)
        add_resize_grip(self.graphic, self.view)

        # time banked while paused + (now - start_time) while running (monotonic, no drift)
        self.elapsed = 0.0
        self.start_time = None

        self.time_text = QGraphicsTextItem()
        self.time_text.setPos(20, 1 + CLOCK_Y_OFFSET)
        self.time_text.setFont(make_font(["Cooper Black", "Georgia", "serif"], 45))
        self.time_text.setDefaultTextColor(TEXT_COLOR)
        self.graphic.addItem(self.time_text)

        self.label = QGraphicsTextItem("Stopwatch")
        self.label.setFont(make_font(["Pluma", "Georgia", "serif"], 10))
        self.label.setDefaultTextColor(TEXT_COLOR)
        self.label.setPos(center_x(self.label), 60 + CLOCK_Y_OFFSET)
        self.graphic.addItem(self.label)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_display)

        self.initial = StartButton(self)
        self.graphic.addItem(self.initial)

        self.reset_button = ResetButton(self)
        self.graphic.addItem(self.reset_button)

        self.align_buttons()
        self.update_display()

    # puts the play button and "Reset" side by side, centred in the window and on one line
    def align_buttons(self, center_y=112 + CLOCK_Y_OFFSET, gap=16):
        start_rect = self.initial.boundingRect()
        reset_rect = self.reset_button.boundingRect()
        total = start_rect.width() + gap + reset_rect.width()
        x0 = (350 - total) / 2
        self.initial.setPos(x0 - start_rect.left(), center_y - start_rect.center().y())
        self.reset_button.setPos(x0 + start_rect.width() + gap - reset_rect.left(),
                                 center_y - reset_rect.center().y())

    def current_elapsed(self):
        if self.start_time is None:
            return self.elapsed
        return self.elapsed + (time.monotonic() - self.start_time)

    # shows the elapsed time as HH : MM : SS
    def update_display(self):
        total = int(self.current_elapsed())
        hours = total // 3600
        minutes = (total % 3600) // 60
        seconds = total % 60
        text = f"{hours:02d} : {minutes:02d} : {seconds:02d}"
        if self.time_text.toPlainText() != text:
            self.time_text.setPlainText(text)

    # the StartButton calls these two
    def start_timer(self):
        self.start_time = time.monotonic()
        self.timer.start(100)

    def stop_timer(self):
        if self.start_time is not None:
            self.elapsed += time.monotonic() - self.start_time
            self.start_time = None
        self.timer.stop()
        self.update_display()

    def reset(self):
        self.stop_timer()
        self.elapsed = 0.0
        self.initial.reset_visual()
        self.update_display()


# ------------------------------------------------------------------- to-do --
TODO_INPUT_STYLE = """
QLineEdit {
    background: rgba(176, 136, 123, 28);
    border: none;
    border-radius: 10px;
    color: rgb(110, 82, 72);
    font-family: "Lucida Fax", "Georgia", serif;
    font-size: 12px;
    padding: 6px 10px;
    selection-background-color: rgb(176, 136, 123);
    selection-color: white;
}
QLineEdit:focus {
    background: rgba(176, 136, 123, 46);
}
"""

TODO_LIST_STYLE = """
QListWidget {
    background: transparent;
    border: none;
    outline: none;
    color: rgb(110, 82, 72);
    font-family: "Lucida Fax", "Georgia", serif;
    font-size: 12px;
}
QListWidget::item {
    padding: 5px 4px;
    margin: 1px 0px;
    border-radius: 8px;
}
QListWidget::item:hover {
    background: rgba(176, 136, 123, 38);
}
QListWidget::item:selected {
    background: rgba(176, 136, 123, 64);
}
%INDICATOR%
QScrollBar:vertical {
    background: transparent;
    width: 6px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: rgba(176, 136, 123, 150);
    border-radius: 3px;
    min-height: 16px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: transparent;
}
"""

_check_icons = None


# draws the round checkbox pictures (empty ring / filled circle with a tick) once
def make_check_icons():
    global _check_icons
    if _check_icons is not None:
        return _check_icons
    folder = Path(tempfile.gettempdir())
    paths = {}
    for name, checked in (("off", False), ("on", True)):
        pixmap = QPixmap(18, 18)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        if checked:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(176, 136, 123)))
            painter.drawEllipse(QRectF(1, 1, 16, 16))
            tick_pen = QPen(QColor(255, 250, 240), 2)
            tick_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            tick_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(tick_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPolyline(QPolygonF([QPointF(5.2, 9.3), QPointF(8, 12), QPointF(13, 6.2)]))
        else:
            painter.setPen(QPen(QColor(176, 136, 123), 1.6))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QRectF(1.5, 1.5, 15, 15))
        painter.end()
        path = folder / f"desktopbuddy_check_{name}.png"
        if not pixmap.save(str(path)):
            _check_icons = {}
            return _check_icons
        paths[name] = path.as_posix()
    _check_icons = paths
    return paths


def build_todo_list_style():
    icons = make_check_icons()
    if icons:
        indicator = (
            "QListWidget::indicator { width: 18px; height: 18px; image: url(%s); }\n"
            "QListWidget::indicator:checked { image: url(%s); }"
        ) % (icons["off"], icons["on"])
    else:   # couldn't write the pictures: plain styled circles instead
        indicator = (
            "QListWidget::indicator { width: 14px; height: 14px; border: 2px solid "
            "rgb(176, 136, 123); border-radius: 8px; background: transparent; }\n"
            "QListWidget::indicator:checked { background: rgb(176, 136, 123); }"
        )
    return TODO_LIST_STYLE.replace("%INDICATOR%", indicator)


# a little Cinder (same look as the desktop cat) that pops up to cheer, party hat and all
class CinderCheer(QGraphicsItemGroup):
    SCALE = 0.8
    HEAD = (55, 40)     # head centre in the cat's own coordinates

    def __init__(self):
        super().__init__()
        outline_pen = QPen(CAT_OUTLINE_COLOR, CAT_OUTLINE_PEN_WIDTH)
        outline_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        fill_pen = QPen(Qt.GlobalColor.white, 3)
        no_pen = QPen(Qt.PenStyle.NoPen)
        white = QBrush(Qt.GlobalColor.white)
        black = QBrush(Qt.GlobalColor.black)
        pink = QBrush(QColor(244, 172, 218))
        yellow = QBrush(QColor(255, 214, 90))

        left_ear = [QPointF(38, 20), QPointF(48, 20), QPointF(41, 5)]
        right_ear = [QPointF(62, 20), QPointF(72, 20), QPointF(70, 5)]

        def add(item, pen, brush):
            item.setPen(pen)
            item.setBrush(brush)
            self.addToGroup(item)
            return item

        # silhouette: body and head, outline first, white fill on top
        def silhouette(pen):
            for x, y, w, h in ((20, 50, 70, 90), (30, 15, 50, 50)):
                add(QGraphicsEllipseItem(x, y, w, h), pen, white)
            for pts in (left_ear, right_ear):
                add(QGraphicsPolygonItem(QPolygonF(pts)), pen, white)
        silhouette(outline_pen)
        silhouette(fill_pen)

        # inner ears
        add(QGraphicsPolygonItem(shrink_polygon(left_ear, 0.5)), no_pen, pink)
        add(QGraphicsPolygonItem(shrink_polygon(right_ear, 0.5)), no_pen, pink)

        # face (same as the desktop cat)
        add(QGraphicsEllipseItem(38, 38, 12, 8), fill_pen, pink)
        add(QGraphicsEllipseItem(62, 38, 12, 8), fill_pen, pink)
        add(QGraphicsEllipseItem(51, 36, 10, 6), fill_pen, black)
        add(QGraphicsEllipseItem(41, 22, 13, 16), fill_pen, black)
        add(QGraphicsEllipseItem(47, 28, 2, 4), fill_pen, white)
        add(QGraphicsEllipseItem(57, 22, 13, 16), fill_pen, black)
        add(QGraphicsEllipseItem(63, 28, 2, 4), fill_pen, white)

        muzzle = QPainterPath()
        muzzle.moveTo(48, 48)
        muzzle.cubicTo(50, 51, 52, 52, 56, 48)
        muzzle.cubicTo(60, 52, 62, 51, 64, 48)
        muzzle.moveTo(56, 48)
        muzzle.lineTo(56, 38)
        add(QGraphicsPathItem(muzzle), QPen(QColor(0, 0, 0, 200)), QBrush())

        whiskers = QPainterPath()
        for x1, y1, x2, y2 in ((44, 40, 34, 38), (44, 42, 34, 42), (44, 44, 34, 46),
                               (68, 40, 78, 38), (68, 42, 78, 42), (68, 44, 78, 46)):
            whiskers.moveTo(x1, y1)
            whiskers.lineTo(x2, y2)
        add(QGraphicsPathItem(whiskers), QPen(QColor(0, 0, 0, 128)), QBrush())

        # collar and bell
        collar = QPainterPath()
        collar.addRoundedRect(QRectF(31, 57, 48, 6), 5, 5)
        add(QGraphicsPathItem(collar), no_pen, QBrush(QColor(240, 54, 116, 200)))
        add(QGraphicsEllipseItem(48, 59, 12, 12), no_pen, yellow)

        # party hat
        hat_pen = QPen(CAT_OUTLINE_COLOR, 1.2)
        add(QGraphicsPolygonItem(QPolygonF([QPointF(48, 18), QPointF(64, 18), QPointF(57, -10)])),
            hat_pen, QBrush(QColor(255, 105, 150)))
        add(QGraphicsEllipseItem(54, 8, 3, 3), no_pen, yellow)
        add(QGraphicsEllipseItem(57, 0, 3, 3), no_pen, yellow)
        add(QGraphicsEllipseItem(53.5, -13.5, 7, 7), QPen(CAT_OUTLINE_COLOR, 1), yellow)


# the little speech bubble next to Cinder
class CheerBubble(QGraphicsItemGroup):
    def __init__(self):
        super().__init__()
        self.width = 0
        self.body = QGraphicsPathItem()
        self.body.setPen(QPen(TEXT_COLOR, 1.5))
        self.body.setBrush(QBrush(QColor(255, 255, 250)))
        self.label = QGraphicsTextItem()
        self.label.setFont(make_font(["Lucida Fax", "Georgia", "serif"], 10))
        self.label.setDefaultTextColor(TODO_TEXT_COLOR)
        self.addToGroup(self.body)
        self.addToGroup(self.label)

    def set_text(self, text):
        self.label.setPlainText(text)
        rect = self.label.boundingRect()
        w, h = rect.width(), rect.height()
        path = QPainterPath()
        path.addRoundedRect(QRectF(0, 0, w, h), 10, 10)
        path.addEllipse(QRectF(w + 2, h * 0.55, 6, 6))        # little trailing bubbles
        path.addEllipse(QRectF(w + 10, h * 0.8, 3.5, 3.5))
        self.body.setPath(path)
        self.width = w + 14


# the task list; Delete / Backspace removes the selected task
class TodoList(QListWidget):
    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            row = self.currentRow()
            if row >= 0:
                self.takeItem(row)
            return
        super().keyPressEvent(event)


class ClearDoneButton(HoverText):
    def __init__(self, parent_widget):
        super().__init__("Clear done")
        self.parent_widget = parent_widget
        self.setFont(make_font(["Lucida Fax", "Georgia", "serif"], 10))
        self.setDefaultTextColor(TEXT_COLOR)

    def mousePressEvent(self, event):
        self.parent_widget.clear_done()


# type a task + Enter to add it, tick it to strike it off (confetti + Cinder!); saved to todos.json
class TodoWidget(QObject):
    WIDTH = 270
    HEIGHT = 250
    CINDER_POS = (WIDTH - 58, HEIGHT - 22)   # where Cinder's head peeks up while celebrating
    CHEER_TIME = 2.6                         # seconds

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        W, H = self.WIDTH, self.HEIGHT

        self.graphic = QGraphicsScene()
        self.graphic.setBackgroundBrush(QBrush(Qt.GlobalColor.transparent))
        self.graphic.setSceneRect(0, 0, W, H)
        self.view = DraggableView(self.graphic, self.main_window, size_key="todo")
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.view.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.view.setStyleSheet("background: transparent; border: none;")

        # cream, rounded panel with a brown border (like the menus) and the faded background image
        self.panel = add_window_background(self.graphic, W, H, image=True, crop=True)
        self.graphic.addRect(QRectF(16, 36, W - 32, 1), QPen(Qt.PenStyle.NoPen),
                             QBrush(QColor(176, 136, 123, 80)))
        add_close_button(self.graphic, self.view, W)
        add_resize_grip(self.graphic, self.view, W, H)

        self.title = QGraphicsTextItem("To-do")
        self.title.setFont(make_font(["Lucida Fax", "Georgia", "serif"], 13))
        self.title.setDefaultTextColor(TODO_TEXT_COLOR)
        self.title.setPos(14, 3)
        self.graphic.addItem(self.title)

        self.count_text = QGraphicsTextItem()
        self.count_text.setFont(make_font(["Lucida Fax", "Georgia", "serif"], 10))
        self.count_text.setDefaultTextColor(TEXT_COLOR)
        self.graphic.addItem(self.count_text)

        self.input = QLineEdit()
        self.input.setFixedWidth(W - 32)
        self.input.setMaxLength(80)
        self.input.setPlaceholderText("Add a task and press Enter")
        self.input.setStyleSheet(TODO_INPUT_STYLE)
        self.input.returnPressed.connect(self.add_from_input)
        input_proxy = self.graphic.addWidget(self.input)
        input_proxy.setPos(16, 42)

        list_height = H - 78 - 42
        self.list = TodoList()
        self.list.setFixedSize(W - 32, list_height)
        self.list.setStyleSheet(build_todo_list_style())
        self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.list.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.list.setWordWrap(False)
        self.list.setUniformItemSizes(True)
        self.list.setToolTip("Tick to strike off, Delete removes the selected task")
        self.list.itemChanged.connect(self.on_item_changed)
        self.list.model().rowsRemoved.connect(self.on_rows_changed)
        self.list_proxy = self.graphic.addWidget(self.list)
        self.list_proxy.setPos(16, 78)

        # shown when the list is empty
        self.empty_hint = QGraphicsTextItem("No tasks yet - add one above!")
        self.empty_hint.setFont(make_font(["Lucida Fax", "Georgia", "serif"], 10))
        self.empty_hint.setDefaultTextColor(TODO_DONE_COLOR)
        self.empty_hint.setPos(center_x(self.empty_hint, W),
                               78 + list_height / 2 - self.empty_hint.boundingRect().height() / 2)
        self.graphic.addItem(self.empty_hint)

        self.clear_button = ClearDoneButton(self)
        self.clear_button.setPos(12, H - 30)
        self.graphic.addItem(self.clear_button)

        # celebration: confetti + Cinder with a speech bubble
        self.confetti = []
        self.cheer_start = None
        self.last_fx = time.time()
        self.cinder = CinderCheer()
        self.cinder.setScale(CinderCheer.SCALE)
        self.cinder.setZValue(900)
        self.cinder.setVisible(False)
        self.graphic.addItem(self.cinder)
        self.bubble = CheerBubble()
        self.bubble.setZValue(900)
        self.bubble.setVisible(False)
        self.graphic.addItem(self.bubble)
        self.fx_timer = QTimer(self)
        self.fx_timer.timeout.connect(self.fx_tick)

        self.load_tasks()
        self.update_count()

    # ---- items ----
    def add_item(self, text, done=False):
        item = QListWidgetItem(text)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(Qt.CheckState.Checked if done else Qt.CheckState.Unchecked)
        item.setData(Qt.ItemDataRole.UserRole, done)     # remembers the last done-state
        item.setToolTip(text)
        self.style_item(item)
        self.list.addItem(item)
        return item

    # done tasks are struck through and faded
    def style_item(self, item):
        done = item.checkState() == Qt.CheckState.Checked
        font = item.font()
        font.setStrikeOut(done)
        item.setFont(font)
        item.setForeground(QBrush(TODO_DONE_COLOR if done else TODO_TEXT_COLOR))

    def add_from_input(self):
        text = self.input.text().strip()
        if not text:
            return
        self.add_item(text)
        self.input.clear()
        self.list.scrollToBottom()
        self.update_count()
        self.save()

    def on_item_changed(self, item):
        done = item.checkState() == Qt.CheckState.Checked
        was_done = bool(item.data(Qt.ItemDataRole.UserRole))
        self.list.blockSignals(True)     # changing an item here would re-trigger itemChanged
        item.setData(Qt.ItemDataRole.UserRole, done)
        self.style_item(item)
        self.list.blockSignals(False)
        self.update_count()
        self.save()
        if done and not was_done:        # just struck off -> celebrate!
            self.celebrate(self.checkbox_origin(item), self.tasks_left() == 0)

    def on_rows_changed(self, *args):
        self.update_count()
        self.save()

    def clear_done(self):
        for row in range(self.list.count() - 1, -1, -1):
            if self.list.item(row).checkState() == Qt.CheckState.Checked:
                self.list.takeItem(row)

    def tasks_left(self):
        return sum(1 for row in range(self.list.count())
                   if self.list.item(row).checkState() != Qt.CheckState.Checked)

    def update_count(self):
        total = self.list.count()
        left = self.tasks_left()
        if total == 0:
            text = "Nothing here yet"
        elif left == 0:
            text = "All done!"
        else:
            text = f"{left} left"
        self.count_text.setPlainText(text)
        # right-aligned, leaving room for the x button
        self.count_text.setPos(self.WIDTH - 30 - self.count_text.boundingRect().width(), 8)
        self.empty_hint.setVisible(total == 0)

    # ---- saving / loading ----
    def load_tasks(self):
        try:
            data = json.loads(TODO_PATH.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return
        if not isinstance(data, list):
            return
        self.list.blockSignals(True)
        for entry in data:
            if isinstance(entry, dict) and str(entry.get("text", "")).strip():
                self.add_item(str(entry["text"]), bool(entry.get("done")))
        self.list.blockSignals(False)

    def save(self):
        data = []
        for row in range(self.list.count()):
            item = self.list.item(row)
            data.append({
                "text": item.text(),
                "done": item.checkState() == Qt.CheckState.Checked,
            })
        try:
            TODO_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        except OSError as err:
            print(f"[DesktopBuddy] Couldn't save the to-do list: {err}")

    # ---- celebration ----
    # scene position of the tick box that was just clicked
    def checkbox_origin(self, item):
        rect = self.list.visualItemRect(item)
        return QPointF(self.list_proxy.x() + rect.left() + 14,
                       self.list_proxy.y() + rect.center().y())

    def celebrate(self, origin, all_done):
        now = time.time()
        extra = 30 if all_done else 0
        self.spawn_confetti(origin, 40 + extra, 24 + extra)

        self.bubble.set_text("All done! Purrfect!" if all_done else random.choice(CHEERS))
        self.bubble.setPos(self.CINDER_POS[0] - 40 - self.bubble.width, self.HEIGHT - 44)
        self.cheer_start = now
        self.cinder.setVisible(True)
        self.bubble.setVisible(True)
        self.update_cheer(now)

        if not self.fx_timer.isActive():
            self.last_fx = now
            self.fx_timer.start(20)

    def spawn_confetti(self, origin, burst, rain):
        now = time.time()
        for _ in range(burst):      # a fan of confetti shooting up from the tick box
            angle = random.uniform(-2.6, -0.55)
            speed = random.uniform(220, 460)
            self.add_piece(origin.x(), origin.y(), cos(angle) * speed, sin(angle) * speed,
                           gravity=480, start=now, life=random.uniform(1.4, 2.2), sway=0)
        for _ in range(rain):       # and a shower from the top
            self.add_piece(random.uniform(14, self.WIDTH - 14), random.uniform(-30, -4),
                           random.uniform(-25, 25), random.uniform(40, 100),
                           gravity=70, start=now + random.uniform(0, 0.9),
                           life=random.uniform(1.8, 2.8), sway=random.uniform(15, 35))

    def add_piece(self, x, y, vx, vy, gravity, start, life, sway):
        shape = random.random()
        if shape < 0.5:
            item = QGraphicsRectItem(-3.5, -2, 7, 4)
        elif shape < 0.75:
            item = QGraphicsEllipseItem(-2.2, -2.2, 4.4, 4.4)
        else:
            item = QGraphicsRectItem(-5, -1.2, 10, 2.4)
        item.setBrush(QBrush(random.choice(CONFETTI_COLORS)))
        item.setPen(QPen(Qt.PenStyle.NoPen))
        item.setZValue(1000)
        item.setPos(x, y)
        item.setVisible(False)       # shown once its start time arrives
        self.graphic.addItem(item)
        self.confetti.append({
            "item": item, "x": x, "y": y, "vx": vx, "vy": vy, "g": gravity,
            "drag": 0.9, "start": start, "life": life, "sway": sway,
            "phase": random.uniform(0, 2 * pi), "flutter": random.uniform(6, 12),
            "rot": random.uniform(0, 360), "vrot": random.uniform(-420, 420),
        })

    def fx_tick(self):
        now = time.time()
        dt = min(now - self.last_fx, 0.05)
        self.last_fx = now
        self.update_confetti(now, dt)
        self.update_cheer(now)
        if not self.confetti and self.cheer_start is None:
            self.fx_timer.stop()

    def update_confetti(self, now, dt):
        alive = []
        for c in self.confetti:
            item = c["item"]
            if now < c["start"]:
                alive.append(c)
                continue
            if not item.isVisible():
                item.setVisible(True)
            age = now - c["start"]
            if age >= c["life"] or c["y"] > self.HEIGHT + 15:
                self.graphic.removeItem(item)
                continue
            k = max(0.0, 1 - c["drag"] * dt)
            c["vx"] *= k
            c["vy"] = c["vy"] * k + c["g"] * dt
            c["x"] += (c["vx"] + sin(age * 6 + c["phase"]) * c["sway"]) * dt
            c["y"] += c["vy"] * dt
            c["rot"] += c["vrot"] * dt
            item.setPos(c["x"], c["y"])
            item.setRotation(c["rot"])
            flip = max(0.2, abs(cos(age * c["flutter"] + c["phase"])))   # fluttering look
            item.setTransform(QTransform().scale(1.0, flip))
            item.setOpacity(min(1.0, (c["life"] - age) / 0.5))
            alive.append(c)
        self.confetti = alive

    # Cinder pops up, bounces happily, then ducks back down
    def update_cheer(self, now):
        if self.cheer_start is None:
            return
        t = now - self.cheer_start
        if t >= self.CHEER_TIME:
            self.cheer_start = None
            self.cinder.setVisible(False)
            self.bubble.setVisible(False)
            return
        rise = 1.0
        bob = 0.0
        if t < 0.35:
            u = t / 0.35
            rise = 1 - (1 - u) ** 3
        elif t > self.CHEER_TIME - 0.4:
            u = (t - (self.CHEER_TIME - 0.4)) / 0.4
            rise = 1 - u * u
        else:
            bob = abs(sin(t * 9)) * 5
        s = CinderCheer.SCALE
        cx, cy = self.CINDER_POS
        self.cinder.setPos(cx - s * CinderCheer.HEAD[0],
                           cy - s * CinderCheer.HEAD[1] + (1 - rise) * 60 - bob)
        self.bubble.setOpacity(max(0.0, min(1.0, rise * 1.5 - 0.5)))


# ------------------------------------------------------------ water reminder --
# clickable text that runs a callback
class ActionText(HoverText):
    def __init__(self, text, callback):
        super().__init__(text)
        self.callback = callback
        self.setFont(make_font(["Lucida Fax", "Georgia", "serif"], 10))
        self.setDefaultTextColor(TEXT_COLOR)

    def mousePressEvent(self, event):
        self.callback()


# pill-shaped button: the preset chips and the - / + stepper
class PillButton(QGraphicsItem):
    clickable = True

    def __init__(self, text, width, height, callback, font_size=9):
        super().__init__()
        self.label_text = text
        self.w = width
        self.h = height
        self.callback = callback
        self.selected = False
        self.hovered = False
        self.label_font = make_font(["Lucida Fax", "Georgia", "serif"], font_size)
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def boundingRect(self):
        return QRectF(0, 0, self.w, self.h)

    def set_selected(self, value):
        if self.selected != value:
            self.selected = value
            self.update()

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(0.8, 0.8, self.w - 1.6, self.h - 1.6)
        radius = rect.height() / 2
        if self.selected:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(TEXT_COLOR))
            text_color = QColor(255, 250, 240)
        else:
            painter.setPen(QPen(HOVER_COLOR if self.hovered else TEXT_COLOR, 1.4))
            painter.setBrush(QBrush(QColor(176, 136, 123, 45)) if self.hovered
                             else Qt.BrushStyle.NoBrush)
            text_color = HOVER_COLOR if self.hovered else TEXT_COLOR
        painter.drawRoundedRect(rect, radius, radius)
        painter.setPen(text_color)
        painter.setFont(self.label_font)
        painter.drawText(self.boundingRect(), Qt.AlignmentFlag.AlignCenter, self.label_text)

    def hoverEnterEvent(self, event):
        self.hovered = True
        self.update()

    def hoverLeaveEvent(self, event):
        self.hovered = False
        self.update()

    def mousePressEvent(self, event):
        self.callback()


# on / off switch
class ToggleSwitch(QGraphicsItem):
    clickable = True
    W = 38
    H = 20

    def __init__(self, checked, callback):
        super().__init__()
        self.checked = bool(checked)
        self.callback = callback
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def boundingRect(self):
        return QRectF(0, 0, self.W, self.H)

    def paint(self, painter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(TEXT_COLOR if self.checked else QColor(222, 208, 200)))
        painter.drawRoundedRect(self.boundingRect(), self.H / 2, self.H / 2)
        knob = self.H - 6
        x = self.W - 3 - knob if self.checked else 3
        painter.setBrush(QBrush(QColor(255, 250, 240)))
        painter.drawEllipse(QRectF(x, 3, knob, knob))

    def mousePressEvent(self, event):
        self.checked = not self.checked
        self.update()
        self.callback(self.checked)


# settings window: on/off, how often, and whether the reminder beats the other windows
class WaterSettingsWidget(QObject):
    W = 350
    H = 220
    PRESETS = (15, 30, 45, 60, 90)
    ROW_ENABLE = 58
    ROW_EVERY = 92
    ROW_CHIPS = 124
    ROW_PRIORITY = 170

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.minutes = main_window.water_minutes
        W, H = self.W, self.H
        right = W - 18

        self.graphic = QGraphicsScene()
        self.graphic.setBackgroundBrush(QBrush(Qt.GlobalColor.transparent))
        self.graphic.setSceneRect(0, 0, W, H)
        self.view = DraggableView(self.graphic, self.main_window, size_key="water")
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.view.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.view.setStyleSheet("background: transparent; border: none;")

        add_window_background(self.graphic, W, H, opacity=WATER_BG_OPACITY)
        add_close_button(self.graphic, self.view, W)
        add_resize_grip(self.graphic, self.view, W, H)

        title = self.add_text("💧 Water reminder", 13, TODO_TEXT_COLOR)
        title.setPos(14, 3)
        self.add_divider(36)
        self.add_divider(148)

        # row 1: on / off
        self.add_label("Reminders", self.ROW_ENABLE)
        self.enable_switch = ToggleSwitch(main_window.water_enabled, main_window.set_water_enabled)
        self.enable_switch.setPos(right - ToggleSwitch.W, self.ROW_ENABLE - ToggleSwitch.H / 2)
        self.graphic.addItem(self.enable_switch)

        # row 2: how often  ( -  30 min  + )
        self.add_label("Every", self.ROW_EVERY)
        btn = 22
        self.plus = PillButton("+", btn, btn, lambda: self.nudge(1), font_size=11)
        self.plus.setPos(right - btn, self.ROW_EVERY - btn / 2)
        self.minus = PillButton("−", btn, btn, lambda: self.nudge(-1), font_size=11)
        self.minus.setPos(right - btn - 4 - 60 - 4 - btn, self.ROW_EVERY - btn / 2)
        self.graphic.addItem(self.plus)
        self.graphic.addItem(self.minus)
        self.value_cx = right - btn - 4 - 30
        self.value_text = self.add_text("", 10, TODO_TEXT_COLOR)

        # preset chips
        chip_w, gap = 46, 8
        x0 = (W - (len(self.PRESETS) * chip_w + (len(self.PRESETS) - 1) * gap)) / 2
        self.chips = {}
        for i, minutes in enumerate(self.PRESETS):
            chip = PillButton(f"{minutes}m", chip_w, 22, lambda m=minutes: self.set_minutes(m))
            chip.setPos(x0 + i * (chip_w + gap), self.ROW_CHIPS - 11)
            self.graphic.addItem(chip)
            self.chips[minutes] = chip

        # row 3: prioritize
        priority = self.add_label("Prioritize over other windows", self.ROW_PRIORITY)
        tip = "When on, Cinder pops up over a timer or to-do window to remind you"
        priority.setToolTip(tip)
        self.priority_switch = ToggleSwitch(main_window.water_prioritize,
                                            main_window.set_water_prioritize)
        self.priority_switch.setPos(right - ToggleSwitch.W, self.ROW_PRIORITY - ToggleSwitch.H / 2)
        self.priority_switch.setToolTip(tip)
        self.graphic.addItem(self.priority_switch)

        # test link
        test = ActionText("Send a test reminder", main_window.test_water)
        test.setFont(make_font(["Lucida Fax", "Georgia", "serif"], 9))
        test.setPos(14, 190)
        self.graphic.addItem(test)

        self.refresh()

    # ---- little layout helpers ----
    def add_text(self, text, size, color):
        item = QGraphicsTextItem(text)
        item.setFont(make_font(["Lucida Fax", "Georgia", "serif"], size))
        item.setDefaultTextColor(color)
        self.graphic.addItem(item)
        return item

    def add_label(self, text, center_y, size=10):
        item = self.add_text(text, size, TODO_TEXT_COLOR)
        item.setPos(14, center_y - item.boundingRect().height() / 2)
        return item

    def add_divider(self, y):
        self.graphic.addRect(QRectF(16, y, self.W - 32, 1), QPen(Qt.PenStyle.NoPen),
                             QBrush(QColor(176, 136, 123, 80)))

    # ---- behaviour ----
    def nudge(self, direction):
        m = self.minutes
        if direction > 0:
            m = m + 1 if m < 10 else m + 5
        else:
            m = m - 1 if m <= 10 else m - 5
        self.set_minutes(m)

    def set_minutes(self, minutes):
        self.minutes = max(WATER_MIN_MINUTES, min(WATER_MAX_MINUTES, minutes))
        self.main_window.set_water_minutes(self.minutes)
        self.refresh()

    def refresh(self):
        self.value_text.setPlainText(f"{self.minutes} min")
        rect = self.value_text.boundingRect()
        self.value_text.setPos(self.value_cx - rect.width() / 2,
                               self.ROW_EVERY - rect.height() / 2)
        for minutes, chip in self.chips.items():
            chip.set_selected(minutes == self.minutes)


# creating a window for the widget
def main():
    app = QApplication(sys.argv)
    window = DesktopBuddy()
    app.aboutToQuit.connect(window.cat.stop_listeners)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()