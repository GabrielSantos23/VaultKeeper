
from typing import List, Optional, Dict, Tuple
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, 
    QScrollArea, QSizePolicy, QProgressBar
)
from PySide6.QtCore import Qt, QTimer, Signal, QThread, QRectF, Property, QPoint, QUrl
from PySide6.QtGui import QColor, QPainter, QPen, QFont, QIcon, QCursor, QPaintEvent, QDesktopServices

from app.core.vault import VaultManager, Credential
from app.core.watchtower_service import WatchtowerService
from app.ui.theme import get_theme
from app.ui.ui_utils import load_svg_icon
from app.ui.components.loading import LoadingOverlay

class CircularProgress(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.value = 0
        self.setFixedSize(70, 70)

    def set_value(self, value):
        self.value = value
        self.update()

    def paintEvent(self, event):
        theme = get_theme()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = QRectF(4, 4, 62, 62)
        pen = QPen(QColor(theme.colors.muted), 8)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.drawArc(rect, 0, 360 * 16)
        pen.setColor(QColor(theme.colors.primary))
        painter.setPen(pen)
        span_angle = -self._val_to_angle(self.value) * 16
        painter.drawArc(rect, 90 * 16, span_angle)
        painter.setPen(QColor(theme.colors.foreground))
        font = QFont("Segoe UI", 16, QFont.Bold)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignCenter, str(int(self.value)))

    def _val_to_angle(self, val):
        return (val / 100.0) * 360



class NavTab(QFrame):
    clicked = Signal()
    def __init__(self, title, count=None, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self.is_active = False
        self.count = count
        theme = get_theme()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        self.lbl_title = QLabel(title)
        self.lbl_title.setStyleSheet(f"font-weight: 600; font-size: 13px; color: {theme.colors.muted_foreground};")
        layout.addWidget(self.lbl_title)
        if count is not None:
            self.lbl_count = QLabel(str(count))
            self.lbl_count.setStyleSheet(f"background-color: {theme.colors.muted}; color: {theme.colors.muted_foreground}; border-radius: 4px; padding: 2px 6px; font-size: 11px; font-weight: bold;")
            layout.addWidget(self.lbl_count)
        layout.addStretch()
        self.update_style()
        
    def update_style(self):
        theme = get_theme()
        if self.is_active:
            self.lbl_title.setStyleSheet(f"font-weight: 600; font-size: 13px; color: {theme.colors.primary}; border-bottom: 2px solid {theme.colors.primary}; padding-bottom: 4px;")
            self.setStyleSheet("border-bottom: none;")
            if hasattr(self, 'lbl_count'):
                self.lbl_count.setStyleSheet(f"background-color: {theme.colors.destructive}; color: {theme.colors.destructive_foreground}; border-radius: 4px; padding: 2px 6px; font-size: 11px; font-weight: bold;")
        else:
            self.lbl_title.setStyleSheet(f"font-weight: 600; font-size: 13px; color: {theme.colors.muted_foreground}; border-bottom: 2px solid transparent; padding-bottom: 4px;")
            self.setStyleSheet("border-bottom: none;")
            if hasattr(self, 'lbl_count'):
                self.lbl_count.setStyleSheet(f"background-color: {theme.colors.muted}; color: {theme.colors.muted_foreground}; border-radius: 4px; padding: 2px 6px; font-size: 11px; font-weight: bold;")
                
    def set_active(self, active):
        self.is_active = active
        self.update_style()
    def set_count(self, count):
        self.count = count
        if hasattr(self, 'lbl_count'): self.lbl_count.setText(str(count))
    def mousePressEvent(self, event):
        self.clicked.emit()

class IncidentItem(QFrame):
    def __init__(self, credential, issue_type="LEAKED", count=None):
        super().__init__()
        self.credential = credential
        theme = get_theme()
        self.setFixedHeight(72)
        self.setStyleSheet(f"QFrame {{ background-color: {theme.colors.card}; border-radius: 8px; }}")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(16)
        
        icon_lbl = QLabel()
        icon_lbl.setFixedSize(40, 40)
        icon_lbl.setStyleSheet(f"background-color: {theme.colors.muted}; border-radius: 8px; color: {theme.colors.foreground}; font-weight: bold; font-size: 16px; qproperty-alignment: AlignCenter;")
        icon_lbl.setText(credential.domain[:1].upper() if credential.domain else "?")
        layout.addWidget(icon_lbl)
        
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)
        info_layout.setAlignment(Qt.AlignVCenter)
        top_line = QHBoxLayout()
        top_line.setSpacing(8)
        name_lbl = QLabel(credential.domain)
        name_lbl.setStyleSheet(f"color: {theme.colors.foreground}; font-weight: bold; font-size: 14px; background: transparent;")
        top_line.addWidget(name_lbl)
        
        tag_color = theme.colors.destructive if issue_type in ["LEAKED", "WEAK"] else theme.colors.warning
        tag_text = issue_type if not count else f"{issue_type}"
        icon_char = "!"
        if issue_type == "REUSED": icon_char = "⇄"
        tag = QLabel(f"  {icon_char} {tag_text}  ")
        tag.setStyleSheet(f"background-color: {tag_color}20; color: {tag_color}; border-radius: 4px; font-size: 10px; font-weight: bold; padding: 3px 6px;")
        top_line.addWidget(tag)
        top_line.addStretch()
        info_layout.addLayout(top_line)
        
        subtext = f"{credential.username}"
        if issue_type == "WEAK": subtext += " • Password is too short"
        elif issue_type == "REUSED": subtext += " • Shared with other sites"
        elif issue_type == "LEAKED": subtext += " • Found in data breach"
        detail_lbl = QLabel(subtext)
        detail_lbl.setStyleSheet(f"color: {theme.colors.muted_foreground}; font-size: 13px; background: transparent;")
        info_layout.addWidget(detail_lbl)
        layout.addLayout(info_layout)
        
        layout.addStretch()
        btn = QPushButton("Update Password")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"QPushButton {{ background-color: {theme.colors.primary}; color: {theme.colors.primary_foreground}; border: none; border-radius: 6px; padding: 8px 16px; font-size: 13px; font-weight: 600; }} QPushButton:hover {{ background-color: {theme.colors.ring}; }}")
        btn.clicked.connect(self.open_url)
        layout.addWidget(btn)

    def open_url(self):
        domain = self.credential.domain
        if not domain:
             return
        if not domain.startswith("http"):
             url = "https://" + domain
        else:
             url = domain
        QDesktopServices.openUrl(QUrl(url))

