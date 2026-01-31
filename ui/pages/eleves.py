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
        
        # Bouton de rafraîchissement
        refresh_btn = QPushButton("🔄 Rafraîchir")
        refresh_btn.setToolTip("Recharger les données depuis la base de données")
        refresh_btn.clicked.connect(self.force_refresh)
        toolbar.addWidget(refresh_btn)
        
        toolbar.addStretch()
        
        add_btn = QPushButton("➕ Ajouter un élève")
        add_btn.setObjectName("primary-button")
        add_btn.clicked.connect(self.add_eleve)
        toolbar.addWidget(add_btn)
        
        layout.addLayout(toolbar)
        
        self.table = QTableWidget()
        self.setup_table()
        layout.addWidget(self.table)
        
        # Label d'info
        self.info_label = QLabel("")
        self.info_label.setStyleSheet("color: #666; font-size: 11px; margin-top: 5px;")
        layout.addWidget(self.info_label)
        
        self.load_data()
    
    def setup_table(self):
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "Nom", "Prénom", "Classe", "Moyenne", "Nb Devoirs", "Actions"
        ])
        
        self.table.setColumnHidden(0, True)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        self.table.doubleClicked.connect(self.edit_eleve)
    
    def load_classes_filter(self):
        self.classe_filter.clear()
        self.classe_filter.addItem("Toutes les classes", None)
        classes = self.db.get_all_classes()
        for classe in classes:
            self.classe_filter.addItem(classe['nom'], classe['id'])
    
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
        search_term = self.search_input.text()
        classe_id = self.classe_filter.currentData()
        
        # Les données sont maintenant TOUJOURS chargées en temps réel depuis la base
        eleves = self.db.get_all_eleves(classe_id, search_term)
        
        self.table.setRowCount(len(eleves))
        
        for row, eleve in enumerate(eleves):
            self.table.setItem(row, 0, QTableWidgetItem(str(eleve['id'])))
            self.table.setItem(row, 1, QTableWidgetItem(eleve['nom']))
            self.table.setItem(row, 2, QTableWidgetItem(eleve['prenom']))
            
            classe_item = QTableWidgetItem(eleve['classe_nom'] or "Sans classe")
            self.table.setItem(row, 3, classe_item)
            
            # Calculer la moyenne en temps réel depuis la base
            moyenne = self.db.get_moyenne_eleve(eleve['id'])
            moyenne_item = QTableWidgetItem(f"{moyenne:.2f}/20")
            moyenne_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Colorer selon la moyenne
            if moyenne >= 15:
                moyenne_item.setBackground(Qt.GlobalColor.green)
                moyenne_item.setForeground(Qt.GlobalColor.white)
            elif moyenne >= 10:
                moyenne_item.setBackground(Qt.GlobalColor.yellow)
            elif moyenne > 0:
                moyenne_item.setBackground(Qt.GlobalColor.red)
                moyenne_item.setForeground(Qt.GlobalColor.white)
            
            self.table.setItem(row, 4, moyenne_item)
            
            # Nombre de devoirs corrigés (calculé en temps réel)
            nb_devoirs = self.db.get_nb_devoirs_eleve(eleve['id'])
            nb_devoirs_item = QTableWidgetItem(str(nb_devoirs))
            nb_devoirs_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 5, nb_devoirs_item)
            
            actions_widget = self.create_actions_widget(eleve['id'])
            self.table.setCellWidget(row, 6, actions_widget)
    
    def create_actions_widget(self, eleve_id):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 0, 5, 0)
        
        edit_btn = QPushButton("✏️")
        edit_btn.setFixedSize(30, 30)
        edit_btn.setToolTip("Modifier l'élève")
        edit_btn.clicked.connect(lambda: self.edit_eleve_by_id(eleve_id))
        layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("🗑️")
        delete_btn.setFixedSize(30, 30)
        delete_btn.setToolTip("Supprimer l'élève")
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
        """Recharge les données à chaque affichage de la page"""
        super().showEvent(event)
        self.load_classes_filter()  # Recharger la liste des classes aussi
        self.load_data()