import sys
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtWidgets import QApplication, QWidget, QMenu
from PyQt6.QtGui import QMouseEvent, QContextMenuEvent

class DesktopBuddy(QWidget):
    #creates a widget for the desktop buddy
    
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        #self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True )
        self.offset = QPoint()
        self.show()

    #lets us select the widget
    def mousePressEvent(self, event: QMouseEvent):
        self.offset= event.position().toPoint()

    #lets us move the widget
    def mouseMoveEvent(self, event: QMouseEvent):
        self.window_Position = event.globalPosition().toPoint() - self.offset
        window.move(self.window_Position)

    #opens context menu on right click
    def contextMenuEvent(self, event: QContextMenuEvent):
        menu = QMenu()
        menu.addAction("Exit", QApplication.instance().quit)
        menu.exec(event.globalPos())

#creating a window for the widget
app=QApplication(sys.argv)
window=DesktopBuddy()
app.exec()