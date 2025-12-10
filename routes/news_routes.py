from flask import Blueprint, request, jsonify, session
from db_setup import db
from models import Noticia, Evento, Comentario, User
from datetime import datetime
from utils.decorators import user_or_admin_required,login_required,admin_required

news_bp = Blueprint('news_bp', __name__, url_prefix='/api/news')

#------------------------------------------------------------------------------------------
# Listar noticias (público)
@news_bp.route('/noticias', methods=['GET'])
def listar_noticias():
    noticias = Noticia.query.all()
    return jsonify([{
        'id': n.id,
        'titulo': n.titulo,
        'contenido': n.contenido,
        'fecha_publicacion': n.fecha_publicacion.strftime("%Y-%m-%d %H:%M:%S"),
        'tipo': n.tipo,
        'permitir_comentarios': n.permitir_comentarios,
        'autor': n.autor.nombre if n.autor else None,
        'evento_relacionado': n.evento.titulo if n.evento else None
    } for n in noticias]), 200


#------------------------------------------------------------------------------------------
# Obtener noticia por titulo 
@news_bp.route('/noticias/titulo/<string:titulo>', methods=['GET'])
def obtener_noticia_por_titulo(titulo):
    noticia = Noticia.query.filter(Noticia.titulo.ilike(f"%{titulo}%")).first()
    if not noticia:
        return jsonify({'error': 'Noticia no encontrada'}), 404

    return jsonify({
        'id': noticia.id,
        'titulo': noticia.titulo,
        'contenido': noticia.contenido,
        'fecha_publicacion': noticia.fecha_publicacion.strftime("%Y-%m-%d %H:%M:%S"),
        'tipo': noticia.tipo,
        'permitir_comentarios': noticia.permitir_comentarios,
        'autor': noticia.autor.nombre if noticia.autor else None,
        'evento_relacionado': noticia.evento.titulo if noticia.evento else None
    }), 200

#------------------------------------------------------------------------------------------
#  Buscar noticia por fecha
@news_bp.route('/noticias/fecha/<string:fecha>', methods=['GET'])
def buscar_por_fecha(fecha):
    try:
        fecha_dt = datetime.strptime(fecha, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({'error': 'Formato de fecha inválido. Use YYYY-MM-DD'}), 400

    noticias = Noticia.query.filter(db.func.date(Noticia.fecha_publicacion) == fecha_dt).all()
    return jsonify([{
        'id': n.id,
        'titulo': n.titulo,
        'fecha_publicacion': n.fecha_publicacion,
        'tipo': n.tipo
    } for n in noticias]), 200

#------------------------------------------------------------------------------------------
@news_bp.route('/noticias', methods=['POST'])
@admin_required
def crear_noticia():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No se enviaron datos'}), 400

    titulo = data.get('titulo')
    contenido = data.get('contenido')
    if not titulo or not contenido:
        return jsonify({'error': 'Faltan campos obligatorios'}), 400

    tipo = data.get('tipo', 'informativa')
    evento_id = data.get('evento_id')

    # Validar sesión
    user_data = session.get("user")
    if not user_data:
        return jsonify({'error': 'No hay usuario en sesión'}), 401
    autor = User.query.get(user_data.get("id"))
    if not autor:
        return jsonify({'error': 'Usuario no encontrado'}), 400

    # Validar evento si es tipo evento
    if tipo == 'evento':
        try:
            evento_id = int(evento_id)
            if not Evento.query.get(evento_id):
                return jsonify({'error': 'Evento no existe'}), 400
        except:
            return jsonify({'error': 'ID de evento inválido'}), 400
    else:
        evento_id = None

    permitir_comentarios = bool(data.get('permitir_comentarios', True))

    try:
        nueva = Noticia(
            titulo=titulo,
            contenido=contenido,
            tipo=tipo,
            permitir_comentarios=permitir_comentarios,
            user_id=autor.id,
            evento_id=evento_id
        )
        db.session.add(nueva)
        db.session.commit()

        return jsonify({
            'mensaje': 'Noticia creada correctamente',
            'noticia': {
                'id': nueva.id,
                'titulo': nueva.titulo,
                'tipo': nueva.tipo,
                'autor': autor.nombre
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        print("ERROR creando noticia:", e)
        return jsonify({'error': f'Error al crear noticia: {str(e)}'}), 500
#------------------------------------------------------------------------------------------
# Editar noticia (solo admin)
@news_bp.route('/noticias/<int:id>', methods=['PUT'])
@admin_required
def editar_noticia(id):
    noticia = Noticia.query.get_or_404(id)
    data = request.get_json()

    noticia.titulo = data.get('titulo', noticia.titulo)
    noticia.contenido = data.get('contenido', noticia.contenido)
    noticia.tipo = data.get('tipo', noticia.tipo)
    noticia.permitir_comentarios = data.get('permitir_comentarios', noticia.permitir_comentarios)
    noticia.evento_id = data.get('evento_id', noticia.evento_id)

    db.session.commit()
    return jsonify({'mensaje': 'Noticia actualizada correctamente'}), 200

#------------------------------------------------------------------------------------------
# Eliminar noticia (solo admin)
@news_bp.route('/noticias/<int:id>', methods=['DELETE'])
@admin_required
def eliminar_noticia(id):
    noticia = Noticia.query.get_or_404(id)
    db.session.delete(noticia)
    db.session.commit()
    return jsonify({'mensaje': 'Noticia eliminada correctamente'}), 200


#------------------------------------------------------------------------------------------
# Comentar noticia (usuarios activos)
@news_bp.route('/noticias/<int:noticia_id>/comentarios', methods=['POST'])
@user_or_admin_required
def comentar_noticia(noticia_id):
    noticia = Noticia.query.get_or_404(noticia_id)
    if not noticia.permitir_comentarios:
        return jsonify({'error': 'Los comentarios están deshabilitados'}), 403

    user = session.get("user")
    usuario = User.query.get(user["id"])

    data = request.get_json()
    nuevo = Comentario(
        texto=data['texto'],
        noticia_id=noticia_id,
        user_id=usuario.id
    )
    db.session.add(nuevo)
    db.session.commit()
    return jsonify({'mensaje': 'Comentario agregado correctamente'}), 201



#------------------------------------------------------------------------------------------
# Listar comentarios de una noticia (público)
@news_bp.route('/noticias/<int:noticia_id>/comentarios', methods=['GET'])
def listar_comentarios(noticia_id):
    comentarios = Comentario.query.filter_by(noticia_id=noticia_id).all()
    return jsonify([{
        'id': c.id,
        'texto': c.texto,
        'fecha': c.fecha.strftime("%Y-%m-%d %H:%M:%S"),
        'autor': c.usuario.nombre if c.usuario else None
    } for c in comentarios]), 200


#------------------------------------------------------------------------------------------
#  Compartir noticia (simulado)
@news_bp.route('/noticias/<int:id>/compartir', methods=['POST'])
@user_or_admin_required
def compartir_noticia(id):
    noticia = Noticia.query.get_or_404(id)

    # Obtener usuario desde session (no JWT)
    user_data = session.get("user")
    usuario = User.query.get(user_data["id"])

    return jsonify({
        'mensaje': f'La noticia "{noticia.titulo}" fue compartida por {usuario.nombre}'
    }), 200



@news_bp.route('/noticias/test', methods=['POST'])
def crear_noticia_test():
    data = request.get_json()
    return jsonify({"recibido": data}), 200