# ffapp-backend

Este proyecto es un backend en Python para la aplicación ffapp.

## Requisitos

- Python 3.8 o superior
- pip
- (Opcional) Docker y Docker Compose

## Instalación

1. Clona el repositorio:

```bash
git clone https://github.com/ejcondorf88/ffapp-backend.git
cd ffapp-backend
```

2. Instala las dependencias:

```bash
pip install -r package/requeriments.txt
```

## Ejecución

### Modo local

Ejecuta la aplicación desde la carpeta `package`:

```bash
python run.py
```

### Usando Docker

1. Construye la imagen:

```bash
docker build -t ffapp-backend ./deploy/docker
```

2. Ejecuta el contenedor:

```bash
docker run -p 8000:8000 ffapp-backend
```

### Variables de entorno

Asegúrate de configurar las variables de entorno necesarias en un archivo `.env` o directamente en tu entorno.

## Estructura del proyecto

- `package/` Código fuente principal
- `deploy/` Archivos de despliegue (Docker, Kubernetes)
- `ci/` Integración continua

## Contacto

Para dudas o soporte, contacta a ejcondorf88.
