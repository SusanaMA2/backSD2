from flask import Blueprint, redirect, url_for, session, jsonify, request
from authlib.integrations.flask_client import OAuth
from models import User
from db_setup import db
from config import Config
from urllib.parse import urlencode
from authlib.jose import jwk
import secrets
from authlib.integrations.base_client import MismatchingStateError



users_bp = Blueprint("users_bp", __name__, url_prefix="/api/users")

oauth = OAuth()
google = None

def init_oauth(app):
    global google
    oauth.init_app(app)
    google = oauth.register(
        name="google",
        client_id=Config.GOOGLE_CLIENT_ID,
        client_secret=Config.GOOGLE_CLIENT_SECRET,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )

@users_bp.route('/google/login')
def google_login():
    nonce = secrets.token_urlsafe(16)
    session['nonce'] = nonce

    return oauth.google.authorize_redirect(
        redirect_uri=Config.GOOGLE_REDIRECT_URI,
        nonce=nonce
    )

@users_bp.route('/google/callback')
def google_callback():
    try:
        token = oauth.google.authorize_access_token()  # <-- protegido
    except MismatchingStateError:
        return jsonify({"error": "State no coincide. Reintentar login"}), 400

    nonce = session.pop('nonce', None)
    if not nonce:
        return jsonify({'error': 'Nonce faltante'}), 400

    user_info = oauth.google.parse_id_token(token, nonce=nonce)

    # Verificar si usuario ya existe
    usuario_db = User.query.filter_by(correo=user_info["email"]).first()
    if usuario_db:
        rol = usuario_db.rol
    else:
        # Crear usuario automáticamente como "user"
        nuevo_usuario = User(
            nombre=user_info.get("name"),
            correo=user_info["email"],
            contraseña="google_sso",
            rol="user",
            estado="activo",
        )
        db.session.add(nuevo_usuario)
        db.session.commit()
        rol = "user"

    # Guardar sesión real con rol correcto
    session["user"] = {
        "id": user_info["email"],
        "nombre": user_info.get("name"),
        "correo": user_info["email"],
        "rol": rol
    }

    # Redirigir al frontend
    return redirect("http://localhost:5173/login/callback")

    

@users_bp.route("/session", methods=["GET"])
def session_info():
    user = session.get("user")
    print("Usuario en sesión:", user)  # <--- agrega esto
    if not user:
        return jsonify({"usuario": None}), 200
    return jsonify({"usuario": user}), 200



@users_bp.route("/registrar", methods=["POST"])
def register_user():
    current_user = session.get("user")

    if not current_user or current_user.get("rol") != "admin":
        return jsonify({"error": "No tienes permisos para registrar usuarios."}), 403

    data = request.get_json()
    nombre = data.get("nombre")
    correo = data.get("correo")
    rol = data.get("rol", "user")

    if User.query.filter_by(correo=correo).first():
        return jsonify({"error": "El usuario ya existe."}), 400

    nuevo_usuario = User(
        nombre=nombre,
        correo=correo,
        contraseña="google_sso",
        rol=rol,
        estado="activo",
    )
    db.session.add(nuevo_usuario)
    db.session.commit()

    return jsonify({"mensaje": f"Usuario {nombre} registrado correctamente con rol {rol}."}), 201


#listar usuarios
@users_bp.route("/", methods=["GET"])
def listar_usuarios():
    current_user = session.get("user")
    if not current_user or current_user.get("rol") != "admin":
        return jsonify({"error": "No tienes permisos de administrador"}), 403

    usuarios = User.query.filter_by(estado="activo").all() 
    return jsonify([
        {
            "id": u.id,
            "nombre": u.nombre,
            "correo": u.correo,
            "rol": u.rol,
            "estado": u.estado,
            "fecha_registro": u.fecha_registro.strftime("%Y-%m-%d %H:%M:%S")
        } for u in usuarios
    ]), 200

#eliminar
@users_bp.route("/<int:id>", methods=["DELETE"])
def desactivar_usuario(id):
    current_user = session.get("user")

    if not current_user or current_user.get("rol") != "admin":
        return jsonify({"error": "No tienes permisos"}), 403

    usuario = User.query.get(id)
    if not usuario:
        return jsonify({"error": "Usuario no encontrado"}), 404

    usuario.estado = "inactivo"  # ← Solo desactiva
    db.session.commit()

    return jsonify({"mensaje": "Usuario desactivado correctamente"}), 200



#editar
@users_bp.route("/<int:id>", methods=["PUT"])
def editar_usuario(id):
    current_user = session.get("user")

    # Solo administradores pueden editar
    if not current_user or current_user.get("rol") != "admin":
        return jsonify({"error": "No tienes permisos"}), 403

    usuario = User.query.get(id)
    if not usuario:
        return jsonify({"error": "Usuario no encontrado"}), 404

    data = request.get_json()

    # Validar valores permitidos
    estado = data.get("estado", usuario.estado)
    rol = data.get("rol", usuario.rol)

    if estado not in ["activo", "inactivo"]:
        return jsonify({"error": "Estado inválido. Valores permitidos: activo o inactivo"}), 400

    if rol not in ["admin", "user"]:
        return jsonify({"error": "Rol inválido. Valores permitidos: admin o user"}), 400

    usuario.estado = estado
    usuario.rol = rol

    db.session.commit()

    return jsonify({
        "mensaje": "Usuario actualizado correctamente",
        "usuario": {
            "id": usuario.id,
            "nombre": usuario.nombre,
            "correo": usuario.correo,
            "rol": usuario.rol,
            "estado": usuario.estado
        }
    }), 200



@users_bp.route("/logout")
def logout():
    session.clear()
    return jsonify({"mensaje": "Sesión cerrada correctamente"})
