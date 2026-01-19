
from typing import Optional

from pathlib import Path

from PySide6.QtWidgets import (

    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,

    QLineEdit, QTextEdit, QFrame, QWidget, QComboBox, QApplication,

    QMenu, QWidgetAction, QFileDialog, QScrollArea

)

from PySide6.QtCore import Qt, Signal, QRegularExpression, QSize, QPoint

from PySide6.QtGui import (

    QFont, QTextCursor, QTextCharFormat, QKeySequence,

    QShortcut, QTextListFormat, QColor, QTextBlockFormat, QIcon, QPixmap

)

from ..core.vault import SecureNote

from .theme import get_theme

from .ui_utils import load_svg_icon

def get_format_icon_path(name: str) -> str:

    return str(Path(__file__).parent / "icons" / "format_text" / f"{name}.svg")

def load_format_icon(name: str, size: int = 16, color: str = None) -> QPixmap:

    icon_path = get_format_icon_path(name)

    return load_svg_icon(icon_path, size, color) if Path(icon_path).exists() else QPixmap()

class RichTextEditor(QTextEdit):

    format_changed = Signal()

    def __init__(self, parent=None):

        super().__init__(parent)

        self.setAcceptRichText(True)

        self._processing = False

        self._bold_active = False

        self._italic_active = False

        self._underline_active = False

        self._code_active = False

        self._setup_shortcuts()

        self.textChanged.connect(self._on_text_changed)

        self._last_length = 0

    def _setup_shortcuts(self):

        bold_shortcut = QShortcut(QKeySequence("Ctrl+B"), self)

        bold_shortcut.activated.connect(self.toggle_bold)

        italic_shortcut = QShortcut(QKeySequence("Ctrl+I"), self)

        italic_shortcut.activated.connect(self.toggle_italic)

        underline_shortcut = QShortcut(QKeySequence("Ctrl+U"), self)

        underline_shortcut.activated.connect(self.toggle_underline)

        code_shortcut = QShortcut(QKeySequence("Ctrl+`"), self)

        code_shortcut.activated.connect(self.toggle_code)

        h1_shortcut = QShortcut(QKeySequence("Ctrl+1"), self)

        h1_shortcut.activated.connect(lambda: self.apply_heading(1))

        h2_shortcut = QShortcut(QKeySequence("Ctrl+2"), self)

        h2_shortcut.activated.connect(lambda: self.apply_heading(2))

        h3_shortcut = QShortcut(QKeySequence("Ctrl+3"), self)

        h3_shortcut.activated.connect(lambda: self.apply_heading(3))

    def _update_format_state(self):

        if self._processing:

            return

        try:

            cursor = self.textCursor()

            fmt = cursor.charFormat()

            self._bold_active = fmt.fontWeight() == QFont.Bold

            self._italic_active = fmt.fontItalic()

            self._underline_active = fmt.fontUnderline()

            font_family = fmt.fontFamily() or ""

            self._code_active = "Consolas" in font_family or "Monaco" in font_family or "monospace" in font_family

            self.format_changed.emit()

        except Exception as e:

            print(f"Error in _update_format_state: {e}")

    def toggle_bold(self):

        cursor = self.textCursor()

        fmt = cursor.charFormat()

        new_weight = QFont.Normal if fmt.fontWeight() == QFont.Bold else QFont.Bold

        fmt.setFontWeight(new_weight)

        if cursor.hasSelection():

            cursor.mergeCharFormat(fmt)

        else:

            self.setCurrentCharFormat(fmt)

        self._bold_active = new_weight == QFont.Bold

        self.format_changed.emit()

    def toggle_italic(self):

        cursor = self.textCursor()

        fmt = cursor.charFormat()

        new_italic = not fmt.fontItalic()

        fmt.setFontItalic(new_italic)

        if cursor.hasSelection():

            cursor.mergeCharFormat(fmt)

        else:

            self.setCurrentCharFormat(fmt)

        self._italic_active = new_italic

        self.format_changed.emit()

    def toggle_underline(self):

        cursor = self.textCursor()

        fmt = cursor.charFormat()

        new_underline = not fmt.fontUnderline()

        fmt.setFontUnderline(new_underline)

        if cursor.hasSelection():

            cursor.mergeCharFormat(fmt)

        else:

            self.setCurrentCharFormat(fmt)

        self._underline_active = new_underline

        self.format_changed.emit()

    def toggle_code(self):

        try:

            cursor = self.textCursor()

            new_fmt = QTextCharFormat()

            new_fmt.setFontFamily("Consolas")

            new_fmt.setBackground(QColor("#2d2d2d"))

            new_fmt.setForeground(QColor("#e06c75"))

            if cursor.hasSelection():

                cursor.mergeCharFormat(new_fmt)

            else:

                self.setCurrentCharFormat(new_fmt)

            self._code_active = True

            self.setFocus()

        except Exception as e:

            print(f"Error in toggle_code: {e}")

    def apply_heading(self, level: int):

        cursor = self.textCursor()

        cursor.movePosition(QTextCursor.StartOfBlock)

        cursor.movePosition(QTextCursor.EndOfBlock, QTextCursor.KeepAnchor)

        fmt = QTextCharFormat()

        sizes = {1: 24, 2: 20, 3: 16}

        fmt.setFontPointSize(sizes.get(level, 14))

        fmt.setFontWeight(QFont.Bold)

        cursor.mergeCharFormat(fmt)

        self.setFocus()

    def insert_bullet_list(self):

        cursor = self.textCursor()

        cursor.insertList(QTextListFormat.ListDisc)

        self.setFocus()

    def insert_numbered_list(self):

        cursor = self.textCursor()

        cursor.insertList(QTextListFormat.ListDecimal)

        self.setFocus()

    def insert_link(self, text: str, url: str):

        if not url:

            return

        cursor = self.textCursor()

        if cursor.hasSelection():

            text = cursor.selectedText()

        if not text:

            text = url

        cursor.insertHtml(f'<a href="{url}" style="color: #3B9EFF;">{text}</a> ')

        self.setFocus()

    def _on_text_changed(self):

        if self._processing:

            return

        self._processing = True

        try:

            cursor = self.textCursor()

            pos = cursor.position()

            cursor.select(QTextCursor.BlockUnderCursor)

            block_text = cursor.selectedText()

            cursor.setPosition(pos)

            self.setTextCursor(cursor)

            self._check_block_markers(block_text, cursor)

        except Exception as e:

            print(f"Error in _on_text_changed: {e}")

        finally:

            self._processing = False

    def _check_block_markers(self, text: str, cursor: QTextCursor):

        stripped = text.strip()

        if stripped in ['- ', '* ', '• ']:

            cursor.select(QTextCursor.BlockUnderCursor)

            cursor.removeSelectedText()

            cursor.insertList(QTextListFormat.ListDisc)

            return

        if stripped == '1. ':

            cursor.select(QTextCursor.BlockUnderCursor)

            cursor.removeSelectedText()

            cursor.insertList(QTextListFormat.ListDecimal)

            return

        if stripped.startswith('# ') and not stripped.startswith('## '):

            self._convert_heading(cursor, 1, stripped[2:])

        elif stripped.startswith('## ') and not stripped.startswith('### '):

            self._convert_heading(cursor, 2, stripped[3:])

        elif stripped.startswith('### '):

            self._convert_heading(cursor, 3, stripped[4:])

    def _convert_heading(self, cursor: QTextCursor, level: int, content: str):

        if not content:

            return

        cursor.select(QTextCursor.BlockUnderCursor)

        fmt = QTextCharFormat()

        sizes = {1: 24, 2: 20, 3: 16}

        fmt.setFontPointSize(sizes.get(level, 14))

        fmt.setFontWeight(QFont.Bold)

        cursor.insertText(content, fmt)

        reset_fmt = QTextCharFormat()

        reset_fmt.setFontPointSize(14)

        reset_fmt.setFontWeight(QFont.Normal)

        self.setCurrentCharFormat(reset_fmt)

    def keyPressEvent(self, event):

        try:

            cursor = self.textCursor()

            if event.key() in (Qt.Key_Space, Qt.Key_Return, Qt.Key_Enter):

                cursor.movePosition(QTextCursor.StartOfBlock, QTextCursor.KeepAnchor)

                text_before = cursor.selectedText()

                cursor = self.textCursor()

                if text_before.endswith('**') and text_before.count('**') >= 2:

                    if self._apply_inline_format(text_before, '**', 'bold'):

                        if event.key() == Qt.Key_Space:

                            super().keyPressEvent(event)

                        return

                if text_before.endswith('*') and not text_before.endswith('**'):

                    count = 0

                    for i, c in enumerate(text_before):

                        if c == '*' and (i == 0 or text_before[i-1] != '*'):

                            if i + 1 < len(text_before) and text_before[i+1] != '*':

                                count += 1

                            elif i + 1 >= len(text_before):

                                count += 1

                    if count >= 2:

                        if self._apply_inline_format(text_before, '*', 'italic'):

                            if event.key() == Qt.Key_Space:

                                super().keyPressEvent(event)

                            return

                if text_before.endswith('_') and text_before.count('_') >= 2:

                    if self._apply_inline_format(text_before, '_', 'italic'):

                        if event.key() == Qt.Key_Space:

                            super().keyPressEvent(event)

                        return

                if text_before.endswith('`') and text_before.count('`') >= 2:

                    if self._apply_inline_format(text_before, '`', 'code'):

                        if event.key() == Qt.Key_Space:

                            super().keyPressEvent(event)

                        return

            super().keyPressEvent(event)

        except Exception as e:

            print(f"Error in keyPressEvent: {e}")

            super().keyPressEvent(event)

    def _apply_inline_format(self, text: str, marker: str, format_type: str) -> bool:

        cursor = self.textCursor()

        marker_len = len(marker)

        if marker == '**':

            end_pos = len(text) - 2

            start_idx = text.rfind('**', 0, end_pos)

            if start_idx == -1 or start_idx == end_pos:

                return False

            content = text[start_idx + 2:-2]

        else:

            end_pos = len(text) - 1

            start_idx = -1

            for i in range(end_pos - 1, -1, -1):

                if text[i] == marker:

                    if marker == '*':

                        if i > 0 and text[i-1] == '*':

                            continue

                        if i + 1 < end_pos and text[i+1] == '*':

                            continue

                    start_idx = i

                    break

            if start_idx == -1:

                return False

            content = text[start_idx + 1:-1]

        if not content or content.isspace():

            return False

        cursor.movePosition(QTextCursor.StartOfBlock)

        cursor.movePosition(QTextCursor.Right, QTextCursor.MoveAnchor, start_idx)

        cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, len(text) - start_idx)

        fmt = QTextCharFormat()

        if format_type == 'bold':

            fmt.setFontWeight(QFont.Bold)

        elif format_type == 'italic':

            fmt.setFontItalic(True)

        elif format_type == 'code':

            fmt.setFontFamily("Consolas, Monaco, monospace")

            fmt.setBackground(QColor("#2d2d2d"))

            fmt.setForeground(QColor("#e06c75"))

        cursor.insertText(content, fmt)

        reset_fmt = QTextCharFormat()

        self.setCurrentCharFormat(reset_fmt)

        return True

    def insertFromMimeData(self, source):

        if source.hasHtml():

            html = source.html()

            self.insertHtml(html)

        elif source.hasText():

            self.insertPlainText(source.text())

        else:

            super().insertFromMimeData(source)

