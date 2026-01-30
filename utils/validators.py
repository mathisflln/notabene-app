# utils/validators.py

def validate_note(points_obtenus, points_max):
    """Valide qu'une note est correcte"""
    if points_obtenus < 0:
        return False, "La note ne peut pas être négative"
    if points_obtenus > points_max:
        return False, f"La note ne peut pas dépasser {points_max}"
    return True, ""

def validate_nom(nom):
    """Valide un nom"""
    if not nom or not nom.strip():
        return False, "Le nom ne peut pas être vide"
    if len(nom) > 100:
        return False, "Le nom est trop long"
    return True, ""