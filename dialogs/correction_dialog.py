# dialogs/correction_dialog.py
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                              QListWidget, QListWidgetItem, QScrollArea, QWidget,
                              QDoubleSpinBox, QTextEdit, QPushButton, QFrame,
                              QMessageBox, QProgressBar, QLineEdit)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from database.db_manager import DatabaseManager

class QuestionNoteWidget(QFrame):
    """Widget pour saisir la note d'une question"""
    noteChanged = pyqtSignal()
    
    def __init__(self, question, points_obtenus=None, commentaire=""):
        super().__init__()
        self.question = question
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 10px;
                margin: 5px;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # Header avec numéro et intitulé
        header = QLabel(f"Q{question['numero']} : {question['intitule']}")
        header.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(header)
        
        # Zone de saisie de points
        points_layout = QHBoxLayout()
        
        points_layout.addWidget(QLabel("Points obtenus:"))
        
        self.spinbox = QDoubleSpinBox()
        self.spinbox.setRange(0, question['points_max'])
        self.spinbox.setSingleStep(0.25)
        self.spinbox.setDecimals(2)
        if points_obtenus is not None:
            self.spinbox.setValue(float(points_obtenus))
        self.spinbox.valueChanged.connect(self.on_value_changed)
        self.spinbox.valueChanged.connect(self.noteChanged.emit)
        points_layout.addWidget(self.spinbox)
        
        points_layout.addWidget(QLabel(f"/ {question['points_max']} pts"))
        
        # Boutons rapides
        btn_0 = QPushButton("0")
        btn_0.setFixedSize(30, 25)
        btn_0.clicked.connect(lambda: self.spinbox.setValue(0))
        points_layout.addWidget(btn_0)
        
        btn_half = QPushButton("½")
        btn_half.setFixedSize(30, 25)
        btn_half.clicked.connect(lambda: self.spinbox.setValue(question['points_max'] / 2))
        points_layout.addWidget(btn_half)
        
        btn_max = QPushButton("Max")
        btn_max.setFixedSize(40, 25)
        btn_max.clicked.connect(lambda: self.spinbox.setValue(question['points_max']))
        points_layout.addWidget(btn_max)
        
        points_layout.addStretch()
        
        layout.addLayout(points_layout)
        
        # Barre de progression visuelle
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setMaximumHeight(8)
        self.update_progress()
        layout.addWidget(self.progress_bar)
        
        # Commentaire pour la question
        self.commentaire_input = QLineEdit()
        self.commentaire_input.setPlaceholderText("Commentaire pour cette question (optionnel)")
        # IMPORTANT: Convertir None en chaîne vide
        self.commentaire_input.setText(commentaire if commentaire else "")
        layout.addWidget(self.commentaire_input)
    
    def on_value_changed(self):
        self.update_progress()
    
    def update_progress(self):
        """Met à jour la barre de progression et la couleur"""
        if self.question['points_max'] > 0:
            percentage = (self.spinbox.value() / self.question['points_max']) * 100
            self.progress_bar.setValue(int(percentage))
            
            # Couleur selon le pourcentage
            if percentage >= 75:
                color = "#4CAF50"  # Vert
            elif percentage >= 50:
                color = "#FFC107"  # Orange
            else:
                color = "#F44336"  # Rouge
            
            self.progress_bar.setStyleSheet(f"""
                QProgressBar {{
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    background-color: #f0f0f0;
                }}
                QProgressBar::chunk {{
                    background-color: {color};
                    border-radius: 3px;
                }}
            """)
    
    def get_points(self):
        return self.spinbox.value()
    
    def get_commentaire(self):
        """Retourne le commentaire (toujours une chaîne, jamais None)"""
        return self.commentaire_input.text().strip()

class EleveListItem(QListWidgetItem):
    """Item de liste pour un élève"""
    def __init__(self, eleve, is_corrected, note_finale=None):
        nom_complet = f"{eleve['nom']} {eleve['prenom']}"
        super().__init__(nom_complet)
        
        self.eleve_id = eleve['id']
        self.eleve_nom = nom_complet
        
        # Icône de statut
        if is_corrected:
            if note_finale is not None:
                self.setText(f"✅ {nom_complet} ({note_finale:.2f}/20)")
                self.setForeground(QColor("#4CAF50"))
            else:
                self.setText(f"✅ {nom_complet}")
        else:
            self.setText(f"⏳ {nom_complet}")
            self.setForeground(QColor("#999"))

