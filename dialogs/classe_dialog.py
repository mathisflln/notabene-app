# dialogs/classe_dialog.py
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit,
                              QPushButton, QHBoxLayout, QMessageBox)
from database.db_manager import DatabaseManager

class ClasseDialog(QDialog):
    def __init__(self, parent=None, classe_id=None):
        super().__init__(parent)
        self.db = DatabaseManager()
        self.classe_id = classe_id
        
        self.setWindowTitle("Créer une classe" if classe_id is None else "Modifier une classe")
        self.setMinimumWidth(400)
        
        self.init_ui()
        
        if classe_id:
            self.load_classe_data()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        form = QFormLayout()
        
        self.nom_input = QLineEdit()
        form.addRow("Nom de la classe *", self.nom_input)
        
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
    
    def load_classe_data(self):
        classe = self.db.get_classe(self.classe_id)
        
        if classe:
            self.nom_input.setText(classe['nom'])
    
    def save(self):
        nom = self.nom_input.text().strip()
        
        if not nom:
            QMessageBox.warning(self, "Erreur", "Le nom de la classe est obligatoire")
            return
        
        try:
            if self.classe_id is None:
                self.db.add_classe(nom)
            else:
                self.db.update_classe(self.classe_id, nom)
            
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la sauvegarde : {str(e)}")