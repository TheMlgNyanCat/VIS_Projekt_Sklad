from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QDateEdit, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QColor
import models.zbozi as mz
import models.pohyb as mp
import csv


# ── Upozornění ─────────────────────────────────────────────

class UpozorneniScreen(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = QLabel("Upozornění — nízký stav")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Medium))
        layout.addWidget(title)

        self.info = QLabel()
        self.info.setStyleSheet("color: #888; font-size: 13px;")
        layout.addWidget(self.info)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Zboží", "Kategorie", "Na skladě", "Minimum", "Chybí"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        self.refresh()

    def refresh(self):
        rows = mz.get_nizky_stav()
        self.info.setText(f"Celkem {len(rows)} položek vyžaduje doplnění." if rows else "✓ Vše je v pořádku.")
        self.table.setRowCount(0)
        for r in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(r['nazev']))
            self.table.setItem(row, 1, QTableWidgetItem(r['kategorie']))
            mnoz_item = QTableWidgetItem(str(r['mnozstvi_na_sklade']))
            mnoz_item.setForeground(QColor("#c0392b"))
            self.table.setItem(row, 2, mnoz_item)
            self.table.setItem(row, 3, QTableWidgetItem(str(r['min_mnozstvi'])))
            chybi_item = QTableWidgetItem(str(r['chybi']))
            chybi_item.setForeground(QColor("#c0392b"))
            self.table.setItem(row, 4, chybi_item)


# ── Reporty ────────────────────────────────────────────────

class ReportyScreen(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = QLabel("Reporty")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Medium))
        layout.addWidget(title)

        # Výběr období
        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("Od:"))
        self.datum_od = QDateEdit(QDate.currentDate().addMonths(-1))
        self.datum_od.setCalendarPopup(True)
        toolbar.addWidget(self.datum_od)

        toolbar.addWidget(QLabel("Do:"))
        self.datum_do = QDateEdit(QDate.currentDate())
        self.datum_do.setCalendarPopup(True)
        toolbar.addWidget(self.datum_do)

        btn_load = QPushButton("Načíst")
        btn_load.clicked.connect(self.refresh)
        toolbar.addWidget(btn_load)

        btn_export = QPushButton("⬇  Export CSV")
        btn_export.clicked.connect(self.export_csv)
        toolbar.addWidget(btn_export)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Statistiky
        self.stats = QLabel()
        self.stats.setStyleSheet("font-size: 13px; color: #555;")
        layout.addWidget(self.stats)

        # Tabulka
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Datum", "Zboží", "Typ", "Množství", "Partner", "Poznámka"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        self.rows = []
        self.refresh()

    def refresh(self):
        datum_od = self.datum_od.date().toPyDate()
        datum_do = self.datum_do.date().toPyDate()
        self.rows = mp.get_report(datum_od, datum_do)

        prijmy = sum(1 for r in self.rows if r['typ'] == 'prijem')
        vydeje = sum(1 for r in self.rows if r['typ'] == 'vydej')
        self.stats.setText(f"Celkem: {len(self.rows)} pohybů  |  Příjmy: {prijmy}  |  Výdeje: {vydeje}")

        self.table.setRowCount(0)
        for r in self.rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            datum = r['datum']
            self.table.setItem(row, 0, QTableWidgetItem(datum.strftime("%d.%m.%Y %H:%M") if datum else ""))
            self.table.setItem(row, 1, QTableWidgetItem(r['zbozi'] or ""))
            typ = r['typ']
            typ_item = QTableWidgetItem("příjem" if typ == "prijem" else "výdej")
            typ_item.setForeground(QColor("#1a7a4a") if typ == "prijem" else QColor("#c0392b"))
            self.table.setItem(row, 2, typ_item)
            self.table.setItem(row, 3, QTableWidgetItem(f"{r['mnozstvi']} {r['jednotka']}"))
            partner = r.get('dodavatel') or r.get('odberatel') or ""
            self.table.setItem(row, 4, QTableWidgetItem(partner))
            self.table.setItem(row, 5, QTableWidgetItem(r['poznamka'] or ""))

    def export_csv(self):
        if not self.rows:
            QMessageBox.information(self, "Export", "Žádná data k exportu.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Uložit CSV", "report.csv", "CSV (*.csv)")
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["Datum", "Zboží", "Typ", "Množství", "Jednotka", "Partner", "Poznámka"])
            for r in self.rows:
                datum = r['datum']
                partner = r.get('dodavatel') or r.get('odberatel') or ""
                writer.writerow([
                    datum.strftime("%d.%m.%Y %H:%M") if datum else "",
                    r['zbozi'], r['typ'], r['mnozstvi'], r['jednotka'],
                    partner, r['poznamka'] or ""
                ])
        QMessageBox.information(self, "Export", f"Soubor uložen:\n{path}")
