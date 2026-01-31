# dialogs/generation_cr_dialog.py
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                              QPushButton, QProgressBar, QTextEdit, QFileDialog,
                              QCheckBox, QMessageBox, QGroupBox, QRadioButton)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from database.db_manager import DatabaseManager
from utils.latex_generator import LatexGenerator
import os

class GenerationThread(QThread):
    """Thread pour générer les PDFs sans bloquer l'interface"""
    progress = pyqtSignal(int, str)  # pourcentage, message
    finished = pyqtSignal(list, str)  # liste des fichiers générés, dossier
    error = pyqtSignal(str)
    
    def __init__(self, devoir_id, output_dir, generate_bareme=False):
        super().__init__()
        self.devoir_id = devoir_id
        self.output_dir = output_dir
        self.generate_bareme = generate_bareme
    
    def run(self):
        try:
            import sqlite3
            
            # Créer une connexion SQLite directe dans ce thread
            conn = sqlite3.connect("nota.db")
            conn.row_factory = sqlite3.Row
            
            # Créer un DatabaseManager qui utilisera cette connexion
            db = DatabaseManager()
            db.conn = conn  # Forcer l'utilisation de notre connexion
            
            # Passer cette connexion au générateur
            generator = LatexGenerator(db)
            
            generated_files = []
            
            # Générer le barème si demandé
            if self.generate_bareme:
                self.progress.emit(0, "Génération du barème...")
                devoir = db.get_devoir(self.devoir_id)
                bareme_path = os.path.join(self.output_dir, f"Bareme_{devoir['nom']}.pdf".replace(' ', '_'))
                bareme_file = generator.generate_bareme_pdf(self.devoir_id, bareme_path)
                generated_files.append(bareme_file)
                self.progress.emit(10, "Barème généré")
            
            # Générer les comptes-rendus
            self.progress.emit(15, "Génération des comptes-rendus...")
            eleves = db.get_eleves_classe_avec_notes(self.devoir_id)
            
            # Filtrer les élèves corrigés
            eleves_corriges = [e for e in eleves if e['nb_notes_saisies'] == e['nb_questions_total']]
            total_eleves = len(eleves_corriges)
            
            if total_eleves == 0:
                self.error.emit("Aucun élève n'a été corrigé pour ce devoir")
                return
            
            for i, eleve in enumerate(eleves_corriges):
                progress_pct = 15 + int((i / total_eleves) * 80)
                self.progress.emit(progress_pct, f"Génération CR: {eleve['nom']} {eleve['prenom']}")
                
                try:
                    filename = f"CR_{eleve['nom']}_{eleve['prenom']}.pdf".replace(' ', '_')
                    output_path = os.path.join(self.output_dir, filename)
                    
                    pdf_path = generator.generate_compte_rendu_pdf(
                        self.devoir_id, 
                        eleve['id'], 
                        output_path
                    )
                    generated_files.append(pdf_path)
                    
                except Exception as e:
                    self.progress.emit(progress_pct, f"Erreur: {eleve['nom']} {eleve['prenom']} - {str(e)}")
            
            self.progress.emit(100, "Génération terminée!")
            self.finished.emit(generated_files, self.output_dir)
            
        except Exception as e:
            self.error.emit(str(e))

