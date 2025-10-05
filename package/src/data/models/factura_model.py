from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Esta instancia será inicializada en app.py
db = None

def create_factura_model(database):
    """Crear el modelo Factura con la instancia de db proporcionada"""
    global db
    db = database
    
    class Factura(db.Model):        
        __table_args__ = {'schema': 'documents'}
        __tablename__ = 'facturas'

        id = db.Column(db.Integer, primary_key=True)
        organizacion = db.Column(db.String(255), nullable=False)
        ruta_factura = db.Column(db.String(500), nullable=False)
        fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
        fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

        def __repr__(self):
            return f'<Factura {self.id}: {self.organizacion}>'

        def to_dict(self):
            return {
                'id': self.id,
                'organizacion': self.organizacion,
                'ruta_factura': self.ruta_factura,
                'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
                'fecha_actualizacion': self.fecha_actualizacion.isoformat() if self.fecha_actualizacion else None
            }
    return Factura
