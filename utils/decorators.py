from functools import wraps
from flask import session, jsonify, request

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        user = session.get("user")
        if not user:
            return jsonify({"error": "Debes iniciar sesión"}), 403
        return f(*args, **kwargs)
    return wrapper

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = session.get("user")
        if not user:
            return jsonify({"error": "No autenticado"}), 401
        if user.get("rol") != "admin":
            return jsonify({"error": "No autorizado"}), 403
        return f(*args, **kwargs)
    return decorated

def user_or_admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        user = session.get("user")
        if not user:
            return jsonify({"error": "Debes iniciar sesión"}), 403
        
        if user.get("rol") not in ["user", "admin"]:
            return jsonify({"error": "No tienes permisos para esta acción"}), 403
        
        return f(*args, **kwargs)
    return wrapper
