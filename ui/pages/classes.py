# ui/pages/classes.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                              QGridLayout, QFrame, QLabel, QMessageBox)
from PyQt6.QtCore import Qt
from database.db_manager import DatabaseManager
from dialogs.classe_dialog import ClasseDialog

class ClasseCard(QFrame):
    def __init__(self, classe_id, nom, nb_eleves, moyenne, nb_devoirs, parent_page):
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
        
        devoirs_label = QLabel(f"📝 {nb_devoirs} devoirs")
        devoirs_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        devoirs_label.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(devoirs_label)
        
        buttons_layout = QHBoxLayout()
        
        edit_btn = QPushButton("✏️")
        edit_btn.setToolTip("Modifier la classe")
        edit_btn.clicked.connect(self.edit_classe)
        buttons_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("🗑️")
        delete_btn.setToolTip("Supprimer la classe")
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
        
        # Bouton de rafraîchissement
        refresh_btn = QPushButton("🔄 Rafraîchir")
        refresh_btn.setToolTip("Recharger les données depuis la base de données")
        refresh_btn.clicked.connect(self.force_refresh)
        header.addWidget(refresh_btn)
        
        add_btn = QPushButton("➕ Créer une classe")
        add_btn.setObjectName("primary-button")
        add_btn.clicked.connect(self.add_classe)
        header.addWidget(add_btn)
        
        layout.addLayout(header)
        
        # Info label
        self.info_label = QLabel("")
        self.info_label.setStyleSheet("color: #666; font-size: 11px; margin-top: 5px;")
        layout.addWidget(self.info_label)
        
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(20)
        layout.addLayout(self.grid_layout)
        
        layout.addStretch()
        
        self.load_data()
    
    def force_refresh(self):
        """Force le rafraîchissement complet des données depuis la base"""
        # Recharger les données
        self.load_data()
        
        # Message de confirmation
        self.info_label.setText("✅ Données rafraîchies depuis la base de données")
        
        # Effacer le message après 3 secondes
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(3000, lambda: self.info_label.setText(""))
    
    def load_data(self):
        # Nettoyer la grille
        for i in reversed(range(self.grid_layout.count())): 
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        # Charger les classes avec leurs stats EN TEMPS RÉEL
        classes = self.db.get_all_classes()
        
        row = 0
        col = 0
        max_cols = 3
        
        for classe in classes:
            # Les stats sont recalculées à chaque fois depuis la base
            stats = self.db.get_classe_stats(classe['id'])
            
            card = ClasseCard(
                classe['id'],
                classe['nom'],
                stats['nb_eleves'],
                stats['moyenne'],
                stats['nb_devoirs'],
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
        """Recharge les données à chaque affichage de la page"""
        super().showEvent(event)
        self.load_data()