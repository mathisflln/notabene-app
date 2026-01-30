# ui/pages/statistiques.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

class StatistiquesPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        
        label = QLabel("📈 Page Statistiques - En construction")
        label.setStyleSheet("font-size: 20px;")
        layout.addWidget(label)