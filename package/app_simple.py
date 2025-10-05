from flask import Flask, request, jsonify, current_app
from flask_cors import CORS
import os
from datetime import datetime
from src.models import db, Factura
from src.configuration.database_config import DatabaseConfig

def create_app():
    from sqlalchemy import text
    app = Flask(__name__)
    
    # Configuración desde DatabaseConfig
    config_dict = DatabaseConfig.get_config_dict()
    app.config.update(config_dict)
    
    # Inicializar extensiones
    db.init_app(app)
    CORS(app)
    
    # Crear tablas (solo si no existen)
    with app.app_context():
        try:
            db.create_all()
            # Verificar si la tabla existe en el esquema correcto
            result = db.session.execute(text("""
                SELECT table_schema, table_name
                FROM information_schema.tables
                WHERE table_schema = 'documents' AND table_name = 'facturas';
            """))
            table_info = result.fetchone()
            if table_info:
                print(f"✅ Tabla '{table_info.table_name}' creada en el esquema '{table_info.table_schema}' correctamente.")
            else:
                print("⚠️  La tabla 'facturas' no se encuentra en el esquema 'documents'. Revisa la configuración y migraciones.")
        except Exception as e:
            print(f"⚠️ Error conectando a la base de datos: {e}")
    
    return app

# Crear la aplicación
app = create_app()

@app.route('/api/facturas/test', methods=['GET'])
def test_connection():
    """Probar conexión a la base de datos"""
    try:
        # Hacer una consulta simple
        result = db.session.execute(db.text("SELECT 1 as test, NOW() as current_time"))
        test_data = result.fetchone()
        
        return jsonify({
            'success': True,
            'message': 'Conexión a base de datos exitosa',
            'test_value': test_data[0],
            'current_time': str(test_data[1]),
            'database_url': app.config.get('SQLALCHEMY_DATABASE_URI', 'No configurado')
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error de conexión a base de datos: {str(e)}',
            'database_url': app.config.get('SQLALCHEMY_DATABASE_URI', 'No configurado')
        }), 500