class CorrectionDialog(QDialog):
    def __init__(self, parent=None, devoir_id=None):
        super().__init__(parent)
        self.devoir_id = devoir_id
        self.db = DatabaseManager()
        self.current_eleve_id = None
        self.question_widgets = []
        
        self.setWindowTitle("Interface de correction")
        self.setMinimumSize(1200, 800)
        
        # Charger les données
        self.devoir = self.db.get_devoir(devoir_id)
        self.questions = self.db.get_questions_devoir(devoir_id)
        self.eleves = self.db.get_eleves_classe_avec_notes(devoir_id)
        
        self.init_ui()
        
        # Charger le premier élève
        if len(self.eleves) > 0:
            self.load_eleve(0)
    
    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(0)
        
        # ========== COLONNE GAUCHE : Liste des élèves ==========
        left_panel = QFrame()
        left_panel.setObjectName("sidebar")
        left_panel.setFixedWidth(250)
        left_layout = QVBoxLayout(left_panel)
        
        # Titre
        titre_eleves = QLabel("👥 Élèves")
        titre_eleves.setStyleSheet("font-weight: bold; font-size: 14px; padding: 10px;")
        left_layout.addWidget(titre_eleves)
        
        # Progression globale
        self.progress_label = QLabel("0/0 corrigés")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(self.progress_label)
        
        self.global_progress = QProgressBar()
        self.global_progress.setMaximum(100)
        left_layout.addWidget(self.global_progress)
        
        # Liste des élèves
        self.eleve_list = QListWidget()
        self.eleve_list.currentRowChanged.connect(self.load_eleve)
        left_layout.addWidget(self.eleve_list)
        
        # Boutons de navigation
        nav_layout = QHBoxLayout()
        
        self.prev_btn = QPushButton("⬅️ Précédent")
        self.prev_btn.clicked.connect(self.previous_eleve)
        nav_layout.addWidget(self.prev_btn)
        
        self.next_btn = QPushButton("Suivant ➡️")
        self.next_btn.clicked.connect(self.next_eleve)
        nav_layout.addWidget(self.next_btn)
        
        left_layout.addLayout(nav_layout)
        
        main_layout.addWidget(left_panel)
        
        # ========== COLONNE CENTRALE : Saisie des notes ==========
        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)
        center_layout.setContentsMargins(20, 20, 20, 20)
        
        # Header élève
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: #3498db; color: white; border-radius: 8px; padding: 15px;")
        header_layout = QVBoxLayout(header_frame)
        
        self.eleve_name_label = QLabel("Sélectionnez un élève")
        self.eleve_name_label.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        header_layout.addWidget(self.eleve_name_label)
        
        self.note_finale_label = QLabel("Note: -/20")
        self.note_finale_label.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        header_layout.addWidget(self.note_finale_label)
        
        center_layout.addWidget(header_frame)
        
        # Zone scrollable pour les questions
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: #f5f5f5; }")
        
        self.questions_container = QWidget()
        self.questions_layout = QVBoxLayout(self.questions_container)
        self.questions_layout.setSpacing(10)
        
        scroll.setWidget(self.questions_container)
        center_layout.addWidget(scroll)
        
        # Zone d'appréciation
        appreciation_label = QLabel("💬 Appréciation générale")
        appreciation_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        center_layout.addWidget(appreciation_label)
        
        self.appreciation_text = QTextEdit()
        self.appreciation_text.setMaximumHeight(100)
        self.appreciation_text.setPlaceholderText("Commentaire pour cet élève...")
        center_layout.addWidget(self.appreciation_text)
        
        # Boutons templates d'appréciation
        templates_layout = QHBoxLayout()
        
        btn_excellent = QPushButton("✨ Excellent travail")
        btn_excellent.clicked.connect(lambda: self.appreciation_text.setText("Excellent travail ! Continuez ainsi."))
        templates_layout.addWidget(btn_excellent)
        
        btn_bien = QPushButton("👍 Bien")
        btn_bien.clicked.connect(lambda: self.appreciation_text.setText("Bon travail dans l'ensemble."))
        templates_layout.addWidget(btn_bien)
        
        btn_efforts = QPushButton("📚 À améliorer")
        btn_efforts.clicked.connect(lambda: self.appreciation_text.setText("Des efforts sont nécessaires. Revoyez les notions."))
        templates_layout.addWidget(btn_efforts)
        
        center_layout.addLayout(templates_layout)
        
        # Boutons d'action
        actions_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 Sauvegarder")
        save_btn.setObjectName("primary-button")
        save_btn.clicked.connect(self.save_current)
        actions_layout.addWidget(save_btn)
        
        save_next_btn = QPushButton("💾➡️ Sauvegarder et suivant")
        save_next_btn.setObjectName("primary-button")
        save_next_btn.clicked.connect(self.save_and_next)
        actions_layout.addWidget(save_next_btn)
        
        center_layout.addLayout(actions_layout)
        
        main_layout.addWidget(center_panel, stretch=1)
        
        # ========== COLONNE DROITE : Statistiques ==========
        right_panel = QFrame()
        right_panel.setFixedWidth(280)
        right_panel.setStyleSheet("background-color: white; border-left: 1px solid #ddd;")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(15, 15, 15, 15)
        
        # Titre
        stats_title = QLabel("📊 Statistiques du devoir")
        stats_title.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")
        right_layout.addWidget(stats_title)
        
        # Stats du devoir
        devoir_info = QLabel(f"<b>{self.devoir['nom']}</b><br>"
                            f"📅 {self.devoir['date']}<br>"
                            f"🏫 {self.devoir['classe_nom']}")
        devoir_info.setWordWrap(True)
        devoir_info.setStyleSheet("background-color: #ecf0f1; padding: 10px; border-radius: 5px;")
        right_layout.addWidget(devoir_info)
        
        right_layout.addSpacing(20)
        
        # Stats live
        self.stats_label = QLabel("Statistiques en cours...")
        self.stats_label.setWordWrap(True)
        self.stats_label.setStyleSheet("background-color: #e8f4f8; padding: 10px; border-radius: 5px; font-size: 12px;")
        right_layout.addWidget(self.stats_label)
        
        right_layout.addStretch()
        
        # Bouton fermer
        close_btn = QPushButton("❌ Fermer")
        close_btn.clicked.connect(self.accept)
        right_layout.addWidget(close_btn)
        
        main_layout.addWidget(right_panel)
        
        # Charger la liste des élèves
        self.refresh_eleve_list()
        self.update_global_progress()
        self.update_stats()
    
    def refresh_eleve_list(self):
        """Rafraîchit la liste des élèves avec leur statut"""
        self.eleve_list.clear()
        
        eleves_data = self.db.get_eleves_classe_avec_notes(self.devoir_id)
        
        for eleve in eleves_data:
            is_corrected = eleve['nb_notes_saisies'] == eleve['nb_questions_total']
            
            # Calculer la note finale si corrigé
            note_finale = None
            if is_corrected:
                note_finale = self.db.calculate_note_finale(eleve['id'], self.devoir_id)
            
            item = EleveListItem(eleve, is_corrected, note_finale)
            self.eleve_list.addItem(item)
    
    def load_eleve(self, index):
        """Charge les données d'un élève"""
        if index < 0 or index >= self.eleve_list.count():
            return
        
        item = self.eleve_list.item(index)
        if item is None:
            return
            
        self.current_eleve_id = item.eleve_id
        
        # Mettre à jour le header
        self.eleve_name_label.setText(f"📝 {item.eleve_nom}")
        
        # Charger les notes
        notes = self.db.get_notes_eleve_devoir(self.current_eleve_id, self.devoir_id)
        
        # Nettoyer simplement
        for widget in self.question_widgets:
            widget.deleteLater()
        self.question_widgets.clear()
        
        # Créer les widgets de question
        for note in notes:
            points = float(note['points_obtenus']) if note['points_obtenus'] is not None else 0.0
            # CORRECTION: Gérer correctement le commentaire (peut être None)
            commentaire = note['commentaire'] if note['commentaire'] is not None else ""
            widget = QuestionNoteWidget(note, points, commentaire)
            widget.noteChanged.connect(self.update_note_finale)
            self.questions_layout.addWidget(widget)
            self.question_widgets.append(widget)
        
        # Charger l'appréciation globale depuis la table compte_rendus
        compte_rendu = self.db.get_compte_rendu(self.devoir_id, self.current_eleve_id)
        if compte_rendu and compte_rendu['appreciation']:
            self.appreciation_text.setText(compte_rendu['appreciation'])
        else:
            self.appreciation_text.clear()
        
        self.update_note_finale()
    
    def update_note_finale(self):
        """Calcule et affiche la note finale en temps réel"""
        if not self.question_widgets:
            return
        
        total_points = 0
        total_max = 0
        
        for i, widget in enumerate(self.question_widgets):
            points = widget.get_points()
            question = self.questions[i]
            
            total_points += points * question['coefficient']
            total_max += question['points_max'] * question['coefficient']
        
        if total_max > 0:
            note_sur_20 = (total_points / total_max) * 20
            self.note_finale_label.setText(f"Note: {note_sur_20:.2f}/20")
            
            # Couleur selon la note
            if note_sur_20 >= 15:
                color = "#4CAF50"
            elif note_sur_20 >= 10:
                color = "#FFC107"
            else:
                color = "#F44336"
            
            self.note_finale_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {color};")
    
    def save_current(self):
        """Sauvegarde les notes de l'élève actuel"""
        if self.current_eleve_id is None:
            QMessageBox.warning(self, "Erreur", "Aucun élève sélectionné")
            return
        
        try:
            # Sauvegarder chaque note avec son commentaire
            for i, widget in enumerate(self.question_widgets):
                question = self.questions[i]
                points = widget.get_points()
                commentaire = widget.get_commentaire()  # Récupère toujours une chaîne
                
                # Debug: afficher ce qu'on sauvegarde
                print(f"Sauvegarde Q{question['numero']}: points={points}, commentaire='{commentaire}'")
                
                self.db.save_note_question(
                    self.current_eleve_id,
                    question['id'],
                    points,
                    commentaire  # Passe une chaîne (vide si pas de commentaire)
                )
            
            # Sauvegarder l'appréciation globale dans la table compte_rendus
            appreciation = self.appreciation_text.toPlainText().strip()
            if appreciation:  # Sauvegarder seulement s'il y a une appréciation
                # Vérifier si un compte-rendu existe déjà
                existing = self.db.get_compte_rendu(self.devoir_id, self.current_eleve_id)
                
                if existing:
                    # Mettre à jour l'appréciation existante
                    self.db.conn.execute("""
                        UPDATE compte_rendus 
                        SET appreciation = ?
                        WHERE id_devoir = ? AND id_eleve = ?
                    """, (appreciation, self.devoir_id, self.current_eleve_id))
                else:
                    # Créer un nouveau compte-rendu (sans PDF pour l'instant)
                    self.db.conn.execute("""
                        INSERT INTO compte_rendus (id_devoir, id_eleve, appreciation)
                        VALUES (?, ?, ?)
                    """, (self.devoir_id, self.current_eleve_id, appreciation))
                
                self.db.conn.commit()
                print(f"Appréciation sauvegardée: '{appreciation}'")
            
            # Recalculer la moyenne du devoir
            self.db.update_moyenne_devoir(self.devoir_id)
            
            # Rafraîchir la liste et les stats
            self.refresh_eleve_list()
            self.update_global_progress()
            self.update_stats()
            
            # Message de confirmation
            QMessageBox.information(self, "Succès", "Notes sauvegardées !")
            
        except Exception as e:
            import traceback
            print(f"Erreur lors de la sauvegarde: {e}")
            print(traceback.format_exc())
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la sauvegarde : {str(e)}")
    
    def save_and_next(self):
        """Sauvegarde et passe à l'élève suivant"""
        self.save_current()
        self.next_eleve()
    
    def previous_eleve(self):
        """Passe à l'élève précédent"""
        current_row = self.eleve_list.currentRow()
        if current_row > 0:
            self.eleve_list.setCurrentRow(current_row - 1)
    
    def next_eleve(self):
        """Passe à l'élève suivant"""
        current_row = self.eleve_list.currentRow()
        if current_row < self.eleve_list.count() - 1:
            self.eleve_list.setCurrentRow(current_row + 1)
    
    def update_global_progress(self):
        """Met à jour la barre de progression globale"""
        eleves_data = self.db.get_eleves_classe_avec_notes(self.devoir_id)
        
        nb_corriges = sum(1 for e in eleves_data if e['nb_notes_saisies'] == e['nb_questions_total'])
        nb_total = len(eleves_data)
        
        self.progress_label.setText(f"{nb_corriges}/{nb_total} corrigés")
        
        if nb_total > 0:
            percentage = (nb_corriges / nb_total) * 100
            self.global_progress.setValue(int(percentage))
    
    def update_stats(self):
        """Met à jour les statistiques du panneau de droite"""
        # Récupérer les notes actuelles
        notes = self.db.get_distribution_notes_devoir(self.devoir_id)
        
        if len(notes) > 0:
            moyenne = sum(notes) / len(notes)
            note_min = min(notes)
            note_max = max(notes)
            
            stats_text = f"""
            <b>📈 Statistiques actuelles</b><br><br>
            <b>Moyenne:</b> {moyenne:.2f}/20<br>
            <b>Note min:</b> {note_min:.2f}/20<br>
            <b>Note max:</b> {note_max:.2f}/20<br>
            <b>Nb notes:</b> {len(notes)}<br>
            """
        else:
            stats_text = "<b>Aucune note saisie pour l'instant</b>"
        
        self.stats_label.setText(stats_text)