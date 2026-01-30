# ui/pages/eleves.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                              QLineEdit, QComboBox, QTableWidget, QTableWidgetItem, 
                              QHeaderView, QMessageBox, QLabel)
from PyQt6.QtCore import Qt
from database.db_manager import DatabaseManager
from dialogs.eleve_dialog import EleveDialog

class ElevesPage(QWidget):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        
        title = QLabel("👥 Gestion des Élèves")
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(title)
        
        toolbar = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Rechercher un élève...")
        self.search_input.textChanged.connect(self.load_data)
        toolbar.addWidget(self.search_input)
        
        self.classe_filter = QComboBox()
        self.classe_filter.addItem("Toutes les classes", None)
        self.load_classes_filter()
        self.classe_filter.currentIndexChanged.connect(self.load_data)
        toolbar.addWidget(self.classe_filter)
        
        toolbar.addStretch()
        
        add_btn = QPushButton("➕ Ajouter un élève")
        add_btn.setObjectName("primary-button")
        add_btn.clicked.connect(self.add_eleve)
        toolbar.addWidget(add_btn)
        
        layout.addLayout(toolbar)
        
        self.table = QTableWidget()
        self.setup_table()
        layout.addWidget(self.table)
        
        self.load_data()
    
    def setup_table(self):
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID", "Nom", "Prénom", "Classe", "Moyenne", "Actions"
        ])
        
        self.table.setColumnHidden(0, True)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        self.table.doubleClicked.connect(self.edit_eleve)
    
    def load_classes_filter(self):
        classes = self.db.get_all_classes()
        for classe in classes:
            self.classe_filter.addItem(classe['nom'], classe['id'])
    
    def load_data(self):
        search_term = self.search_input.text()
        classe_id = self.classe_filter.currentData()
        
        eleves = self.db.get_all_eleves(classe_id, search_term)
        
        self.table.setRowCount(len(eleves))
        
        for row, eleve in enumerate(eleves):
            self.table.setItem(row, 0, QTableWidgetItem(str(eleve['id'])))
            self.table.setItem(row, 1, QTableWidgetItem(eleve['nom']))
            self.table.setItem(row, 2, QTableWidgetItem(eleve['prenom']))
            
            classe_item = QTableWidgetItem(eleve['classe_nom'] or "Sans classe")
            self.table.setItem(row, 3, classe_item)
            
            moyenne = self.db.get_moyenne_eleve(eleve['id'])
            moyenne_item = QTableWidgetItem(f"{moyenne:.2f}")
            moyenne_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 4, moyenne_item)
            
            actions_widget = self.create_actions_widget(eleve['id'])
            self.table.setCellWidget(row, 5, actions_widget)
    
    def create_actions_widget(self, eleve_id):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 0, 5, 0)
        
        edit_btn = QPushButton("✏️")
        edit_btn.setFixedSize(30, 30)
        edit_btn.clicked.connect(lambda: self.edit_eleve_by_id(eleve_id))
        layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("🗑️")
        delete_btn.setFixedSize(30, 30)
        delete_btn.clicked.connect(lambda: self.delete_eleve(eleve_id))
        layout.addWidget(delete_btn)
        
        return widget
    
    def add_eleve(self):
        dialog = EleveDialog(self)
        if dialog.exec():
            self.load_data()
    
    def edit_eleve(self):
        current_row = self.table.currentRow()
        if current_row >= 0:
            eleve_id = int(self.table.item(current_row, 0).text())
            self.edit_eleve_by_id(eleve_id)
    
    def edit_eleve_by_id(self, eleve_id):
        dialog = EleveDialog(self, eleve_id)
        if dialog.exec():
            self.load_data()
    
    def delete_eleve(self, eleve_id):
        reply = QMessageBox.question(
            self, 
            "Confirmer la suppression",
            "Êtes-vous sûr de vouloir supprimer cet élève ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success, message = self.db.delete_eleve(eleve_id)
            
            if success:
                QMessageBox.information(self, "Succès", message)
                self.load_data()
            else:
                QMessageBox.warning(self, "Erreur", message)
    
    def showEvent(self, event):
        super().showEvent(event)
        self.load_data()