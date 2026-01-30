# ui/main_window.py
from PyQt6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, 
                              QVBoxLayout, QPushButton, QStackedWidget,
                              QLabel, QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
import os

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GestionProf - Gestion de notes")
        self.setMinimumSize(1400, 800)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.sidebar = self.create_sidebar()
        main_layout.addWidget(self.sidebar)
        
        self.content_stack = QStackedWidget()
        main_layout.addWidget(self.content_stack)
        
        self.add_pages()
        
        self.load_stylesheet()
        
        self.show_page(0)
    
    def create_sidebar(self):
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(10, 20, 10, 20)
        layout.setSpacing(5)
        
        title = QLabel("📚 GestionProf")
        title.setObjectName("sidebar-title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        layout.addSpacing(30)
        
        buttons_info = [
            ("📊", "Tableau de bord", 0),
            ("👥", "Élèves", 1),
            ("🏫", "Classes", 2),
            ("📝", "Devoirs", 3),
            ("📈", "Statistiques", 4),
        ]
        
        self.nav_buttons = []
        for icon, text, page_idx in buttons_info:
            btn = QPushButton(f"{icon}  {text}")
            btn.setObjectName("nav-button")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, idx=page_idx: self.show_page(idx))
            layout.addWidget(btn)
            self.nav_buttons.append(btn)
        
        layout.addStretch()
        
        settings_btn = QPushButton("⚙️  Paramètres")
        settings_btn.setObjectName("nav-button")
        layout.addWidget(settings_btn)
        
        version_label = QLabel("v1.0.0")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setStyleSheet("color: #999; font-size: 11px;")
        layout.addWidget(version_label)
        
        return sidebar
    
    def add_pages(self):
        from ui.pages.dashboard import DashboardPage
        from ui.pages.eleves import ElevesPage
        from ui.pages.classes import ClassesPage
        from ui.pages.devoirs import DevoirsPage
        from ui.pages.statistiques import StatistiquesPage
        
        self.content_stack.addWidget(DashboardPage())
        self.content_stack.addWidget(ElevesPage())
        self.content_stack.addWidget(ClassesPage())
        self.content_stack.addWidget(DevoirsPage())
        self.content_stack.addWidget(StatistiquesPage())
    
    def show_page(self, index):
        self.content_stack.setCurrentIndex(index)
        
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
    
    def load_stylesheet(self):
        qss_path = os.path.join(os.path.dirname(__file__), "styles", "style.qss")
        if os.path.exists(qss_path):
            with open(qss_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())