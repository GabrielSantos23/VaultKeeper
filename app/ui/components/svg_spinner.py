from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QPainter, QColor
from PySide6.QtSvg import QSvgRenderer

SVG_DATA = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 -960 960 960">
  <path fill="currentColor"
    d="M480-80q-82 0-155-31.5t-127.5-86Q143-252 111.5-325T80-480q0-83 31.5-155.5t86-127Q252-817 325-848.5T480-880q17 0 28.5 11.5T520-840q0 17-11.5 28.5T480-800q-133 0-226.5 93.5T160-480q0 133 93.5 226.5T480-160q133 0 226.5-93.5T800-480q0-17 11.5-28.5T840-520q17 0 28.5 11.5T880-480q0 82-31.5 155t-86 127.5q-54.5 54.5-127 86T480-80Z"/>
</svg>
"""

class SvgSpinner(QWidget):
    def __init__(self, size: int = 48, speed: int = 1000, color: str = "#3b82f6", parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        
        # Transparent background for the widget itself
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        
        # Data
        self.angle = 0
        self.color = color
        
        # Renderer
        self.renderer = QSvgRenderer(bytearray(SVG_DATA.replace("currentColor", color), encoding='utf-8'))
        
        # Timer for animation
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._rotate)
        # Calculate interval for ~60fps or consistent speed
        # speed is ms for 360 degrees.
        # step size?
        self.step = 10 
        interval = int(speed / (360 / self.step))
        self.timer.setInterval(max(10, interval))

    def _rotate(self):
        self.angle = (self.angle + self.step) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Coordinate translation for rotation
        w, h = self.width(), self.height()
        painter.translate(w / 2, h / 2)
        painter.rotate(self.angle)
        painter.translate(-w / 2, -h / 2)
        
        # Render SVG
        self.renderer.render(painter)
        painter.end()

    def start(self):
        if not self.timer.isActive():
            self.timer.start()
            self.show()

    def stop(self):
        self.timer.stop()
        self.hide()
