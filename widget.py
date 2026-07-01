import sys
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtWidgets import QApplication, QGraphicsView, QWidget, QMenu, QGraphicsScene, QVBoxLayout
from PyQt6.QtGui import QMouseEvent, QContextMenuEvent, QPainterPath, QBrush, QPen

class DesktopBuddy(QWidget):
    #creates a widget for the desktop buddy
    
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True )
        self.offset = QPoint()

        #creates the cat , layouts it and adds it into the widget
        self.cat = BuddyCat()
        self.layout=QVBoxLayout()
        self.layout.addWidget(self.cat.view)
        self.setLayout(self.layout)
        self.show()

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

class BuddyCat:
    def __init__(self):
        #Creates transparent QGraphicScene displayed by QGraphicViews
        self.graphic = QGraphicsScene()
        self.graphic.setBackgroundBrush(QBrush(Qt.GlobalColor.transparent))
        self.graphic.setSceneRect(0,0,120,150)
        self.view = QGraphicsView(self.graphic)
        self.view.setStyleSheet("background: transparent; border: none;")
        self.view.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)  #done so that this doesnt overshadow our mousepress events in other class

        #setting the style of our pen and brush
        self.pen = QPen(Qt.GlobalColor.white, 3, Qt.PenStyle.SolidLine)
        self.brush = QBrush(Qt.GlobalColor.white, Qt.BrushStyle.SolidPattern)

        #body
        self.graphic.addEllipse(20,60, 70, 80, self.pen, self.brush)

        #head
        self.graphic.addEllipse(30, 25, 50, 50, self.pen, self.brush)
        
        #tail
        self.path = QPainterPath()
        self.path.moveTo(65, 138)                                   
        self.path.cubicTo(95, 135, 109, 120, 118, 85)                   
        self.path.cubicTo(115, 77, 110, 77, 107, 85)                 
        self.path.cubicTo(103, 88, 110, 118, 78, 118)               
        self.path.closeSubpath()
        self.graphic.addPath(self.path, self.pen, self.brush)

#creating a window for the widget
app = QApplication(sys.argv)
window = DesktopBuddy()
app.exec()