class LinkDialog(QDialog):

    def __init__(self, parent=None, selected_text: str = ""):

        super().__init__(parent)

        self.setWindowTitle("Insert Link")

        self.setFixedSize(350, 200)

        self.setModal(True)

        self.setup_ui(selected_text)

    def setup_ui(self, selected_text: str):

        theme = get_theme()

        self.setStyleSheet(f"""
            QDialog {{

                background-color: {theme.colors.background};
            }}
        """)

        layout = QVBoxLayout(self)

        layout.setContentsMargins(16, 16, 16, 16)

        layout.setSpacing(12)

        text_group = QVBoxLayout()

        text_group.setSpacing(4)

        text_label = QLabel("Text")

        text_label.setStyleSheet(f"color: {theme.colors.foreground}; font-size: 12px;")

        text_group.addWidget(text_label)

        self.text_input = QLineEdit()

        self.text_input.setPlaceholderText("Link text")

        self.text_input.setText(selected_text)

        self.text_input.setStyleSheet(f"""
            QLineEdit {{

                background-color: {theme.colors.input};
                color: {theme.colors.foreground};
                border: 1px solid {theme.colors.border};
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
            }}
        """)

        text_group.addWidget(self.text_input)

        layout.addLayout(text_group)

        url_group = QVBoxLayout()

        url_group.setSpacing(4)

        url_label = QLabel("URL")

        url_label.setStyleSheet(f"color: {theme.colors.foreground}; font-size: 12px;")

        url_group.addWidget(url_label)

        self.url_input = QLineEdit()

        self.url_input.setPlaceholderText("https://example.com")

        self.url_input.setStyleSheet(f"""
            QLineEdit {{

                background-color: {theme.colors.input};
                color: {theme.colors.foreground};
                border: 1px solid {theme.colors.border};
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
            }}
        """)

        url_group.addWidget(self.url_input)

        layout.addLayout(url_group)

        btn_layout = QHBoxLayout()

        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")

        cancel_btn.setCursor(Qt.PointingHandCursor)

        cancel_btn.setStyleSheet(f"""
            QPushButton {{

                background-color: {theme.colors.card};
                color: {theme.colors.foreground};
                border: 1px solid {theme.colors.border};
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
            }}
            QPushButton:hover {{

                background-color: {theme.colors.accent};
            }}
        """)

        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(cancel_btn)

        insert_btn = QPushButton("Insert Link")

        insert_btn.setCursor(Qt.PointingHandCursor)

        insert_btn.setStyleSheet(f"""
            QPushButton {{

                background-color: {theme.colors.primary};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
                font-weight: 600;
            }}
            QPushButton:hover {{

                background-color: #2563eb;
            }}
        """)

        insert_btn.clicked.connect(self.accept)

        btn_layout.addWidget(insert_btn)

        layout.addLayout(btn_layout)

    def get_data(self) -> tuple:

        return (self.text_input.text().strip(), self.url_input.text().strip())

