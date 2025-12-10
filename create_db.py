from app import create_app
from db_setup import db

app = create_app()

with app.app_context():
    db.create_all()
    print("Tablas creadas o ya existen.")
