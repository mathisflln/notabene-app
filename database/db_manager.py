# database/db_manager.py
import sqlite3
import json
from typing import List, Dict, Optional
from datetime import datetime

class DatabaseManager:
    _instance = None
    
    def __new__(cls, db_path="nota.db"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.db_path = db_path
            cls._instance.conn = None
        return cls._instance
    
    def connect(self):
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None
    
    # ========== MÉTHODES DE RECALCUL ==========
    
    def recalculate_all_moyennes(self):
        """Recalcule toutes les moyennes de tous les devoirs"""
        devoirs = self.conn.execute("SELECT id FROM devoirs").fetchall()
        for devoir in devoirs:
            self.update_moyenne_devoir(devoir['id'])
    
    def clear_devoir_notes(self, devoir_id):
        """Supprime toutes les notes d'un devoir et recalcule la moyenne"""
        self.conn.execute("""
            DELETE FROM note_question 
            WHERE id_question IN (SELECT id FROM questions WHERE id_devoir = ?)
        """, (devoir_id,))
        self.conn.commit()
        self.update_moyenne_devoir(devoir_id)
    
    # ========== CLASSES ==========
    
    def get_all_classes(self):
        cursor = self.conn.execute("SELECT * FROM classes ORDER BY nom")
        return cursor.fetchall()
    
    def get_classe(self, classe_id):
        cursor = self.conn.execute("SELECT * FROM classes WHERE id=?", (classe_id,))
        return cursor.fetchone()
    
    def add_classe(self, nom):
        cursor = self.conn.execute("INSERT INTO classes (nom) VALUES (?)", (nom,))
        self.conn.commit()
        return cursor.lastrowid
    
    def update_classe(self, classe_id, nom):
        self.conn.execute("UPDATE classes SET nom=? WHERE id=?", (nom, classe_id))
        self.conn.commit()
    
    def delete_classe(self, classe_id):
        cursor = self.conn.execute("SELECT COUNT(*) FROM eleves WHERE id_classe=?", (classe_id,))
        if cursor.fetchone()[0] > 0:
            return False, "Cette classe contient des élèves"
        
        self.conn.execute("DELETE FROM classes WHERE id=?", (classe_id,))
        self.conn.commit()
        return True, "Classe supprimée"
    
    def get_classe_stats(self, classe_id):
        nb_eleves = self.conn.execute(
            "SELECT COUNT(*) FROM eleves WHERE id_classe=?", (classe_id,)
        ).fetchone()[0]
        
        nb_devoirs = self.conn.execute(
            "SELECT COUNT(*) FROM devoirs WHERE id_classe=?", (classe_id,)
        ).fetchone()[0]
        
        moyenne = self.get_moyenne_classe(classe_id)
        
        return {
            'nb_eleves': nb_eleves,
            'nb_devoirs': nb_devoirs,
            'moyenne': moyenne
        }
    
    # ========== ELEVES ==========
    
    def get_all_eleves(self, classe_id=None, search_term=""):
        query = """
            SELECT e.*, c.nom as classe_nom 
            FROM eleves e 
            LEFT JOIN classes c ON e.id_classe = c.id
            WHERE 1=1
        """
        params = []
        
        if classe_id:
            query += " AND e.id_classe = ?"
            params.append(classe_id)
        
        if search_term:
            query += " AND (e.nom LIKE ? OR e.prenom LIKE ?)"
            params.extend([f"%{search_term}%", f"%{search_term}%"])
        
        query += " ORDER BY e.nom, e.prenom"
        
        cursor = self.conn.execute(query, params)
        return cursor.fetchall()
    
    def get_eleve(self, eleve_id):
        cursor = self.conn.execute(
            "SELECT e.*, c.nom as classe_nom FROM eleves e LEFT JOIN classes c ON e.id_classe = c.id WHERE e.id=?",
            (eleve_id,)
        )
        return cursor.fetchone()
    
    def add_eleve(self, nom, prenom, id_classe):
        cursor = self.conn.execute(
            "INSERT INTO eleves (nom, prenom, id_classe) VALUES (?, ?, ?)",
            (nom, prenom, id_classe)
        )
        self.conn.commit()
        return cursor.lastrowid
    
    def update_eleve(self, eleve_id, nom, prenom, id_classe):
        self.conn.execute(
            "UPDATE eleves SET nom=?, prenom=?, id_classe=? WHERE id=?",
            (nom, prenom, id_classe, eleve_id)
        )
        self.conn.commit()
    
    def delete_eleve(self, eleve_id):
        cursor = self.conn.execute(
            "SELECT COUNT(*) FROM note_question WHERE id_eleve=?",
            (eleve_id,)
        )
        if cursor.fetchone()[0] > 0:
            return False, "Cet élève a des notes, impossible de le supprimer"
        
        self.conn.execute("DELETE FROM eleves WHERE id=?", (eleve_id,))
        self.conn.commit()
        return True, "Élève supprimé"
    
    def get_moyenne_eleve(self, eleve_id):
        """Calcule la moyenne d'un élève en temps réel depuis la base de données"""
        query = """
            SELECT AVG(note_finale) as moyenne
            FROM (
                SELECT d.id,
                       (SUM(nq.points_obtenus * q.coefficient) / 
                        SUM(q.points_max * q.coefficient) * 20) as note_finale
                FROM devoirs d
                JOIN questions q ON q.id_devoir = d.id
                LEFT JOIN note_question nq ON nq.id_question = q.id AND nq.id_eleve = ?
                WHERE d.id_classe = (SELECT id_classe FROM eleves WHERE id = ?)
                GROUP BY d.id
                HAVING COUNT(nq.points_obtenus) = (SELECT COUNT(*) FROM questions WHERE id_devoir = d.id)
            )
        """
        cursor = self.conn.execute(query, (eleve_id, eleve_id))
        result = cursor.fetchone()
        moyenne = result['moyenne'] if result and result['moyenne'] else 0
        return round(moyenne, 2)
    
    def get_nb_devoirs_eleve(self, eleve_id):
        query = """
            SELECT COUNT(DISTINCT d.id)
            FROM devoirs d
            JOIN questions q ON q.id_devoir = d.id
            JOIN note_question nq ON nq.id_question = q.id
            WHERE nq.id_eleve = ?
            AND (SELECT COUNT(*) FROM note_question nq2 
                 JOIN questions q2 ON nq2.id_question = q2.id 
                 WHERE q2.id_devoir = d.id AND nq2.id_eleve = ?) = 
                (SELECT COUNT(*) FROM questions WHERE id_devoir = d.id)
        """
        cursor = self.conn.execute(query, (eleve_id, eleve_id))
        return cursor.fetchone()[0]
    
    # ========== DEVOIRS ==========
    
    def get_all_devoirs(self, classe_id=None, search_term=""):
        """Récupère tous les devoirs avec leurs statistiques EN TEMPS RÉEL"""
        query = """
            SELECT d.*, c.nom as classe_nom,
                   (SELECT COUNT(*) FROM questions WHERE id_devoir = d.id) as nb_questions,
                   (SELECT COUNT(DISTINCT e.id)
                    FROM eleves e
                    WHERE e.id_classe = d.id_classe
                    AND (SELECT COUNT(*)
                         FROM note_question nq
                         JOIN questions q ON nq.id_question = q.id
                         WHERE q.id_devoir = d.id AND nq.id_eleve = e.id) = 
                        (SELECT COUNT(*) FROM questions WHERE id_devoir = d.id)
                   ) as nb_corriges,
                   (SELECT COUNT(*) FROM eleves WHERE id_classe = d.id_classe) as nb_eleves_total
            FROM devoirs d
            LEFT JOIN classes c ON d.id_classe = c.id
            WHERE 1=1
        """
        params = []
        
        if classe_id:
            query += " AND d.id_classe = ?"
            params.append(classe_id)
        
        if search_term:
            query += " AND d.nom LIKE ?"
            params.append(f"%{search_term}%")
        
        query += " ORDER BY d.date DESC"
        
        cursor = self.conn.execute(query, params)
        return cursor.fetchall()
    
    def get_devoir(self, devoir_id):
        cursor = self.conn.execute(
            "SELECT d.*, c.nom as classe_nom FROM devoirs d LEFT JOIN classes c ON d.id_classe = c.id WHERE d.id=?",
            (devoir_id,)
        )
        return cursor.fetchone()
    
    def add_devoir(self, nom, date, id_classe, bareme=None):
        cursor = self.conn.execute(
            "INSERT INTO devoirs (nom, date, id_classe, bareme) VALUES (?, ?, ?, ?)",
            (nom, date, id_classe, bareme)
        )
        devoir_id = cursor.lastrowid
        self.conn.commit()
        return devoir_id
    
    def update_devoir(self, devoir_id, nom, date):
        self.conn.execute(
            "UPDATE devoirs SET nom=?, date=? WHERE id=?",
            (nom, date, devoir_id)
        )
        self.conn.commit()
    
    def delete_devoir(self, devoir_id):
        cursor = self.conn.execute("""
            SELECT COUNT(*) FROM note_question nq
            JOIN questions q ON nq.id_question = q.id
            WHERE q.id_devoir = ?
        """, (devoir_id,))
        
        if cursor.fetchone()[0] > 0:
            return False, "Ce devoir a des notes, impossible de le supprimer"
        
        self.conn.execute("DELETE FROM questions WHERE id_devoir=?", (devoir_id,))
        self.conn.execute("DELETE FROM devoirs WHERE id=?", (devoir_id,))
        self.conn.commit()
        return True, "Devoir supprimé"
    
    def update_moyenne_devoir(self, devoir_id):
        """Recalcule la moyenne d'un devoir depuis la base de données"""
        query = """
            SELECT AVG(note_finale) as moyenne
            FROM (
                SELECT e.id,
                       (SUM(nq.points_obtenus * q.coefficient) / 
                        SUM(q.points_max * q.coefficient) * 20) as note_finale
                FROM eleves e
                JOIN questions q ON q.id_devoir = ?
                LEFT JOIN note_question nq ON nq.id_question = q.id AND nq.id_eleve = e.id
                WHERE e.id_classe = (SELECT id_classe FROM devoirs WHERE id = ?)
                GROUP BY e.id
                HAVING COUNT(nq.points_obtenus) = (SELECT COUNT(*) FROM questions WHERE id_devoir = ?)
            )
        """
        cursor = self.conn.execute(query, (devoir_id, devoir_id, devoir_id))
        result = cursor.fetchone()
        moyenne = result['moyenne'] if result['moyenne'] else None
        
        self.conn.execute("UPDATE devoirs SET moyenne=? WHERE id=?", (moyenne, devoir_id))
        self.conn.commit()
        
        return moyenne
    
    # ========== QUESTIONS ==========
    
    def get_questions_devoir(self, devoir_id):
        cursor = self.conn.execute(
            "SELECT * FROM questions WHERE id_devoir=? ORDER BY numero",
            (devoir_id,)
        )
        return cursor.fetchall()
    
    def add_question(self, id_devoir, numero, intitule, points_max, coefficient):
        cursor = self.conn.execute(
            "INSERT INTO questions (id_devoir, numero, intitule, points_max, coefficient) VALUES (?, ?, ?, ?, ?)",
            (id_devoir, numero, intitule, points_max, coefficient)
        )
        self.conn.commit()
        return cursor.lastrowid
    
    def update_question(self, question_id, numero, intitule, points_max, coefficient):
        self.conn.execute(
            "UPDATE questions SET numero=?, intitule=?, points_max=?, coefficient=? WHERE id=?",
            (numero, intitule, points_max, coefficient, question_id)
        )
        self.conn.commit()
    
    def delete_question(self, question_id):
        self.conn.execute("DELETE FROM note_question WHERE id_question=?", (question_id,))
        self.conn.execute("DELETE FROM questions WHERE id=?", (question_id,))
        self.conn.commit()
    
    def get_bareme_total(self, devoir_id):
        cursor = self.conn.execute(
            "SELECT SUM(points_max * coefficient) as total FROM questions WHERE id_devoir=?",
            (devoir_id,)
        )
        result = cursor.fetchone()
        return result['total'] if result['total'] else 0
    
    # ========== NOTES ==========
    
    def save_note_question(self, id_eleve, id_question, points_obtenus):
        """Sauvegarde une note"""
        self.conn.execute("""
            INSERT INTO note_question (id_eleve, id_question, points_obtenus)
            VALUES (?, ?, ?)
            ON CONFLICT(id_eleve, id_question) 
            DO UPDATE SET points_obtenus = excluded.points_obtenus
        """, (id_eleve, id_question, points_obtenus))
        self.conn.commit()
    
    def get_notes_eleve_devoir(self, id_eleve, id_devoir):
        query = """
            SELECT q.id, q.numero, q.intitule, q.points_max, 
                   q.coefficient, nq.points_obtenus
            FROM questions q
            LEFT JOIN note_question nq 
                ON q.id = nq.id_question AND nq.id_eleve = ?
            WHERE q.id_devoir = ?
            ORDER BY q.numero
        """
        cursor = self.conn.execute(query, (id_eleve, id_devoir))
        return cursor.fetchall()
    
    def calculate_note_finale(self, id_eleve, id_devoir):
        notes = self.get_notes_eleve_devoir(id_eleve, id_devoir)
        
        total_points = 0
        total_max = 0
        all_filled = True
        
        for note in notes:
            if note['points_obtenus'] is None:
                all_filled = False
                break
            
            points_obtenus = note['points_obtenus']
            points_max = note['points_max']
            coef = note['coefficient']
            
            total_points += points_obtenus * coef
            total_max += points_max * coef
        
        if not all_filled or total_max == 0:
            return None
        
        note_sur_20 = (total_points / total_max) * 20
        return round(note_sur_20, 2)
    
    def get_eleves_classe_avec_notes(self, devoir_id):
        """Récupère les élèves avec leur statut de correction EN TEMPS RÉEL"""
        query = """
            SELECT e.id, e.nom, e.prenom,
                   (SELECT COUNT(*) 
                    FROM note_question nq 
                    JOIN questions q ON nq.id_question = q.id 
                    WHERE nq.id_eleve = e.id AND q.id_devoir = ?) as nb_notes_saisies,
                   (SELECT COUNT(*) 
                    FROM questions WHERE id_devoir = ?) as nb_questions_total
            FROM eleves e
            WHERE e.id_classe = (SELECT id_classe FROM devoirs WHERE id = ?)
            ORDER BY e.nom, e.prenom
        """
        cursor = self.conn.execute(query, (devoir_id, devoir_id, devoir_id))
        return cursor.fetchall()
    
    # ========== COMPTES-RENDUS ==========
    
    def save_compte_rendu(self, id_devoir, id_eleve, pdf_data, appreciation=""):
        cursor = self.conn.execute("""
            INSERT OR REPLACE INTO compte_rendus (id_devoir, id_eleve, pdf, appreciation)
            VALUES (?, ?, ?, ?)
        """, (id_devoir, id_eleve, pdf_data, appreciation))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_compte_rendu(self, id_devoir, id_eleve):
        cursor = self.conn.execute(
            "SELECT * FROM compte_rendus WHERE id_devoir=? AND id_eleve=?",
            (id_devoir, id_eleve)
        )
        return cursor.fetchone()
    
    def get_all_comptes_rendus_devoir(self, devoir_id):
        query = """
            SELECT cr.*, e.nom, e.prenom
            FROM compte_rendus cr
            JOIN eleves e ON cr.id_eleve = e.id
            WHERE cr.id_devoir = ?
            ORDER BY e.nom, e.prenom
        """
        cursor = self.conn.execute(query, (devoir_id,))
        return cursor.fetchall()
    
    def delete_compte_rendu(self, cr_id):
        self.conn.execute("DELETE FROM compte_rendus WHERE id=?", (cr_id,))
        self.conn.commit()
    
    # ========== STATISTIQUES ==========
    
    def get_moyenne_classe(self, classe_id):
        """Calcule la moyenne d'une classe EN TEMPS RÉEL"""
        query = """
            SELECT AVG(note_finale) as moyenne
            FROM (
                SELECT e.id, d.id as devoir_id,
                       (SUM(nq.points_obtenus * q.coefficient) / 
                        SUM(q.points_max * q.coefficient) * 20) as note_finale
                FROM eleves e
                JOIN devoirs d ON d.id_classe = e.id_classe
                JOIN questions q ON q.id_devoir = d.id
                LEFT JOIN note_question nq ON nq.id_question = q.id AND nq.id_eleve = e.id
                WHERE e.id_classe = ?
                GROUP BY e.id, d.id
                HAVING COUNT(nq.points_obtenus) = (SELECT COUNT(*) FROM questions WHERE id_devoir = d.id)
            )
        """
        cursor = self.conn.execute(query, (classe_id,))
        result = cursor.fetchone()
        moyenne = result['moyenne'] if result and result['moyenne'] else 0
        return round(moyenne, 2)
    
    def get_distribution_notes_devoir(self, devoir_id):
        query = """
            SELECT 
                (SUM(nq.points_obtenus * q.coefficient) / 
                 SUM(q.points_max * q.coefficient) * 20) as note_finale
            FROM eleves e
            JOIN questions q ON q.id_devoir = ?
            LEFT JOIN note_question nq ON nq.id_question = q.id AND nq.id_eleve = e.id
            WHERE e.id_classe = (SELECT id_classe FROM devoirs WHERE id = ?)
            GROUP BY e.id
            HAVING COUNT(nq.points_obtenus) = (SELECT COUNT(*) FROM questions WHERE id_devoir = ?)
        """
        cursor = self.conn.execute(query, (devoir_id, devoir_id, devoir_id))
        return [row['note_finale'] for row in cursor.fetchall()]
    
    def get_stats_globales(self):
        """Calcule les statistiques globales EN TEMPS RÉEL"""
        nb_eleves = self.conn.execute("SELECT COUNT(*) FROM eleves").fetchone()[0]
        nb_classes = self.conn.execute("SELECT COUNT(*) FROM classes").fetchone()[0]
        nb_devoirs = self.conn.execute("SELECT COUNT(*) FROM devoirs").fetchone()[0]
        
        # Nombre de devoirs à corriger (élèves qui n'ont pas toutes leurs notes)
        query = """
            SELECT COUNT(DISTINCT d.id)
            FROM devoirs d
            WHERE (SELECT COUNT(DISTINCT e.id)
                   FROM eleves e
                   WHERE e.id_classe = d.id_classe
                   AND (SELECT COUNT(*)
                        FROM note_question nq
                        JOIN questions q ON nq.id_question = q.id
                        WHERE q.id_devoir = d.id AND nq.id_eleve = e.id) = 
                       (SELECT COUNT(*) FROM questions WHERE id_devoir = d.id)
                  ) < (SELECT COUNT(*) FROM eleves WHERE id_classe = d.id_classe)
        """
        nb_a_corriger = self.conn.execute(query).fetchone()[0]
        
        # Moyenne globale (recalculée en temps réel)
        query = """
            SELECT AVG(note_finale) as moyenne
            FROM (
                SELECT e.id, d.id as devoir_id,
                       (SUM(nq.points_obtenus * q.coefficient) / 
                        SUM(q.points_max * q.coefficient) * 20) as note_finale
                FROM eleves e
                JOIN devoirs d ON d.id_classe = e.id_classe
                JOIN questions q ON q.id_devoir = d.id
                LEFT JOIN note_question nq ON nq.id_question = q.id AND nq.id_eleve = e.id
                GROUP BY e.id, d.id
                HAVING COUNT(nq.points_obtenus) = (SELECT COUNT(*) FROM questions WHERE id_devoir = d.id)
            )
        """
        cursor = self.conn.execute(query)
        result = cursor.fetchone()
        moyenne_globale = round(result['moyenne'], 2) if result and result['moyenne'] else 0
        
        return {
            'nb_eleves': nb_eleves,
            'nb_classes': nb_classes,
            'nb_devoirs': nb_devoirs,
            'nb_a_corriger': nb_a_corriger,
            'moyenne_globale': moyenne_globale
        }