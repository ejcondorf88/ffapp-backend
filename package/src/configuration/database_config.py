import os

# Configuración simplificada para Supabase
class DatabaseConfig:
    """Configuración de la base de datos Supabase"""
    
    # Configuración de Supabase
    HOST = 'aws-1-us-east-1.pooler.supabase.com'
    PORT = 6543
    DATABASE = 'ffapp-bd'
    USERNAME = 'postgres.iodmqffuisrjjhfzpcwk'
    PASSWORD = 'Pigo0173!'
    DRIVER = 'postgresql'
    
    @classmethod
    def get_connection_string(cls):
        """Genera la cadena de conexión para SQLAlchemy"""
        return f"{cls.DRIVER}://{cls.USERNAME}:{cls.PASSWORD}@{cls.HOST}:{cls.PORT}/{cls.DATABASE}"
    
    @classmethod
    def get_config_dict(cls):
        """Retorna configuración como diccionario"""
        return {
            'SQLALCHEMY_DATABASE_URI': cls.get_connection_string(),
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
            'SECRET_KEY': 'hackathon-favorita-secret-key-2024',
            'MAX_CONTENT_LENGTH': 10 * 1024 * 1024  # 10MB
        }
