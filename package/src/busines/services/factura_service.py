import os
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from werkzeug.utils import secure_filename
from ...data.repository.factura_repository import FacturaRepository
from ...data.models.factura_model import Factura

class FacturaService:
    
    ALLOWED_EXTENSIONS = {'pdf'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    @staticmethod
    def allowed_file(filename: str) -> bool:
        """Verificar si el archivo tiene una extensión permitida"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in FacturaService.ALLOWED_EXTENSIONS
    
    @staticmethod
    def generate_filename(organizacion: str) -> str:
        """Generar nombre de archivo con formato: ONG-Nombre_Factura_DDMMAAAA.pdf"""
        # Obtener fecha actual
        now = datetime.now()
        fecha_str = now.strftime("%d%m%Y")
        
        # Limpiar nombre de la organización para el archivo
        org_clean = organizacion.replace(' ', '_').replace('(', '').replace(')', '').replace('-', '_')
        org_clean = ''.join(c for c in org_clean if c.isalnum() or c in ['_'])
        
        # Generar nombre del archivo
        filename = f"ONG-{org_clean}_Factura_{fecha_str}.pdf"
        
        return filename
    
    @staticmethod
    def validate_file(file) -> Dict[str, Any]:
        """Validar el archivo antes de procesarlo"""
        if not file:
            return {'valid': False, 'error': 'No se proporcionó ningún archivo'}
        
        if not file.filename:
            return {'valid': False, 'error': 'El archivo no tiene nombre'}
        
        if not FacturaService.allowed_file(file.filename):
            return {'valid': False, 'error': 'Solo se permiten archivos PDF'}
        
        # Verificar tamaño del archivo
        file.seek(0, 2)  # Ir al final del archivo
        file_size = file.tell()
        file.seek(0)  # Volver al inicio
        
        if file_size > FacturaService.MAX_FILE_SIZE:
            return {'valid': False, 'error': f'El archivo es demasiado grande. Máximo {FacturaService.MAX_FILE_SIZE // (1024*1024)}MB'}
        
        return {'valid': True}
    
    @staticmethod
    def save_file(file, upload_folder: str, organizacion: str) -> Dict[str, Any]:
        """Guardar el archivo en el sistema de archivos con nombre estructurado"""
        try:
            # Crear directorio si no existe
            os.makedirs(upload_folder, exist_ok=True)
            
            # Generar nombre estructurado para el archivo
            base_filename = FacturaService.generate_filename(organizacion)
            
            # Verificar si el archivo ya existe y agregar sufijo único si es necesario
            file_path = os.path.join(upload_folder, base_filename)
            counter = 1
            while os.path.exists(file_path):
                name, ext = os.path.splitext(base_filename)
                file_path = os.path.join(upload_folder, f"{name}_{counter}{ext}")
                counter += 1
            
            # Obtener el nombre final del archivo
            final_filename = os.path.basename(file_path)
            
            # Guardar archivo
            file.save(file_path)
            
            return {
                'success': True,
                'file_path': file_path,
                'filename': final_filename
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error al guardar el archivo: {str(e)}'
            }
    
    @staticmethod
    def create_factura(organizacion: str, file, upload_folder: str) -> Dict[str, Any]:
        """Crear una nueva factura con archivo"""
        try:
            # Validar archivo
            validation = FacturaService.validate_file(file)
            if not validation['valid']:
                return {
                    'success': False,
                    'error': validation['error']
                }
            
            # Guardar archivo
            save_result = FacturaService.save_file(file, upload_folder, organizacion)
            if not save_result['success']:
                return save_result
            
            # Crear registro en base de datos
            factura = FacturaRepository.create_factura(
                organizacion=organizacion,
                ruta_factura=save_result['file_path']
            )
            
            return {
                'success': True,
                'factura': factura.to_dict(),
                'message': 'Factura creada exitosamente'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Error al crear la factura: {str(e)}'
            }
    
    @staticmethod
    def get_factura_by_id(factura_id: int) -> Optional[Dict[str, Any]]:
        """Obtener una factura por ID"""
        factura = FacturaRepository.get_factura_by_id(factura_id)
        return factura.to_dict() if factura else None
    
    @staticmethod
    def get_all_facturas() -> List[Dict[str, Any]]:
        """Obtener todas las facturas"""
        facturas = FacturaRepository.get_all_facturas()
        return [factura.to_dict() for factura in facturas]
    
    @staticmethod
    def get_facturas_by_organizacion(organizacion: str) -> List[Dict[str, Any]]:
        """Obtener facturas por organización"""
        facturas = FacturaRepository.get_facturas_by_organizacion(organizacion)
        return [factura.to_dict() for factura in facturas]
    
    @staticmethod
    def delete_factura(factura_id: int) -> Dict[str, Any]:
        """Eliminar una factura y su archivo"""
        try:
            factura = FacturaRepository.get_factura_by_id(factura_id)
            if not factura:
                return {
                    'success': False,
                    'error': 'Factura no encontrada'
                }
            
            # Eliminar archivo del sistema de archivos
            try:
                if os.path.exists(factura.ruta_factura):
                    os.remove(factura.ruta_factura)
            except Exception as e:
                print(f"Error al eliminar archivo: {str(e)}")
            
            # Eliminar registro de la base de datos
            success = FacturaRepository.delete_factura(factura_id)
            
            if success:
                return {
                    'success': True,
                    'message': 'Factura eliminada exitosamente'
                }
            else:
                return {
                    'success': False,
                    'error': 'Error al eliminar la factura de la base de datos'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Error al eliminar la factura: {str(e)}'
            }
