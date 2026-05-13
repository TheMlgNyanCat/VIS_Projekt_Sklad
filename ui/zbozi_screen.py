from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QDialog, QFormLayout, QDoubleSpinBox,
    QSpinBox, QMessageBox, QDialogButtonBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
import models.zbozi as mz
import models.partneri as mp


class ZboziDialog(QDialog):
    def __init__(self, parent, kategorie, data=None):
        super().__init__(parent)
        self.setWindowTitle("Přidat zboží" if not data else "Upravit zboží")
        self.setMinimumWidth(360)
        self.kategorie = kategorie

        layout = QFormLayout(self)
        layout.setSpacing(10)

        self.nazev = QLineEdit(data['nazev'] if data else "")
        layout.addRow("Název:", self.nazev)

        self.kategorie_cb = QComboBox()
        for k in kategorie:
            self.kategorie_cb.addItem(k['nazev'], k['id'])
        if data:
            idx = next((i for i, k in enumerate(kategorie) if k['id'] == data['kategorie_id']), 0)
            self.kategorie_cb.setCurrentIndex(idx)
        layout.addRow("Kategorie:", self.kategorie_cb)

        self.jednotka = QComboBox()
        self.jednotka.addItems(["ks", "kg", "l", "m", "m²", "bal"])
        self.jednotka.setEditable(True)
        if data:
            self.jednotka.setCurrentText(data['jednotka'])
        layout.addRow("Jednotka:", self.jednotka)

        self.min_mnozstvi = QSpinBox()
        self.min_mnozstvi.setRange(0, 999999)
        self.min_mnozstvi.setValue(data['min_mnozstvi'] if data else 0)
        layout.addRow("Minimální stav:", self.min_mnozstvi)

        self.cena = QDoubleSpinBox()
        self.cena.setRange(0, 9999999)
        self.cena.setDecimals(2)
        self.cena.setSuffix(" Kč")
        self.cena.setValue(float(data['cena_za_jednotku']) if data else 0)
        layout.addRow("Cena / jednotku:", self.cena)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addRow(btns)

    def get_data(self):
        return {
            "nazev":           self.nazev.text().strip(),
            "kategorie_id":    self.kategorie_cb.currentData(),
            "jednotka":        self.jednotka.currentText(),
            "min_mnozstvi":    self.min_mnozstvi.value(),
            "cena_za_jednotku": self.cena.value(),
        }


class ZboziScreen(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = QLabel("Zboží")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Medium))
        layout.addWidget(title)

        # Toolbar
        toolbar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Hledat zboží…")
        self.search.textChanged.connect(self.refresh)
        toolbar.addWidget(self.search)

        self.kat_filter = QComboBox()
        self.kat_filter.setFixedWidth(160)
        self.kat_filter.currentIndexChanged.connect(self.refresh)
        toolbar.addWidget(self.kat_filter)

        btn_add = QPushButton("＋  Přidat zboží")
        btn_add.clicked.connect(self.add_zbozi)
        toolbar.addWidget(btn_add)
        layout.addLayout(toolbar)

        # Tabulka
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Název", "Kategorie", "Na skladě", "Min. stav", "Jednotka", "Cena/j.", ""])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setColumnWidth(6, 80)
        layout.addWidget(self.table)
        self.table.cellDoubleClicked.connect(self._on_double_click)

        self._load_kategorie()
        self.refresh()

    def _load_kategorie(self):
        self.kategorie = mp.get_all_kategorie()
        self.kat_filter.clear()
        self.kat_filter.addItem("Všechny kategorie", None)
        for k in self.kategorie:
            self.kat_filter.addItem(k['nazev'], k['id'])

    def refresh(self):
        search = self.search.text()
        kid = self.kat_filter.currentData()
        rows = mz.get_all(search=search, kategorie_id=kid)
        self.table.setRowCount(0)
        for r in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(r['nazev']))
            self.table.setItem(row, 1, QTableWidgetItem(r['kategorie']))
            mnoz = r['mnozstvi_na_sklade']
            mnoz_item = QTableWidgetItem(str(mnoz))
            if mnoz <= r['min_mnozstvi']:
                mnoz_item.setForeground(QColor("#c0392b"))
            self.table.setItem(row, 2, mnoz_item)
            self.table.setItem(row, 3, QTableWidgetItem(str(r['min_mnozstvi'])))
            self.table.setItem(row, 4, QTableWidgetItem(r['jednotka']))
            self.table.setItem(row, 5, QTableWidgetItem(f"{float(r['cena_za_jednotku']):.2f} Kč"))
            btn = QPushButton("Upravit")
            btn.clicked.connect(lambda _, rid=r['id']: self.edit_zbozi(rid))
            self.table.setCellWidget(row, 6, btn)

    def add_zbozi(self):
        dlg = ZboziDialog(self, self.kategorie)
        if dlg.exec():
            d = dlg.get_data()
            if not d['nazev']:
                QMessageBox.warning(self, "Chyba", "Název nesmí být prázdný.")
                return
            mz.create(d['kategorie_id'], d['nazev'], d['jednotka'], d['min_mnozstvi'], d['cena_za_jednotku'])
            self.refresh()

    def edit_zbozi(self, zbozi_id):
        data = mz.get_by_id(zbozi_id)
        dlg = ZboziDialog(self, self.kategorie, data)
        if dlg.exec():
            d = dlg.get_data()
            mz.update(zbozi_id, d['kategorie_id'], d['nazev'], d['jednotka'], d['min_mnozstvi'], d['cena_za_jednotku'])
            self.refresh()

    def _on_double_click(self, row, col):
        zbozi_id = self.table.item(row, 0)
        if not zbozi_id:
            return
        
        btn = self.table.cellWidget(row, 6)
        if btn:
            btn.click()