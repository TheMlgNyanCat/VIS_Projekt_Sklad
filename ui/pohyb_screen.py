from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QDialog, QFormLayout, QSpinBox,
    QMessageBox, QDialogButtonBox, QTextEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
import models.pohyb as mp
import models.zbozi as mz
import models.partneri as mpart
import psycopg2


class PohybDialog(QDialog):
    def __init__(self, parent, zbozi, dodavatele, odberatele):
        super().__init__(parent)
        self.setWindowTitle("Nový pohyb")
        self.setMinimumWidth(380)
        self.dodavatele = dodavatele
        self.odberatele = odberatele

        layout = QFormLayout(self)
        layout.setSpacing(10)

        self.typ = QComboBox()
        self.typ.addItems(["prijem", "vydej"])
        self.typ.currentTextChanged.connect(self._on_typ_change)
        layout.addRow("Typ pohybu:", self.typ)

        self.zbozi_cb = QComboBox()
        for z in zbozi:
            self.zbozi_cb.addItem(z['nazev'], z['id'])
        layout.addRow("Zboží:", self.zbozi_cb)

        self.mnozstvi = QSpinBox()
        self.mnozstvi.setRange(1, 999999)
        layout.addRow("Množství:", self.mnozstvi)

        self.partner_label = QLabel("Dodavatel:")
        self.partner_cb = QComboBox()
        layout.addRow(self.partner_label, self.partner_cb)

        self.poznamka = QTextEdit()
        self.poznamka.setFixedHeight(60)
        self.poznamka.setPlaceholderText("Volitelná poznámka…")
        layout.addRow("Poznámka:", self.poznamka)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addRow(btns)

        self._on_typ_change("prijem")

    def _on_typ_change(self, typ):
        self.partner_cb.clear()
        if typ == "prijem":
            self.partner_label.setText("Dodavatel:")
            for d in self.dodavatele:
                self.partner_cb.addItem(d['nazev'], d['id'])
        else:
            self.partner_label.setText("Odběratel:")
            for o in self.odberatele:
                self.partner_cb.addItem(o['nazev'], o['id'])

    def get_data(self):
        typ = self.typ.currentText()
        partner_id = self.partner_cb.currentData()
        return {
            "zbozi_id":     self.zbozi_cb.currentData(),
            "typ":          typ,
            "mnozstvi":     self.mnozstvi.value(),
            "dodavatel_id": partner_id if typ == "prijem" else None,
            "odberatel_id": partner_id if typ == "vydej" else None,
            "poznamka":     self.poznamka.toPlainText().strip(),
        }


class PohybScreen(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = QLabel("Pohyby skladu")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Medium))
        layout.addWidget(title)

        toolbar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Hledat podle zboží…")
        self.search.textChanged.connect(self.refresh)
        toolbar.addWidget(self.search)

        self.typ_filter = QComboBox()
        self.typ_filter.setFixedWidth(120)
        self.typ_filter.addItem("Vše", None)
        self.typ_filter.addItem("Příjem", "prijem")
        self.typ_filter.addItem("Výdej", "vydej")
        self.typ_filter.currentIndexChanged.connect(self.refresh)
        toolbar.addWidget(self.typ_filter)

        btn_add = QPushButton("＋  Nový pohyb")
        btn_add.clicked.connect(self.add_pohyb)
        toolbar.addWidget(btn_add)
        layout.addLayout(toolbar)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Datum", "Zboží", "Typ", "Množství", "Partner", "Poznámka"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)


        self.refresh()

    def refresh(self):
        search = self.search.text()
        typ = self.typ_filter.currentData()
        rows = mp.get_all(search=search, typ=typ)
        self.table.setRowCount(0)
        for r in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            datum = r['datum']
            self.table.setItem(row, 0, QTableWidgetItem(datum.strftime("%d.%m.%Y %H:%M") if datum else ""))
            self.table.setItem(row, 1, QTableWidgetItem(r['zbozi'] or ""))
            typ_val = r['typ']
            typ_item = QTableWidgetItem("příjem" if typ_val == "prijem" else "výdej")
            typ_item.setForeground(QColor("#1a7a4a") if typ_val == "prijem" else QColor("#c0392b"))
            self.table.setItem(row, 2, typ_item)
            self.table.setItem(row, 3, QTableWidgetItem(f"{r['mnozstvi']} {r['jednotka']}"))
            partner = r.get('dodavatel') or r.get('odberatel') or ""
            self.table.setItem(row, 4, QTableWidgetItem(partner))
            self.table.setItem(row, 5, QTableWidgetItem(r['poznamka'] or ""))

    def add_pohyb(self):
        zbozi = mz.get_all()
        dodavatele = mpart.get_all_dodavatele()
        odberatele = mpart.get_all_odberatele()
        if not zbozi:
            QMessageBox.warning(self, "Chyba", "Nejprve přidejte nějaké zboží.")
            return
        dlg = PohybDialog(self, zbozi, dodavatele, odberatele)
        if dlg.exec():
            d = dlg.get_data()
            try:
                mp.create(**d)
                self.refresh()
            except psycopg2.Error as e:
                QMessageBox.critical(self, "Chyba databáze", str(e))

