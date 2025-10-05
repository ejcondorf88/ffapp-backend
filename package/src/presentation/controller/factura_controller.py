from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os

factura_bp = Blueprint('facturas', __name__, url_prefix='/api/facturas')

@factura_bp.route('/test', methods=['GET'])
def test_connection():
    """Endpoint de prueba para verificar la conexión"""
    try:
        from ...data.models.factura_model import create_factura_model
        from ...app import db
        
        # Crear el modelo con la instancia de db actual
        Factura = create_factura_model(db)
        
        # Hacer una consulta simple
        result = db.session.execute(db.text("SELECT 1 as test"))
        test_value = result.fetchone()[0]
        
        return jsonify({
            'success': True,
            'message': 'Conexión a base de datos exitosa',
            'test_value': test_value,
            'database_url': current_app.config.get('SQLALCHEMY_DATABASE_URI', 'No configurado')
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error de conexión a base de datos: {str(e)}',
            'database_url': current_app.config.get('SQLALCHEMY_DATABASE_URI', 'No configurado')
        }), 500

@factura_bp.route('/upload', methods=['POST'])
def upload_factura():
    """Endpoint para subir una factura PDF"""
    try:
        print("🔍 DEBUG: Iniciando upload de factura")
        print(f"🔍 DEBUG: Headers: {dict(request.headers)}")
        print(f"🔍 DEBUG: Form data: {dict(request.form)}")
        print(f"🔍 DEBUG: Files: {list(request.files.keys())}")
        
        # Verificar que se envió un archivo
        if 'file' not in request.files:
            print("❌ ERROR: No se proporcionó ningún archivo")
            return jsonify({
                'success': False,
                'error': 'No se proporcionó ningún archivo'
            }), 400
        
        file = request.files['file']
        organizacion = request.form.get('organizacion')
        
        print(f"🔍 DEBUG: Archivo recibido: {file.filename if file else 'None'}")
        print(f"🔍 DEBUG: Organización: {organizacion}")
        
        if not organizacion:
            print("❌ ERROR: No se proporcionó la organización")
            return jsonify({
                'success': False,
                'error': 'No se proporcionó la organización'
            }), 400
        
        if not file or file.filename == '':
            print("❌ ERROR: Archivo vacío o sin nombre")
            return jsonify({
                'success': False,
                'error': 'Archivo vacío o sin nombre'
            }), 400
        
        # Configurar directorio de uploads
        upload_folder = os.path.join(current_app.root_path, '..', 'configuration', 'files')
        upload_folder = os.path.abspath(upload_folder)
        print(f"🔍 DEBUG: Carpeta de upload: {upload_folder}")
        
        # Validar archivo
        if not file.filename.lower().endswith('.pdf'):
            print("❌ ERROR: Solo se permiten archivos PDF")
            return jsonify({
                'success': False,
                'error': 'Solo se permiten archivos PDF'
            }), 400
        
        # Crear directorio si no existe
        os.makedirs(upload_folder, exist_ok=True)
        
        # Generar nombre de archivo estructurado
        from datetime import datetime
        now = datetime.now()
        fecha_str = now.strftime("%d%m%Y")
        
        # Limpiar nombre de la organización
        org_clean = organizacion.replace(' ', '_').replace('(', '').replace(')', '').replace('-', '_')
        org_clean = ''.join(c for c in org_clean if c.isalnum() or c in ['_'])
        
        # Generar nombre del archivo
        filename = f"ONG-{org_clean}_Factura_{fecha_str}.pdf"
        file_path = os.path.join(upload_folder, filename)
        
        # Verificar si el archivo ya existe y agregar sufijo si es necesario
        counter = 1
        while os.path.exists(file_path):
            name, ext = os.path.splitext(filename)
            filename = f"{name}_{counter}{ext}"
            file_path = os.path.join(upload_folder, filename)
            counter += 1
        
        # Guardar archivo
        file.save(file_path)
        print(f"✅ SUCCESS: Archivo guardado en: {file_path}")
        
        # Intentar guardar en base de datos (opcional)
        try:
            from ...data.models.factura_model import create_factura_model
            from ...app import db
            
            # Crear el modelo con la instancia de db actual
            Factura = create_factura_model(db)
            
            factura = Factura(
                organizacion=organizacion,
                ruta_factura=file_path
            )
            db.session.add(factura)
            db.session.commit()
            print("✅ SUCCESS: Registro guardado en base de datos")
            
            return jsonify({
                'success': True,
                'message': 'Factura guardada exitosamente',
                'filename': filename,
                'file_path': file_path,
                'factura_id': factura.id
            }), 201
        except Exception as db_error:
            print(f"⚠️ WARNING: Error en base de datos: {db_error}")
            print("🔄 Continuando sin base de datos...")
            
            return jsonify({
                'success': True,
                'message': 'Factura guardada exitosamente (sin base de datos)',
                'filename': filename,
                'file_path': file_path,
                'warning': 'No se pudo guardar en base de datos'
            }), 201
            
    except Exception as e:
        print(f"💥 EXCEPTION: Error interno del servidor: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Error interno del servidor: {str(e)}'
        }), 500

@factura_bp.route('/', methods=['GET'])
def get_all_facturas():
    """Obtener todas las facturas"""
    try:
        facturas = FacturaService.get_all_facturas()
        return jsonify({
            'success': True,
            'facturas': facturas
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error al obtener las facturas: {str(e)}'
        }), 500

@factura_bp.route('/<int:factura_id>', methods=['GET'])
def get_factura(factura_id):
    """Obtener una factura por ID"""
    try:
        factura = FacturaService.get_factura_by_id(factura_id)
        if factura:
            return jsonify({
                'success': True,
                'factura': factura
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

@factura_bp.route('/organizacion/<string:organizacion>', methods=['GET'])
def get_facturas_by_organizacion(organizacion):
    """Obtener facturas por organización"""
    try:
        facturas = FacturaService.get_facturas_by_organizacion(organizacion)
        return jsonify({
            'success': True,
            'facturas': facturas
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error al obtener las facturas: {str(e)}'
        }), 500

@factura_bp.route('/<int:factura_id>', methods=['DELETE'])
def delete_factura(factura_id):
    """Eliminar una factura"""
    try:
        result = FacturaService.delete_factura(factura_id)
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error al eliminar la factura: {str(e)}'
        }), 500
