from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, QEvent
from PySide6.QtGui import QPainter, QPen, QColor
from app.ui.theme import get_theme

class LoadingOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._rotate)
        # Block mouse events
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        
        if parent:
            self.resize(parent.size())
            parent.installEventFilter(self)
            
    def eventFilter(self, obj, event):
        if obj == self.parent() and event.type() == QEvent.Resize:
            self.resize(event.size())
        return super().eventFilter(obj, event)
        
    def showEvent(self, event):
        self.timer.start(16)
        # Ensure we cover parent when shown for the first time or if parent resized while we were hidden (though event filter handles that too)
        if self.parent():
            self.resize(self.parent().size())
        super().showEvent(event)
        
    def hideEvent(self, event):
        self.timer.stop()
        super().hideEvent(event)

    def _rotate(self):
        self.angle = (self.angle + 10) % 360
        self.update()

    def paintEvent(self, event):
        theme = get_theme()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw Opaque Background to hide UI
        painter.fillRect(self.rect(), QColor(theme.colors.background))
        
        # Draw Spinner Centered
        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(self.angle)
        
        pen = QPen(QColor(theme.colors.primary), 4)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        
        # Draw an arc
        painter.drawArc(-24, -24, 48, 48, 0, 270 * 16)
