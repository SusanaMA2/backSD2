from datetime import datetime
from db_setup import db

# ==========================
#  USUARIOS
# ==========================
class User(db.Model):
    __tablename__ = "usuarios"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    correo = db.Column(db.String(100), unique=True, nullable=False)
    contraseña = db.Column(db.String(200), nullable=False)
    rol = db.Column(db.String(20), default="user")  # 'admin' o 'user'
    estado = db.Column(db.String(20), default="activo")
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)

    noticias = db.relationship("Noticia", backref="autor", lazy=True)
    eventos = db.relationship("Evento", backref="autor", lazy=True)
    imagenes = db.relationship("Imagen", backref="autor", lazy=True)
    videos = db.relationship("Video", backref="autor", lazy=True)
    comentarios = db.relationship("Comentario", backref="usuario", lazy=True)
    inscripciones_evento = db.relationship("InscripcionEvento", back_populates="usuario", lazy=True)


# ==========================
#  NOTICIAS
# ==========================
class Noticia(db.Model):
    __tablename__ = "noticias"
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    contenido = db.Column(db.Text, nullable=False)
    fecha_publicacion = db.Column(db.DateTime, default=datetime.utcnow)
    permitir_comentarios = db.Column(db.Boolean, default=True)
    tipo = db.Column(db.String(20), default="informativa")  # 'informativa' o 'evento'

    evento_id = db.Column(db.Integer, db.ForeignKey("eventos.id"), nullable=True)
    evento = db.relationship("Evento", back_populates="noticia")

    user_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)

    comentarios = db.relationship("Comentario", backref="noticia", lazy=True)


# ==========================
#  EVENTOS
# ==========================
class Evento(db.Model):
    __tablename__ = "eventos"
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(150), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    fecha_evento = db.Column(db.DateTime, nullable=False)
    ubicacion = db.Column(db.String(255), nullable=False)
    cupos = db.Column(db.Integer, nullable=True)
    activo = db.Column(db.Boolean, default=True)

    noticia = db.relationship("Noticia", back_populates="evento", uselist=False)
    inscripciones = db.relationship("InscripcionEvento", back_populates="evento", lazy=True)

    user_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)


# ==========================
#  INSCRIPCIONES A EVENTOS
# ==========================
class InscripcionEvento(db.Model):
    __tablename__ = "inscripciones_evento"
    id = db.Column(db.Integer, primary_key=True)
    fecha_inscripcion = db.Column(db.DateTime, default=datetime.utcnow)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    evento_id = db.Column(db.Integer, db.ForeignKey("eventos.id"), nullable=False)

    usuario = db.relationship("User", back_populates="inscripciones_evento", lazy=True)
    evento = db.relationship("Evento", back_populates="inscripciones", lazy=True)


# ==========================
#  COMENTARIOS
# ==========================
class Comentario(db.Model):
    __tablename__ = "comentarios"
    id = db.Column(db.Integer, primary_key=True)
    texto = db.Column(db.Text, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    noticia_id = db.Column(db.Integer, db.ForeignKey("noticias.id"), nullable=False)


# ==========================
#  IMÁGENES
# ==========================
class Imagen(db.Model):
    __tablename__ = "imagenes"
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(300), nullable=False)
    descripcion = db.Column(db.Text)
    fecha_subida = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)


# ==========================
#  VIDEOS
# ==========================
class Video(db.Model):
    __tablename__ = "videos"
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(300), nullable=False)
    descripcion = db.Column(db.Text)
    fecha_subida = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
