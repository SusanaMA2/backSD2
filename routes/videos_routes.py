from flask import Blueprint, request, jsonify, session
from db_setup import db
from models import Video, User
from datetime import datetime
from utils.decorators import user_or_admin_required,login_required,admin_required

videos_bp = Blueprint('videos_bp', __name__, url_prefix='/api/videos')


# Listar todos los videos (público)
@videos_bp.route('/', methods=['GET'])
def listar_videos():
    videos = Video.query.all()
    return jsonify([{
        'id': v.id,
        'titulo': v.titulo,
        'url': v.url,
        'descripcion': v.descripcion,
        'fecha_subida': v.fecha_subida.strftime("%Y-%m-%d %H:%M:%S") if v.fecha_subida else None,
        'autor': v.autor.nombre if v.autor else None
    } for v in videos]), 200

# Crear nuevo video (solo admin)
@videos_bp.route('/', methods=['POST'])
@admin_required
def crear_video():
    data = request.get_json()
    user = session.get("user")
    autor = User.query.get(user["id"])

    if not data.get('titulo') or not data.get('url'):
        return jsonify({'error': 'El título y la URL son obligatorios'}), 400

    nuevo = Video(
        titulo=data['titulo'],
        url=data['url'],
        descripcion=data.get('descripcion', ''),
        fecha_subida=datetime.now(),
        user_id=autor.id
    )
    db.session.add(nuevo)
    db.session.commit()

    return jsonify({'mensaje': 'Video creado correctamente', 'id': nuevo.id}), 201

# Editar video (solo admin)
@videos_bp.route('/<int:id>', methods=['PUT'])
@admin_required
def editar_video(id):
    video = Video.query.get_or_404(id)
    data = request.get_json()

    video.titulo = data.get('titulo', video.titulo)
    video.url = data.get('url', video.url)
    video.descripcion = data.get('descripcion', video.descripcion)

    db.session.commit()
    return jsonify({'mensaje': 'Video actualizado correctamente'}), 200

# Eliminar video (solo admin)
@videos_bp.route('/<int:id>', methods=['DELETE'])
@admin_required
def eliminar_video(id):
    video = Video.query.get_or_404(id)
    db.session.delete(video)
    db.session.commit()
    return jsonify({'mensaje': 'Video eliminado correctamente'}), 200
