from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QStackedWidget, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from ui.dashboard import DashboardScreen
from ui.zbozi_screen import ZboziScreen
from ui.pohyb_screen import PohybScreen
from ui.partneri_screen import PartneriScreen
from ui.upozorneni_screen import UpozorneniScreen
from ui.reporty_screen import ReportyScreen


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SkladIS")
        self.setMinimumSize(1100, 680)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Sidebar
        self._nav_buttons = {}
        self.sidebar = self._build_sidebar()
        layout.addWidget(self.sidebar)

        # Oddělovač
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFixedWidth(1)
        sep.setStyleSheet("color: #ddd;")
        layout.addWidget(sep)

        # Hlavní obsah
        self.stack = QStackedWidget()
        layout.addWidget(self.stack, 1)

        # Obrazovky
        self.screens = {
            "dashboard":   DashboardScreen(),
            "zbozi":       ZboziScreen(),
            "pohyby":      PohybScreen(),
            "dodavatele":  PartneriScreen(mode="dodavatel"),
            "odberatele":  PartneriScreen(mode="odberatel"),
            "upozorneni":  UpozorneniScreen(),
            "reporty":     ReportyScreen(),
        }
        for screen in self.screens.values():
            self.stack.addWidget(screen)

        self._show("dashboard")

    def _build_sidebar(self):
        sidebar = QWidget()
        sidebar.setFixedWidth(190)
        sidebar.setStyleSheet("background: #f8f8f8;")
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 16, 0, 16)
        layout.setSpacing(2)

        logo = QLabel("📦  SkladIS")
        logo.setFont(QFont("Segoe UI", 13, QFont.Weight.Medium))
        logo.setContentsMargins(16, 0, 0, 16)
        layout.addWidget(logo)

        nav_items = [
            ("dashboard",  "🏠  Přehled"),
            ("zbozi",      "📦  Zboží"),
            ("pohyby",     "↕️  Pohyby"),
            ("dodavatele", "🚚  Dodavatelé"),
            ("odberatele", "👥  Odběratelé"),
            ("upozorneni", "🔔  Upozornění"),
        ]
        for key, label in nav_items:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setAutoExclusive(False)
            btn.setStyleSheet(self._nav_style())
            btn.clicked.connect(lambda _, k=key: self._show(k))
            layout.addWidget(btn)
            self._nav_buttons[key] = btn

        layout.addStretch()

        btn_rep = QPushButton("📊  Reporty")
        btn_rep.setCheckable(True)
        btn.setAutoExclusive(False)
        btn_rep.setStyleSheet(self._nav_style())
        btn_rep.clicked.connect(lambda: self._show("reporty"))
        layout.addWidget(btn_rep)
        self._nav_buttons["reporty"] = btn_rep

        return sidebar

    def _nav_style(self):
        return """
            QPushButton {
                text-align: left;
                padding: 9px 16px;
                border: none;
                background: transparent;
                font-size: 13px;
                color: #555;
            }
            QPushButton:hover { background: #ececec; color: #111; }
            QPushButton:checked { background: #fff; color: #111; font-weight: bold;
                                  border-right: 2px solid #111; }
        """

    def _show(self, key):
        for k, btn in self._nav_buttons.items():
            btn.setChecked(k == key)
        screen = self.screens[key]
        self.stack.setCurrentWidget(screen)
        if hasattr(screen, "refresh"):
            screen.refresh()
