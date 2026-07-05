import sys
from PyQt6.QtCore import Qt, QPoint, QPointF, QRectF
from PyQt6.QtWidgets import QApplication, QGraphicsView, QWidget, QMenu, QGraphicsScene, QVBoxLayout
from PyQt6.QtGui import QMouseEvent, QContextMenuEvent, QPainterPath, QBrush, QPen, QPolygonF, QColor

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
        #creates transparent QGraphicScene displayed by QGraphicViews
        self.graphic = QGraphicsScene()
        self.graphic.setBackgroundBrush(QBrush(Qt.GlobalColor.transparent))
        self.graphic.setSceneRect(0,0,120,150)
        self.view = QGraphicsView(self.graphic)
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
        self.path = QPainterPath()
        self.path.moveTo(65, 138)                                   
        self.path.cubicTo(95, 135, 109, 120, 118, 85)                   
        self.path.cubicTo(115, 77, 110, 77, 107, 85)                 
        self.path.cubicTo(103, 88, 110, 118, 78, 118)               
        self.path.closeSubpath()
        self.graphic.addPath(self.path, self.pen, self.white_brush)

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
        self.graphic.addEllipse(41,22,13,16, self.pen, self.black_brush)
        self.graphic.addEllipse(47,28,2,4, self.pen, self.white_brush)
        self.graphic.addEllipse(57,22,13,16, self.pen, self.black_brush)
        self.graphic.addEllipse(63,28,2,4, self.pen, self.white_brush)

        #mouth
        mouth_pen = QPen(QColor(0, 0, 0, 200))
        muzzle_path = QPainterPath()
        muzzle_path.moveTo(48,48)
        muzzle_path.cubicTo(50,51,52,52,56,48)
        muzzle_path.cubicTo(60,52,62,51,64,48)
        
        muzzle_path.moveTo(56,48)
        muzzle_path.lineTo(56,38)
        self.graphic.addPath(muzzle_path, mouth_pen)

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
        
#creating a window for the widget
app = QApplication(sys.argv)
window = DesktopBuddy()
app.exec()