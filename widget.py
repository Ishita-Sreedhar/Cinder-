import sys
from PyQt6.QtCore import Qt, QPoint, QPointF, QRectF, QTimer, QObject
from PyQt6.QtWidgets import QApplication, QGraphicsView, QWidget, QMenu, QGraphicsScene, QVBoxLayout, QLabel, QGraphicsTextItem, QGraphicsItemGroup,QGraphicsPolygonItem, QGraphicsRectItem
from PyQt6.QtGui import QMouseEvent, QContextMenuEvent, QPainterPath, QBrush, QPen, QPolygonF, QColor, QCursor, QPainter, QPixmap, QFont
from math import sin, sqrt
import time, datetime
from pynput import keyboard, mouse
from datetime import datetime

class DesktopBuddy(QWidget):
    #creates a widget for the desktop buddy
    
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True )
        self.offset = QPoint()
        self.setFixedSize(600,200)

        #creates the cat , layouts it and adds it into the widget
        self.cat = BuddyCat()
        self.layout=QVBoxLayout()
        self.layout.addWidget(self.cat.view)
        self.setLayout(self.layout)
        self.show()

        #greeting
        curr_time = datetime.now().hour
        if(curr_time >=0 and curr_time<4): self.text = "Buddy it's midnight. SLEEP!!!!"
        elif ( curr_time >= 4 and curr_time <= 8): self.text = "Wakey Wakey!"
        elif (curr_time > 8 and curr_time <= 12): self.text = "Good Morning!"
        elif (curr_time >12 and curr_time <= 15): self.text = "Afternoon already?"
        elif (curr_time > 15 and curr_time <=19 ): self.text = "Tea timeee"
        elif ( curr_time > 19 and curr_time <= 22): self.text = "Chill mode? or hustle mode?"
        elif (curr_time > 22 and curr_time <=23 ): self.text = "Giving night owl vibes.."
        
        message = QLabel(self.text)
        message.setStyleSheet(""" background-color: rgb(243, 243, 219); 
                              padding: 6px 10px;
                              border-radius: 10px;
                              color: black;
                              font-size: 12px""")
        message.setParent(self)
        message.adjustSize()
        message.move(300,3)
        message.show()
        QTimer.singleShot(6000, message.hide)

    #lets us select the widget
    def mousePressEvent(self, event: QMouseEvent):
        self.offset=  event.globalPosition().toPoint() - self.pos()

    #lets us move the widget
    def mouseMoveEvent(self, event: QMouseEvent):
        self.window_Position = event.globalPosition().toPoint() - self.offset
        self.move(self.window_Position)

    #opens context menu on right click
    def contextMenuEvent(self, event: QContextMenuEvent):
        menu = QMenu()
        menu.addAction("Exit", QApplication.instance().quit)
        menu.exec(event.globalPos())