class SecureNoteDialog(QDialog):

    def __init__(self, note: Optional[SecureNote] = None, folders: list = None, parent=None):

        super().__init__(parent)

        self.note = note

        self.folders = folders or []

        self.attachments = []

        self.setWindowTitle("Edit Secure Note" if note else "Add Secure Note")

        self.setFixedSize(800, 550)

        self.setModal(True)

        self._toolbar_buttons = {}

        self.setup_ui()

    def setup_ui(self):

        theme = get_theme()

        self.setStyleSheet(f"""
            QDialog {{

                background-color: {theme.colors.background};
            }}
        """)

        main_layout = QVBoxLayout(self)

        main_layout.setContentsMargins(28, 24, 28, 20)

        main_layout.setSpacing(20)

        header_layout = QHBoxLayout()

        header_layout.setSpacing(12)

        icon_label = QLabel()

        icon_label.setPixmap(load_svg_icon("note", 28, "#3B9EFF"))

        header_layout.addWidget(icon_label)

        title = QLabel("Edit Secure Note" if self.note else "Add Secure Note")

        title.setStyleSheet(f"""
            color: {theme.colors.foreground};
            font-size: 18px;
            font-weight: 600;
        """)

        header_layout.addWidget(title)

        header_layout.addStretch()

        content_layout = QHBoxLayout()

        content_layout.setSpacing(24)

        left_column = QVBoxLayout()

        left_column.setSpacing(12)

        title_group = QVBoxLayout()

        title_group.setSpacing(6)

        title_label = QLabel("TITLE")

        title_label.setStyleSheet(f"""
            color: {theme.colors.primary};
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.5px;
        """)

        title_group.addWidget(title_label)

        self.title_input = QLineEdit()

        self.title_input.setPlaceholderText("Note Title (e.g., Server Configuration, Recovery Keys)")

        self.title_input.setStyleSheet(self._get_input_style(theme))

        if self.note:

            self.title_input.setText(self.note.title)

        title_group.addWidget(self.title_input)

        left_column.addLayout(title_group)

        content_group = QVBoxLayout()

        content_group.setSpacing(6)

        content_label = QLabel("NOTE CONTENT")

        content_label.setStyleSheet(f"""
            color: {theme.colors.primary};
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.5px;
        """)

        content_group.addWidget(content_label)

        editor_container = QFrame()

        editor_container.setStyleSheet(f"""
            QFrame {{

                background-color: {theme.colors.input};
                border: 1px solid {theme.colors.border};
                border-radius: 8px;
            }}
        """)

        editor_layout = QVBoxLayout(editor_container)

        editor_layout.setContentsMargins(0, 0, 0, 0)

        editor_layout.setSpacing(0)

        toolbar = QHBoxLayout()

        toolbar.setContentsMargins(8, 4, 8, 4)

        toolbar.setSpacing(2)

        toolbar.setAlignment(Qt.AlignVCenter)

        self.bold_btn = self._create_icon_button("bold", "Bold (Ctrl+B)", theme)

        self.bold_btn.clicked.connect(self._on_bold_click)

        self._toolbar_buttons['bold'] = self.bold_btn

        toolbar.addWidget(self.bold_btn)

        self.italic_btn = self._create_icon_button("italic", "Italic (Ctrl+I)", theme)

        self.italic_btn.clicked.connect(self._on_italic_click)

        self._toolbar_buttons['italic'] = self.italic_btn

        toolbar.addWidget(self.italic_btn)

        self.underline_btn = self._create_icon_button("underline", "Underline (Ctrl+U)", theme)

        self.underline_btn.clicked.connect(self._on_underline_click)

        self._toolbar_buttons['underline'] = self.underline_btn

        toolbar.addWidget(self.underline_btn)

        sep1 = QFrame()

        sep1.setFixedSize(1, 20)

        sep1.setStyleSheet(f"background-color: {theme.colors.border};")

        toolbar.addWidget(sep1)

        self.h1_btn = self._create_icon_button("h1", "Heading 1 (Ctrl+1)", theme)

        self.h1_btn.clicked.connect(lambda: self.content_input.apply_heading(1))

        toolbar.addWidget(self.h1_btn)

        self.h2_btn = self._create_icon_button("h2", "Heading 2 (Ctrl+2)", theme)

        self.h2_btn.clicked.connect(lambda: self.content_input.apply_heading(2))

        toolbar.addWidget(self.h2_btn)

        self.h3_btn = self._create_icon_button("h3", "Heading 3 (Ctrl+3)", theme)

        self.h3_btn.clicked.connect(lambda: self.content_input.apply_heading(3))

        toolbar.addWidget(self.h3_btn)

        sep2 = QFrame()

        sep2.setFixedSize(1, 20)

        sep2.setStyleSheet(f"background-color: {theme.colors.border};")

        toolbar.addWidget(sep2)

        self.ul_btn = self._create_icon_button("list", "Bullet List", theme)

        self.ul_btn.clicked.connect(lambda: self.content_input.insert_bullet_list())

        toolbar.addWidget(self.ul_btn)

        self.ol_btn = self._create_icon_button("list_num", "Numbered List", theme)

        self.ol_btn.clicked.connect(lambda: self.content_input.insert_numbered_list())

        toolbar.addWidget(self.ol_btn)

        sep3 = QFrame()

        sep3.setFixedSize(1, 20)

        sep3.setStyleSheet(f"background-color: {theme.colors.border};")

        toolbar.addWidget(sep3)

        self.code_btn = self._create_icon_button("code", "Code (Ctrl+`)", theme)

        self.code_btn.clicked.connect(self._on_code_click)

        self._toolbar_buttons['code'] = self.code_btn

        toolbar.addWidget(self.code_btn)

        self.link_btn = self._create_icon_button("link", "Insert Link", theme)

        self.link_btn.clicked.connect(self._show_link_dialog)

        toolbar.addWidget(self.link_btn)

        toolbar.addStretch()

        toolbar_widget = QWidget()

        toolbar_widget.setFixedHeight(40)

        toolbar_widget.setLayout(toolbar)

        toolbar_widget.setStyleSheet(f"""
            QWidget {{

                background-color: {theme.colors.card};
                border-bottom: 1px solid {theme.colors.border};
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }}
        """)

        editor_layout.addWidget(toolbar_widget)

        self.content_input = RichTextEditor()

        self.content_input.setPlaceholderText("Start writing your secure note here...\n\nTips:\n• Use **text** for bold, *text* for italic\n• Use # Heading, ## Heading 2, ### Heading 3\n• Use `text` for inline code\n• Use - or 1. for lists")

        self.content_input.setMinimumHeight(280)

        self.content_input.setStyleSheet(f"""
            QTextEdit {{

                background-color: {theme.colors.input};
                color: {theme.colors.foreground};
                border: none;
                padding: 12px;
                font-size: 14px;
            }}
        """)

        self.content_input.format_changed.connect(self._update_toolbar_state)

        if self.note:

            self.content_input.setHtml(self.note.content)

        editor_layout.addWidget(self.content_input)

        content_group.addWidget(editor_container)

        left_column.addLayout(content_group)

        content_layout.addLayout(left_column, 3)

        right_column = QVBoxLayout()

        right_column.setSpacing(16)

        folder_group = QVBoxLayout()

        folder_group.setSpacing(6)

        folder_label = QLabel("FOLDER")

        folder_label.setStyleSheet(f"""
            color: {theme.colors.primary};
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.5px;
        """)

        folder_group.addWidget(folder_label)

        self.folder_combo = QComboBox()

        self.folder_combo.addItem("No Folder", None)

        for folder in self.folders:

            self.folder_combo.addItem(folder.name, folder.id)

        self.folder_combo.setStyleSheet(f"""
            QComboBox {{

                background-color: {theme.colors.input};
                color: {theme.colors.foreground};
                border: 1px solid {theme.colors.border};
                border-radius: 8px;
                padding: 10px 12px;
                font-size: 13px;
            }}
            QComboBox::drop-down {{

                border: none;
                padding-right: 10px;
            }}
            QComboBox QAbstractItemView {{

                background-color: {theme.colors.card};
                color: {theme.colors.foreground};
                border: 1px solid {theme.colors.border};
                selection-background-color: {theme.colors.accent};
            }}
        """)

        if self.note and self.note.folder_id:

            index = self.folder_combo.findData(self.note.folder_id)

            if index >= 0:

                self.folder_combo.setCurrentIndex(index)

        folder_group.addWidget(self.folder_combo)

        right_column.addLayout(folder_group)

        attach_group = QVBoxLayout()

        attach_group.setSpacing(6)

        attach_label = QLabel("ATTACHMENTS")

        attach_label.setStyleSheet(f"""
            color: {theme.colors.primary};
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.5px;
        """)

        attach_group.addWidget(attach_label)

        self.attach_area = QFrame()

        self.attach_area.setMinimumHeight(80)

        self.attach_area.setStyleSheet(f"""
            QFrame {{

                background-color: transparent;
                border: 2px dashed {theme.colors.border};
                border-radius: 8px;
            }}
            QFrame:hover {{

                border-color: {theme.colors.primary};
            }}
        """)

        self.attach_area.setCursor(Qt.PointingHandCursor)

        self.attach_area.mousePressEvent = self._on_attach_click

        self.attach_inner_layout = QVBoxLayout(self.attach_area)

        self.attach_inner_layout.setAlignment(Qt.AlignCenter)

        self.attach_inner_layout.setSpacing(6)

        self.attach_icon = QLabel()

        self.attach_icon.setPixmap(load_svg_icon("folder", 24, theme.colors.muted_foreground))

        self.attach_icon.setAlignment(Qt.AlignCenter)

        self.attach_icon.setStyleSheet("border: none;")

        self.attach_inner_layout.addWidget(self.attach_icon)

        self.attach_text = QLabel("Click to attach files")

        self.attach_text.setAlignment(Qt.AlignCenter)

        self.attach_text.setWordWrap(True)

        self.attach_text.setStyleSheet(f"""
            color: {theme.colors.muted_foreground};
            font-size: 11px;
            border: none;
        """)

        self.attach_inner_layout.addWidget(self.attach_text)

        attach_group.addWidget(self.attach_area)

        self.attachments_list = QVBoxLayout()

        self.attachments_list.setSpacing(4)

        attach_group.addLayout(self.attachments_list)

        right_column.addLayout(attach_group)

        right_column.addStretch()

        content_layout.addLayout(right_column, 1)

        main_layout.addLayout(content_layout)

        btn_layout = QHBoxLayout()

        btn_layout.setSpacing(12)

        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")

        cancel_btn.setFixedSize(100, 40)

        cancel_btn.setCursor(Qt.PointingHandCursor)

        cancel_btn.setStyleSheet(f"""
            QPushButton {{

                background-color: {theme.colors.card};
                color: {theme.colors.foreground};
                border: 1px solid {theme.colors.border};
                border-radius: 8px;
                font-size: 14px;
                font-weight: 500;
            }}
            QPushButton:hover {{

                background-color: {theme.colors.accent};
            }}
        """)

        cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save Note")

        save_btn.setFixedSize(120, 40)

        save_btn.setCursor(Qt.PointingHandCursor)

        save_btn.setStyleSheet(f"""
            QPushButton {{

                background-color: {theme.colors.primary};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 600;
            }}
            QPushButton:hover {{

                background-color: #2563eb;
            }}
        """)

        save_btn.clicked.connect(self._on_save_click)

        btn_layout.addWidget(save_btn)

        main_layout.addLayout(btn_layout)

    def _on_bold_click(self):

        self.content_input.toggle_bold()

        self.content_input.setFocus()

    def _on_italic_click(self):

        self.content_input.toggle_italic()

        self.content_input.setFocus()

    def _on_underline_click(self):

        self.content_input.toggle_underline()

        self.content_input.setFocus()

    def _on_code_click(self):

        self.content_input.toggle_code()

        self.content_input.setFocus()

    def _update_toolbar_state(self):

        theme = get_theme()

        for name, btn in self._toolbar_buttons.items():

            is_active = False

            if name == 'bold':

                is_active = self.content_input._bold_active

            elif name == 'italic':

                is_active = self.content_input._italic_active

            elif name == 'underline':

                is_active = self.content_input._underline_active

            elif name == 'code':

                is_active = self.content_input._code_active

            if is_active:

                btn.setStyleSheet(f"""
                    QPushButton {{

                        background-color: {theme.colors.primary};
                        color: white;
                        border: none;
                        border-radius: 4px;
                    }}
                    QPushButton:hover {{

                        background-color: {theme.colors.primary};
                    }}
                """)

            else:

                btn.setStyleSheet(f"""
                    QPushButton {{

                        background-color: transparent;
                        color: {theme.colors.foreground};
                        border: none;
                        border-radius: 4px;
                    }}
                    QPushButton:hover {{

                        background-color: {theme.colors.accent};
                    }}
                """)

    def _show_link_dialog(self):

        cursor = self.content_input.textCursor()

        selected_text = cursor.selectedText() if cursor.hasSelection() else ""

        dialog = LinkDialog(self, selected_text)

        if dialog.exec():

            text, url = dialog.get_data()

            self.content_input.insert_link(text, url)

    def _on_attach_click(self, event):

        files, _ = QFileDialog.getOpenFileNames(

            self,

            "Select Files to Attach",

            "",

            "All Files (*.*)"

        )

        for file_path in files:

            if file_path not in self.attachments:

                self.attachments.append(file_path)

                self._add_attachment_item(file_path)

    def _add_attachment_item(self, file_path: str):

        theme = get_theme()

        item = QFrame()

        item.setStyleSheet(f"""
            QFrame {{

                background-color: {theme.colors.card};
                border: 1px solid {theme.colors.border};
                border-radius: 4px;
                padding: 4px;
            }}
        """)

        item_layout = QHBoxLayout(item)

        item_layout.setContentsMargins(8, 4, 4, 4)

        item_layout.setSpacing(8)

        file_name = Path(file_path).name

        name_label = QLabel(file_name)

        name_label.setStyleSheet(f"""
            color: {theme.colors.foreground};
            font-size: 11px;
        """)

        name_label.setToolTip(file_path)

        item_layout.addWidget(name_label, 1)

        remove_btn = QPushButton("×")

        remove_btn.setFixedSize(16, 16)

        remove_btn.setCursor(Qt.PointingHandCursor)

        remove_btn.setStyleSheet(f"""
            QPushButton {{

                background: transparent;
                color: {theme.colors.muted_foreground};
                border: none;
                font-size: 14px;
            }}
            QPushButton:hover {{

                color: #ff6b6b;
            }}
        """)

        remove_btn.clicked.connect(lambda: self._remove_attachment(file_path, item))

        item_layout.addWidget(remove_btn)

        self.attachments_list.addWidget(item)

        self.attach_text.setText(f"{len(self.attachments)} file(s) attached")

    def _remove_attachment(self, file_path: str, item: QFrame):

        if file_path in self.attachments:

            self.attachments.remove(file_path)

        item.deleteLater()

        if not self.attachments:

            self.attach_text.setText("Click to attach files")

        else:

            self.attach_text.setText(f"{len(self.attachments)} file(s) attached")

    def _create_icon_button(self, icon_name: str, tooltip: str, theme) -> QPushButton:

        btn = QPushButton()

        btn.setFixedSize(28, 28)

        btn.setToolTip(tooltip)

        btn.setCursor(Qt.PointingHandCursor)

        icon_path = get_format_icon_path(icon_name)

        if Path(icon_path).exists():

            pixmap = load_svg_icon(icon_path, 16, theme.colors.foreground)

            btn.setIcon(QIcon(pixmap))

            btn.setIconSize(QSize(16, 16))

        else:

            fallback_text = {

                "bold": "B", "italic": "I", "underline": "U",

                "h1": "H1", "h2": "H2", "h3": "H3",

                "list": "•", "list_num": "1.",

                "code": "</>", "link": "🔗"

            }

            btn.setText(fallback_text.get(icon_name, icon_name))

        btn.setStyleSheet(f"""
            QPushButton {{

                background-color: transparent;
                color: {theme.colors.foreground};
                border: none;
                border-radius: 4px;
            }}
            QPushButton:hover {{

                background-color: {theme.colors.accent};
            }}
        """)

        return btn

    def _get_input_style(self, theme):

        return f"""
            QLineEdit {{

                background-color: {theme.colors.input};
                color: {theme.colors.foreground};
                border: 1px solid {theme.colors.border};
                border-radius: 8px;
                padding: 10px 12px;
                font-size: 13px;
            }}
            QLineEdit:focus {{

                border-color: {theme.colors.primary};
            }}
        """

    def _on_save_click(self):

        title = self.title_input.text().strip()

        content = self.content_input.toPlainText().strip()

        if not title:

            self.title_input.setFocus()

            self.title_input.setStyleSheet(self._get_input_style(get_theme()).replace(

                "border: 1px solid", "border: 2px solid #ef4444; border: 1px solid"

            ))

            return

        if not content:

            self.content_input.setFocus()

            return

        self.accept()

    def get_data(self) -> dict:

        return {

            'title': self.title_input.text().strip(),

            'content': self.content_input.toHtml(),

            'folder_id': self.folder_combo.currentData()

        }