@app.route('/api/facturas/upload', methods=['POST'])
def upload_factura():
    try:
        # Obtener archivo y datos del formulario
        file = request.files.get('file')
        organizacion = request.form.get('organizacion')
        fecha_str = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        org_clean = organizacion.replace(" ", "_") if organizacion else "Desconocida"
        files_folder = os.path.join(os.path.dirname(__file__), 'src', 'configuration', 'files')
        if not os.path.exists(files_folder):
            os.makedirs(files_folder)

        # Generar nombre del archivo
        filename = f"ONG-{org_clean}_Factura_{fecha_str}.pdf"
        file_path = os.path.join(files_folder, filename)
        archivo_existe = os.path.exists(file_path)
        reemplazar = request.form.get('reemplazar', 'false').lower() == 'true'

        # Buscar registro existente en base de datos por organización
        factura_existente = Factura.query.filter_by(organizacion=organizacion).first()

        if factura_existente and not reemplazar:
            return jsonify({
                'success': False,
                'error': 'Archivo ya existe',
                'message': 'Ya existe una factura para esta organización',
                'archivo_existente': True,
                'factura_id': factura_existente.id,
                'filename': filename,
                'sugerencia': 'Si desea reemplazarlo, envíe reemplazar=true en el formulario'
            }), 409  # Conflict

        if factura_existente and reemplazar:
            # Eliminar archivo anterior si existe
            try:
                if os.path.exists(factura_existente.ruta_factura):
                    os.remove(factura_existente.ruta_factura)
                    print(f"🗑️ Archivo anterior eliminado: {factura_existente.ruta_factura}")
            except Exception as e:
                print(f"⚠️ Error eliminando archivo anterior: {e}")
            # Actualizar registro existente
            factura_existente.ruta_factura = file_path
            factura_existente.fecha_actualizacion = datetime.utcnow()
            file.save(file_path)
            db.session.commit()
            print("✅ Registro existente actualizado en base de datos")
            return jsonify({
                'success': True,
                'message': 'Factura reemplazada exitosamente',
                'filename': filename,
                'file_path': file_path,
                'factura_id': factura_existente.id,
                'organizacion': organizacion,
                'reemplazado': True
            }), 200

        if not factura_existente:
            # Guardar archivo y crear nuevo registro
            file.save(file_path)
            print(f"✅ SUCCESS: Archivo guardado en: {file_path}")
            try:
                factura = Factura(
                    organizacion=organizacion,
                    ruta_factura=file_path
                )
                db.session.add(factura)
                db.session.commit()
                print("✅ SUCCESS: Nuevo registro guardado en base de datos")
                return jsonify({
                    'success': True,
                    'message': 'Factura guardada exitosamente',
                    'filename': filename,
                    'file_path': file_path,
                    'factura_id': factura.id,
                    'organizacion': organizacion,
                    'reemplazado': False
                }), 201
            except Exception as db_error:
                print(f"❌ ERROR: Error en base de datos: {db_error}")
                db.session.rollback()
                return jsonify({
                    'success': False,
                    'error': f'Error guardando en base de datos: {str(db_error)}'
                }), 500

        # Si existe y se quiere reemplazar, eliminar el archivo anterior
        if archivo_existe and reemplazar:
            try:
                os.remove(file_path)
                print(f"🗑️ Archivo anterior eliminado: {file_path}")

                # Actualizar registro en base de datos si existe
                factura_existente = Factura.query.filter_by(
                    organizacion=organizacion,
                    ruta_factura=file_path
                ).first()

                if factura_existente:
                    factura_existente.fecha_actualizacion = datetime.utcnow()
                    db.session.commit()
                    print("✅ Registro existente actualizado en base de datos")

            except Exception as e:
                print(f"⚠️ Error eliminando archivo anterior: {e}")

        # Guardar archivo
        file.save(file_path)
        print(f"✅ SUCCESS: Archivo guardado en: {file_path}")

        # Guardar en base de datos
        try:
            # Si no existe o se está reemplazando, crear nuevo registro
            if not archivo_existe or reemplazar:
                factura = Factura(
                    organizacion=organizacion,
                    ruta_factura=file_path
                )
                db.session.add(factura)
                db.session.commit()
                print("✅ SUCCESS: Nuevo registro guardado en base de datos")

                return jsonify({
                    'success': True,
                    'message': 'Factura guardada exitosamente',
                    'filename': filename,
                    'file_path': file_path,
                    'factura_id': factura.id,
                    'organizacion': organizacion,
                    'reemplazado': reemplazar
                }), 201
            else:
                return jsonify({
                    'success': True,
                    'message': 'Archivo ya existe, no se realizaron cambios',
                    'filename': filename,
                    'file_path': file_path,
                    'organizacion': organizacion
                }), 200

        except Exception as db_error:
            print(f"❌ ERROR: Error en base de datos: {db_error}")
            db.session.rollback()
            return jsonify({
                'success': False,
                'error': f'Error guardando en base de datos: {str(db_error)}'
            }), 500

    except Exception as e:
        print(f"💥 EXCEPTION: Error interno del servidor: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }), 500

@app.route('/api/facturas/', methods=['GET'])
def get_all_facturas():
    """Obtener todas las facturas"""
    try:
        facturas = Factura.query.all()
        return jsonify({
            'success': True,
            'facturas': [factura.to_dict() for factura in facturas],
            'total': len(facturas)
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error al obtener las facturas: {str(e)}'
        }), 500

@app.route('/api/facturas/<int:factura_id>', methods=['GET'])
def get_factura(factura_id):
    """Obtener una factura por ID"""
    try:
        factura = Factura.query.get(factura_id)
        if factura:
            return jsonify({
                'success': True,
                'factura': factura.to_dict()
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Factura no encontrada'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error al obtener la factura: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
