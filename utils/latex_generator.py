# utils/latex_generator.py
import os
import subprocess
from datetime import datetime
from database.db_manager import DatabaseManager

class LatexGenerator:
    def __init__(self, db=None):
        self.db = db
        self.templates_dir = "resources/templates"
        self.output_dir = "exports"
        
        # Créer les dossiers s'ils n'existent pas
        os.makedirs(self.templates_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
    
    def _get_db(self):
        """Retourne l'instance de db ou en crée une nouvelle"""
        if self.db is None:
            self.db = DatabaseManager()
            self.db.connect()
        return self.db
    
    def generate_bareme_pdf(self, devoir_id, output_path=None):
        """Génère le PDF du barème d'un devoir"""
        db = self._get_db()
        devoir = db.get_devoir(devoir_id)
        questions = db.get_questions_devoir(devoir_id)
        
        if not output_path:
            output_path = os.path.join(self.output_dir, f"bareme_{devoir['nom'].replace(' ', '_')}.pdf")
        
        # Générer le contenu LaTeX
        latex_content = self._generate_bareme_latex(devoir, questions)
        
        # Compiler en PDF
        pdf_path = self._compile_latex(latex_content, output_path)
        
        return pdf_path
    
    def generate_compte_rendu_pdf(self, devoir_id, eleve_id, output_path=None):
        """Génère le PDF du compte-rendu d'un élève"""
        db = self._get_db()
        devoir = db.get_devoir(devoir_id)
        eleve = db.get_eleve(eleve_id)
        notes = db.get_notes_eleve_devoir(eleve_id, devoir_id)
        note_finale = db.calculate_note_finale(eleve_id, devoir_id)
        
        # Calculer les stats du devoir
        distribution = db.get_distribution_notes_devoir(devoir_id)
        moyenne_classe = sum(distribution) / len(distribution) if distribution else 0
        
        if not output_path:
            filename = f"CR_{devoir['nom']}_{eleve['nom']}_{eleve['prenom']}.pdf".replace(' ', '_')
            output_path = os.path.join(self.output_dir, filename)
        
        # Générer le contenu LaTeX
        latex_content = self._generate_cr_latex(devoir, eleve, notes, note_finale, moyenne_classe)
        
        # Compiler en PDF
        pdf_path = self._compile_latex(latex_content, output_path)
        
        return pdf_path
    
    def generate_all_comptes_rendus(self, devoir_id, output_dir=None):
        """Génère tous les comptes-rendus d'un devoir"""
        db = self._get_db()
        if not output_dir:
            devoir = db.get_devoir(devoir_id)
            devoir_name = devoir['nom'].replace(' ', '_')
            output_dir = os.path.join(self.output_dir, f"CR_{devoir_name}")
        
        os.makedirs(output_dir, exist_ok=True)
        
        eleves = db.get_eleves_classe_avec_notes(devoir_id)
        generated_files = []
        
        for eleve in eleves:
            # Vérifier que l'élève a toutes ses notes
            if eleve['nb_notes_saisies'] == eleve['nb_questions_total']:
                try:
                    filename = f"CR_{eleve['nom']}_{eleve['prenom']}.pdf".replace(' ', '_')
                    output_path = os.path.join(output_dir, filename)
                    
                    pdf_path = self.generate_compte_rendu_pdf(devoir_id, eleve['id'], output_path)
                    generated_files.append(pdf_path)
                except Exception as e:
                    print(f"Erreur pour {eleve['nom']} {eleve['prenom']}: {e}")
        
        return generated_files, output_dir
    
    def _generate_bareme_latex(self, devoir, questions):
        """Génère le code LaTeX pour le barème"""
        # Trier les questions par numéro (en gérant les nombres)
        def sort_key(q):
            import re
            # Extraire le premier nombre de la question
            match = re.search(r'(\d+)', str(q['numero']))
            if match:
                return (int(match.group(1)), str(q['numero']))
            return (0, str(q['numero']))
        
        questions_triees = sorted(questions, key=sort_key)
        
        total_points = sum(q['points_max'] * q['coefficient'] for q in questions_triees)
        
        latex = r"""\documentclass[11pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[french]{babel}
\usepackage[T1]{fontenc}
\usepackage{geometry}
\usepackage{array}
\usepackage{booktabs}
\usepackage{colortbl}
\usepackage{xcolor}

\geometry{margin=2cm}

\begin{document}

\begin{center}
    {\LARGE\bfseries """ + devoir['nom'] + r"""}\\[0.5cm]
    {\large """ + devoir['classe_nom'] + r""" -- """ + devoir['date'] + r"""}\\[0.3cm]
    {\large\textbf{Barème}}
\end{center}

\vspace{1cm}

\begin{table}[h]
\centering
\begin{tabular}{|c|p{10cm}|c|c|c|}
\hline
\rowcolor{gray!30}
\textbf{N°} & \textbf{Question} & \textbf{Points} & \textbf{Coef.} & \textbf{Total} \\
\hline
"""
        
        for q in questions_triees:
            points_ponderes = q['points_max'] * q['coefficient']
            # Afficher plus de décimales pour les coefficients
            latex += f"{q['numero']} & {q['intitule']} & {q['points_max']:.2f} & {q['coefficient']:.2f} & {points_ponderes:.2f} \\\\\n\\hline\n"
        
        latex += r"""\rowcolor{gray!20}
\multicolumn{4}{|r|}{\textbf{Total des points :}} & \textbf{""" + f"{total_points:.2f}" + r"""} \\
\hline
\end{tabular}
\end{table}

\vspace{1cm}

\textbf{Note finale sur 20} (conversion automatique)

\vspace{0.5cm}

\textit{Formule de calcul :} Note finale = $\frac{\text{Points obtenus}}{\text{""" + f"{total_points:.2f}" + r"""}} \times 20$

\end{document}
"""
        return latex
    
    def _generate_cr_latex(self, devoir, eleve, notes, note_finale, moyenne_classe):
        """Génère le code LaTeX pour un compte-rendu individuel"""
        
        # Trier les questions par numéro
        def sort_key(n):
            import re
            match = re.search(r'(\d+)', str(n['numero']))
            if match:
                return (int(match.group(1)), str(n['numero']))
            return (0, str(n['numero']))
        
        notes_triees = sorted(notes, key=sort_key)
        
        # Calculer les statistiques
        total_points = sum(n['points_max'] * n['coefficient'] for n in notes_triees)
        points_obtenus = sum((n['points_obtenus'] or 0) * n['coefficient'] for n in notes_triees)
        
        # Déterminer la couleur selon la note
        if note_finale >= 15:
            color = "green!70"
        elif note_finale >= 10:
            color = "orange!70"
        else:
            color = "red!70"
        
        latex = r"""\documentclass[11pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[french]{babel}
\usepackage[T1]{fontenc}
\usepackage{geometry}
\usepackage{array}
\usepackage{booktabs}
\usepackage{colortbl}
\usepackage{xcolor}
\usepackage{tikz}
\usepackage{tcolorbox}

\geometry{margin=2cm}

\begin{document}

\begin{center}
    {\LARGE\bfseries Compte-Rendu}\\[0.3cm]
    {\large """ + devoir['nom'] + r"""}\\[0.5cm]
\end{center}

\vspace{0.5cm}

\begin{tabular}{ll}
\textbf{Élève :} & """ + eleve['nom'] + " " + eleve['prenom'] + r""" \\
\textbf{Classe :} & """ + devoir['classe_nom'] + r""" \\
\textbf{Date :} & """ + devoir['date'] + r""" \\
\end{tabular}

\vspace{1cm}

\begin{center}
\begin{tikzpicture}
    \draw[line width=2pt, """ + color + r"""] (0,0) rectangle (12,2);
    \node at (6,1) {\Huge\bfseries """ + f"{note_finale:.2f}" + r""" / 20};
\end{tikzpicture}
\end{center}

\vspace{0.5cm}

\begin{center}
\begin{tabular}{|c|c|c|}
\hline
\rowcolor{gray!30}
\textbf{Points obtenus} & \textbf{Moyenne classe} & \textbf{Écart} \\
\hline
""" + f"{points_obtenus:.2f} / {total_points:.2f}" + r""" & """ + f"{moyenne_classe:.2f} / 20" + r""" & """

        ecart = note_finale - moyenne_classe
        ecart_str = f"+{ecart:.2f}" if ecart >= 0 else f"{ecart:.2f}"
        
        latex += ecart_str + r""" \\
\hline
\end{tabular}
\end{center}

\vspace{1cm}

\section*{Détail par question}

"""
        
        for n in notes_triees:
            points_max = n['points_max'] * n['coefficient']
            points_obtenu = (n['points_obtenus'] or 0) * n['coefficient']
            pourcentage = (points_obtenu / points_max * 100) if points_max > 0 else 0
            
            # Couleur selon le pourcentage
            if pourcentage >= 75:
                box_color = "green!20"
            elif pourcentage >= 50:
                box_color = "orange!20"
            elif points_obtenu > 0:
                box_color = "red!20"
            else:
                box_color = "gray!10"
            
            latex += r"""
\begin{tcolorbox}[colback=""" + box_color + r""", colframe=black!50, boxrule=0.5pt, arc=2mm]
\textbf{Question """ + str(n['numero']) + r"""} : """ + n['intitule'] + r"""

\vspace{0.3cm}

\begin{tabular}{ll}
\textbf{Points :} & """ + f"{points_obtenu:.2f} / {points_max:.2f}" + r""" (""" + f"{pourcentage:.0f}" + r"""\%) \\
\end{tabular}
"""
            
            # Ajouter le commentaire s'il existe
            commentaire = n.get('commentaire', '')
            if commentaire and commentaire.strip():
                # Échapper les caractères spéciaux LaTeX
                commentaire_escaped = commentaire.replace('&', r'\&').replace('%', r'\%').replace('_', r'\_')
                latex += r"""

\vspace{0.2cm}

\textit{Commentaire :} """ + commentaire_escaped + r"""
"""
            
            latex += r"""
\end{tcolorbox}

"""
        
        latex += r"""
\vspace{1cm}

\textit{Ce compte-rendu a été généré automatiquement le """ + datetime.now().strftime("%d/%m/%Y à %H:%M") + r"""}

\end{document}
"""
        return latex
    
    def _compile_latex(self, latex_content, output_path):
        """Compile le code LaTeX en PDF"""
        # Créer un fichier temporaire .tex
        base_name = os.path.splitext(output_path)[0]
        tex_file = base_name + ".tex"
        
        # Écrire le contenu LaTeX
        with open(tex_file, 'w', encoding='utf-8') as f:
            f.write(latex_content)
        
        try:
            # Compiler avec pdflatex
            process = subprocess.run(
                ['pdflatex', '-interaction=nonstopmode', '-output-directory', 
                 os.path.dirname(output_path) or '.', tex_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Vérifier si le PDF a été créé même avec des warnings
            pdf_path = base_name + ".pdf"
            if os.path.exists(pdf_path):
                # Nettoyer les fichiers temporaires
                for ext in ['.aux', '.log', '.tex']:
                    temp_file = base_name + ext
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                return pdf_path
            else:
                # Lire le fichier log pour plus de détails
                log_file = base_name + ".log"
                error_details = ""
                if os.path.exists(log_file):
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        error_details = f.read()
                
                raise Exception(f"PDF non généré. Détails:\n{process.stderr}\n\nLog:\n{error_details[-1000:]}")
        
        except FileNotFoundError:
            raise Exception("pdflatex n'est pas installé. Installez une distribution LaTeX (TeX Live, MiKTeX, etc.)")
        except subprocess.TimeoutExpired:
            raise Exception("La compilation LaTeX a pris trop de temps")