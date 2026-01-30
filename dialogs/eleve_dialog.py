# dialogs/eleve_dialog.py
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
                              QComboBox, QPushButton, QHBoxLayout, QMessageBox)
from database.db_manager import DatabaseManager

class EleveDialog(QDialog):
    def __init__(self, parent=None, eleve_id=None):
        super().__init__(parent)
        self.db = DatabaseManager()
        self.eleve_id = eleve_id
        
        self.setWindowTitle("Ajouter un élève" if eleve_id is None else "Modifier un élève")
        self.setMinimumWidth(400)
        
        self.init_ui()
        
        if eleve_id:
            self.load_eleve_data()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        form = QFormLayout()
        
        self.nom_input = QLineEdit()
        form.addRow("Nom *", self.nom_input)
        
        self.prenom_input = QLineEdit()
        form.addRow("Prénom *", self.prenom_input)
        
        self.classe_combo = QComboBox()
        self.load_classes()
        form.addRow("Classe *", self.classe_combo)
        
        layout.addLayout(form)
        
        buttons = QHBoxLayout()
        
        save_btn = QPushButton("💾 Enregistrer")
        save_btn.setObjectName("primary-button")
        save_btn.clicked.connect(self.save)
        buttons.addWidget(save_btn)
        
        cancel_btn = QPushButton("❌ Annuler")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(cancel_btn)
        
        layout.addLayout(buttons)
    
    def load_classes(self):
        classes = self.db.get_all_classes()
        for classe in classes:
            self.classe_combo.addItem(classe['nom'], classe['id'])
    
    def load_eleve_data(self):
        eleve = self.db.get_eleve(self.eleve_id)
        
        if eleve:
            self.nom_input.setText(eleve['nom'])
            self.prenom_input.setText(eleve['prenom'])
            
            index = self.classe_combo.findData(eleve['id_classe'])
            if index >= 0:
                self.classe_combo.setCurrentIndex(index)
    
    def save(self):
        nom = self.nom_input.text().strip()
        prenom = self.prenom_input.text().strip()
        classe_id = self.classe_combo.currentData()
        
        if not nom or not prenom:
            QMessageBox.warning(self, "Erreur", "Le nom et le prénom sont obligatoires")
            return
        
        if classe_id is None:
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner une classe")
            return
        
        try:
            if self.eleve_id is None:
                self.db.add_eleve(nom, prenom, classe_id)
            else:
                self.db.update_eleve(self.eleve_id, nom, prenom, classe_id)
            
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la sauvegarde : {str(e)}")