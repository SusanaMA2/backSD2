from flask import Blueprint, request, jsonify, session
from db_setup import db
from datetime import datetime
from models import Evento, User, InscripcionEvento
from utils.decorators import user_or_admin_required,login_required,admin_required

events_bp = Blueprint("events_bp", __name__, url_prefix="/api/events")

#-------------------------------------------------------------------------
# Listar todos los eventos (público)
@events_bp.route("/", methods=["GET"])
def listar_eventos():
    eventos = Evento.query.all()
    return jsonify([
        {
            "id": e.id,
            "titulo": e.titulo,
            "descripcion": e.descripcion,
            "fecha_evento": e.fecha_evento.strftime("%Y-%m-%d %H:%M:%S"),
            "ubicacion": e.ubicacion,
            "cupos": e.cupos,
            "activo": e.activo,
            "autor": e.autor.nombre if e.autor else None
        } for e in eventos
    ]), 200


#-------------------------------------------------------------------------
# Obtener evento por ID (público)
@events_bp.route("/<int:id>", methods=["GET"])
def obtener_evento(id):
    evento = Evento.query.get_or_404(id)
    return jsonify({
        "id": evento.id,
        "titulo": evento.titulo,
        "descripcion": evento.descripcion,
        "fecha_evento": evento.fecha_evento.strftime("%Y-%m-%d %H:%M:%S"),
        "ubicacion": evento.ubicacion,
        "cupos": evento.cupos,
        "activo": evento.activo,
        "autor": evento.autor.nombre if evento.autor else None
    }), 200


#-------------------------------------------------------------------------
# Crear evento (solo admin)
@events_bp.route("/", methods=["POST"])
@admin_required
def crear_evento():
    data = request.get_json()
    if not data.get("titulo") or not data.get("descripcion") or not data.get("fecha_evento"):
        return jsonify({"error": "Faltan campos obligatorios"}), 400
    try:
        fecha_evento = datetime.strptime(data["fecha_evento"], "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return jsonify({"error": "Formato de fecha inválido. Usa YYYY-MM-DD HH:MM:SS"}), 400
    user = session.get("user")
    usuario = User.query.get(user["id"])
    nuevo_evento = Evento(
        titulo=data["titulo"],
        descripcion=data["descripcion"],
        fecha_evento=fecha_evento,
        ubicacion=data.get("ubicacion", "Por definir"),
        cupos=data.get("cupos"),
        activo=True,
        user_id=usuario.id
    )
    db.session.add(nuevo_evento)
    db.session.commit()
    return jsonify({
        "mensaje": "Evento creado correctamente",
        "evento": {
            "id": nuevo_evento.id,
            "titulo": nuevo_evento.titulo,
            "autor": usuario.nombre,
            "fecha_evento": nuevo_evento.fecha_evento.strftime("%Y-%m-%d %H:%M:%S")
        }
    }), 201

#-------------------------------------------------------------------------
# Editar evento (solo admin)
@events_bp.route("/<int:id>", methods=["PUT"])
@admin_required
def editar_evento(id):
    evento = Evento.query.get_or_404(id)
    data = request.get_json()
    if "titulo" in data:
        evento.titulo = data["titulo"]
    if "descripcion" in data:
        evento.descripcion = data["descripcion"]
    if "fecha_evento" in data:
        try:
            evento.fecha_evento = datetime.strptime(data["fecha_evento"], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return jsonify({"error": "Formato de fecha inválido"}), 400
    if "ubicacion" in data:
        evento.ubicacion = data["ubicacion"]
    if "cupos" in data:
        evento.cupos = data["cupos"]
    if "activo" in data:
        evento.activo = data["activo"]
    db.session.commit()
    return jsonify({"mensaje": "Evento actualizado correctamente"}), 200

#-------------------------------------------------------------------------
# Eliminar evento (solo admin)

@events_bp.route("/<int:id>", methods=["DELETE"])
@admin_required
def eliminar_evento(id):
    evento = Evento.query.get_or_404(id)
    db.session.delete(evento)
    db.session.commit()
    return jsonify({"mensaje": "Evento eliminado correctamente"}), 200

#-------------------------------------------------------------------------
# Inscribirse a un evento (solo usuario)
@events_bp.route("/<int:evento_id>/inscribirse", methods=["POST"])
@user_or_admin_required
def inscribirse_evento(evento_id):
    # Obtener usuario desde el decorador (queda en session)
    user_data = session.get("user")
    usuario = User.query.get(user_data["id"])
    rol = user_data.get("rol")

    evento = Evento.query.get_or_404(evento_id)

    if not evento.activo:
        return jsonify({"error": "Evento no disponible"}), 404

    # Verificar si ya está inscrito
    existente = InscripcionEvento.query.filter_by(
        usuario_id=usuario.id,
        evento_id=evento_id
    ).first()

    if existente:
        return jsonify({"error": "Ya estás inscrito en este evento"}), 400

    # Crear inscripción
    inscripcion = InscripcionEvento(usuario_id=usuario.id, evento_id=evento_id)
    db.session.add(inscripcion)
    db.session.commit()

    return jsonify({
        "mensaje": f"Inscripción al evento '{evento.titulo}' registrada exitosamente",
        "usuario": usuario.nombre
    }), 201

#-------------------------------------------------------------------------
# Listar inscripciones a un evento (solo admin)

@events_bp.route("/<int:evento_id>/inscripciones", methods=["GET"])
@admin_required
def listar_inscripciones_evento(evento_id):
    evento = Evento.query.get_or_404(evento_id)
    inscripciones = InscripcionEvento.query.filter_by(evento_id=evento_id).all()
    return jsonify([
        {
            "id": ins.id,
            "usuario": ins.usuario.nombre,
            "correo": ins.usuario.correo,
            "fecha_inscripcion": ins.fecha_inscripcion.strftime("%Y-%m-%d %H:%M:%S")
        } for ins in inscripciones
    ]), 200

#-------------------------------------------------------------------------
# Listar inscripciones del usuario autenticado

@events_bp.route("/mis-inscripciones", methods=["GET"])
@user_or_admin_required
def mis_inscripciones():
    user_data = session.get("user")
    usuario = User.query.get(user_data["id"])

    inscripciones = InscripcionEvento.query.filter_by(usuario_id=usuario.id).all()

    return jsonify([
        {
            "evento": i.evento.titulo,
            "fecha_evento": i.evento.fecha_evento.strftime("%Y-%m-%d %H:%M:%S"),
            "ubicacion": i.evento.ubicacion,
            "fecha_inscripcion": i.fecha_inscripcion.strftime("%Y-%m-%d %H:%M:%S")
        }
        for i in inscripciones
    ]), 200
