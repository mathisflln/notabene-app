# dialogs/correction_dialog.py
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel

class CorrectionDialog(QDialog):
    def __init__(self, parent=None, devoir_id=None):
        super().__init__(parent)
        self.devoir_id = devoir_id
        
        self.setWindowTitle("Correction du devoir")
        self.setMinimumSize(1000, 700)
        
        layout = QVBoxLayout(self)
        label = QLabel("Interface de correction - En construction")
        layout.addWidget(label)