from typing import List, Optional
from ..models.factura_model import Factura, db

class FacturaRepository:
    
    @staticmethod
    def create_factura(organizacion: str, ruta_factura: str) -> Factura:
        """Crear una nueva factura en la base de datos"""
        factura = Factura(
            organizacion=organizacion,
            ruta_factura=ruta_factura
        )
        db.session.add(factura)
        db.session.commit()
        return factura
    
    @staticmethod
    def get_factura_by_id(factura_id: int) -> Optional[Factura]:
        """Obtener una factura por su ID"""
        return Factura.query.get(factura_id)
    
    @staticmethod
    def get_all_facturas() -> List[Factura]:
        """Obtener todas las facturas"""
        return Factura.query.all()
    
    @staticmethod
    def get_facturas_by_organizacion(organizacion: str) -> List[Factura]:
        """Obtener facturas por organización"""
        return Factura.query.filter_by(organizacion=organizacion).all()
    
    @staticmethod
    def update_factura(factura_id: int, organizacion: str = None, ruta_factura: str = None) -> Optional[Factura]:
        """Actualizar una factura existente"""
        factura = FacturaRepository.get_factura_by_id(factura_id)
        if factura:
            if organizacion is not None:
                factura.organizacion = organizacion
            if ruta_factura is not None:
                factura.ruta_factura = ruta_factura
            db.session.commit()
        return factura
    
    @staticmethod
    def delete_factura(factura_id: int) -> bool:
        """Eliminar una factura"""
        factura = FacturaRepository.get_factura_by_id(factura_id)
        if factura:
            db.session.delete(factura)
            db.session.commit()
            return True
        return False
