# ui/pages/dashboard.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGridLayout, QFrame, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt
from database.db_manager import DatabaseManager

class StatCard(QFrame):
    def __init__(self, title, value, icon="📊"):
        super().__init__()
        self.setObjectName("stat-card")
        
        layout = QVBoxLayout(self)
        
        self.value_label = QLabel(f"{icon} {value}")
        self.value_label.setObjectName("stat-value")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.value_label)
        
        title_label = QLabel(title)
        title_label.setObjectName("stat-title")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        self.icon = icon

class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Header avec titre et bouton rafraîchir
        header = QHBoxLayout()
        
        title = QLabel("📊 Tableau de bord")
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        header.addWidget(title)
        
        header.addStretch()
        
        refresh_btn = QPushButton("🔄 Rafraîchir")
        refresh_btn.setToolTip("Recharger toutes les statistiques")
        refresh_btn.clicked.connect(self.force_refresh)
        header.addWidget(refresh_btn)
        
        layout.addLayout(header)
        
        stats_grid = QGridLayout()
        stats_grid.setSpacing(20)
        
        self.card_eleves = StatCard("Élèves", "0", "👥")
        self.card_classes = StatCard("Classes", "0", "🏫")
        self.card_devoirs = StatCard("Devoirs", "0", "📝")
        self.card_moyenne = StatCard("Moyenne générale", "0.0", "📈")
        
        stats_grid.addWidget(self.card_eleves, 0, 0)
        stats_grid.addWidget(self.card_classes, 0, 1)
        stats_grid.addWidget(self.card_devoirs, 0, 2)
        stats_grid.addWidget(self.card_moyenne, 0, 3)
        
        layout.addLayout(stats_grid)
        
        # Info label
        self.info_label = QLabel("")
        self.info_label.setStyleSheet("color: #666; font-size: 11px; margin-top: 10px;")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.info_label)
        
        layout.addStretch()
        
        self.load_stats()
    
    def force_refresh(self):
        """Force le recalcul de toutes les statistiques"""
        self.db.recalculate_all_moyennes()
        self.load_stats()
        
        # Message de confirmation
        self.info_label.setText("✅ Statistiques recalculées depuis la base de données")
        
        # Effacer le message après 3 secondes
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(3000, lambda: self.info_label.setText(""))
    
    def load_stats(self):
        """Charge les statistiques EN TEMPS RÉEL depuis la base de données"""
        stats = self.db.get_stats_globales()
        
        self.update_card(self.card_eleves, stats['nb_eleves'])
        self.update_card(self.card_classes, stats['nb_classes'])
        self.update_card(self.card_devoirs, stats['nb_devoirs'])
        self.update_card(self.card_moyenne, f"{stats['moyenne_globale']:.2f}/20")
    
    def update_card(self, card, value):
        card.value_label.setText(f"{card.icon} {value}")
    
    def showEvent(self, event):
        """Recharge les stats à chaque affichage de la page"""
        super().showEvent(event)
        self.load_stats()