from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
from models import User

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        current_user_id = get_jwt_identity()
        if not isinstance(current_user_id, str):
            current_user_id = str(current_user_id)
        rol = claims.get("rol", None)
        if rol != "admin":
            return jsonify({"error": "Acceso denegado. Solo administradores."}), 403
        return fn(*args, **kwargs)
    return wrapper


def user_required(fn):
    
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        current_user_id = get_jwt_identity()
        if not isinstance(current_user_id, str):
            current_user_id = str(current_user_id)
        rol = claims.get("rol", None)

        usuario = User.query.get(current_user_id)
        if not usuario or usuario.estado != "activo":
            return jsonify({"error": "Usuario no válido o inactivo"}), 403

        if rol not in ["user", "admin"]:
            return jsonify({"error": "Acceso denegado"}), 403

        kwargs["usuario"] = usuario
        kwargs["rol"] = rol
        return fn(*args, **kwargs)
    return wrapper