class BuddyCat(QObject):
    def __init__(self):
        #creates transparent QGraphicScene displayed by QGraphicViews
        super().__init__()
        self.graphic = QGraphicsScene()
        self.graphic.setBackgroundBrush(QBrush(Qt.GlobalColor.transparent))
        self.graphic.setSceneRect(0,0,120,150)
        self.view = QGraphicsView(self.graphic)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.view.setStyleSheet("background: transparent; border: none;")
        self.view.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)  #done so that this doesnt overshadow our mousepress events in other class
        
        #setting the style of our pen and brush
        self.pen = QPen(Qt.GlobalColor.white, 3, Qt.PenStyle.SolidLine)
        self.white_brush = QBrush(Qt.GlobalColor.white, Qt.BrushStyle.SolidPattern)
        self.black_brush = QBrush(Qt.GlobalColor.black, Qt.BrushStyle.SolidPattern)
        pink_brush = QBrush(QColor(244, 172, 218))

        #body
        self.graphic.addEllipse(20,50, 70, 90, self.pen, self.white_brush)

        #head
        self.graphic.addEllipse(30, 15, 50, 50, self.pen, self.white_brush)
        
        #tail
        self.tail_item = self.graphic.addPath(QPainterPath(), self.pen)
        self.tail_item.setBrush(self.white_brush)
        self.draw_tail()
        self.sway_angle = 0
        self.timer1 = QTimer(self)
        self.timer1.timeout.connect(self.animate_tail)
        self.timer1.timeout.connect(self.track_cursor)
        self.timer1.timeout.connect(self.update_state)
        self.timer1.start(50)
        

        #ears
        left_ear = QPolygonF([QPointF(38,20), QPointF(48,20), QPointF(41,5)])
        self.graphic.addPolygon(left_ear, self.pen, self.white_brush )
        right_ear = QPolygonF([QPointF(62,20), QPointF(72,20), QPointF(70,5)])
        self.graphic.addPolygon(right_ear, self.pen, self.white_brush)

        #inner ear
        lefti_ear = QPolygonF([QPointF(38,20), QPointF(48,20), QPointF(41,5)])
        self.graphic.addPolygon(lefti_ear, self.pen, pink_brush)
        righti_ear = QPolygonF([QPointF(62,20), QPointF(72,20), QPointF(70,5)])
        self.graphic.addPolygon(righti_ear, self.pen, pink_brush)

        #faciacl features
        #blush
        self.graphic.addEllipse(38,38,12,8,self.pen,pink_brush)
        self.graphic.addEllipse(62,38,12,8,self.pen,pink_brush)

        #nose
        self.graphic.addEllipse(51,36,10,6, self.pen, self.black_brush)

        #eyes
        self.left_eye = self.graphic.addEllipse(41,22,13,16, self.pen, self.black_brush)
        self.left_eye_inner = self.graphic.addEllipse(47,28,2,4, self.pen, self.white_brush)
        self.right_eye = self.graphic.addEllipse(57,22,13,16, self.pen, self.black_brush)
        self.right_eye_inner = self.graphic.addEllipse(63,28,2,4, self.pen, self.white_brush)

        closed_left_eye_path = QPainterPath()
        closed_eye_pen = QPen(Qt.GlobalColor.black, 1)
        closed_left_eye_path.moveTo(41,30)
        closed_left_eye_path.cubicTo(41,36, 49,36, 49,30)
        self.closed_left_eye = self.graphic.addPath(closed_left_eye_path, closed_eye_pen)
        self.closed_left_eye.setVisible(False)
        closed_right_eye_path = QPainterPath()
        closed_right_eye_path.moveTo(60,30)
        closed_right_eye_path.cubicTo(60,36, 68,36, 68,30)
        self.closed_right_eye = self.graphic.addPath(closed_right_eye_path, closed_eye_pen)
        self.closed_right_eye.setVisible(False)
        

        self.blinkheight = 16
        self.closing = True
        self.timer2 = QTimer(self)
        self.timer2.timeout.connect(self.animate_blink)
        self.timer2.start(4000)
        

        #mouth
        mouth_pen = QPen(QColor(0, 0, 0, 200))
        muzzle_path = QPainterPath()
        muzzle_path.moveTo(48,48)
        muzzle_path.cubicTo(50,51,52,52,56,48)
        muzzle_path.cubicTo(60,52,62,51,64,48)
        
        muzzle_path.moveTo(56,48)
        muzzle_path.lineTo(56,38)
        self.muzzle = self.graphic.addPath(muzzle_path, mouth_pen)
        self.sleep_muzzle = self.graphic.addEllipse(52.5,44, 8, 8, mouth_pen, self.black_brush)
        self.sleep_muzzle.setVisible(False)

        #whiskers
        whisker_pen = QPen(QColor(0, 0, 0, 128))
        whisker = QPainterPath()
        whisker.moveTo(44,40)
        whisker.lineTo(34,38)
        whisker.moveTo(44,42)
        whisker.lineTo(34,42)
        whisker.moveTo(44,44)
        whisker.lineTo(34,46)
        whisker.moveTo(68,40)
        whisker.lineTo(78,38)
        whisker.moveTo(68,42)
        whisker.lineTo(78,42)
        whisker.moveTo(68,44)
        whisker.lineTo(78,46)
        self.graphic.addPath(whisker, whisker_pen)

        #paws
        paw_pen=QPen(Qt.GlobalColor.black, 1.5, Qt.PenStyle.SolidLine)
        paws= QPainterPath()
        paws.moveTo(37,120)
        paws.cubicTo(37,146,52,146,52,120)
        paws.moveTo(63,120)
        paws.cubicTo(63,145,78,145,78,120)
        self.graphic.addPath(paws,paw_pen)

        #collar 
        collar_path = QPainterPath()
        collar_path.addRoundedRect(QRectF(31, 57, 48, 6), 5, 5)
        self.graphic.addPath(collar_path,QPen(Qt.PenStyle.NoPen),QBrush(QColor(240, 54, 116, 200))) 

        #bell
        self.graphic.addEllipse(48,59,12,12,QPen(Qt.PenStyle.NoPen),QBrush(QColor(245, 215, 90)))

        #sleep tracking
        self.sleeping = False 
        self.last_activity = time.time()
        self.keyboard_activity = keyboard.Listener(on_press = self.key_press)
        self.keyboard_activity.start()
        self.mouse_listener = mouse.Listener(on_scroll=self.on_scroll)
        self.mouse_listener.start()

    def draw_tail(self, x_offset = 0):
        self.path = QPainterPath()
        self.path.moveTo(65 , 138 )                                   
        self.path.cubicTo(95 + x_offset, 135, 109 + x_offset, 120, 118 + x_offset, 85)                   
        self.path.cubicTo(115 + x_offset, 77, 110 + x_offset, 77, 107 + x_offset, 85)                 
        self.path.cubicTo(103 + x_offset, 88, 110 + x_offset, 118, 78 + x_offset, 118)               
        self.path.closeSubpath()
        self.tail_item.setPath(self.path)

    def animate_tail(self):
        self.sway_angle += 0.1
        if (self.sleeping): 
            pulse = sin(self.sway_angle) * 2 + 4
            self.sleep_muzzle.setRect(55.75 - (pulse/2), 47 - (pulse/2), pulse, pulse)
            return 
        x_offset = sin(self.sway_angle) * 4
        self.draw_tail(x_offset)

    def animate_blink(self):
        if (self.sleeping): return
        self.left_eye.setRect(41,22,13,0)   # close
        self.right_eye.setRect(57,22,13,0)  # close
        QTimer.singleShot(200, self.reopen_eyes)

    def reopen_eyes(self):
        if(self.sleeping): return
        self.left_eye.setRect(41,22,13,16)
        self.right_eye.setRect(57,22,13,16)

    def track_cursor(self):
        current_pos = QCursor.pos()
        if(current_pos == getattr(self, 'last_mouse_pos', None)):
            return
        self.last_mouse_pos = current_pos
        self.last_activity = time.time()
        mouse_scene = self.view.mapToScene(self.view.mapFromGlobal(current_pos))
        mouse_x = mouse_scene.x()
        mouse_y = mouse_scene.y()
        max_offset = 3
        dx_left = mouse_x - 47 
        dx_right = mouse_x - 63
        dy_left = mouse_y - 28
        dy_right = mouse_y - 28
        distance_left = sqrt((dx_left*dx_left) + (dy_left*dy_left))
        distance_right = sqrt((dx_right*dx_right) + (dy_right*dy_right))
        self.left_eye_inner.setPos( dx_left * (max_offset / distance_left), dy_left * (max_offset / distance_left))
        self.right_eye_inner.setPos( dx_right * (max_offset / distance_right), dy_right * (max_offset / distance_right))

    def key_press(self, key):
        self.last_activity = time.time()

    def on_scroll(self, x, y, dx, dy):
        self.last_activity = time.time()

    def update_state(self):
        if (time.time() - self.last_activity > 600) and (self.sleeping == False) :
            self.sleeping = True
            self.closed_left_eye.setVisible(True)
            self.closed_right_eye.setVisible(True) 
            self.sleep_muzzle.setVisible(True)
            self.left_eye.setVisible(False)
            self.right_eye.setVisible(False)
            self.muzzle.setVisible(False)
            self.left_eye.setRect(41,22,13,0)
            self.right_eye.setRect(57,22,13,0)

        elif (time.time() - self.last_activity <= 600) and (self.sleeping == True):
            self.sleeping = False
            self.closed_left_eye.setVisible(False)
            self.closed_right_eye.setVisible(False) 
            self.sleep_muzzle.setVisible(False)
            self.left_eye.setVisible(True)
            self.right_eye.setVisible(True)
            self.muzzle.setVisible(True)
            self.left_eye.setRect(41,22,13,16)
            self.right_eye.setRect(57,22,13,16)

