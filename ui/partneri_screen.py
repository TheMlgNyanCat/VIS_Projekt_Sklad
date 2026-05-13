from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QFormLayout, QDialogButtonBox, QMessageBox
)
from PyQt6.QtGui import QFont
import models.partneri as mp


class PartnerDialog(QDialog):
    def __init__(self, parent, mode, data=None):
        super().__init__(parent)
        label = "Dodavatel" if mode == "dodavatel" else "Odběratel"
        self.setWindowTitle(f"{'Přidat' if not data else 'Upravit'} {label.lower()}")
        self.setMinimumWidth(340)

        layout = QFormLayout(self)
        layout.setSpacing(10)

        self.nazev   = QLineEdit(data['nazev']   if data else "")
        self.kontakt = QLineEdit(data['kontakt'] if data else "")
        self.email   = QLineEdit(data['email']   if data else "")
        self.telefon = QLineEdit(data['telefon'] if data else "")

        layout.addRow("Název:",   self.nazev)
        layout.addRow("Kontakt:", self.kontakt)
        layout.addRow("Email:",   self.email)
        layout.addRow("Telefon:", self.telefon)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addRow(btns)

    def get_data(self):
        return {
            "nazev":   self.nazev.text().strip(),
            "kontakt": self.kontakt.text().strip(),
            "email":   self.email.text().strip(),
            "telefon": self.telefon.text().strip(),
        }


class PartneriScreen(QWidget):
    def __init__(self, mode="dodavatel"):
        super().__init__()
        self.mode = mode
        label = "Dodavatelé" if mode == "dodavatel" else "Odběratelé"

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = QLabel(label)
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Medium))
        layout.addWidget(title)

        toolbar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText(f"Hledat {label.lower()}…")
        self.search.textChanged.connect(self.refresh)
        toolbar.addWidget(self.search)

        btn_add = QPushButton(f"＋  Přidat")
        btn_add.clicked.connect(self.add_partner)
        toolbar.addWidget(btn_add)
        layout.addLayout(toolbar)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Název", "Kontakt", "Email", "Telefon", ""])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnWidth(4, 80)
        layout.addWidget(self.table)
        self.table.cellDoubleClicked.connect(self._on_double_click)
        
        self.refresh()

    def _get_all(self, search=""):
        if self.mode == "dodavatel":
            return mp.get_all_dodavatele(search)
        return mp.get_all_odberatele(search)

    def refresh(self):
        rows = self._get_all(self.search.text())
        self.table.setRowCount(0)
        for r in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(r['nazev'] or ""))
            self.table.setItem(row, 1, QTableWidgetItem(r['kontakt'] or ""))
            self.table.setItem(row, 2, QTableWidgetItem(r['email'] or ""))
            self.table.setItem(row, 3, QTableWidgetItem(r['telefon'] or ""))
            btn = QPushButton("Upravit")
            btn.clicked.connect(lambda _, rid=r['id']: self.edit_partner(rid, r))
            self.table.setCellWidget(row, 4, btn)

    def add_partner(self):
        dlg = PartnerDialog(self, self.mode)
        if dlg.exec():
            d = dlg.get_data()
            if not d['nazev']:
                QMessageBox.warning(self, "Chyba", "Název nesmí být prázdný.")
                return
            if self.mode == "dodavatel":
                mp.create_dodavatel(**d)
            else:
                mp.create_odberatel(**d)
            self.refresh()

    def edit_partner(self, pid, data):
        dlg = PartnerDialog(self, self.mode, data)
        if dlg.exec():
            d = dlg.get_data()
            if self.mode == "dodavatel":
                mp.update_dodavatel(pid, **d)
            else:
                mp.update_odberatel(pid, **d)
            self.refresh()

    def _on_double_click(self, row, col):
        btn = self.table.cellWidget(row, 4)
        if btn:
            btn.click()