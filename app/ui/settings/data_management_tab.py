from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QMessageBox, QFileDialog, QFrame
)
from PySide6.QtCore import Qt
from ..theme import get_theme
from .components import create_separator

class DataManagementTab(QWidget):
    def __init__(self, vault_manager, parent=None):
        super().__init__(parent)
        self.vault = vault_manager
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(24)
        theme = get_theme()

        # Header
        header = QWidget()
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(6)

        page_title = QLabel("Data Management")
        page_title.setStyleSheet(f"""
            color: {theme.colors.foreground};
            font-size: 18px;
            font-weight: 600;
        """)
        header_layout.addWidget(page_title)

        page_subtitle = QLabel("Import or export your vault data.")
        page_subtitle.setStyleSheet(f"""
            color: {theme.colors.muted_foreground};
            font-size: 14px;
        """)
        header_layout.addWidget(page_subtitle)
        layout.addWidget(header)

        layout.addSpacing(8)

        # Import Section
        self._setup_import_section(layout, theme)
        layout.addWidget(create_separator())

        # Export Section
        self._setup_export_section(layout, theme)
        layout.addWidget(create_separator())
        
        # Secure Notes Export/Import Section
        self._setup_notes_section(layout, theme)
        layout.addWidget(create_separator())
        
        # Credit Cards Export/Import Section
        self._setup_cards_section(layout, theme)
        
        layout.addStretch()

    def _setup_import_section(self, layout, theme):
        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        
        title = QLabel("Import Passwords")
        title.setStyleSheet(f"color: {theme.colors.foreground}; font-size: 14px; font-weight: 500;")
        text_layout.addWidget(title)
        
        subtitle = QLabel("Import passwords from a CSV file (e.g. from Chrome, LastPass).")
        subtitle.setStyleSheet(f"color: {theme.colors.muted_foreground}; font-size: 12px;")
        text_layout.addWidget(subtitle)
        
        row.addLayout(text_layout)

        import_btn = QPushButton("Import CSV")
        import_btn.setCursor(Qt.PointingHandCursor)
        import_btn.setFixedWidth(120)
        import_btn.setFixedHeight(32)
        import_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.colors.card};
                border: 1px solid {theme.colors.border};
                color: {theme.colors.foreground};
                border-radius: 6px;
                font-size: 13px;
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                background-color: {theme.colors.accent};
            }}
        """)
        import_btn.clicked.connect(self._handle_import)
        row.addWidget(import_btn)

        layout.addWidget(container)

    def _setup_export_section(self, layout, theme):
        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        
        title = QLabel("Export Database")
        title.setStyleSheet(f"color: {theme.colors.foreground}; font-size: 14px; font-weight: 500;")
        text_layout.addWidget(title)
        
        subtitle = QLabel("Export your vault data to a CSV file for backup.")
        subtitle.setStyleSheet(f"color: {theme.colors.muted_foreground}; font-size: 12px;")
        text_layout.addWidget(subtitle)
        
        row.addLayout(text_layout)

        export_btn = QPushButton("Export CSV")
        export_btn.setCursor(Qt.PointingHandCursor)
        export_btn.setFixedWidth(120)
        export_btn.setFixedHeight(32)
        export_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme.colors.card};
                border: 1px solid {theme.colors.border};
                color: {theme.colors.foreground};
                border-radius: 6px;
                font-size: 13px;
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                background-color: {theme.colors.accent};
            }}
        """)
        export_btn.clicked.connect(self._handle_export)
        row.addWidget(export_btn)

        layout.addWidget(container)

    def _handle_import(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select CSV File",
            "",
            "CSV Files (*.csv);;All Files (*.*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                parsed_items = self.vault.parse_csv_content(content)
                imported_count = 0
                updated_count = 0
                skipped_count = 0
                
                yes_to_all = False
                no_to_all = False
                
                for item in parsed_items:
                    existing = self.vault.find_duplicate_credential(item['domain'], item['username'])
                    
                    if existing:
                        if no_to_all:
                            skipped_count += 1
                            continue
                            
                        if yes_to_all:
                            self.vault.update_credential(existing.id, **item)
                            updated_count += 1
                            continue

                        msg_box = QMessageBox(self)
                        msg_box.setWindowTitle("Duplicate Credential")
                        msg_box.setText(f"Credential for '{item['domain']}' ({item['username']}) already exists.")
                        msg_box.setInformativeText("Do you want to update it with the data from the CSV?")
                        
                        btn_update = msg_box.addButton("Update", QMessageBox.YesRole)
                        btn_skip = msg_box.addButton("Skip", QMessageBox.NoRole)
                        btn_update_all = msg_box.addButton("Update All", QMessageBox.YesRole)
                        btn_skip_all = msg_box.addButton("Skip All", QMessageBox.NoRole)
                        
                        msg_box.exec()
                        
                        clicked_button = msg_box.clickedButton()
                        
                        if clicked_button == btn_update_all:
                            yes_to_all = True
                            self.vault.update_credential(existing.id, **item)
                            updated_count += 1
                        elif clicked_button == btn_update:
                            self.vault.update_credential(existing.id, **item)
                            updated_count += 1
                        elif clicked_button == btn_skip_all:
                            no_to_all = True
                            skipped_count += 1
                        else:
                            skipped_count += 1
                    else:
                        self.vault.add_credential(**item)
                        imported_count += 1
                
                QMessageBox.information(
                    self, 
                    "Import Complete", 
                    f"Import Results:\n\n• New items imported: {imported_count}\n• Items updated: {updated_count}\n• Items skipped: {skipped_count}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Import Failed",
                    f"An error occurred while importing:\n{str(e)}"
                )

    def _handle_export(self):
        reply = QMessageBox.question(
            self,
            "Confirm Export",
            "Are you sure you want to export your passwords to an unencrypted CSV file?\n\nAnyone with access to this file will be able to see your passwords.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                csv_content = self.vault.export_to_csv()
                
                file_path, _ = QFileDialog.getSaveFileName(
                    self,
                    "Save CSV File",
                    "vault_export.csv",
                    "CSV Files (*.csv)"
                )
                
                if file_path:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(csv_content)
                    
                    QMessageBox.information(
                        self,
                        "Export Successful",
                        f"Vault exported successfully to:\n{file_path}"
                    )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Export Failed",
                    f"An error occurred while exporting:\n{str(e)}"
                )

    def _setup_notes_section(self, layout, theme):
        """Setup Secure Notes export/import section."""
        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        
        title = QLabel("Secure Notes")
        title.setStyleSheet(f"color: {theme.colors.foreground}; font-size: 14px; font-weight: 500;")
        text_layout.addWidget(title)
        
        subtitle = QLabel("Export or import secure notes as JSON (for transfer between devices).")
        subtitle.setStyleSheet(f"color: {theme.colors.muted_foreground}; font-size: 12px;")
        text_layout.addWidget(subtitle)
        
        row.addLayout(text_layout)

        btn_style = f"""
            QPushButton {{
                background-color: {theme.colors.card};
                border: 1px solid {theme.colors.border};
                color: {theme.colors.foreground};
                border-radius: 6px;
                font-size: 13px;
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                background-color: {theme.colors.accent};
            }}
        """

        export_btn = QPushButton("Export")
        export_btn.setCursor(Qt.PointingHandCursor)
        export_btn.setFixedWidth(80)
        export_btn.setFixedHeight(32)
        export_btn.setStyleSheet(btn_style)
        export_btn.clicked.connect(self._handle_notes_export)
        row.addWidget(export_btn)

        import_btn = QPushButton("Import")
        import_btn.setCursor(Qt.PointingHandCursor)
        import_btn.setFixedWidth(80)
        import_btn.setFixedHeight(32)
        import_btn.setStyleSheet(btn_style)
        import_btn.clicked.connect(self._handle_notes_import)
        row.addWidget(import_btn)

        layout.addWidget(container)

    def _setup_cards_section(self, layout, theme):
        """Setup Credit Cards export/import section."""
        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        
        title = QLabel("Credit Cards")
        title.setStyleSheet(f"color: {theme.colors.foreground}; font-size: 14px; font-weight: 500;")
        text_layout.addWidget(title)
        
        subtitle = QLabel("Export or import credit cards as JSON (for transfer between devices).")
        subtitle.setStyleSheet(f"color: {theme.colors.muted_foreground}; font-size: 12px;")
        text_layout.addWidget(subtitle)
        
        row.addLayout(text_layout)

        btn_style = f"""
            QPushButton {{
                background-color: {theme.colors.card};
                border: 1px solid {theme.colors.border};
                color: {theme.colors.foreground};
                border-radius: 6px;
                font-size: 13px;
                padding: 6px 12px;
            }}
            QPushButton:hover {{
                background-color: {theme.colors.accent};
            }}
        """

        export_btn = QPushButton("Export")
        export_btn.setCursor(Qt.PointingHandCursor)
        export_btn.setFixedWidth(80)
        export_btn.setFixedHeight(32)
        export_btn.setStyleSheet(btn_style)
        export_btn.clicked.connect(self._handle_cards_export)
        row.addWidget(export_btn)

        import_btn = QPushButton("Import")
        import_btn.setCursor(Qt.PointingHandCursor)
        import_btn.setFixedWidth(80)
        import_btn.setFixedHeight(32)
        import_btn.setStyleSheet(btn_style)
        import_btn.clicked.connect(self._handle_cards_import)
        row.addWidget(import_btn)

        layout.addWidget(container)

    def _handle_notes_export(self):
        """Export secure notes to JSON file."""
        if not self.vault:
            QMessageBox.warning(self, "Error", "Vault not available.")
            return
            
        reply = QMessageBox.question(
            self,
            "Confirm Export",
            "This will export your secure notes to a JSON file.\n\nThe content will be UNENCRYPTED. Keep this file secure.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                import json
                notes = self.vault.get_all_secure_notes()
                
                export_data = []
                for note in notes:
                    export_data.append({
                        "title": note.title,
                        "content": note.content,
                        "is_favorite": note.is_favorite,
                        "created_at": note.created_at,
                        "updated_at": note.updated_at
                    })
                
                file_path, _ = QFileDialog.getSaveFileName(
                    self,
                    "Save Secure Notes",
                    "secure_notes_export.json",
                    "JSON Files (*.json)"
                )
                
                if file_path:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(export_data, f, indent=2, ensure_ascii=False)
                    
                    QMessageBox.information(
                        self,
                        "Export Successful",
                        f"Exported {len(notes)} secure notes to:\n{file_path}"
                    )
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", f"Error: {str(e)}")

    def _handle_notes_import(self):
        """Import secure notes from JSON file."""
        if not self.vault:
            QMessageBox.warning(self, "Error", "Vault not available.")
            return
            
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select JSON File",
            "",
            "JSON Files (*.json);;All Files (*.*)"
        )
        
        if file_path:
            try:
                import json
                with open(file_path, 'r', encoding='utf-8') as f:
                    notes_data = json.load(f)
                
                imported_count = 0
                for note in notes_data:
                    self.vault.add_secure_note(
                        title=note.get('title', 'Untitled'),
                        content=note.get('content', '')
                    )
                    imported_count += 1
                
                QMessageBox.information(
                    self,
                    "Import Successful",
                    f"Imported {imported_count} secure notes."
                )
            except Exception as e:
                QMessageBox.critical(self, "Import Failed", f"Error: {str(e)}")

    def _handle_cards_export(self):
        """Export credit cards to JSON file."""
        if not self.vault:
            QMessageBox.warning(self, "Error", "Vault not available.")
            return
            
        reply = QMessageBox.question(
            self,
            "Confirm Export",
            "This will export your credit cards to a JSON file.\n\nThe content will be UNENCRYPTED. Keep this file secure.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                import json
                cards = self.vault.get_all_credit_cards()
                
                export_data = []
                for card in cards:
                    export_data.append({
                        "title": card.title,
                        "cardholder_name": card.cardholder_name,
                        "card_number": card.card_number,
                        "expiry_date": card.expiry_date,
                        "cvv": card.cvv,
                        "notes": card.notes,
                        "is_favorite": card.is_favorite,
                        "created_at": card.created_at,
                        "updated_at": card.updated_at
                    })
                
                file_path, _ = QFileDialog.getSaveFileName(
                    self,
                    "Save Credit Cards",
                    "credit_cards_export.json",
                    "JSON Files (*.json)"
                )
                
                if file_path:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(export_data, f, indent=2, ensure_ascii=False)
                    
                    QMessageBox.information(
                        self,
                        "Export Successful",
                        f"Exported {len(cards)} credit cards to:\n{file_path}"
                    )
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", f"Error: {str(e)}")

    def _handle_cards_import(self):
        """Import credit cards from JSON file."""
        if not self.vault:
            QMessageBox.warning(self, "Error", "Vault not available.")
            return
            
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select JSON File",
            "",
            "JSON Files (*.json);;All Files (*.*)"
        )
        
        if file_path:
            try:
                import json
                with open(file_path, 'r', encoding='utf-8') as f:
                    cards_data = json.load(f)
                
                imported_count = 0
                for card in cards_data:
                    self.vault.add_credit_card(
                        title=card.get('title', 'Untitled'),
                        cardholder_name=card.get('cardholder_name', ''),
                        card_number=card.get('card_number', ''),
                        expiry_date=card.get('expiry_date', ''),
                        cvv=card.get('cvv', ''),
                        notes=card.get('notes')
                    )
                    imported_count += 1
                
                QMessageBox.information(
                    self,
                    "Import Successful",
                    f"Imported {imported_count} credit cards."
                )
            except Exception as e:
                QMessageBox.critical(self, "Import Failed", f"Error: {str(e)}")
