
from PySide6.QtWidgets import QPushButton, QWidget, QVBoxLayout, QLabel

from PySide6.QtCore import Qt, QSize

from PySide6.QtGui import QIcon, QPixmap

from app.ui.theme import get_theme

from app.ui.ui_utils import load_svg_icon
from app.ui.components.svg_spinner import SvgSpinner

class SidebarButton(QPushButton):

    def __init__(self, icon_name: str, text: str, font_size: int = 14, padding_left: int = 12, is_selectable: bool = True, parent=None):

        super().__init__(parent)

        self.icon_name = icon_name

        self.label_text = text

        self.font_size = font_size

        self.padding_left = padding_left

        self.is_selectable = is_selectable

        self.setText(f"  {text}")

        if is_selectable:

            self.setCheckable(True)

            self.setCursor(Qt.PointingHandCursor)

        else:

            self.setCheckable(False)

            self.setCursor(Qt.ArrowCursor)

        self.setMinimumHeight(40)

        self.is_loading = False
        self.spinner = None

        self.update_style()

    def update_style(self):

        theme = get_theme()

        icon_color = theme.colors.sidebar_foreground

        if self.isChecked():

            icon_color = theme.colors.sidebar_primary_foreground
        
        if self.is_loading:
            # Use transparent icon to maintain spacing
            pixmap = QPixmap(18, 18)
            pixmap.fill(Qt.transparent)
            self.setIcon(QIcon(pixmap))
        else:
            self.setIcon(QIcon(load_svg_icon(self.icon_name, 18, icon_color)))

        self.setIconSize(QSize(18, 18))

        hover_style = ""

        checked_style = ""

        if self.is_selectable:

            hover_style = f"""
            QPushButton:hover {{

                background-color: {theme.colors.sidebar_accent};
            }} """

            checked_style = f"""
            QPushButton:checked {{

                background-color: {theme.colors.sidebar_primary};
                color: {theme.colors.sidebar_primary_foreground};
            }} """

        self.setStyleSheet(f"""
            QPushButton {{

                background-color: transparent;
                color: {theme.colors.sidebar_foreground};
                border: none;
                border-radius: 8px;
                padding: 10px {self.padding_left}px;
                text-align: left;
                font-size: {self.font_size}px;
                font-weight: 500;
            }}
            {hover_style}
            {checked_style}
        """)

    def setChecked(self, checked: bool):

        super().setChecked(checked)

        self.update_style()

    def start_loading(self):
        if self.is_loading:
            return
            
        self.is_loading = True
        self.update_style()
        
        if not self.spinner:
            # Calculate position based on padding
            # Default padding is 12 (or self.padding_left), icon size is 18
            # Vertically center: (height - 18) / 2
            
            self.spinner = SvgSpinner(size=18, parent=self)
            
            # Position manually
            y = (self.height() - 18) // 2
            self.spinner.move(self.padding_left, y)
            self.spinner.raise_()
            self.spinner.show()
            
        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()
            
    def stop_loading(self):
        if not self.is_loading:
            return
            
        self.is_loading = False
        
        if self.spinner:
            self.spinner.stop()
            self.spinner.deleteLater()
            self.spinner = None
            
        self.update_style()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.spinner:
             y = (self.height() - 18) // 2
             self.spinner.move(self.padding_left, y)

class SidebarSection(QWidget):

    def __init__(self, title: str, parent=None):

        super().__init__(parent)

        layout = QVBoxLayout(self)

        layout.setContentsMargins(16, 16, 16, 8)

        layout.setSpacing(0)

        theme = get_theme()

        title_label = QLabel(title)

        title_label.setStyleSheet(f"""
            color: {theme.colors.sidebar_muted};
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.5px;
        """)

        layout.addWidget(title_label)
