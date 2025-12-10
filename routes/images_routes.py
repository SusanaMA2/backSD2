from flask import Blueprint, request, jsonify,session
from datetime import datetime
from models import Imagen, User
from db_setup import db
from utils.decorators import user_or_admin_required,login_required,admin_required

images_bp = Blueprint("images_bp", __name__, url_prefix="/api/images")

# Obtener todas las imágenes
@images_bp.route("/", methods=["GET"])

def obtener_imagenes():
    imagenes = Imagen.query.all()
    lista = []
    for img in imagenes:
        lista.append({
            "id": img.id,
            "titulo": img.titulo,
            "url": img.url,
            "descripcion": img.descripcion,
            "fecha_subida": img.fecha_subida.strftime("%Y-%m-%d %H:%M:%S"),
            "autor": User.query.get(img.user_id).nombre if img.user_id else ""
        })
    return jsonify(lista), 200

# Crear imagen (rol enviado desde frontend)
@images_bp.route('/', methods=['POST'])
@admin_required
def crear_imagen():
    data = request.get_json()
    user = session.get("user")
    usuario = User.query.get(user["id"])

    if not data.get('titulo') or not data.get('url'):
        return jsonify({'error': 'El título y la URL son obligatorios'}), 400

    nueva = Imagen(
        titulo=data['titulo'],
        url=data['url'],
        descripcion=data.get('descripcion', ''),
        fecha_subida=datetime.now(),
        user_id=usuario.id
    )
    db.session.add(nueva)
    db.session.commit()

    return jsonify({'mensaje': 'Imagen creada correctamente', 'id': nueva.id}), 201



# Editar imagen
@images_bp.route('/<int:id>', methods=['PUT'])
@admin_required
def editar_imagen(id):
    imagen = Imagen.query.get_or_404(id)
    data = request.get_json()
    imagen.titulo = data.get("titulo", imagen.titulo)
    imagen.url = data.get("url", imagen.url)
    imagen.descripcion = data.get("descripcion", imagen.descripcion)
    db.session.commit()
    return jsonify({"mensaje": "Imagen actualizada correctamente"}), 200


# Eliminar imagen
@images_bp.route("/<int:id>", methods=["DELETE"])
@admin_required
def eliminar_imagen(id):
    data = request.get_json()
    rol = data.get("rol", "").upper()

    if rol != "ADMIN":
        return jsonify({"error": "No tienes permisos de administrador"}), 403

    imagen = Imagen.query.get(id)
    if not imagen:
        return jsonify({"error": "Imagen no encontrada"}), 404

    db.session.delete(imagen)
    db.session.commit()
    return jsonify({"mensaje": "Imagen eliminada correctamente"}), 200


@images_bp.route("/check-session")
def check_session():
    return jsonify(session.get("user"))
