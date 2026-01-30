# ui/pages/devoirs.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                              QLineEdit, QComboBox, QTableWidget, QTableWidgetItem,
                              QHeaderView, QMessageBox, QLabel)
from PyQt6.QtCore import Qt
from database.db_manager import DatabaseManager
from dialogs.devoir_dialog import DevoirDialog

class DevoirsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        
        title = QLabel("📝 Gestion des Devoirs")
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(title)
        
        toolbar = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Rechercher un devoir...")
        self.search_input.textChanged.connect(self.load_data)
        toolbar.addWidget(self.search_input)
        
        self.classe_filter = QComboBox()
        self.classe_filter.addItem("Toutes les classes", None)
        self.load_classes_filter()
        self.classe_filter.currentIndexChanged.connect(self.load_data)
        toolbar.addWidget(self.classe_filter)
        
        toolbar.addStretch()
        
        add_btn = QPushButton("➕ Créer un devoir")
        add_btn.setObjectName("primary-button")
        add_btn.clicked.connect(self.add_devoir)
        toolbar.addWidget(add_btn)
        
        layout.addLayout(toolbar)
        
        self.table = QTableWidget()
        self.setup_table()
        layout.addWidget(self.table)
        
        self.load_data()
    
    def setup_table(self):
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "Nom", "Date", "Classe", "Nb Questions", "Moyenne", "Correction", "Actions"
        ])
        
        self.table.setColumnHidden(0, True)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        self.table.doubleClicked.connect(self.edit_devoir)
    
    def load_classes_filter(self):
        classes = self.db.get_all_classes()
        for classe in classes:
            self.classe_filter.addItem(classe['nom'], classe['id'])
    
    def load_data(self):
        search_term = self.search_input.text()
        classe_id = self.classe_filter.currentData()
        
        devoirs = self.db.get_all_devoirs(classe_id, search_term)
        
        self.table.setRowCount(len(devoirs))
        
        for row, devoir in enumerate(devoirs):
            self.table.setItem(row, 0, QTableWidgetItem(str(devoir['id'])))
            self.table.setItem(row, 1, QTableWidgetItem(devoir['nom']))
            self.table.setItem(row, 2, QTableWidgetItem(devoir['date']))
            self.table.setItem(row, 3, QTableWidgetItem(devoir['classe_nom']))
            
            nb_q = QTableWidgetItem(str(devoir['nb_questions']))
            nb_q.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 4, nb_q)
            
            moyenne = devoir['moyenne']
            moyenne_text = f"{moyenne:.2f}/20" if moyenne else "N/A"
            moyenne_item = QTableWidgetItem(moyenne_text)
            moyenne_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 5, moyenne_item)
            
            nb_corriges = devoir['nb_corriges']
            nb_total = devoir['nb_eleves_total']
            correction_text = f"{nb_corriges}/{nb_total}"
            correction_item = QTableWidgetItem(correction_text)
            correction_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 6, correction_item)
            
            actions_widget = self.create_actions_widget(devoir['id'])
            self.table.setCellWidget(row, 7, actions_widget)
    
    def create_actions_widget(self, devoir_id):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 0, 5, 0)
        
        edit_btn = QPushButton("✏️")
        edit_btn.setFixedSize(30, 30)
        edit_btn.clicked.connect(lambda: self.edit_devoir_by_id(devoir_id))
        layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("🗑️")
        delete_btn.setFixedSize(30, 30)
        delete_btn.clicked.connect(lambda: self.delete_devoir(devoir_id))
        layout.addWidget(delete_btn)
        
        return widget
    
    def add_devoir(self):
        dialog = DevoirDialog(self)
        if dialog.exec():
            self.load_data()
    
    def edit_devoir(self):
        current_row = self.table.currentRow()
        if current_row >= 0:
            devoir_id = int(self.table.item(current_row, 0).text())
            self.edit_devoir_by_id(devoir_id)
    
    def edit_devoir_by_id(self, devoir_id):
        dialog = DevoirDialog(self, devoir_id)
        if dialog.exec():
            self.load_data()
    
    def delete_devoir(self, devoir_id):
        reply = QMessageBox.question(
            self,
            "Confirmer la suppression",
            "Êtes-vous sûr de vouloir supprimer ce devoir ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success, message = self.db.delete_devoir(devoir_id)
            
            if success:
                QMessageBox.information(self, "Succès", message)
                self.load_data()
            else:
                QMessageBox.warning(self, "Erreur", message)
    
    def showEvent(self, event):
        super().showEvent(event)
        self.load_data()