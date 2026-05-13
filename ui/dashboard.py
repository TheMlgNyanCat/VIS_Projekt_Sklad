from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
import models.zbozi as mz
import models.pohyb as mp


class StatCard(QFrame):
    def __init__(self, label, value, sub="", danger=False):
        super().__init__()
        self.setStyleSheet("""
            QFrame { background: #f5f5f5; border-radius: 8px; }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)

        lbl = QLabel(label)
        lbl.setStyleSheet("font-size: 12px; color: #888;")
        layout.addWidget(lbl)

        val = QLabel(str(value))
        val.setFont(QFont("Segoe UI", 22, QFont.Weight.Medium))
        layout.addWidget(val)

        if sub:
            s = QLabel(sub)
            color = "#c0392b" if danger else "#27ae60"
            s.setStyleSheet(f"font-size: 11px; color: {color};")
            layout.addWidget(s)


class DashboardScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.layout_ = QVBoxLayout(self)
        self.layout_.setContentsMargins(24, 24, 24, 24)
        self.layout_.setSpacing(16)

        title = QLabel("Přehled")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Medium))
        self.layout_.addWidget(title)

        self.cards_row = QHBoxLayout()
        self.cards_row.setSpacing(12)
        self.layout_.addLayout(self.cards_row)

        tbl_label = QLabel("Poslední pohyby")
        tbl_label.setStyleSheet("font-size: 12px; color: #888; font-weight: bold; text-transform: uppercase;")
        self.layout_.addWidget(tbl_label)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Zboží", "Typ", "Množství", "Partner", "Datum"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.layout_.addWidget(self.table)

        self.refresh()

    def refresh(self):
        # Vyčisti karty
        while self.cards_row.count():
            item = self.cards_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        nizky = mz.get_nizky_stav()
        pohyby = mp.get_all()

        prijmy = sum(1 for p in pohyby if p['typ'] == 'prijem')
        vydeje = sum(1 for p in pohyby if p['typ'] == 'vydej')

        self.cards_row.addWidget(StatCard("Pohyby celkem", len(pohyby), f"{prijmy} příjmů / {vydeje} výdejů"))
        self.cards_row.addWidget(StatCard("Nízký stav", len(nizky),
                                          "vyžaduje pozornost" if nizky else "vše v pořádku",
                                          danger=bool(nizky)))

        # Tabulka pohybů
        self.table.setRowCount(0)
        for row_data in pohyby[:20]:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(row_data['zbozi'] or ""))
            typ = row_data['typ']
            typ_item = QTableWidgetItem("příjem" if typ == "prijem" else "výdej")
            typ_item.setForeground(QColor("#1a7a4a") if typ == "prijem" else QColor("#c0392b"))
            self.table.setItem(row, 1, typ_item)
            self.table.setItem(row, 2, QTableWidgetItem(f"{row_data['mnozstvi']} {row_data['jednotka']}"))
            partner = row_data.get('dodavatel') or row_data.get('odberatel') or ""
            self.table.setItem(row, 3, QTableWidgetItem(partner))
            datum = row_data['datum']
            self.table.setItem(row, 4, QTableWidgetItem(datum.strftime("%d.%m.%Y %H:%M") if datum else ""))
