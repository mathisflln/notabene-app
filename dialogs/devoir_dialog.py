# dialogs/devoir_dialog.py
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit,
                              QComboBox, QPushButton, QHBoxLayout, QMessageBox,
                              QDateEdit, QLabel, QScrollArea, QWidget, QDoubleSpinBox,
                              QFrame)
from PyQt6.QtCore import QDate, Qt
from database.db_manager import DatabaseManager

class QuestionWidget(QFrame):
    def __init__(self, numero="", intitule="", points_max=0, coefficient=1, parent_dialog=None):
        super().__init__()
        self.parent_dialog = parent_dialog
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setStyleSheet("QFrame { background-color: white; border: 1px solid #ddd; border-radius: 5px; padding: 10px; margin: 5px; }")
        
        layout = QVBoxLayout(self)
        
        header = QHBoxLayout()
        header.addWidget(QLabel("Question"))
        header.addStretch()
        
        delete_btn = QPushButton("🗑️")
        delete_btn.setFixedSize(30, 30)
        delete_btn.clicked.connect(self.delete_question)
        header.addWidget(delete_btn)
        
        layout.addLayout(header)
        
        form = QFormLayout()
        
        self.numero_input = QLineEdit(numero)
        self.numero_input.setPlaceholderText("Ex: 1, 1.a, 2.1...")
        form.addRow("Numéro:", self.numero_input)
        
        self.intitule_input = QLineEdit(intitule)
        self.intitule_input.setPlaceholderText("Intitulé de la question")
        form.addRow("Intitulé:", self.intitule_input)
        
        self.points_input = QDoubleSpinBox()
        self.points_input.setRange(0, 1000)
        self.points_input.setValue(points_max)
        self.points_input.setSingleStep(0.5)
        self.points_input.valueChanged.connect(self.update_parent_total)
        form.addRow("Points max:", self.points_input)
        
        self.coef_input = QDoubleSpinBox()
        self.coef_input.setRange(0.1, 10)
        self.coef_input.setValue(coefficient)
        self.coef_input.setSingleStep(0.1)
        self.coef_input.valueChanged.connect(self.update_parent_total)
        form.addRow("Coefficient:", self.coef_input)
        
        layout.addLayout(form)
    
    def delete_question(self):
        if self.parent_dialog:
            self.parent_dialog.remove_question_widget(self)
    
    def update_parent_total(self):
        if self.parent_dialog:
            self.parent_dialog.update_bareme_total()
    
    def get_data(self):
        return {
            'numero': self.numero_input.text().strip(),
            'intitule': self.intitule_input.text().strip(),
            'points_max': self.points_input.value(),
            'coefficient': self.coef_input.value()
        }

