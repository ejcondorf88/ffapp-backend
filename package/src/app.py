from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import os
from configuration.database_config import DatabaseConfig

# Inicializar extensiones
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    
    # Cargar configuración
    # Cargar configuración directamente desde DatabaseConfig
    config_dict = DatabaseConfig.get_config_dict()
    app.config.update(config_dict)
    
    # Inicializar extensiones con la app
    db.init_app(app)
    CORS(app)
    
    # Crear el modelo con la instancia de db
    from data.models.factura_model import create_factura_model
    Factura = create_factura_model(db)
    
    # Registrar blueprints
    from presentation.controller.factura_controller import factura_bp
    app.register_blueprint(factura_bp)
    
    # Verificar y crear el esquema 'documents' si no existe
    with app.app_context():
        try:
            db.session.execute("CREATE SCHEMA IF NOT EXISTS documents;")
            db.session.commit()
            db.create_all()
            # Verificar si la tabla existe en el esquema correcto
            result = db.session.execute("""
                SELECT table_schema, table_name
                FROM information_schema.tables
                WHERE table_schema = 'documents' AND table_name = 'facturas';
            """)
            table_info = result.fetchone()
            if table_info:
                print(f"✅ Tabla '{table_info.table_name}' creada en el esquema '{table_info.table_schema}' correctamente.")
            else:
                print("⚠️  La tabla 'facturas' no se encuentra en el esquema 'documents'. Revisa la configuración y migraciones.")
        except Exception as e:
            print(f"⚠️  Error conectando a la base de datos o creando esquema/tablas: {e}")
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)