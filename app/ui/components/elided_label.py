from PySide6.QtWidgets import QLabel, QSizePolicy
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFontMetrics, QPainter, QPalette

class ElidedLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        # Set size policy to Ignored horizontally so it doesn't force the layout to be 
        # as wide as the full text, allowing it to shrink and elide.
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)

    def paintEvent(self, event):
        painter = QPainter(self)
        
        metrics = QFontMetrics(self.font())
        rect = self.contentsRect()
        
        full_text = self.text()
        
        # Elide the text to fit the width
        elided = metrics.elidedText(full_text, Qt.ElideRight, rect.width())
        
        color = self.palette().color(QPalette.WindowText)
        painter.setPen(color)
        painter.setFont(self.font())
        
        painter.drawText(rect, self.alignment(), elided)

    def sizeHint(self):
        # Return the size hint for the full text, but the policy allows it to shrink
        return super().sizeHint()
    
    def minimumSizeHint(self):
        # Allow shrinking to very small
        return QSize(0, super().minimumSizeHint().height())