class TimerWidget(QObject):
    def __init__(self):
        super().__init__()
        self.graphic = QGraphicsScene()
        self.graphic.setBackgroundBrush(QBrush(Qt.GlobalColor.transparent))
        self.graphic.setSceneRect(0, 0, 350, 200)
        self.view = QGraphicsView(self.graphic)
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.view.setStyleSheet("background: transparent; border: none;")

        pixmap = QPixmap("cind.jpg")
        pixmap = pixmap.scaled(350, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.backgorund = self.graphic.addPixmap(pixmap)

        self.time_text = QGraphicsTextItem("00 : 00 : 00")
        self.time_text.setPos(20,1)
        self.time_text.setFont(QFont("Cooper Black", 45))
        self.time_text.setDefaultTextColor(QColor(176, 136, 123))
        self.graphic.addItem(self.time_text)
        self.seconds_left =10
        self.phase = "Work"
        self.phase_text = QGraphicsTextItem("Work Time!")
        self.phase_text.setPos(140,60)
        self.phase_text.setFont(QFont("Pluma", 10))
        self.phase_text.setDefaultTextColor(QColor(176, 136, 123))
        self.graphic.addItem(self.phase_text)
        self.count = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)

        self.initial = StartButton(self)
        self.initial.setPos(170,75)
        self.graphic.addItem(self.initial)


    def tick(self):
        self.seconds_left -= 1
        self.seconds = self.seconds_left
        self.hours = self.seconds//3600
        self.seconds = self.seconds % 3600
        self.minutes = self.seconds//60
        self.seconds = self.seconds%60
        self.time_text.setPlainText(f"{self.hours:02d} : {self.minutes:02d} : {self.seconds:02d}")
        if (self.seconds_left == 0 and self.phase == "Work"):
            QApplication.beep()
            self.phase_text.setPlainText("Break Time!")
            self.seconds_left = 3
            self.phase = "Break"
        elif ( self.seconds_left ==0 and self.phase == "Break"):
            self.count  +=1
            if (self.count == 2): 
                QApplication.beep()
                QApplication.beep()
                self.timer.stop()
                self.phase = ""
                QApplication.beep()
                self.initial.setVisible(False)
                self.phase_text.setPlainText("")
                self.time_text.setPlainText("Time's Up!")
            else:
                QApplication.beep()
                self.phase="Work"
                self.phase_text.setPlainText("Work Time!")
                self.seconds_left = 15

    def start_timer(self):
        self.timer.start(1000)

    def stop_timer(self):
        self.timer.stop()