class WatchtowerWorker(QThread):
    finished = Signal(dict)
    
    def __init__(self, service, network_scan):
        super().__init__()
        self.service = service
        self.network_scan = network_scan
        
    def run(self):
        try:
            results = self.service.scan_vault(self.network_scan)
            self.finished.emit(results)
        except Exception as e:
            print(f"Watchtower scan error: {e}")
            self.finished.emit({})

class WatchtowerView(QWidget):
    def __init__(self, vault_manager: VaultManager):
        super().__init__()
        self.vault_manager = vault_manager
        self.service = WatchtowerService(vault_manager)
        
        self.active_category = "action_required"
        self.expanded_incidents = False
        self.scan_results = {
            'leaked': [], 'reused': [], 'weak': [], 'score': 0, 'total_count': 0, 'avg_age_days': 0, '2fa_count': 0
        }
        
        self.setup_ui()
        # Initial fast load (local only) deferred until explicitly called
        
    def start_initial_scan(self):
        # Use singleShot with 0 to update mostly immediately but after init
        QTimer.singleShot(10, lambda: self.run_scan(network_scan=False))
        
    # run_scan moved below

        
    def on_scan_finished(self, results):
        if not results:
            return
            
        self.scan_results = results
        self.update_ui()
        
    def setup_ui(self):
        theme = get_theme()
        self.setStyleSheet(f"background-color: {theme.colors.background};")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- HEADER ---
        header_container = QWidget()
        header_container.setStyleSheet(f"background-color: {theme.colors.background};")
        header_layout = QVBoxLayout(header_container)
        header_layout.setContentsMargins(40, 32, 40, 0)
        header_layout.setSpacing(24)
        
        title_row = QHBoxLayout()
        title_info = QVBoxLayout()
        title_info.setSpacing(4)
        title_lbl = QLabel("Watchtower")
        title_lbl.setStyleSheet(f"color: {theme.colors.foreground}; font-size: 24px; font-weight: bold;")
        subtitle_lbl = QLabel("Unified Security Remediation Dashboard")
        subtitle_lbl.setStyleSheet(f"color: {theme.colors.muted_foreground}; font-size: 14px;")
        title_info.addWidget(title_lbl)
        title_info.addWidget(subtitle_lbl)
        title_row.addLayout(title_info)
        title_row.addStretch()
        
        btn_sort = QPushButton("  Sort by Severity")
        btn_sort.setIcon(QIcon(load_svg_icon("filter", 16, theme.colors.muted_foreground)))
        btn_sort.setStyleSheet(f"QPushButton {{ background-color: {theme.colors.card}; color: {theme.colors.foreground}; border: none; border-radius: 6px; padding: 10px 16px; font-weight: 600; font-size: 13px; }} QPushButton:hover {{ background-color: {theme.colors.muted}; }}")
        
        self.btn_scan = QPushButton("  Scan Now")
        self.btn_scan.setIcon(QIcon(load_svg_icon("refresh", 16, theme.colors.primary_foreground)))
        self.btn_scan.setStyleSheet(f"QPushButton {{ background-color: {theme.colors.primary}; color: {theme.colors.primary_foreground}; border: none; border-radius: 6px; padding: 10px 20px; font-weight: 600; font-size: 13px; }} QPushButton:hover {{ background-color: {theme.colors.ring}; }}")
        self.btn_scan.clicked.connect(lambda: self.run_scan(network_scan=True))
        
        title_row.addWidget(btn_sort)
        title_row.addSpacing(12)
        title_row.addWidget(self.btn_scan)
        header_layout.addLayout(title_row)
        
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(0)
        self.tab_action = NavTab("Action Required", 0); self.tab_action.clicked.connect(lambda: self.set_active_category("action_required"))
        self.tab_leaked = NavTab("Leaked Passwords", 0); self.tab_leaked.clicked.connect(lambda: self.set_active_category("leaked"))
        self.tab_reused = NavTab("Reused Passwords", 0); self.tab_reused.clicked.connect(lambda: self.set_active_category("reused"))
        self.tab_weak = NavTab("Weak Passwords", 0); self.tab_weak.clicked.connect(lambda: self.set_active_category("weak"))
        nav_layout.addWidget(self.tab_action); nav_layout.addWidget(self.tab_leaked); nav_layout.addWidget(self.tab_reused); nav_layout.addWidget(self.tab_weak); nav_layout.addStretch()
        header_layout.addLayout(nav_layout)
        main_layout.addWidget(header_container)
        
        # Divider
        divider = QFrame(); divider.setFrameShape(QFrame.HLine); divider.setStyleSheet(f"color: {theme.colors.border};")
        main_layout.addWidget(divider)
        
        # --- CONTENT ---
        # Overlay Stack
        self.stack = QFrame()
        self.stack_layout = QHBoxLayout(self.stack) # Use HBox to center loading
        self.stack_layout.setContentsMargins(0, 0, 0, 0)
        
        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        content_widget = QWidget()
        scroll_layout = QVBoxLayout(content_widget)
        scroll_layout.setContentsMargins(40, 32, 40, 40)
        scroll_layout.setSpacing(24)
        
        # Active Incidents
        lbl_active = QLabel("ACTIVE INCIDENTS")
        lbl_active.setStyleSheet(f"color: {theme.colors.muted_foreground}; font-size: 12px; font-weight: bold; letter-spacing: 1px;")
        scroll_layout.addWidget(lbl_active)
        self.items_container = QVBoxLayout()
        self.items_container.setSpacing(12)
        scroll_layout.addLayout(self.items_container)
        
        self.btn_show_more = QPushButton("Show more incidents...")
        self.btn_show_more.setStyleSheet(f"QPushButton {{ background-color: {theme.colors.card}; color: {theme.colors.primary}; border: none; border-radius: 20px; padding: 10px 24px; font-weight: 600; font-size: 13px; }} QPushButton:hover {{ background-color: {theme.colors.muted}; }}")
        self.btn_show_more.setCursor(Qt.PointingHandCursor)
        self.btn_show_more.clicked.connect(self.toggle_show_more)
        self.btn_show_more.setFixedWidth(240)
        center_btn = QHBoxLayout(); center_btn.addStretch(); center_btn.addWidget(self.btn_show_more); center_btn.addStretch()
        scroll_layout.addLayout(center_btn)
        scroll_layout.addSpacing(24)
        sep = QFrame(); sep.setFrameShape(QFrame.HLine); sep.setStyleSheet(f"color: {theme.colors.border}; margin-top: 16px; margin-bottom: 16px;")
        scroll_layout.addWidget(sep)
        
        # Health Summary
        lbl_health = QLabel("SYSTEM HEALTH SUMMARY")
        lbl_health.setStyleSheet(f"color: {theme.colors.muted_foreground}; font-size: 12px; font-weight: bold; letter-spacing: 1px;")
        scroll_layout.addWidget(lbl_health)
        
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)
        
        self.card_score = QFrame(); self.card_score.setStyleSheet(f"background-color: {theme.colors.card}; border-radius: 12px; border: 1px solid {theme.colors.border};"); self.card_score.setFixedHeight(120)
        l_score = QHBoxLayout(self.card_score); l_score.setContentsMargins(24, 0, 24, 0)
        self.progress_ring = CircularProgress(); self.progress_ring.set_value(0)
        t_score = QVBoxLayout(); t_score.setSpacing(4); t_score.setAlignment(Qt.AlignVCenter)
        l1 = QLabel("Security Score"); l1.setStyleSheet(f"color: {theme.colors.foreground}; font-weight: bold; font-size: 15px; border: none;")
        l2 = QLabel("Overall Rating: Good"); l2.setStyleSheet(f"color: {theme.colors.muted_foreground}; font-size: 12px; border: none;")
        t_score.addWidget(l1); t_score.addWidget(l2)
        l_score.addWidget(self.progress_ring); l_score.addSpacing(16); l_score.addLayout(t_score); l_score.addStretch()
        
        self.card_age = QFrame(); self.card_age.setStyleSheet(f"background-color: {theme.colors.card}; border-radius: 12px; border: 1px solid {theme.colors.border};"); self.card_age.setFixedHeight(120)
        l_age = QVBoxLayout(self.card_age); l_age.setContentsMargins(24, 24, 24, 24); l_age.setSpacing(12)
        row_age = QHBoxLayout(); la1 = QLabel("Password Age"); la1.setStyleSheet(f"color: {theme.colors.foreground}; font-weight: 500; font-size: 13px; border: none;")
        self.lbl_age_val = QLabel("0d"); self.lbl_age_val.setStyleSheet(f"color: {theme.colors.foreground}; font-weight: bold; font-size: 18px; border: none;")
        row_age.addWidget(la1); row_age.addStretch(); row_age.addWidget(self.lbl_age_val)
        self.bar_age = QProgressBar(); self.bar_age.setTextVisible(False); self.bar_age.setFixedHeight(6); self.bar_age.setValue(0); self.bar_age.setStyleSheet(f"QProgressBar {{ border: none; background-color: {theme.colors.muted}; border-radius: 3px; }} QProgressBar::chunk {{ background-color: {theme.colors.warning}; border-radius: 3px; }}")
        l_age.addLayout(row_age); l_age.addWidget(self.bar_age); l_age.addStretch()
        
        self.card_2fa = QFrame(); self.card_2fa.setStyleSheet(f"background-color: {theme.colors.card}; border-radius: 12px; border: 1px solid {theme.colors.border};"); self.card_2fa.setFixedHeight(120)
        l_2fa = QVBoxLayout(self.card_2fa); l_2fa.setContentsMargins(24, 24, 24, 24); l_2fa.setSpacing(12)
        row_2fa = QHBoxLayout(); lt1 = QLabel("2FA Adoption"); lt1.setStyleSheet(f"color: {theme.colors.foreground}; font-weight: 500; font-size: 13px; border: none;")
        self.lbl_2fa_val = QLabel("0/0"); self.lbl_2fa_val.setStyleSheet(f"color: {theme.colors.foreground}; font-weight: bold; font-size: 18px; border: none;")
        row_2fa.addWidget(lt1); row_2fa.addStretch(); row_2fa.addWidget(self.lbl_2fa_val)
        self.bar_2fa = QProgressBar(); self.bar_2fa.setTextVisible(False); self.bar_2fa.setFixedHeight(6); self.bar_2fa.setValue(0); self.bar_2fa.setStyleSheet(f"QProgressBar {{ border: none; background-color: {theme.colors.muted}; border-radius: 3px; }} QProgressBar::chunk {{ background-color: {theme.colors.success}; border-radius: 3px; }}")
        l_2fa.addLayout(row_2fa); l_2fa.addWidget(self.bar_2fa); l_2fa.addStretch()
        
        cards_layout.addWidget(self.card_score, 1); cards_layout.addWidget(self.card_age, 1); cards_layout.addWidget(self.card_2fa, 1)
        scroll_layout.addLayout(cards_layout)
        footer_lbl = QLabel("WATCHTOWER SCANNING ENGINE V4.2.1 • LAST FULL AUDIT: JUST NOW")
        footer_lbl.setAlignment(Qt.AlignCenter); footer_lbl.setStyleSheet(f"color: {theme.colors.muted_foreground}; font-size: 10px; font-weight: bold; letter-spacing: 1px; margin-top: 32px;")
        scroll_layout.addWidget(footer_lbl)
        
        content_widget.setLayout(scroll_layout)
        scroll.setWidget(content_widget)
        
        # Add loading overlay and scroll to stack
        self.stack_layout.addWidget(scroll)
        
        # Loading Overlay (Initially hidden)
        self.loading = LoadingOverlay(self)
        self.loading.hide()
        
        main_layout.addWidget(self.stack)
        
        self.set_active_category("action_required")

    def resizeEvent(self, event):
        if self.loading.isVisible():
             self.loading.move(self.width() // 2 - 32, self.height() // 2 - 32)
        super().resizeEvent(event)

    def set_active_category(self, category):
        for tab in [self.tab_action, self.tab_leaked, self.tab_reused, self.tab_weak]: tab.set_active(False)
        if category == "action_required": self.tab_action.set_active(True)
        elif category == "leaked": self.tab_leaked.set_active(True)
        elif category == "reused": self.tab_reused.set_active(True)
        elif category == "weak": self.tab_weak.set_active(True)
        self.active_category = category
        self.expanded_incidents = False
        self.render_incidents()

    def run_scan(self, network_scan=False):
        if network_scan:
            self.btn_scan.setText("  Scanning...")
            self.btn_scan.setEnabled(False)
        
        # Show loading
        self.loading.raise_()
        self.loading.move(self.width() // 2 - 32, self.height() // 2 - 32)
        self.loading.show()
        
        if hasattr(self, 'scan_worker') and self.scan_worker.isRunning():
            return
            
        self.scan_worker = WatchtowerWorker(self.service, network_scan)
        self.scan_worker.finished.connect(self.on_scan_finished)
        self.scan_worker.start()
        
    def on_scan_finished(self, results):
        self.loading.hide()
        self.btn_scan.setEnabled(True)
        self.btn_scan.setText("  Scan Now")
        self.scan_results = results
        
        leaked_c = len(self.scan_results['leaked'])
        reused_c = len(self.scan_results['reused'])
        weak_c = len(self.scan_results['weak'])
        total_action = leaked_c + reused_c + weak_c
        
        self.tab_action.set_count(total_action)
        self.tab_leaked.set_count(leaked_c)
        self.tab_reused.set_count(reused_c)
        self.tab_weak.set_count(weak_c)
        
        self.progress_ring.set_value(self.scan_results.get('score', 0))
        avg_age = self.scan_results.get('avg_age_days', 0)
        self.lbl_age_val.setText(f"{avg_age}d")
        age_prog = max(0, min(100, 100 - (avg_age / 3.65)))
        self.bar_age.setValue(int(age_prog))
        
        tfa = self.scan_results.get('2fa_count', 0)
        total = self.scan_results.get('total_count', 1) or 1
        self.lbl_2fa_val.setText(f"{tfa}/{total}")
        self.bar_2fa.setValue(int((tfa/total)*100))
        
        self.render_incidents()
        
    def toggle_show_more(self):
        self.expanded_incidents = not self.expanded_incidents
        self.render_incidents()

    def render_incidents(self):
        while self.items_container.count():
            w = self.items_container.takeAt(0)
            if w.widget(): w.widget().deleteLater()
            
        items = []
        if self.active_category == "action_required":
            for c, cnt in self.scan_results['leaked']: items.append((c, "LEAKED"))
            for c in self.scan_results['reused']: items.append((c, "REUSED"))
            for c in self.scan_results['weak']: items.append((c, "WEAK"))
        elif self.active_category == "leaked":
            for c, cnt in self.scan_results['leaked']: items.append((c, "LEAKED"))
        elif self.active_category == "reused":
            for c in self.scan_results['reused']: items.append((c, "REUSED"))
        elif self.active_category == "weak":
            for c in self.scan_results['weak']: items.append((c, "WEAK"))
            
        if not items:
            lbl = QLabel("No incidents found. Good job!")
            theme = get_theme()
            lbl.setStyleSheet(f"color: {theme.colors.muted_foreground}; font-size: 14px; padding: 20px;")
            lbl.setAlignment(Qt.AlignCenter)
            self.items_container.addWidget(lbl)
            self.btn_show_more.setVisible(False)
        else:
            limit = 50 if self.expanded_incidents else 5
            visible_items = items[:limit]
            
            for c, issue in visible_items:
                self.items_container.addWidget(IncidentItem(c, issue))
                
            remaining = len(items) - len(visible_items)
            self.btn_show_more.setVisible(remaining > 0 or self.expanded_incidents)
            
            if self.expanded_incidents:
                self.btn_show_more.setText("Show Less")
            else:
                self.btn_show_more.setText(f"Show {remaining} more incidents...")

