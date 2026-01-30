# config.py
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "nota.db")
RESOURCES_DIR = os.path.join(BASE_DIR, "resources")
TEMPLATES_DIR = os.path.join(RESOURCES_DIR, "templates")
ICONS_DIR = os.path.join(RESOURCES_DIR, "icons")

THEME = "light"

COLORS = {
    "primary": "#3498db",
    "secondary": "#2c3e50",
    "success": "#27ae60",
    "warning": "#f39c12",
    "danger": "#e74c3c",
    "light": "#ecf0f1",
    "dark": "#2c3e50"
}