class DevoirDialog(QDialog):
    def __init__(self, parent=None, devoir_id=None):
        super().__init__(parent)
        self.db = DatabaseManager()
        self.devoir_id = devoir_id
        self.question_widgets = []
        
        self.setWindowTitle("Créer un devoir" if devoir_id is None else "Modifier un devoir")
        self.setMinimumSize(800, 600)
        
        self.init_ui()
        
        if devoir_id:
            self.load_devoir_data()
    
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Informations générales
        info_group = QVBoxLayout()
        info_label = QLabel("Informations générales")
        info_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 10px;")
        info_group.addWidget(info_label)
        
        form = QFormLayout()
        
        self.nom_input = QLineEdit()
        form.addRow("Nom du devoir *", self.nom_input)
        
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setDisplayFormat("dd/MM/yyyy")
        form.addRow("Date *", self.date_input)
        
        self.classe_combo = QComboBox()
        self.load_classes()
        form.addRow("Classe *", self.classe_combo)
        
        info_group.addLayout(form)
        main_layout.addLayout(info_group)
        
        # Section barème
        bareme_label = QLabel("Construction du barème")
        bareme_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 20px;")
        main_layout.addWidget(bareme_label)
        
        add_question_btn = QPushButton("➕ Ajouter une question")
        add_question_btn.clicked.connect(self.add_question)
        main_layout.addWidget(add_question_btn)
        
        # Zone scrollable pour les questions
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(300)
        
        self.questions_container = QWidget()
        self.questions_layout = QVBoxLayout(self.questions_container)
        self.questions_layout.addStretch()
        
        scroll.setWidget(self.questions_container)
        main_layout.addWidget(scroll)
        
        # Récapitulatif
        self.total_label = QLabel("📊 Total: 0 questions | 0 points")
        self.total_label.setStyleSheet("font-weight: bold; font-size: 13px; margin-top: 10px;")
        main_layout.addWidget(self.total_label)
        
        # Boutons
        buttons = QHBoxLayout()
        
        save_btn = QPushButton("💾 Enregistrer")
        save_btn.setObjectName("primary-button")
        save_btn.clicked.connect(self.save)
        buttons.addWidget(save_btn)
        
        cancel_btn = QPushButton("❌ Annuler")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(cancel_btn)
        
        main_layout.addLayout(buttons)
    
    def load_classes(self):
        classes = self.db.get_all_classes()
        for classe in classes:
            self.classe_combo.addItem(classe['nom'], classe['id'])
    
    def add_question(self, numero="", intitule="", points_max=0, coefficient=1):
        question_widget = QuestionWidget(numero, intitule, points_max, coefficient, self)
        self.question_widgets.append(question_widget)
        
        # Insérer avant le stretch
        self.questions_layout.insertWidget(len(self.question_widgets) - 1, question_widget)
        self.update_bareme_total()
    
    def remove_question_widget(self, widget):
        self.question_widgets.remove(widget)
        widget.deleteLater()
        self.update_bareme_total()
    
    def update_bareme_total(self):
        total_questions = len(self.question_widgets)
        total_points = sum(q.points_input.value() * q.coef_input.value() for q in self.question_widgets)
        
        self.total_label.setText(f"📊 Total: {total_questions} questions | {total_points:.1f} points")
    
    def load_devoir_data(self):
        devoir = self.db.get_devoir(self.devoir_id)
        
        if devoir:
            self.nom_input.setText(devoir['nom'])
            
            date = QDate.fromString(devoir['date'], "yyyy-MM-dd")
            if not date.isValid():
                date = QDate.fromString(devoir['date'], "dd/MM/yyyy")
            self.date_input.setDate(date)
            
            index = self.classe_combo.findData(devoir['id_classe'])
            if index >= 0:
                self.classe_combo.setCurrentIndex(index)
        
        # Charger les questions
        questions = self.db.get_questions_devoir(self.devoir_id)
        for q in questions:
            self.add_question(q['numero'], q['intitule'], q['points_max'], q['coefficient'])
    
    def save(self):
        nom = self.nom_input.text().strip()
        date = self.date_input.date().toString("yyyy-MM-dd")
        classe_id = self.classe_combo.currentData()
        
        if not nom:
            QMessageBox.warning(self, "Erreur", "Le nom du devoir est obligatoire")
            return
        
        if classe_id is None:
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner une classe")
            return
        
        if len(self.question_widgets) == 0:
            QMessageBox.warning(self, "Erreur", "Veuillez ajouter au moins une question")
            return
        
        # Valider les questions
        for i, q_widget in enumerate(self.question_widgets):
            data = q_widget.get_data()
            if not data['numero'] or not data['intitule']:
                QMessageBox.warning(self, "Erreur", f"La question {i+1} est incomplète")
                return
        
        try:
            if self.devoir_id is None:
                # Créer le devoir
                devoir_id = self.db.add_devoir(nom, date, classe_id)
            else:
                # Modifier le devoir
                devoir_id = self.devoir_id
                self.db.update_devoir(devoir_id, nom, date)
                
                # Supprimer les anciennes questions
                old_questions = self.db.get_questions_devoir(devoir_id)
                for q in old_questions:
                    self.db.delete_question(q['id'])
            
            # Ajouter les questions
            for q_widget in self.question_widgets:
                data = q_widget.get_data()
                self.db.add_question(
                    devoir_id,
                    data['numero'],
                    data['intitule'],
                    data['points_max'],
                    data['coefficient']
                )
            
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la sauvegarde : {str(e)}")