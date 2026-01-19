
from PySide6.QtWidgets import (

    QWidget, QHBoxLayout, QMessageBox

)

from PySide6.QtCore import Signal, QTimer, Qt

from app.core.vault import VaultManager, Credential, SecureNote, CreditCard, Folder

from app.ui.theme import get_theme

from app.ui.main_window.sidebar import Sidebar

from app.ui.main_window.item_list import CredentialsList

from app.ui.main_window.detail_panel import DetailPanel

from app.ui.dialogs.folder_dialog import FolderDialog

from app.ui.dialogs.credential_dialog import CredentialDialog

from app.ui.item_dialogs import (

    SecureNoteDialog, CreditCardDialog, AddNewItemDialog

)

from app.ui.settings_dialog import SettingsDialog

from app.ui.gdrive_dialog import GoogleDriveDialog

class VaultWidget(QWidget):

    lock_requested = Signal()

    def __init__(self, vault: VaultManager, parent=None):

        super().__init__(parent)

        self.vault = vault

        self.sidebar_visible = True

        self.current_category = "all"

        self.setup_ui()

        QTimer.singleShot(50, self.load_data)

    def load_data(self):

        self.load_folders()

        self.load_credentials()

    def setup_ui(self):

        theme = get_theme()

        self.main_layout = QHBoxLayout(self)

        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.main_layout.setSpacing(0)

        self.sidebar = Sidebar()

        self.sidebar.category_changed.connect(self.on_category_changed)

        self.sidebar.toggle_sidebar.connect(self.toggle_sidebar)

        self.sidebar.add_folder_clicked.connect(self.add_folder)

        self.sidebar.folder_edit_requested.connect(self.on_folder_edit)

        self.sidebar.folder_delete_requested.connect(self.on_folder_delete)

        self.sidebar.settings_clicked.connect(self.on_settings_clicked)

        self.sidebar.google_drive_clicked.connect(self.on_google_drive_clicked)

        self.main_layout.addWidget(self.sidebar)

        self.credentials_list = CredentialsList()

        self.credentials_list.credential_selected.connect(self.on_credential_selected)

        self.credentials_list.add_clicked.connect(self.add_credential)

        self.credentials_list.toggle_sidebar_requested.connect(self.toggle_sidebar)

        self.credentials_list.setMinimumWidth(280)

        self.credentials_list.setMaximumWidth(350)

        self.main_layout.addWidget(self.credentials_list)

        self.detail_panel = DetailPanel()

        self.detail_panel.edit_requested.connect(self.edit_credential)

        self.detail_panel.delete_requested.connect(self.delete_credential)

        self.detail_panel.favorite_toggled.connect(self.toggle_favorite)

        self.detail_panel.folder_move_requested.connect(self.move_credential_to_folder)

        self.detail_panel.status_message.connect(self.show_status)

        self.main_layout.addWidget(self.detail_panel, stretch=1)

    def toggle_sidebar(self):

        self.sidebar_visible = not self.sidebar_visible

        self.sidebar.setVisible(self.sidebar_visible)

        self.credentials_list.set_sidebar_toggle_visible(not self.sidebar_visible)

    def load_folders(self):

        try:

            folders = self.vault.get_all_folders()

            self.sidebar.set_folders(folders)

            self.detail_panel.set_available_folders(folders)

        except Exception as e:

            print(f"Error loading folders: {e}")

    def load_credentials(self):

        try:

            credentials = self.vault.get_all_credentials()

            secure_notes = self.vault.get_all_secure_notes()

            credit_cards = self.vault.get_all_credit_cards()

            self.credentials_list.set_all_items(credentials, secure_notes, credit_cards)

        except Exception as e:

            print(f"Error loading items: {e}")

    def on_category_changed(self, category: str):

        self.current_category = category

        if category == "all":

            self.credentials_list.set_filter("all")

        elif category == "favorites":

            self.credentials_list.set_filter("favorites")

        elif category == "secure_notes":

            self.credentials_list.set_filter("secure_notes")

        elif category == "credit_cards":

            self.credentials_list.set_filter("credit_cards")

        elif category.startswith("folder_"):

            try:

                folder_id = int(category.split("_")[1])

                self.credentials_list.set_filter("folder", folder_id)

            except (IndexError, ValueError):

                self.credentials_list.set_filter("all")

        self.detail_panel.show_empty_state()

    def on_credential_selected(self, item):

        if isinstance(item, Credential):

            self.detail_panel.show_credential(item)

        elif isinstance(item, SecureNote):

            self.detail_panel.show_secure_note(item)

        elif isinstance(item, CreditCard):

            self.detail_panel.show_credit_card(item)

    def add_folder(self):

        dialog = FolderDialog(self, "Create Folder")

        if dialog.exec():

            name = dialog.folder_name

            if name:

                try:

                    self.vault.create_folder(name)

                    self.load_folders()

                    self.sidebar.personal_folders_container.setVisible(True)

                    self.show_status(f"Folder '{name}' created")

                except Exception as e:

                    QMessageBox.critical(self, "Error", f"Failed to create folder: {e}")

    def on_folder_edit(self, folder: Folder):

        dialog = FolderDialog(self, "Rename Folder", folder.name)

        if dialog.exec():

            name = dialog.folder_name

            if name and name != folder.name:

                try:

                    if self.vault.update_folder(folder.id, name):

                        self.load_folders()

                        self.show_status(f"Folder renamed to '{name}'")

                except Exception as e:

                    QMessageBox.critical(self, "Error", f"Failed to rename folder: {e}")

    def on_folder_delete(self, folder: Folder):

        reply = QMessageBox.question(

            self,

            "Delete Folder",

            f"Are you sure you want to delete folder '{folder.name}'?\nCredentials inside will not be deleted but will be moved to 'All Items'.",

            QMessageBox.Yes | QMessageBox.No,

            QMessageBox.No

        )

        if reply == QMessageBox.Yes:

            try:

                if self.vault.delete_folder(folder.id):

                    self.load_folders()

                    self.show_status(f"Folder '{folder.name}' deleted")

                    if self.current_category == f"folder_{folder.id}":

                        self.set_category("all")

            except Exception as e:

                QMessageBox.critical(self, "Error", f"Failed to delete folder: {e}")

    def move_credential_to_folder(self, credential, folder_id):

        try:

            if self.vault.set_credential_folder(credential.id, folder_id):

                updated_cred = self.vault.get_credential(credential.id)

                if updated_cred:

                    self.detail_panel.show_credential(updated_cred)

                    self.load_credentials()

                    if folder_id is None:

                        self.show_status("Removed from folder")

                    else:

                        folder_name = next((f.name for f in self.vault.get_all_folders() if f.id == folder_id), "folder")

                        self.show_status(f"Moved to {folder_name}")

        except Exception as e:

            QMessageBox.critical(self, "Error", f"Failed to move credential: {e}")

    def toggle_favorite(self, item):

        try:

            if isinstance(item, Credential):

                self.vault.toggle_credential_favorite(item.id)

                updated = next((c for c in self.vault.get_all_credentials() if c.id == item.id), None)

                if updated:

                    self.detail_panel.show_credential(updated)

            elif isinstance(item, SecureNote):

                self.vault.toggle_secure_note_favorite(item.id)

                updated = next((n for n in self.vault.get_all_secure_notes() if n.id == item.id), None)

                if updated:

                    self.detail_panel.show_secure_note(updated)

            elif isinstance(item, CreditCard):

                self.vault.toggle_credit_card_favorite(item.id)

                updated = next((c for c in self.vault.get_all_credit_cards() if c.id == item.id), None)

                if updated:

                    self.detail_panel.show_credit_card(updated)

            self.load_credentials()

        except Exception as e:

            print(f"Error toggling favorite: {e}")

    def on_settings_clicked(self):

        dialog = SettingsDialog(self)

        dialog.exec()

    def on_google_drive_clicked(self):

        dialog = GoogleDriveDialog(self)

        dialog.connection_successful.connect(self._on_gdrive_connected)

        dialog.exec()

    def _on_gdrive_connected(self):

        self.show_status("Connected to Google Drive")

    def add_credential(self):

        dialog = AddNewItemDialog(parent=self)

        dialog.login_selected.connect(self._add_login)

        dialog.credit_card_selected.connect(self._add_credit_card)

        dialog.secure_note_selected.connect(self._add_secure_note)

        dialog.exec()

    def _add_login(self):

        dialog = CredentialDialog(parent=self)

        if dialog.exec():

            data = dialog.get_data()

            if data['domain'] and data['username'] and data['password']:

                add_data = {k: v for k, v in data.items() if k not in ('clear_totp', 'clear_backup')}

                self.vault.add_credential(**add_data)

                self.load_credentials()

    def _add_credit_card(self):

        dialog = CreditCardDialog(parent=self)

        if dialog.exec():

            data = dialog.get_data()

            if data['title'] and data['card_number']:

                self.vault.add_credit_card(**data)

                self.load_credentials()

    def _add_secure_note(self):

        folders = self.vault.get_all_folders()

        dialog = SecureNoteDialog(folders=folders, parent=self)

        if dialog.exec():

            data = dialog.get_data()

            if data['title'] and data['content']:

                self.vault.add_secure_note(**data)

                self.load_credentials()

    def edit_credential(self, item):

        if isinstance(item, Credential):

            dialog = CredentialDialog(item, parent=self)

            if dialog.exec():

                data = dialog.get_data()

                self.vault.update_credential(item.id, **data)

                self.load_credentials()

                updated = next((c for c in self.vault.get_all_credentials() if c.id == item.id), None)

                if updated:

                    self.detail_panel.show_credential(updated)

        elif isinstance(item, SecureNote):

            folders = self.vault.get_all_folders()

            dialog = SecureNoteDialog(item, folders=folders, parent=self)

            if dialog.exec():

                data = dialog.get_data()

                self.vault.update_secure_note(item.id, **data)

                self.load_credentials()

                updated = next((n for n in self.vault.get_all_secure_notes() if n.id == item.id), None)

                if updated:

                    self.detail_panel.show_secure_note(updated)

        elif isinstance(item, CreditCard):

            dialog = CreditCardDialog(item, parent=self)

            if dialog.exec():

                data = dialog.get_data()

                self.vault.update_credit_card(item.id, **data)

                self.load_credentials()

                updated = next((c for c in self.vault.get_all_credit_cards() if c.id == item.id), None)

                if updated:

                    self.detail_panel.show_credit_card(updated)

    def delete_credential(self, item):

        if isinstance(item, Credential):

            name = item.domain

            item_type = "credential"

        elif isinstance(item, SecureNote):

            name = item.title

            item_type = "secure note"

        elif isinstance(item, CreditCard):

            name = item.title

            item_type = "credit card"

        else:

            return

        reply = QMessageBox.question(

            self,

            "Confirm Delete",

            f"Are you sure you want to delete the {item_type}?\n\n{name}\n\nThis action cannot be undone.",

            QMessageBox.Yes | QMessageBox.No,

            QMessageBox.No

        )

        if reply == QMessageBox.Yes:

            if isinstance(item, Credential):

                self.vault.delete_credential(item.id)

            elif isinstance(item, SecureNote):

                self.vault.delete_secure_note(item.id)

            elif isinstance(item, CreditCard):

                self.vault.delete_credit_card(item.id)

            self.load_credentials()

            self.detail_panel.show_empty_state()

    def show_status(self, message: str):

        pass

    def setup_extension(self):

        try:

            from ..native.installer import NativeHostInstaller

            installer = NativeHostInstaller()

            installer.create_wrapper_script()

            results = installer.install_all()

            installed = [browser.title() for browser, success, msg in results if success]

            if installed:

                QMessageBox.information(

                    self,

                    "Extension Configured",

                    f"Native Host installed for:\n\n• " + "\n• ".join(installed)

                )

            else:

                QMessageBox.warning(

                    self,

                    "No Browser Found",

                    "No compatible browser was found."

                )

        except Exception as e:

            QMessageBox.critical(self, "Error", f"Failed to configure:\n\n{e}")
