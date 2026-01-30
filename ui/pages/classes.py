# ui/pages/classes.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                              QGridLayout, QFrame, QLabel, QMessageBox)
from PyQt6.QtCore import Qt
from database.db_manager import DatabaseManager
from dialogs.classe_dialog import ClasseDialog

class ClasseCard(QFrame):
    def __init__(self, classe_id, nom, nb_eleves, moyenne, parent_page):
        super().__init__()
        self.classe_id = classe_id
        self.parent_page = parent_page
        self.setObjectName("stat-card")
        
        layout = QVBoxLayout(self)
        
        nom_label = QLabel(nom)
        nom_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        nom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(nom_label)
        
        eleves_label = QLabel(f"👥 {nb_eleves} élèves")
        eleves_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(eleves_label)
        
        moyenne_label = QLabel(f"📊 Moyenne: {moyenne:.2f}/20")
        moyenne_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(moyenne_label)
        
        buttons_layout = QHBoxLayout()
        
        edit_btn = QPushButton("✏️")
        edit_btn.clicked.connect(self.edit_classe)
        buttons_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("🗑️")
        delete_btn.clicked.connect(self.delete_classe)
        buttons_layout.addWidget(delete_btn)
        
        layout.addLayout(buttons_layout)
    
    def edit_classe(self):
        self.parent_page.edit_classe(self.classe_id)
    
    def delete_classe(self):
        self.parent_page.delete_classe(self.classe_id)

class ClassesPage(QWidget):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        
        header = QHBoxLayout()
        
        title = QLabel("🏫 Gestion des Classes")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        header.addWidget(title)
        
        header.addStretch()
        
        add_btn = QPushButton("➕ Créer une classe")
        add_btn.setObjectName("primary-button")
        add_btn.clicked.connect(self.add_classe)
        header.addWidget(add_btn)
        
        layout.addLayout(header)
        
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(20)
        layout.addLayout(self.grid_layout)
        
        layout.addStretch()
        
        self.load_data()
    
    def load_data(self):
        # Nettoyer la grille
        for i in reversed(range(self.grid_layout.count())): 
            self.grid_layout.itemAt(i).widget().setParent(None)
        
        classes = self.db.get_all_classes()
        
        row = 0
        col = 0
        max_cols = 3
        
        for classe in classes:
            stats = self.db.get_classe_stats(classe['id'])
            
            card = ClasseCard(
                classe['id'],
                classe['nom'],
                stats['nb_eleves'],
                stats['moyenne'],
                self
            )
            
            self.grid_layout.addWidget(card, row, col)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
    
    def add_classe(self):
        dialog = ClasseDialog(self)
        if dialog.exec():
            self.load_data()
    
    def edit_classe(self, classe_id):
        dialog = ClasseDialog(self, classe_id)
        if dialog.exec():
            self.load_data()
    
    def delete_classe(self, classe_id):
        reply = QMessageBox.question(
            self,
            "Confirmer la suppression",
            "Êtes-vous sûr de vouloir supprimer cette classe ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success, message = self.db.delete_classe(classe_id)
            
            if success:
                QMessageBox.information(self, "Succès", message)
                self.load_data()
            else:
                QMessageBox.warning(self, "Erreur", message)
    
    def showEvent(self, event):
        super().showEvent(event)
        self.load_data()