class GenerationCRDialog(QDialog):
    def __init__(self, parent=None, devoir_id=None):
        super().__init__(parent)
        self.devoir_id = devoir_id
        self.db = DatabaseManager()
        self.generated_files = []
        self.output_dir = None
        
        self.setWindowTitle("Génération des comptes-rendus")
        self.setMinimumSize(600, 500)
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Infos du devoir
        devoir = self.db.get_devoir(self.devoir_id)
        eleves = self.db.get_eleves_classe_avec_notes(self.devoir_id)
        eleves_corriges = sum(1 for e in eleves if e['nb_notes_saisies'] == e['nb_questions_total'])
        
        info_label = QLabel(f"<b>Devoir:</b> {devoir['nom']}<br>"
                           f"<b>Classe:</b> {devoir['classe_nom']}<br>"
                           f"<b>Élèves corrigés:</b> {eleves_corriges}/{len(eleves)}")
        layout.addWidget(info_label)
        
        # Options
        options_group = QGroupBox("Options de génération")
        options_layout = QVBoxLayout()
        
        self.bareme_checkbox = QCheckBox("Générer aussi le barème")
        self.bareme_checkbox.setChecked(True)
        options_layout.addWidget(self.bareme_checkbox)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # Dossier de sortie
        output_group = QGroupBox("Dossier de sortie")
        output_layout = QHBoxLayout()
        
        self.output_label = QLabel("exports/CR_" + devoir['nom'].replace(' ', '_'))
        output_layout.addWidget(self.output_label)
        
        browse_btn = QPushButton("📁 Parcourir")
        browse_btn.clicked.connect(self.browse_output_dir)
        output_layout.addWidget(browse_btn)
        
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)
        
        # Barre de progression
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(100)
        layout.addWidget(self.progress_bar)
        
        # Log
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        layout.addWidget(self.log_text)
        
        # Boutons
        buttons_layout = QHBoxLayout()
        
        self.generate_btn = QPushButton("🚀 Générer")
        self.generate_btn.setObjectName("primary-button")
        self.generate_btn.clicked.connect(self.start_generation)
        buttons_layout.addWidget(self.generate_btn)
        
        self.open_folder_btn = QPushButton("📁 Ouvrir le dossier")
        self.open_folder_btn.setEnabled(False)
        self.open_folder_btn.clicked.connect(self.open_output_folder)
        buttons_layout.addWidget(self.open_folder_btn)
        
        close_btn = QPushButton("Fermer")
        close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(close_btn)
        
        layout.addLayout(buttons_layout)
    
    def browse_output_dir(self):
        """Sélectionner un dossier de sortie"""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Sélectionner le dossier de sortie",
            "exports"
        )
        
        if dir_path:
            self.output_label.setText(dir_path)
    
    def start_generation(self):
        """Démarre la génération des PDFs"""
        self.generate_btn.setEnabled(False)
        self.log_text.clear()
        self.progress_bar.setValue(0)
        
        output_dir = self.output_label.text()
        os.makedirs(output_dir, exist_ok=True)
        
        # Créer et démarrer le thread
        self.thread = GenerationThread(
            self.devoir_id,
            output_dir,
            self.bareme_checkbox.isChecked()
        )
        
        self.thread.progress.connect(self.update_progress)
        self.thread.finished.connect(self.generation_finished)
        self.thread.error.connect(self.generation_error)
        
        self.thread.start()
    
    def update_progress(self, percentage, message):
        """Met à jour la barre de progression et le log"""
        self.progress_bar.setValue(percentage)
        self.log_text.append(f"[{percentage}%] {message}")
    
    def generation_finished(self, files, output_dir):
        """Appelé quand la génération est terminée"""
        self.generated_files = files
        self.output_dir = output_dir
        
        self.log_text.append(f"\n✅ Génération terminée!")
        self.log_text.append(f"{len(files)} fichier(s) générés")
        
        self.generate_btn.setEnabled(True)
        self.open_folder_btn.setEnabled(True)
        
        QMessageBox.information(
            self,
            "Succès",
            f"Génération terminée!\n\n{len(files)} fichier(s) générés dans:\n{output_dir}"
        )
    
    def generation_error(self, error_message):
        """Appelé en cas d'erreur"""
        self.log_text.append(f"\n❌ ERREUR: {error_message}")
        self.generate_btn.setEnabled(True)
        
        QMessageBox.critical(
            self,
            "Erreur",
            f"Erreur lors de la génération:\n\n{error_message}"
        )
    
    def open_output_folder(self):
        """Ouvre le dossier de sortie dans l'explorateur"""
        if self.output_dir and os.path.exists(self.output_dir):
            import platform
            import subprocess
            
            if platform.system() == "Windows":
                os.startfile(self.output_dir)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", self.output_dir])
            else:  # Linux
                subprocess.run(["xdg-open", self.output_dir])