class ChoiceSelection(QObject):
     def __init__(self):
            super().__init__()
            self.graphic = QGraphicsScene()
            self.graphic.setBackgroundBrush(QBrush(Qt.GlobalColor.transparent))
            self.graphic.setSceneRect(0, 0, 350, 200)
            self.view = QGraphicsView(self.graphic)
            self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
            self.view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            self.view.setStyleSheet("background: transparent; border: none;")
    
            pixmap = QPixmap("cind.jpg")
            pixmap = pixmap.scaled(350, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.backgorund = self.graphic.addPixmap(pixmap)

            self.pomodoro = PomodoroChoice(self)
            self.pomodoro.setFont(QFont("Lucida Fax", 18))
            self.pomodoro.setPos(70, 55)
            self.pomodoro.setDefaultTextColor(QColor(176, 136, 123))
            self.graphic.addItem(self.pomodoro)

            self.custom = CustomChoice(self)
            self.custom.setFont(QFont("Lucida Fax", 18))
            self.custom.setPos(80, 100)
            self.custom.setDefaultTextColor(QColor(176, 136, 123))
            self.graphic.addItem(self.custom)

     def launchPomodoro(self):
            self.timer_widget = TimerWidget()
            self.timer_widget.view.setWindowFlags(Qt.WindowType.FramelessWindowHint)
            self.timer_widget.view.show()
            self.view.hide()

class PomodoroChoice(QGraphicsTextItem):
    def __init__(self, parent_widget):
        super().__init__("Pomodoro")
        self.parent_widget = parent_widget

    def mousePressEvent(self, event):
        self.parent_widget.launchPomodoro()

class CustomChoice(QGraphicsTextItem):
    def __init__(self, parent_widget):
        super().__init__("Custom")
        self.parent_widget = parent_widget

    def mousePressEvent(self, event):
        self.parent_widget.launchCustom()

class StartButton(QGraphicsItemGroup):
    def __init__(self, timer_widget):
        super().__init__()
        self.running =False
        self.timer_widget = timer_widget

        triangle = QPolygonF([QPointF(2,4), QPointF(2, 14), QPointF(10,9)])
        self.start = QGraphicsPolygonItem(triangle)
        self.start.setBrush(QBrush(QColor(176, 136, 123)))
        self.start.setPen(QPen(QColor(176, 136, 123)))
        self.addToGroup(self.start)

        self.pause_bar_1 = QGraphicsRectItem( 4, 5, 2, 8)
        self.pause_bar_1.setBrush(QBrush(QColor(176, 136, 123)))
        self.pause_bar_1.setPen(QPen(QColor(176, 136, 123)))
        self.pause_bar_2 = QGraphicsRectItem(8, 5, 2, 8)
        self.pause_bar_2.setPen(QPen(QColor(176, 136, 123)))
        self.pause_bar_2.setBrush(QBrush(QColor(176, 136, 123)))
        self.addToGroup(self.pause_bar_1)
        self.addToGroup(self.pause_bar_2)
        self.pause_bar_1.setVisible(False)
        self.pause_bar_2.setVisible(False)

    def mousePressEvent(self, event):
        if (not self.running):
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
#creating a window for the widget
#app = QApplication(sys.argv)
#window = DesktopBuddy()
#app.exec()
if __name__ == "__main__":
    app = QApplication(sys.argv)
    timer_widget = ChoiceSelection()
    timer_widget.view.setWindowFlags(Qt.WindowType.FramelessWindowHint)
    timer_widget.view.show()
    app.exec()